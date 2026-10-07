"""SKL-STYLE — قياس البصمة الأسلوبية للنص العربي (Stylometric Profile).

يحوّل البصمة من أوصاف انطباعية إلى مؤشرات قابلة للقياس والمقارنة:
طول الجملة وتوزيعه، كثافة الترقيم، نسبة الفاصلة إلى النقطة، أدوات الربط،
ضمائر المتكلم، الأسئلة البلاغية، العبارات التفسيرية، التنوع المعجمي (MATTR)،
ألفاظ اللهجة، وأنماط القوالب الأكاديمية.

لا يحكم على جودة النص؛ يقيس المسافة بين نص وملف مرجعي معتمد.
"""
from __future__ import annotations
import re
import statistics as st
from collections import Counter

AR_WORD = re.compile(r"[ء-ي٠-٩ٱ-ۓA-Za-z0-9]+")
DIACRITICS = re.compile(r"[ً-ْ]")
SENT_SPLIT = re.compile(r"(?<=[\.؟!\?…])\s+|\n{2,}")
HEADING = re.compile(r"^\s*(#|\||\[|\\)", re.M)  # عناوين، جداول، فهارس، حقول Word

# أدوات الربط: تُعد في بداية الكلمة المستقلة (لا كسوابق ملتصقة) إلا ما نُص عليه
CONNECTIVES = {
    "لكن": r"(?:و)?لكن(?:ّ)?",
    "بل": r"بل",
    "ثم": r"ثم(?:ّ)?",
    "إذ": r"إذ",
    "حيث": r"حيث",
    "فضلا_عن": r"فضلا?ً? عن",
    "ربما": r"ربما",
    "لعل": r"لعل(?:ّ)?",
    "ولا_شك": r"ولا ?شك",
    "إن_التوكيد": r"إن(?:ّ)?",
    "أما_ف": r"أما(?:ّ)?",
    "من_ثم": r"ومن ث(?:َ)?م",
    "لذلك": r"(?:و)?لذلك",
    "أي": r"أي",
}
FIRST_SG = r"(?:أنا|لي|عندي|أرى|أظن|أعتقد|لا أدري|أذكر|أتذكر)"
FIRST_PL = r"(?:نحن|لنا|علينا|إننا|لدينا|منا|عندنا|نرى|نحتاج|نعرف|لسنا|ثقافتنا|هويتنا|مجتمعنا|تراثنا)"
EXPLANATORY = [r"وهذا يعني", r"بمعنى آخر", r"أي أن(?:ّ)?", r"والمقصود", r"المقصود:", r"وخلاصة القول", r"ومن هنا"]
TEMPLATE = [r"المقصود:", r"مثال:", r"النتيجة:", r"الفجوة (?:الأولى|الثانية|الثالثة)", r"جدول ?\(", r"شكل ?\("]
DIALECT = ["الفريج", "البرزة", "الميبر", "الصيرم", "المشاجيج", "السفير", "الصديج", "الطريج", "خشمك", "الفزعة", "السنع", "يالس", "وايد", "اليبيل", "چ"]


def _clean(text: str) -> str:
    """يحذف العناوين والجداول، ويزيل التشكيل والتطويل وعلامات الاتجاه حتى لا تقطع الكلمات."""
    lines = [l for l in text.splitlines() if not HEADING.match(l)]
    t = "\n".join(lines)
    return re.sub(r"[\u064B-\u0652\u0640\u200e\u200f]", "", t)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT_SPLIT.split(_clean(text)) if len(AR_WORD.findall(s)) >= 3]


def words(text: str) -> list[str]:
    return AR_WORD.findall(_clean(text))


def mattr(tokens: list[str], window: int = 500) -> float:
    if len(tokens) < window:
        return round(len(set(tokens)) / max(len(tokens), 1), 3)
    vals = [len(set(tokens[i:i + window])) / window for i in range(0, len(tokens) - window + 1, window // 2)]
    return round(sum(vals) / len(vals), 3)


def _per_k(n: int, total: int) -> float:
    return round(1000 * n / total, 2) if total else 0.0


def profile(text: str) -> dict:
    diacritics = len(DIACRITICS.findall(text))
    body = _clean(text)
    ws = words(body)
    ss = sentences(body)
    lens = [len(AR_WORD.findall(s)) for s in ss] or [0]
    paras = [p for p in re.split(r"\n\s*\n", body) if len(AR_WORD.findall(p)) >= 5]
    W = len(ws)
    punct = {
        "comma": len(re.findall(r"[،,]", body)), "period": len(re.findall(r"\.(?!\.)", body)),
        "colon": body.count(":"), "semicolon": body.count("؛"), "question": len(re.findall(r"[؟?]", body)),
        "exclamation": body.count("!"), "guillemets": body.count("«"), "quotes": len(re.findall(r"[“\"]", body)) // 2,
        "parentheses": body.count("("), "dash": len(re.findall(r"[—–]", body)),
    }
    conn = {k: len(re.findall(rf"(?<!\w){v}(?!\w)", body)) for k, v in CONNECTIVES.items()}
    wa_initial = sum(1 for s in ss if re.match(r"^[«“\"]?و\S", s))
    fa_initial = sum(1 for s in ss if re.match(r"^[«“\"]?ف\S", s))
    return {
        "words": W, "sentences": len(ss), "paragraphs": len(paras),
        "sentence_len": {"mean": round(st.mean(lens), 1), "median": st.median(lens),
                         "p90": sorted(lens)[int(0.9 * (len(lens) - 1))],
                         "share_over_40": round(sum(l > 40 for l in lens) / len(lens), 3),
                         "share_under_12": round(sum(l < 12 for l in lens) / len(lens), 3)},
        "paragraph_len_mean": round(st.mean([len(AR_WORD.findall(p)) for p in paras]), 1) if paras else 0,
        "punct_per_1k": {k: _per_k(v, W) for k, v in punct.items()},
        "comma_period_ratio": round(punct["comma"] / max(punct["period"], 1), 2),
        "connectives_per_1k": {k: _per_k(v, W) for k, v in conn.items()},
        "sentence_initial": {"wa": round(wa_initial / max(len(ss), 1), 3), "fa": round(fa_initial / max(len(ss), 1), 3)},
        "first_person_per_1k": {"singular": _per_k(len(re.findall(rf"(?<!\w){FIRST_SG}(?!\w)", body)), W),
                                "plural": _per_k(len(re.findall(rf"(?<!\w){FIRST_PL}(?!\w)", body)), W)},
        "rhetorical_q_per_1k": _per_k(punct["question"], W),
        "explanatory_per_1k": _per_k(sum(len(re.findall(p, body)) for p in EXPLANATORY), W),
        "template_markers_per_1k": _per_k(sum(len(re.findall(p, body)) for p in TEMPLATE), W),
        "diacritics_per_1k_chars": round(1000 * diacritics / max(len(body), 1), 2),
        "mattr_500": mattr(ws),
        "dialect_hits": {d: body.count(d) for d in DIALECT if body.count(d)},
        "top_bigrams": [" ".join(b) for b, _ in Counter(zip(ws, ws[1:])).most_common(15)],
    }


KEYS = [("sentence_len", "mean"), ("sentence_len", "share_over_40"), ("sentence_len", "share_under_12"),
        ("comma_period_ratio",), ("punct_per_1k", "colon"), ("punct_per_1k", "question"),
        ("first_person_per_1k", "plural"), ("first_person_per_1k", "singular"),
        ("explanatory_per_1k",), ("template_markers_per_1k",), ("mattr_500",), ("sentence_initial", "wa")]


def _get(p, path):
    for k in path:
        p = p[k]
    return p


def distance(sample: dict, reference: dict) -> dict:
    """انحراف نسبي لكل مؤشر عن الملف المرجعي (0 = مطابق). يُستعمل في QG5 تنبيهاً لا حكماً."""
    out = {}
    for path in KEYS:
        r, s = _get(reference, path), _get(sample, path)
        out[".".join(path)] = round((s - r) / r, 2) if r else (0.0 if s == 0 else None)
    return out


# ---- الملفات المرجعية (AUTHOR_ONLY: تُقرأ من المسار الخاص غير المتتبع) ----
REGISTER_BY_TYPE = {"op_ed": "essay", "intellectual_book": "essay", "strategic_report": "essay",
                    "academic_book": "academic", "journal_article": "academic", "systematic_review": "academic",
                    "literature_review": "academic", "policy_study": "academic", "foresight_study": "academic"}


def register_for(project_id: str) -> str | None:
    import yaml
    from .paths import PROJECTS
    mf = PROJECTS / project_id / "manifest.yaml"
    if not mf.exists():
        return None
    return REGISTER_BY_TYPE.get(yaml.safe_load(mf.read_text(encoding="utf-8")).get("project_type"))


def load_reference(name: str | None) -> dict | None:
    import json
    from .paths import ROOT
    if not name:
        return None
    p = ROOT / "memory/author/private" / f"style_reference_{name}.json"
    return json.loads(p.read_text(encoding="utf-8"))["profile"] if p.exists() else None


def _log_gap(a: float, b: float) -> float:
    import math
    return abs(math.log((a + 0.5) / (b + 0.5)))


def pole(sample: dict, author_ref: dict, assisted_ref: dict) -> dict:
    """أيّ القطبين أقرب إليه النص: صوت المؤلف أم الصياغة المُعانة؟ (مؤشر تنبيه لا حكم).
    يقارن الفجوة اللوغاريتمية على مؤشرات البنية التي تفصل القطبين."""
    keys = [("sentence_len", "median"), ("comma_period_ratio",), ("punct_per_1k", "colon"),
            ("template_markers_per_1k",), ("explanatory_per_1k",), ("diacritics_per_1k_chars",)]
    da = sum(_log_gap(_get(sample, k), _get(author_ref, k)) for k in keys)
    db = sum(_log_gap(_get(sample, k), _get(assisted_ref, k)) for k in keys)
    share = round(da / (da + db), 2) if (da + db) else 0.5  # 0 = صوت المؤلف تماماً، 1 = الصياغة المُعانة تماماً
    return {"closer_to": "author" if da <= db else "assisted", "assisted_share": share,
            "gap_author": round(da, 2), "gap_assisted": round(db, 2)}


def load_assisted_pole() -> dict | None:
    import json
    from .paths import ROOT
    p = ROOT / "memory/author/private/style_pole_assisted.json"
    return json.loads(p.read_text(encoding="utf-8"))["profile"] if p.exists() else None
