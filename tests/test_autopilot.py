"""الطيار الآلي: الوكلاء يمضون تباعاً، ويتوقفون عند قرار المؤلف بخيارات سريعة؛ والتسميات العربية كاملة."""
import glob

import pytest
import yaml

from test_book import FAKE, bk, _new  # noqa: F401 — المحرّك التجريبي وأداة التشغيل نفسها

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def _ap(bk, pid, *extra):
    return yaml.safe_load(bk("autopilot", pid, "--engine", "claude_code", *extra).stdout)


def test_every_workflow_task_has_arabic_label():
    labels = yaml.safe_load((REPO_ROOT / "config/labels_ar.yaml").read_text(encoding="utf-8"))
    tasks = {s["task"] for f in glob.glob(str(REPO_ROOT / "workflows/*.yaml"))
             for s in yaml.safe_load(open(f, encoding="utf-8"))["steps"] if "task" in s}
    assert not tasks - set(labels["tasks"])
    states = yaml.safe_load((REPO_ROOT / "schemas/state.schema.json").read_text(encoding="utf-8"))["properties"]["STATE"]["enum"]
    assert not set(states) - set(labels["states"])


def test_op_ed_runs_to_completion_with_quick_choices(bk):
    pid, _ = _new(bk, "عمود", "--type", "op_ed")
    r = _ap(bk, pid)
    assert r["question"] == "المسودة الكاملة جاهزة للمراجعة"
    assert set(r["choices"]) == {"review", "align_flagged", "approve_all"}
    r = _ap(bk, pid, "--answer", "approve_all")                    # يكمل التدقيق والتحرير آلياً حتى اعتماد المؤلف
    assert r["question"] == "اعتماد «طلب اعتماد المؤلف»"
    assert bk("autopilot", pid, "--answer", "approve_note", ok=False).returncode != 0   # الخيار يحتاج ملاحظة
    r = _ap(bk, pid, "--answer", "approve")
    assert r["status"] == "done"
    plan = yaml.safe_load((bk.root / "projects" / pid / "plan.yaml").read_text(encoding="utf-8"))
    assert all(s["status"] in ("DONE", "SKIPPED") for s in plan["steps"])
    dec = yaml.safe_load((bk.root / "projects" / pid / "decisions.yaml").read_text(encoding="utf-8"))["decisions"]
    assert any(d["approved_by"] == "HUMAN-AUTHOR" and "اعتمد وتابع" in d["decision"] for d in dec)
    # المدقق رأى نص العمود نفسه لا أسماء الملفات
    s03 = (bk.root / "projects" / pid / "runs/S03/prompt.md").read_text(encoding="utf-8")
    assert "المسودة المجمّعة للعمل" in s03


def test_staged_book_asks_per_unit_and_pauses(bk):
    pid, _ = _new(bk, "دراسة", "--type", "policy_study", "--level", "staged", "--pages", "8")
    r = _ap(bk, pid)
    assert r["question"] == "اعتماد «تحديد مشكلة السياسة»"            # L4 بعد تنفيذ الوكيل
    r = _ap(bk, pid, "--answer", "approve")
    while r.get("question", "").startswith("اعتماد «") and "الوحدة" not in r["question"] and "مخطط" not in r["question"]:
        r = _ap(bk, pid, "--answer", "approve")
    assert r["question"] == "اعتماد مخطط العمل"
    r = _ap(bk, pid, "--answer", "approve")
    assert r["question"].startswith("اعتماد الوحدة «U00")
    r = _ap(bk, pid, "--answer", "approve")
    assert r["question"].startswith("اعتماد الوحدة «U01")             # التدرّج: وحدة بعد اعتماد سابقتها
    r = _ap(bk, pid, "--answer", "review")
    assert r["status"] == "paused" or r.get("question")
    st = yaml.safe_load((bk.root / "projects" / pid / "autopilot.yaml").read_text(encoding="utf-8"))
    assert st["status"] in ("paused", "waiting")


def test_project_types_get_their_own_workflow_not_a_subworkflow():
    import sys
    sys.path.insert(0, str(REPO_ROOT / "runtime"))
    from rkpos import workflow as WF, registry as R
    sub = {st["uses"] for w in R.workflows().values() for st in w["steps"] if "uses" in st}
    expect = {"policy_study": "WF-POLICY-STUDY", "strategic_report": "WF-STRATEGIC-REPORT", "foresight_study": "WF-FORESIGHT",
              "journal_article": "WF-JOURNAL-ARTICLE", "re_edition": "WF-REEDITION", "novel": "WF-NOVEL"}
    for t, w in expect.items():
        assert WF.workflow_for(t) == w and w not in sub
