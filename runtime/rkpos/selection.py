"""الاستدعاء الديناميكي للوكلاء — يختار الحد الأدنى الكافي وفق عوامل المشروع."""
from __future__ import annotations

from . import registry as R
from .paths import ROOT

FACTORS = ["task_complexity", "research_type", "domain", "evidence_requirement", "risk", "deadline", "budget", "publication_target"]


def rules() -> dict:
    return R.load_yaml(ROOT / "validation/agent_selection_rules.yaml")


def _match(cond: dict, ctx: dict) -> bool:
    for k, v in cond.items():
        val = ctx.get(k)
        if isinstance(v, list):
            if val not in v:
                return False
        elif isinstance(v, bool):
            if bool(val) != v:
                return False
        elif val != v:
            return False
    return True


def select(ctx: dict) -> dict:
    """ctx: project_type, operating_model, domain, has_data, risk, evidence_requirement, ...
    يعيد {'agents': {type: [ids]}, 'rationale': [...]}"""
    rs = rules()
    A = R.agents()
    model = ctx.get("operating_model", "A")
    chosen: dict[str, str] = {}

    def add(aid, why):
        if aid not in A:
            raise KeyError(aid)
        if model not in A[aid]["operating_models"] and not A[aid].get("mvp"):
            # الوكيل غير متاح في هذا النموذج التشغيلي؛ تُنفَّذ وظيفته بمهارة داخل وكيل MVP
            sub = rs["model_substitutions"].get(aid)
            if sub:
                chosen.setdefault(sub, f"يغطي {aid} في النموذج {model}: {why}")
            return
        chosen.setdefault(aid, why)

    for aid in rs["always"][model]:
        add(aid, f"أساسي في النموذج {model}")
    for rule in rs["rules"]:
        if _match(rule["when"], ctx):
            for aid in rule["add"]:
                add(aid, rule["why"])
    out: dict[str, list[str]] = {}
    for aid in chosen:
        out.setdefault(A[aid]["type"], []).append(aid)
    return {"agents": out, "rationale": [f"{k}: {v}" for k, v in chosen.items()]}
