"""سلامة المنظومة: كل إحالة صحيحة، والصلاحيات تحترم Least Privilege، والملفات المولدة متزامنة."""
from rkpos import registry as R, generate, evals


def test_system_integrity():
    assert R.check_integrity() == []


def test_generated_files_in_sync():
    assert generate.write(check=True) == [], "run `rkpos generate`"


def test_agent_count_controls_inflation():
    A = R.agents()
    assert 25 <= len(A) <= 40, "تجنب التضخم: السجل يجب أن يبقى مدمجاً"


def test_mvp_is_exactly_eight():
    mvp = sorted(a for a, x in R.agents().items() if x["mvp"])
    assert mvp == sorted(["AG-ORC", "AG-DSC", "AG-SRC", "AG-WRT", "AG-SED", "AG-INT", "AG-PUB", "AG-KNW"])


def test_no_agent_writes_institutional_or_author_memory():
    for aid, a in R.agents().items():
        assert "MEM-INSTITUTIONAL" not in a["memory"]["write"], aid
        assert "MEM-AUTHOR" not in a["memory"]["write"], aid


def test_orchestrator_cannot_change_content():
    o = R.agents()["AG-ORC"]
    assert not {"ST-DRAFT", "ST-EDITED", "ST-APPROVED"} & set(o["memory"]["write"])
    assert any("المخطوط" in p for p in o["permissions"]["prohibited"])


def test_reviewers_independent_tier():
    A = R.agents()
    for aid in ("AG-RED", "AG-PRV", "AG-EVA", "AG-SUP-MTH", "AG-SUP-EVD", "AG-SUP-EDT", "AG-SUP-INT"):
        assert A[aid]["model_tier"] == "T4-independent", aid


def test_every_skill_used_and_every_tool_used():
    A = R.agents()
    used_s = {s for a in A.values() for s in a["skills"]}
    used_t = {t for a in A.values() for t in a["tools"]}
    assert set(R.skills()) - used_s == set(), "مهارات يتيمة"
    assert set(R.tools()) - used_t == set(), "أدوات يتيمة"


def test_eval_suites_structurally_valid():
    errs = [e for a in R.agents() for e in evals.offline_check(a)]
    assert errs == []


def test_system_prompts_are_specific():
    """لا System Prompt عام: كل برومبت يحمل مهمة وكيله ولا يتطابق برومبتان."""
    from rkpos.runner import compose_system_prompt
    prompts = {a: compose_system_prompt(a) for a in R.agents()}
    assert len(set(prompts.values())) == len(prompts)
    for aid, p in prompts.items():
        for section in ("SYSTEM ROLE", "MISSION", "AUTHORIZED TASKS", "PROHIBITED TASKS", "TOOLS", "MEMORY POLICY",
                        "SOURCE POLICY", "QUALITY STANDARD", "HANDOFF RULES", "ESCALATION RULES", "OUTPUT CONTRACT",
                        "STOP CONDITIONS", "DECISION LOGGING", "CONSULTATION"):
            assert section in p, (aid, section)
        assert aid in p
        assert "Zero Fabrication" in p  # الدستور ملحق


def test_every_workflow_requested_exists():
    W = R.workflows()
    for wid in ["WF-BOOK-INTELLECTUAL", "WF-BOOK-ACADEMIC", "WF-POLICY-STUDY", "WF-SYSTEMATIC-REVIEW", "WF-LIT-REVIEW",
                "WF-FORESIGHT", "WF-CRITICAL-EDITION", "WF-JOURNAL-ARTICLE", "WF-OPED", "WF-STRATEGIC-REPORT",
                "WF-TRANSLATION", "WF-REEDITION", "WF-BOOK-PRODUCTION"]:
        assert wid in W
