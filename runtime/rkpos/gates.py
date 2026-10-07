"""بوابات الجودة — الفحوص الآلية وتسجيل القرارات. الاعتماد نفسه للمشرف/المجلس/المؤلف."""
from __future__ import annotations
from pathlib import Path

import yaml

from . import audit, registry as R
from .ids import now_iso
from .paths import PROJECTS
from .verify import citations, claims


def source_metrics(sources: list[dict]) -> dict:
    verifiable = [s for s in sources if s["Verification_Status"] != "NOT_VERIFIABLE"]
    verified = [s for s in verifiable if s["Verification_Status"] == "VERIFIED"]
    bad = [s["Source_ID"] for s in sources if s["Verification_Status"] in ("FAILED", "RETRACTED")]
    t12 = [s for s in sources if (s.get("Tier") or 9) <= 2]
    return {"total": len(sources), "verified_ratio": round(len(verified) / len(verifiable), 3) if verifiable else 0.0,
            "tier12_share": round(len(t12) / len(sources), 3) if sources else 0.0, "failed_or_retracted": bad}


def auto_checks(gate: str, sources: list[dict], manuscript_text: str | None = None,
                red_team: list[dict] | None = None) -> list[dict]:
    """فحوص آلية تساند (لا تحل محل) قرار المعتمِد."""
    res = []
    if gate == "QG1":
        m = source_metrics(sources)
        res += [
            {"criterion": "≥95% من المصادر القابلة للتحقق VERIFIED", "result": "PASS" if m["verified_ratio"] >= 0.95 else "FAIL", "evidence": str(m["verified_ratio"])},
            {"criterion": "Tier 1-2 ≥ 70%", "result": "PASS" if m["tier12_share"] >= 0.7 else "FAIL", "evidence": str(m["tier12_share"])},
            {"criterion": "صفر FAILED/RETRACTED", "result": "PASS" if not m["failed_or_retracted"] else "FAIL", "evidence": ",".join(m["failed_or_retracted"]) or "none"},
        ]
    if gate in ("QG3", "QG4") and manuscript_text is not None:
        c = claims.audit(manuscript_text)
        res.append({"criterion": "كل الفقرات موسومة وFACT/EBI مسندة", "result": "PASS" if c["passes"] else "FAIL",
                    "evidence": f"untagged={c['untagged']} fact_without_source={c['fact_without_source']}"})
    if gate == "QG3" and red_team is not None:
        open_crit = [c["id"] for c in red_team if c.get("severity") in ("critical", "high") and c.get("status", "OPEN") == "OPEN"]
        res.append({"criterion": "لا تحديات Red Team حرجة/عالية مفتوحة", "result": "FAIL" if open_crit else "PASS",
                    "evidence": ",".join(open_crit) or "none"})
    if gate == "QG4" and manuscript_text is not None:
        a = citations.audit(manuscript_text, sources)
        res.append({"criterion": "كل استشهاد يحيل إلى مصدر موجود ومتحقق", "result": "PASS" if a["passes_qg4"] else "FAIL",
                    "evidence": f"missing={a['missing']} blocking={a['blocking']}"})
    return res


def record(pid: str, gate: str, decision: str, approver: str, criteria: list[dict], conditions=None,
           reviewer_model=None, scope: str = "project") -> Path:
    G = R.gates()
    if gate not in G:
        raise KeyError(gate)
    g = G[gate]
    allowed = {g.get("approver"), g.get("fallback_approver"), g.get("final_release_approver"), "HUMAN-AUTHOR"} - {None}
    if approver not in allowed:
        raise PermissionError(f"{approver} cannot approve {gate}; allowed: {sorted(allowed)}")
    if decision == "APPROVED" and any(c["result"] == "FAIL" for c in criteria) and approver != "HUMAN-AUTHOR":
        raise ValueError("cannot APPROVE with failing criteria; use CONDITIONAL/REJECTED or escalate to author")
    rec = {"gate": gate, "project_id": pid, "scope": scope, "decision": decision, "approver": approver,
           "reviewer_model": reviewer_model, "criteria_checked": criteria, "conditions": list(conditions or []), "date": now_iso()}
    errs = R.validate(rec, "gate_decision")
    if errs:
        raise ValueError(errs)
    out = PROJECTS / pid / "reviews" / f"gate_{gate}_{scope}_{rec['date'][:10]}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(rec, allow_unicode=True, sort_keys=False), encoding="utf-8")
    audit.log(approver if approver.startswith(("AG-", "HUMAN-")) else "AG-ORC", f"gate_{gate}_{decision}", project=pid,
              files_changed=[str(out.relative_to(PROJECTS.parent))], decision=decision, decision_level=g["decision_level"],
              approval=approver)
    return out
