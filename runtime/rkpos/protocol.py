"""بروتوكول التواصل بين الوكلاء وحزم التسليم.

يرفض: الأنواع غير المعرّفة، التسليم بلا سياق، المراسلة خارج handoffs المصرّح بها.
"""
from __future__ import annotations
import json
from pathlib import Path

from . import registry as R
from .ids import short_id, now_iso
from .paths import PROJECTS

MESSAGE_TYPES = {"TASK", "RESULT", "REVIEW", "REQUEST", "CHALLENGE", "CORRECTION", "ESCALATION", "APPROVAL", "REJECT"}


class ProtocolError(ValueError):
    pass


def route_allowed(frm: str, to: str) -> bool:
    """هل يحق لـ frm إرسال عمل إلى to؟ (المنسق والبشر والمجلس دائماً مسموحون)."""
    if frm in ("AG-ORC", "HUMAN-AUTHOR", "AG-COUNCIL") or to in ("AG-ORC", "HUMAN-AUTHOR"):
        return True
    A = R.agents()
    if frm not in A:
        return False
    a = A[frm]
    allowed = set(a["handoffs"]["sends_to"]) | {c["agent"] for c in a["consult"]} | {e["to"] for e in a["escalation"]}
    return to in allowed or "ALL" in allowed


def message(project_id, type_, frm, to, subject, content, action_required, evidence=None,
            in_reply_to=None, handoff_id=None, decision_level=None) -> dict:
    msg = {"MESSAGE_ID": short_id("MSG"), "PROJECT_ID": project_id, "TYPE": type_, "FROM": frm, "TO": to,
           "TIMESTAMP": now_iso(), "SUBJECT": subject, "CONTENT": content, "EVIDENCE": list(evidence or []),
           "ACTION_REQUIRED": action_required, "IN_REPLY_TO": in_reply_to, "HANDOFF_ID": handoff_id,
           "DECISION_LEVEL": decision_level}
    errs = R.validate(msg, "message")
    if errs:
        raise ProtocolError(f"invalid message: {errs}")
    if type_ in ("TASK", "REQUEST", "CHALLENGE", "CORRECTION") and not route_allowed(frm, to):
        raise ProtocolError(f"route {frm} -> {to} not permitted by handoffs.yaml; route via AG-ORC")
    return msg


def handoff(project_id, frm, to, task, context, input_files, decisions, unresolved, sources,
            quality_status, deadline, expected_output, workflow_step=None) -> dict:
    pkg = {"HANDOFF_ID": short_id("HO"), "PROJECT_ID": project_id, "FROM_AGENT": frm, "TO_AGENT": to,
           "TASK": task, "INPUT_FILES": list(input_files), "CONTEXT": context,
           "DECISIONS_ALREADY_MADE": list(decisions), "UNRESOLVED_QUESTIONS": list(unresolved),
           "SOURCE_LIST": list(sources), "QUALITY_STATUS": quality_status, "DEADLINE": deadline,
           "EXPECTED_OUTPUT": expected_output, "WORKFLOW_STEP": workflow_step}
    errs = R.validate(pkg, "handoff")
    if errs:
        raise ProtocolError(f"invalid handoff: {errs}")
    if not route_allowed(frm, to):
        raise ProtocolError(f"handoff {frm} -> {to} not permitted")
    return pkg


def post(obj: dict, project_dir: Path | None = None) -> Path:
    """يُلحق الرسالة/الحزمة بصندوق المشروع (JSONL)."""
    pid = obj.get("PROJECT_ID")
    project_dir = project_dir or (PROJECTS / pid)
    box = project_dir / "messages" / ("handoffs.jsonl" if "HANDOFF_ID" in obj and "TYPE" not in obj else "messages.jsonl")
    box.parent.mkdir(parents=True, exist_ok=True)
    with open(box, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return box
