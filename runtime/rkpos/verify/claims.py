"""SKL-CLAIMTAG — فحص وسم الادعاءات في المسودات.

قواعد: كل فقرة مضمونية تحمل وسماً واحداً على الأقل؛ [FACT] و[EBI] يلزمهما استشهاد @SRC في الفقرة نفسها.
"""
from __future__ import annotations
import re

TAGS = ("FACT", "EBI", "INTERP", "HYP", "AUTHOR")
TAG_RE = re.compile(r"\[(FACT|EBI|INTERP|HYP|AUTHOR)\]")
NEEDS_RE = re.compile(r"\[NEEDS-EVIDENCE\]")


def paragraphs(text: str) -> list[str]:
    out = []
    for p in re.split(r"\n\s*\n", text):
        s = p.strip()
        if not s or s.startswith(("#", "```", "---", ">", "|", "<!--")):
            continue
        out.append(s)
    return out


def audit(text: str) -> dict:
    res = {"paragraphs": 0, "untagged": [], "fact_without_source": [], "needs_evidence": 0,
           "tag_counts": {t: 0 for t in TAGS}}
    for i, p in enumerate(paragraphs(text), 1):
        res["paragraphs"] += 1
        tags = TAG_RE.findall(p)
        for t in tags:
            res["tag_counts"][t] += 1
        res["needs_evidence"] += len(NEEDS_RE.findall(p))
        if not tags:
            res["untagged"].append(i)
        elif ({"FACT", "EBI"} & set(tags)) and "@SRC-" not in p:
            res["fact_without_source"].append(i)
    res["tagged_ratio"] = round(1 - len(res["untagged"]) / res["paragraphs"], 3) if res["paragraphs"] else 1.0
    res["passes"] = not res["untagged"] and not res["fact_without_source"]
    return res
