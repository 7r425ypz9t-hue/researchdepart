"""SKL-BIBCLEAN — كشف التكرار في سجل المصادر (DOI ثم عنوان مطبّع + سنة)."""
from __future__ import annotations
import re
import unicodedata


def _key(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "").lower()
    t = re.sub(r"[ً-ْـ]", "", t)          # التشكيل والتطويل
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\W+", "", t)


def duplicates(records: list[dict]) -> list[tuple[str, str, str]]:
    seen_doi, seen_t, dups = {}, {}, []
    for r in records:
        sid = r["Source_ID"]
        if r.get("DOI"):
            d = r["DOI"].lower()
            if d in seen_doi:
                dups.append((seen_doi[d], sid, "doi"))
            seen_doi.setdefault(d, sid)
        k = (_key(r.get("Title", "")), str(r.get("Year")))
        if k in seen_t:
            dups.append((seen_t[k], sid, "title+year"))
        seen_t.setdefault(k, sid)
    return dups
