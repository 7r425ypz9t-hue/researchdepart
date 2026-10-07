"""حوكمة الكلفة — أحداث الكلفة والتجميع والإنذار (AG-CST / SKL-COSTTRACK)."""
from __future__ import annotations
import json
from collections import defaultdict

from . import registry as R
from .ids import now_iso
from .paths import CONFIG, LOGS

EVENTS = LOGS / "cost_events.jsonl"


def price(model: str) -> dict | None:
    p = R.load_yaml(CONFIG / "pricing.yaml")["models"].get(model)
    if not p or p.get("input_per_mtok") is None:
        return None
    return p


def record(model: str, input_tokens: int, output_tokens: int, project: str | None, agent: str,
           stage: str | None = None, path=EVENTS, usd: float | None = None) -> dict:
    """usd: كلفة أبلغ بها المحرّك نفسه (Claude Code) تُقدَّم على الحساب من جدول الأسعار."""
    p = price(model)
    if usd is not None:
        usd = round(float(usd), 6)
    else:
        usd = None if p is None else round(input_tokens / 1e6 * p["input_per_mtok"] + output_tokens / 1e6 * p["output_per_mtok"], 6)
    ev = {"ts": now_iso(), "model": model, "input_tokens": input_tokens, "output_tokens": output_tokens,
          "usd": usd, "estimate": usd is None, "project": project, "agent": agent, "stage": stage}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    return ev


def report(project: str | None = None, path=EVENTS) -> dict:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()] if path.exists() else []
    rows = [r for r in rows if project is None or r["project"] == project]
    agg = {"total_usd": 0.0, "unpriced_events": 0, "by_agent": defaultdict(float), "by_stage": defaultdict(float),
           "by_project": defaultdict(float), "tokens_in": 0, "tokens_out": 0}
    for r in rows:
        agg["tokens_in"] += r["input_tokens"]
        agg["tokens_out"] += r["output_tokens"]
        if r["usd"] is None:
            agg["unpriced_events"] += 1
            continue
        agg["total_usd"] += r["usd"]
        agg["by_agent"][r["agent"]] += r["usd"]
        agg["by_stage"][r["stage"] or "-"] += r["usd"]
        agg["by_project"][r["project"] or "-"] += r["usd"]
    agg = {k: (dict(v) if isinstance(v, defaultdict) else v) for k, v in agg.items()}
    agg["total_usd"] = round(agg["total_usd"], 4)
    return agg


def alerts(spent: float, limit: float | None) -> list[str]:
    if not limit:
        return []
    th = R.load_yaml(CONFIG / "cost_limits.yaml")["alerts_at"]
    out = [f"ALERT {int(t*100)}%: {spent:.2f}/{limit:.2f} USD" for t in th if spent >= t * limit]
    if spent > limit:
        out.append(f"LIMIT EXCEEDED: {spent:.2f}/{limit:.2f} USD → ESCALATION L4")
    return out
