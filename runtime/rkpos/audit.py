"""سجل التدقيق الإلحاقي — Audit Trail."""
from __future__ import annotations
import json

from .ids import short_id, now_iso
from .paths import LOGS
from .registry import validate


def log(agent: str, action: str, project: str | None = None, files_changed=None, source_used=None,
        decision: str | None = None, decision_level: str | None = None, approval: str | None = None,
        model: str | None = None, cost_usd: float | None = None, path=None) -> dict:
    rec = {
        "ACTION_ID": short_id("ACT"), "AGENT": agent, "DATE": now_iso(), "PROJECT": project,
        "ACTION": action, "FILES_CHANGED": list(files_changed or []), "SOURCE_USED": list(source_used or []),
        "DECISION": decision, "DECISION_LEVEL": decision_level, "APPROVAL": approval,
        "MODEL": model, "COST_USD": cost_usd,
    }
    errs = validate(rec, "audit")
    if errs:
        raise ValueError(f"invalid audit record: {errs}")
    path = path or LOGS / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read(project: str | None = None, path=None) -> list[dict]:
    path = path or LOGS / "audit.jsonl"
    if not path.exists():
        return []
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows if project is None or r["PROJECT"] == project]
