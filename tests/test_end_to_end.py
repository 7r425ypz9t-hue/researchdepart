"""السيناريو المرجعي (القسم 60): «ابدأ مشروع كتاب عن حوكمة الذكاء الاصطناعي في القطاع الثقافي»."""
import json

import yaml


def test_book_project_lifecycle(sandbox):
    r = sandbox("new-project", "حوكمة الذكاء الاصطناعي في القطاع الثقافي", "--type", "intellectual_book",
                "--domain", "cultural_governance", "--model", "B")
    out = yaml.safe_load(r.stdout)
    pid = out["project_id"]
    assert pid.startswith("RKP-") and out["workflow"] == "WF-BOOK-INTELLECTUAL"
    root = sandbox.root / "projects" / pid
    for f in ("manifest.yaml", "state.yaml", "plan.yaml", "decisions.yaml", "CHANGELOG.md"):
        assert (root / f).exists()
    assert (root / "manuscript/approved").is_dir()

    # الخطوة التالية: S02 بواسطة AG-RQA، حزمة برومبت يدوية
    sandbox("run-step", pid)
    prompt = (root / "runs/S02/prompt.md").read_text(encoding="utf-8")
    assert "AG-RQA" in prompt and "HANDOFF_ID" in prompt and "CONSTITUTION" in prompt

    # المنسق لا يعتمد L4
    bad = sandbox("complete", pid, "S02", "--actor", "AG-ORC", ok=False)
    assert bad.returncode != 0 and "HUMAN-AUTHOR" in bad.stderr
    sandbox("complete", pid, "S02", "--actor", "HUMAN-AUTHOR", "--decision", "اعتماد الإشكالية")
    st = yaml.safe_load((root / "state.yaml").read_text(encoding="utf-8"))
    assert "DC-001" in st["PINNED_DECISIONS"] and st["STAGE_ID"] != "S02"
    assert st["QUALITY_GATE"]["current"] in ("QG0", "QG1")

    audit = [json.loads(l) for l in (sandbox.root / "logs/audit.jsonl").read_text(encoding="utf-8").splitlines()]
    assert any(a["DECISION"] == "DC-001" and a["APPROVAL"] == "HUMAN-AUTHOR" for a in audit)

    sandbox("dashboard")
    html = (sandbox.root / "publishing/dashboard/index.html").read_text(encoding="utf-8")
    assert pid in html and "#1F4E79" in html


def test_check_manuscript_exit_codes(sandbox):
    pid = yaml.safe_load(sandbox("new-project", "مقال", "--type", "op_ed").stdout)["project_id"]
    f = sandbox.root / "draft.md"
    f.write_text("[FACT] واقعة بلا مصدر.", encoding="utf-8")
    r = sandbox("check-manuscript", pid, str(f), ok=False)
    assert r.returncode == 2
