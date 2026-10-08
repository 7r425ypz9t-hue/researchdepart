"""الأجناس ومستويات الإنتاج ومحرّك بناء العمل (المخطط ← الوحدات ← الصوت ← الاعتماد ← التجميع)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]

FAKE = """#!{py}
import json, sys
args = sys.argv[1:]
user = sys.stdin.read()
n = 0
for tok in user.split():
    if tok.isdigit():
        n = int(tok)
if "units:" in user and "اقترح مخطط" in user:
    out = "```yaml\\nunits:\\n  - {{title: المقدمة, kind: introduction, brief: تمهيد}}\\n  - {{title: محور الهوية, kind: axis, brief: أ}}\\n  - {{title: الخاتمة, kind: conclusion, brief: ب}}\\n```\\nتعليل."
else:
    body = " ".join(["كلمة"] * 120)
    out = "===BEGIN_TEXT===\\n" + body + "\\n===END_TEXT===\\nNOTES: لا شيء"
print(json.dumps({{"type": "result", "is_error": False, "stop_reason": "end_turn", "result": out,
                  "total_cost_usd": 0.01, "usage": {{"input_tokens": 1, "output_tokens": 1}}, "modelUsage": {{"m": {{}}}}}}))
"""


@pytest.fixture
def bk(sandbox, tmp_path):
    fake = tmp_path / "fake_claude"
    fake.write_text(FAKE.format(py=sys.executable), encoding="utf-8")
    fake.chmod(0o755)
    root = sandbox.root
    env = {**os.environ, "RKPOS_ROOT": str(root), "PYTHONPATH": str(REPO / "runtime"), "RKPOS_CLAUDE_BIN": str(fake)}

    def run(*args, ok=True):
        r = subprocess.run([sys.executable, "-m", "rkpos", *args], cwd=root, env=env, capture_output=True, text=True)
        if ok and r.returncode != 0:
            raise AssertionError(f"rkpos {args}:\n{r.stdout}\n{r.stderr}")
        return r
    run.root = root
    return run


def _new(bk, *args):
    out = yaml.safe_load(bk("new-project", *args).stdout)
    return out["project_id"], out


def _ob(bk, pid):
    return yaml.safe_load((bk.root / "projects" / pid / "structure/outline.yaml").read_text(encoding="utf-8"))


def test_genre_derivation_and_manifest(bk):
    pid, out = _new(bk, "رواية تجريبية", "--type", "novel", "--level", "full", "--pages", "4")
    assert out["genre"] == "creative" and out["workflow"] == "WF-NOVEL"
    assert out["production"] == {"level": "full", "target_pages": 4, "words_per_page": 250, "target_words": 1000}
    assert "AG-NOV" in out["agents"]["specialist"]
    m = yaml.safe_load((bk.root / "projects" / pid / "manifest.yaml").read_text(encoding="utf-8"))
    assert m["citation_style"] == "none"
    _, op = _new(bk, "عمود", "--type", "op_ed")
    assert op["genre"] == "op_ed" and op["production"]["target_words"] == 300 and op["production"]["level"] == "full"
    r = bk("new-project", "عمود", "--type", "op_ed", "--level", "staged", ok=False)
    assert r.returncode != 0  # عمود الرأي لا يُبنى تدرّجياً


def test_genre_profile_reaches_prompt(bk):
    pid, _ = _new(bk, "رواية", "--type", "novel")
    r = bk("activate", "AG-NOV", "اكتب مشهداً", "--project", pid)
    run = next((bk.root / "projects" / pid / "runs").glob("ADH-*"))
    p = (run / "prompt.md").read_text(encoding="utf-8")
    assert "GENRE PROFILE — الإبداع الروائي والسردي" in p and "GENRE: creative" in p


def test_staged_sequence_and_author_approval(bk):
    pid, _ = _new(bk, "كتاب فكري", "--type", "intellectual_book", "--level", "staged", "--pages", "40")
    ob = yaml.safe_load(bk("book", pid, "skeleton", "--n", "2").stdout)
    assert [u["id"] for u in ob["units"]] == ["U00", "U01", "U02", "U03"]
    assert abs(sum(u["target_words"] for u in ob["units"]) - 10000) <= 40
    assert bk("book", pid, "draft", "U00", "--engine", "claude_code", ok=False).returncode != 0   # المخطط غير معتمد
    assert bk("book", pid, "approve-outline", "--actor", "AG-ORC", ok=False).returncode != 0      # L4 للمؤلف
    bk("book", pid, "approve-outline", "--actor", "HUMAN-AUTHOR")
    bk("book", pid, "draft", "U00", "--engine", "claude_code")
    r = bk("book", pid, "draft", "U01", "--engine", "claude_code", ok=False)                      # التدرّج: اعتماد U00 أولاً
    assert r.returncode != 0 and "U00" in r.stderr
    edited = bk.root / "edited.md"
    edited.write_text(" ".join(["نص"] * 60 + ["كلمة"] * 60), encoding="utf-8")
    out = yaml.safe_load(bk("book", pid, "approve", "U00", "--actor", "HUMAN-AUTHOR", "--file", str(edited)).stdout)
    assert 0 < out["author_change"] <= 1                                                         # يُرصد تدخل المؤلف
    bk("book", pid, "draft", "U01", "--engine", "claude_code")
    assert _ob(bk, pid)["units"][1]["status"] == "DRAFTED"
    assert (bk.root / "projects" / pid / "manuscript/drafts/U01.ai.md").exists()


def test_full_book_in_one_run_then_assemble(bk):
    pid, _ = _new(bk, "دراسة", "--type", "policy_study", "--level", "full", "--pages", "8")
    r = yaml.safe_load(bk("book", pid, "propose-outline", "--engine", "claude_code").stdout)
    assert [u["title"] for u in r["outline"]["units"]] == ["المقدمة", "محور الهوية", "الخاتمة"]
    est = yaml.safe_load(bk("book", pid, "estimate").stdout)
    assert est["units"] == 3 and est["pages"] == 8
    bk("book", pid, "approve-outline", "--actor", "HUMAN-AUTHOR")
    out = yaml.safe_load(bk("book", pid, "draft-all", "--engine", "claude_code").stdout.split("\n", 4)[-1])
    ob = _ob(bk, pid)
    assert all(u["status"] == "DRAFTED" for u in ob["units"])
    book = bk.root / "projects" / pid / "manuscript/book_full.md"
    assert book.exists() and "## محور الهوية" in book.read_text(encoding="utf-8")
    rep = yaml.safe_load(bk("book", pid, "voice").stdout)
    assert rep["total_words"] > 0 and len(rep["units"]) == 3


def test_scaffold_level_writes_cards_not_text(bk):
    pid, _ = _new(bk, "بحث", "--type", "journal_article", "--level", "scaffold", "--pages", "20")
    bk("book", pid, "skeleton", "--n", "1")
    bk("book", pid, "approve-outline", "--actor", "HUMAN-AUTHOR")
    bk("book", pid, "draft", "U01", "--engine", "claude_code")          # المستوى الحر: لا تسلسل
    d = bk.root / "projects" / pid / "manuscript/drafts"
    assert (d / "U01.card.md").exists() and not (d / "U01.md").exists()
    assert _ob(bk, pid)["units"][1]["status"] == "CARDED"
    assert bk("book", pid, "draft-all", "--engine", "claude_code", ok=False).returncode != 0      # الكامل للمستوى الكامل
