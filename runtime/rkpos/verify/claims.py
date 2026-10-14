"""SKL-CLAIMTAG — فحص وسم الادعاءات في المسودات، وتثليث الأدلة واستقلال أصولها في سجل الادعاءات.

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


# ------------------------------------------------------------------ التثليث واستقلال الأصول
# يُحسب الدعم بالأصول المستقلة لا بعدد الإحالات: المصادر التي تشترك في أصل واحد (الحقل Origin في سجل المصدر،
# أو origin في إحالة الادعاء، أو DOI واحد) تُعدّ شهادة واحدة. ويُعلَّم الادعاء المعتمد (SUPPORTED)
# إذا استند إلى الصحافة أو الويب وحدهما (المستويان 4 و5 في هرم المصادر) أو إلى أصل واحد.
ESTABLISHED = {"SUPPORTED"}
PRESS_TIER = 4          # governance/source_hierarchy.yaml: الصحافة الموثوقة؛ وما دونها (5) استكشاف
TYPE_AR = {"peer_reviewed_journal": "بحث محكّم", "primary_dataset": "بيانات أولية", "government_record": "سجل رسمي",
           "university_research": "بحث جامعي", "international_organization": "منظمة دولية", "university_press": "مطبعة جامعية",
           "academic_book": "كتاب أكاديمي", "research_institute": "معهد بحثي", "professional_report": "تقرير مهني",
           "consultancy_report": "تقرير استشاري", "ngo_report": "تقرير منظمة أهلية", "reputable_journalism": "صحافة موثوقة",
           "general_web": "ويب عام", "blog": "مدونة", "social_media": "وسائل التواصل", "encyclopedia_open": "موسوعة مفتوحة",
           "manuscript": "مخطوط", "interview": "مقابلة", "classical_text": "نص تراثي محقق", "other": "أخرى"}
FLAG_AR = {"press_only": "معتمد يستند إلى الصحافة أو الويب وحدهما",
           "single_origin": "معتمد يستند إلى أصل واحد",
           "no_sources": "معتمد بلا مصادر مسجلة",
           "unknown_sources": "إحالة إلى مصدر غير مسجل"}


def _tier(src: dict | None) -> int | None:
    if not src:
        return None
    if src.get("Tier"):
        return int(src["Tier"])
    from .sources import TIER_BY_TYPE
    return TIER_BY_TYPE.get(src.get("Source_Type"))


def _origin(ref: dict, src: dict | None) -> str:
    if ref.get("origin"):
        return str(ref["origin"]).strip().lower()
    if src and src.get("Origin"):
        return str(src["Origin"]).strip().lower()
    if src and src.get("DOI"):
        return "doi:" + src["DOI"].lower()
    return "src:" + ref["source_id"]


def triangulation(claim: dict, sources: list[dict]) -> dict:
    """تقرير التثليث لادعاء واحد من سجل الادعاءات (evidence/claims.jsonl)."""
    idx = {s["Source_ID"]: s for s in sources}
    refs = [r for r in claim.get("sources") or [] if r.get("source_id")]
    origins: dict[str, list[str]] = {}
    types, tiers, unknown = set(), [], []
    for r in refs:
        s = idx.get(r["source_id"])
        if s is None:
            unknown.append(r["source_id"])
        origins.setdefault(_origin(r, s), []).append(r["source_id"])
        if s:
            types.add(s.get("Source_Type") or "other")
            t = _tier(s)
            if t:
                tiers.append(t)
    rep = {"claim_id": claim.get("claim_id"), "tag": claim.get("tag"), "status": claim.get("status"),
           "supporting_sources": len(refs), "independent_origins": len(origins),
           "dependent_links": len(refs) - len(origins),
           "shared_origins": {k: v for k, v in origins.items() if len(v) > 1},
           "evidence_types": sorted(types), "types_count": len(types),
           "type_labels": [TYPE_AR.get(t, t) for t in sorted(types)],
           "best_tier": min(tiers) if tiers else None, "unknown_sources": unknown, "flags": []}
    rep["press_only"] = bool(tiers) and min(tiers) >= PRESS_TIER and len(tiers) == len(refs) - len(unknown)
    if claim.get("status") in ESTABLISHED:
        if not refs:
            rep["flags"].append("no_sources")
        else:
            if rep["press_only"]:
                rep["flags"].append("press_only")
            if len(origins) < 2:
                rep["flags"].append("single_origin")
    if unknown:
        rep["flags"].append("unknown_sources")
    rep["flags_ar"] = [FLAG_AR[f] for f in rep["flags"]]
    return rep


def triangulate(claims: list[dict], sources: list[dict]) -> dict:
    """تقرير التثليث لسجل ادعاءات كامل: لكل ادعاء، ثم خلاصة بالأعداد والمتوسط."""
    items = [triangulation(c, sources) for c in claims]
    est = [i for i in items if i["status"] in ESTABLISHED]
    summary = {"claims": len(items), "established": len(est),
               "press_only_established": sum(1 for i in items if "press_only" in i["flags"]),
               "single_origin_established": sum(1 for i in items if "single_origin" in i["flags"]),
               "unsourced_established": sum(1 for i in items if "no_sources" in i["flags"]),
               "unknown_sources": sorted({s for i in items for s in i["unknown_sources"]}),
               "independent_avg": round(sum(i["independent_origins"] for i in items) / len(items), 2) if items else 0.0}
    summary["passes"] = not (summary["press_only_established"] or summary["unsourced_established"] or summary["unknown_sources"])
    return {"summary": summary, "claims": items, "flagged": [i for i in items if i["flags"]]}


def load_ledger(path) -> list[dict]:
    import json
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def triangulate_project(pid: str) -> dict:
    """يقرأ سجل ادعاءات المشروع ومصادره (مع المصادر المركزية) ويعيد تقرير التثليث."""
    from ..paths import PROJECTS
    from . import sources as S
    root = PROJECTS / pid
    if not (root / "manifest.yaml").exists():
        raise ValueError(f"مشروع غير موجود: {pid}")
    srcs = S.load(root / "research/sources.jsonl") + S.load()
    return {"project": pid, **triangulate(load_ledger(root / "evidence/claims.jsonl"), srcs)}
