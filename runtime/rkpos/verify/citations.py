"""SKL-CITEVERIFY — فحص الاستشهادات في المسودات.

اصطلاح الوحدة: الاستشهاد داخل النص بمفتاح Pandoc على معرّف المصدر: [@SRC-000123, p. 45]
فيُتحقق آلياً من وجوده وحالته، ثم يُنسَّق APA/Chicago عبر CSL عند الإخراج.
"""
from __future__ import annotations
import re

CITE_RE = re.compile(r"@(SRC-\d{6})")
OK = {"VERIFIED"}
WARN = {"PARTIAL", "NOT_VERIFIABLE"}
BAD = {"FAILED", "RETRACTED", "UNVERIFIED"}


def extract(text: str) -> list[str]:
    return CITE_RE.findall(text)


def audit(text: str, sources: list[dict]) -> dict:
    idx = {s["Source_ID"]: s for s in sources}
    keys = extract(text)
    report = {"total": len(keys), "unique": len(set(keys)), "verified": [], "warn": [], "blocking": [], "missing": []}
    for k in sorted(set(keys)):
        s = idx.get(k)
        if s is None:
            report["missing"].append(k)
        elif s["Verification_Status"] in OK:
            report["verified"].append(k)
        elif s["Verification_Status"] in WARN:
            report["warn"].append(k)
        else:
            report["blocking"].append(f"{k}:{s['Verification_Status']}")
    report["passes_qg4"] = not report["missing"] and not report["blocking"]
    return report
