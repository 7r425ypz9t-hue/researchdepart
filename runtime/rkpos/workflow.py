"""تحميل سير العمل وتوسيعه إلى خطة تنفيذ مخصصة للمشروع."""
from __future__ import annotations
from types import SimpleNamespace

from . import registry as R


class _Obj(SimpleNamespace):
    def __getattr__(self, item):  # الحقول غير المعروفة = None
        return None


class _Unknown(Exception):
    pass


def _ns(d: dict) -> _Obj:
    return _Obj(**{k: (_ns(v) if isinstance(v, dict) else v) for k, v in d.items()})


def eval_condition(expr: str, ctx: dict):
    """يقيّم optional_if على سياق المشروع.
    يعيد True/False، أو None إن اعتمد الشرط على بيانات وقت التشغيل (مثل chapter.*).
    ملاحظة: التعابير مصدرها ملفات سير العمل الموثوقة في المستودع؛ التقييم معزول عن builtins."""
    names = {"project": _ns(ctx.get("project", {}))}
    for k in ("chapter", "article", "outline", "review", "dispute", "recommendation", "revision_map"):
        names[k] = _ns(ctx[k]) if k in ctx else None
    for k in ("skill_found", "existing_agent_found"):
        names[k] = ctx.get(k)
    try:
        if any(f"{k}." in expr or expr.strip() in (k, f"not {k}") for k, v in names.items() if v is None):
            return None
        return bool(eval(expr, {"__builtins__": {}}, names))  # noqa: S307 — trusted repo expressions only
    except Exception:
        return None


def expand(workflow_id: str, ctx: dict, _depth: int = 0) -> list[dict]:
    if _depth > 3:
        raise RecursionError("workflow nesting too deep")
    W = R.workflows()
    steps = []
    for st in W[workflow_id]["steps"]:
        st = dict(st)
        st["workflow"] = workflow_id
        if "uses" in st:
            sub = expand(st["uses"], ctx, _depth + 1)
            for s in sub:
                s["id"] = f"{st['id']}.{s['id']}"
                if "foreach" in st:
                    s["foreach"] = st["foreach"]
            steps.extend(sub)
            continue
        cond = st.get("optional_if")
        if cond:
            r = eval_condition(cond, ctx)
            st["status"] = "SKIPPED" if r is True else ("CONDITIONAL" if r is None else "PENDING")
        else:
            st["status"] = "PENDING"
        steps.append(st)
    return steps


def workflow_for(project_type: str) -> str:
    for wid, w in R.workflows().items():
        if project_type in w.get("project_types", []) and wid not in ("WF-BOOK-PRODUCTION",):
            return wid
    return "WF-BOOK-PRODUCTION"
