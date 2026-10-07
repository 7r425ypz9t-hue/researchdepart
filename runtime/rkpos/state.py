"""حالة المشروع — STATE / NEXT_ACTION / CURRENT_AGENT / WAITING_FOR / BLOCKERS / VERSION / QUALITY_GATE.
تضمن الاستئناف دون إعادة بناء السياق (القسم 54 + project-runtime-protocol-ar)."""
from __future__ import annotations
from pathlib import Path

import yaml

from . import registry as R
from .ids import now_iso
from .paths import PROJECTS


def path(pid: str) -> Path:
    return PROJECTS / pid / "state.yaml"


def load(pid: str) -> dict:
    return yaml.safe_load(path(pid).read_text(encoding="utf-8"))


def save(pid: str, st: dict) -> None:
    st["UPDATED"] = now_iso()
    errs = R.validate(st, "state")
    if errs:
        raise ValueError(f"invalid state: {errs}")
    path(pid).write_text(yaml.safe_dump(st, allow_unicode=True, sort_keys=False), encoding="utf-8")


def plan(pid: str) -> dict:
    return yaml.safe_load((PROJECTS / pid / "plan.yaml").read_text(encoding="utf-8"))


def save_plan(pid: str, p: dict) -> None:
    (PROJECTS / pid / "plan.yaml").write_text(yaml.safe_dump(p, allow_unicode=True, sort_keys=False), encoding="utf-8")


def next_step(p: dict) -> dict | None:
    for s in p["steps"]:
        if s["status"] in ("PENDING", "CONDITIONAL", "IN_PROGRESS", "IN_REVIEW", "AWAITING_AUTHOR", "REJECTED"):
            return s
    return None


STAGE_BY_AGENT = {
    "AG-RQA": "SCOPING", "AG-DIR": "SCOPING", "AG-DSC": "DISCOVERY", "AG-SRC": "EVIDENCE", "AG-LRV": "EVIDENCE",
    "AG-THR": "THEORY_METHOD", "AG-MTH": "THEORY_METHOD", "AG-POL": "ANALYSIS", "AG-DAT": "ANALYSIS",
    "AG-BKA": "ARCHITECTURE", "AG-WRT": "DRAFTING", "AG-TRN": "DRAFTING", "AG-TAH": "EVIDENCE", "AG-EVA": "AUDIT",
    "AG-RED": "RED_TEAM", "AG-PRV": "RED_TEAM", "AG-SED": "REVISION", "AG-ARE": "LANGUAGE_EDIT",
    "AG-INT": "INTEGRITY", "AG-SUP-INT": "INTEGRITY", "AG-SUP-EDT": "LANGUAGE_EDIT", "AG-VIS": "PRODUCTION",
    "AG-PUB": "PRODUCTION", "AG-SUP-PUB": "ARCHIVING", "AG-KNW": "ARCHIVING", "AG-VCS": "ARCHIVING",
}


def refresh(pid: str) -> dict:
    """يعيد احتساب الحالة من الخطة."""
    st, p = load(pid), plan(pid)
    total = len([s for s in p["steps"] if s["status"] != "SKIPPED"]) or 1
    done = len([s for s in p["steps"] if s["status"] == "DONE"])
    nx = next_step(p)
    st["COMPLETION_PCT"] = round(100 * done / total, 1)
    from . import cost
    st["COST_USD"] = cost.report(pid)["total_usd"]
    if nx:
        st["STATE"] = "AWAITING_AUTHOR" if nx["status"] == "AWAITING_AUTHOR" else STAGE_BY_AGENT.get(nx.get("agent"), st["STATE"])
        st["STAGE_ID"] = nx["id"]
        st["CURRENT_AGENT"] = nx.get("agent", "AG-ORC")
        st["NEXT_ACTION"] = f"{nx['id']}: {nx.get('agent')} → {nx.get('task')}"
        st["WAITING_FOR"] = "HUMAN-AUTHOR" if nx["status"] == "AWAITING_AUTHOR" else nx.get("agent")
        if nx.get("gate"):
            st["QUALITY_GATE"] = {"current": nx["gate"], "status": "PENDING"}
    else:
        st["STATE"], st["NEXT_ACTION"], st["WAITING_FOR"], st["CURRENT_AGENT"] = "CLOSED", "—", None, "AG-ORC"
    st["PENDING_HUMAN_DECISIONS"] = [f"{s['id']}: {s.get('task')}" for s in p["steps"] if s["status"] == "AWAITING_AUTHOR"]
    save(pid, st)
    return st
