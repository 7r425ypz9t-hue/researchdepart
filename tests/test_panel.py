"""لوحة التحكم ومحرّك Claude Code: الأمان (الرمز والمضيف)، الحوكمة (إقرار L4)، ومسار التشغيل كاملاً."""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

FAKE_CLAUDE = """#!{py}
import json, sys
args = sys.argv[1:]
system = open(args[args.index("--system-prompt-file") + 1], encoding="utf-8").read()
user = sys.stdin.read()
assert "--tools" in args and args[args.index("--tools") + 1] == ""
print(json.dumps({{"type": "result", "is_error": False, "stop_reason": "end_turn",
                  "result": "RESULT من المحرّك التجريبي | system=%d | user=%d" % (len(system), len(user)),
                  "total_cost_usd": 0.0123, "usage": {{"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 7}},
                  "modelUsage": {{"claude-test-model": {{}}}}}}))
"""


@pytest.fixture
def fake_claude(tmp_path):
    p = tmp_path / "fake_claude"
    p.write_text(FAKE_CLAUDE.format(py=sys.executable), encoding="utf-8")
    p.chmod(0o755)
    return p


def test_claude_code_adapter_passes_system_prompt_by_file(fake_claude, monkeypatch):
    sys.path.insert(0, str(REPO / "runtime"))
    from rkpos.adapters.claude_code_adapter import ClaudeCodeAdapter
    monkeypatch.setenv("RKPOS_CLAUDE_BIN", str(fake_claude))
    ad = ClaudeCodeAdapter("claude-sonnet-5-5")
    assert ad.available()
    c = ad.complete("نظام " * 5000, "مهمة")
    assert "system=" in c.text and c.model == "claude_code:claude-test-model"
    assert c.input_tokens == 15 and c.output_tokens == 7 and c.raw["total_cost_usd"] == 0.0123


def test_router_engine_and_independence(fake_claude, monkeypatch):
    sys.path.insert(0, str(REPO / "runtime"))
    from rkpos.adapters import router
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "LOCAL_LLM_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RKPOS_CLAUDE_BIN", str(fake_claude))
    ad, _ = router.resolve("AG-WRT", engine="claude_code")
    assert ad.provider == "claude_code" and ad.model == "claude-opus-5-5"
    ad, _ = router.resolve("AG-WRT", engine="auto")          # لا مفاتيح ← Claude Code قبل اليدوي
    assert ad.provider == "claude_code"
    ad, w = router.resolve("AG-WRT", engine="api")           # مفاتيح فقط ← يدوي
    assert ad.provider == "manual"
    ad, _ = router.resolve("AG-WRT", engine="manual")
    assert ad.provider == "manual"
    # المراجع T4 لا يُعدّ Claude Code مستقلاً عن كاتب Anthropic
    ad, w = router.resolve("AG-SUP-INT", author_model="claude_code:claude-opus-5-5", engine="claude_code")
    assert any("INDEPENDENCE_DEGRADED" in x for x in w)


@pytest.fixture
def panel(sandbox, fake_claude, tmp_path):
    root = sandbox.root
    state = tmp_path / "panel.json"
    env = {**os.environ, "RKPOS_ROOT": str(root), "PYTHONPATH": str(REPO / "runtime"), "RKPOS_PANEL_STATE": str(state),
           "RKPOS_CLAUDE_BIN": str(fake_claude)}
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"):
        env.pop(k, None)
    proc = subprocess.Popen([sys.executable, "-m", "rkpos", "panel", "--no-browser", "--new"], cwd=root, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(100):
        if state.exists():
            break
        time.sleep(0.1)
    st = json.loads(state.read_text())

    def call(name, body=None, token=st["token"], host=None, q=""):
        url = f"http://127.0.0.1:{st['port']}/api/{name}{q}"
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, headers={"X-Rkpos-Token": token, "Content-Type": "application/json"})
        if host:
            req.add_header("Host", host)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
    call.root = root
    yield call
    proc.terminate()
    proc.wait(timeout=10)


def test_panel_security(panel):
    assert panel("ping", token="wrong")[0] == 401
    assert panel("ping", host="evil.example")[0] == 403
    code, r = panel("file", q="?path=../pyproject.toml")
    assert code == 400 and not r["ok"]
    code, r = panel("engines")
    assert r["data"]["claude_code"] is True and "ANTHROPIC_API_KEY" in r["data"]["api_keys"]
    assert all(v in (True, False) for v in r["data"]["api_keys"].values())  # لا تُعرض قيم المفاتيح


def test_panel_full_project_cycle(panel):
    code, r = panel("new_project", {"title": "عمود تجريبي", "type": "op_ed"})
    assert code == 200, r
    pid = r["data"]["project_id"]
    # S01 يدوياً: حزمة برومبت
    code, r = panel("run_step", {"project": pid, "engine": "manual"})
    assert r["data"]["kind"] == "prompt.md" and "AG-ORC" in r["data"]["text"]
    assert panel("record_output", {"project": pid, "step": "S01", "text": "RESULT يدوي"})[0] == 200
    assert panel("complete", {"project": pid, "step": "S01", "actor": "AG-ORC"})[0] == 200
    # S02 عبر محرّك Claude Code (التجريبي)
    code, r = panel("run_step", {"project": pid, "engine": "claude_code"})
    assert r["data"]["kind"] == "output.md" and "المحرّك التجريبي" in r["data"]["text"]
    code, r = panel("cost", q=f"?project={pid}")
    assert r["data"]["total_usd"] == pytest.approx(0.0123)
    # فحص المخرج من اللوحة
    code, r = panel("check_text", {"text": "[AUTHOR] نص قصير للفحص، فيه جملة واحدة.", "project": pid})
    assert code == 200 and "claims" in r["data"]
    for s in ("S02", "S03", "S04"):
        panel("complete", {"project": pid, "step": s, "actor": "AG-ORC"})
    # S05 L4: مهمة للمؤلف، ولا يُغلق بلا إقرار
    code, r = panel("run_step", {"project": pid, "engine": "claude_code"})
    assert r["data"]["kind"] == "author_task.md"
    code, r = panel("complete", {"project": pid, "step": "S05", "actor": "HUMAN-AUTHOR", "decision": "اعتماد"})
    assert code == 400 and "L4" in r["error"]
    code, r = panel("complete", {"project": pid, "step": "S05", "actor": "AG-ORC", "confirm_author": True})
    assert code == 400 and "HUMAN-AUTHOR" in r["error"]
    code, r = panel("complete", {"project": pid, "step": "S05", "actor": "HUMAN-AUTHOR", "decision": "اعتماد",
                                 "approved_text": "النص المعتمد", "approved_name": "final.md", "confirm_author": True})
    assert code == 200 and r["data"]["decision"]["approved_by"] == "HUMAN-AUTHOR"
    assert (panel.root / "projects" / pid / "manuscript/approved/final.md").read_text(encoding="utf-8") == "النص المعتمد"


def test_panel_adhoc_and_memory_governance(panel):
    code, r = panel("adhoc", {"agent": "AG-WRT", "task": "اقترح عنواناً", "register": "essay", "engine": "manual"})
    assert code == 200 and r["data"]["output"] is None and "TO: AG-WRT" in r["data"]["user"]
    assert r["data"]["dir"].startswith("workspace/adhoc/")
    code, r = panel("adhoc", {"agent": "AG-SRC", "task": "تحقق من مصدر", "engine": "claude_code"})
    assert "المحرّك التجريبي" in r["data"]["output"]
    code, r = panel("adhoc", {"agent": "AG-NOPE", "task": "x"})
    assert code == 400
    # الترقية إلى الذاكرة المؤسسية تتطلب إقرار المؤلف
    sys.path.insert(0, str(REPO / "runtime"))
    cand = {"Memory_ID": "MEM-LESSON-009999", "Type": "lesson", "Project": None, "Created_By": "AG-KNW",
            "Created_Date": "2026-10-07", "Confidence": "HIGH", "Source": "test", "Version": 1, "Access_Level": "INTERNAL",
            "Expiry": None, "Content": "درس تجريبي", "Tags": [], "Layer": "ST-KB-CANDIDATES", "Verified": False, "Approved_By": None}
    f = panel.root / "knowledge-base/candidates/candidates.jsonl"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(cand, ensure_ascii=False) + "\n", encoding="utf-8")
    ids = lambda: {c["Memory_ID"] for c in panel("candidates")[1]["data"]["items"]}  # noqa: E731
    assert "MEM-LESSON-009999" in ids()
    code, r = panel("promote", {"memory_id": "MEM-LESSON-009999", "layer": "MEM-INSTITUTIONAL"})
    assert code == 400
    code, r = panel("promote", {"memory_id": "MEM-LESSON-009999", "layer": "MEM-INSTITUTIONAL", "confirm_author": True})
    assert code == 200 and r["data"]["Approved_By"] == "HUMAN-AUTHOR"
    assert "MEM-LESSON-009999" not in ids()
    assert panel("memory")[1]["data"]["layers"]["MEM-INSTITUTIONAL"]["count"] == 1


def test_panel_book_production(panel):
    code, r = panel("new_project", {"title": "رواية", "type": "novel", "genre": "creative", "level": "full", "pages": 4})
    assert code == 200, r
    pid = r["data"]["project_id"]
    assert panel("genres")[1]["data"]["genres"]["creative"]["lead_agent"] == "AG-NOV"
    assert panel("book_skeleton", {"project": pid, "n": 2})[0] == 200
    assert panel("book_approve_outline", {"project": pid})[0] == 400                       # بلا إقرار المؤلف
    assert panel("book_draft_all", {"project": pid, "engine": "claude_code", "confirm_cost": True})[0] == 400  # المخطط غير معتمد
    assert panel("book_approve_outline", {"project": pid, "confirm_author": True})[0] == 200
    assert panel("book_draft_all", {"project": pid, "engine": "claude_code"})[0] == 400     # بلا إقرار الكلفة
    code, job = panel("book_draft_all", {"project": pid, "engine": "claude_code", "confirm_cost": True})
    assert code == 200
    for _ in range(100):
        j = panel("job", q=f"?id={job['data']['id']}")[1]["data"]
        if j["state"] != "running":
            break
        time.sleep(0.2)
    assert j["state"] == "done", j
    b = panel("book", q=f"?id={pid}")[1]["data"]
    assert all(u["status"] == "DRAFTED" for u in b["outline"]["units"]) and b["book"]
    assert panel("book_approve_unit", {"project": pid, "unit": "U01", "text": "نص المؤلف"})[0] == 400
    code, r = panel("book_approve_unit", {"project": pid, "unit": "U01", "text": "نص المؤلف", "confirm_author": True})
    assert code == 200 and r["data"]["author_change"] > 0.5


def test_claude_code_not_logged_in_is_explained(tmp_path, monkeypatch):
    sys.path.insert(0, str(REPO / "runtime"))
    from rkpos.adapters import claude_code_adapter as CC
    fake = tmp_path / "claude_logged_out"
    fake.write_text(f"""#!{sys.executable}
import json, sys
if sys.argv[1:3] == ["auth", "status"]:
    print(json.dumps({{"loggedIn": False}})); sys.exit(1)
sys.stdin.read()
print(json.dumps({{"type": "result", "is_error": True, "result": "Not logged in · Please run /login"}}))
sys.exit(1)
""", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("RKPOS_CLAUDE_BIN", str(fake))
    assert CC.auth_status() == {"loggedIn": False}
    with pytest.raises(CC.AdapterUnavailable) as e:
        CC.ClaudeCodeAdapter("claude-sonnet-5-5").complete("s", "u")
    assert "claude auth login" in str(e.value) and "الإعدادات" in str(e.value)
