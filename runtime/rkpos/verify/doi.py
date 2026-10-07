"""SKL-DOI — التحقق من DOI عبر Crossref REST API (واجهة عامة).

لا يُعيَّن VERIFIED إلا باستجابة فعلية من Crossref تطابق العنوان. لا تخمين ولا تصحيح.
البيئة: RKPOS_CONTACT_EMAIL يُرسل في mailto (polite pool) — اختياري.
"""
from __future__ import annotations
import difflib
import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from ..ids import now_iso

CROSSREF = "https://api.crossref.org/works/"
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def normalize_doi(doi: str) -> str:
    doi = doi.strip()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi, flags=re.I)
    return doi.lower()


def normalize_title(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").lower()
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def title_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def fetch(doi: str, timeout: float = 20.0, opener=urllib.request.urlopen) -> dict | None:
    url = CROSSREF + urllib.parse.quote(doi, safe="/")
    mail = os.environ.get("RKPOS_CONTACT_EMAIL")
    if mail:
        url += "?" + urllib.parse.urlencode({"mailto": mail})
    req = urllib.request.Request(url, headers={"User-Agent": f"RKPOS/0.1 (mailto:{mail or 'unset'})"})
    try:
        with opener(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def verify(doi: str, expected_title: str | None = None, expected_year: int | None = None,
           threshold: float = 0.9, fetcher=fetch) -> dict:
    """يعيد {'status', 'evidence', 'metadata'}; status ∈ VERIFIED|PARTIAL|FAILED|RETRACTED|PENDING."""
    d = normalize_doi(doi)
    if not DOI_RE.match(d):
        return {"status": "FAILED", "evidence": {"tool": "TL-CROSSREF", "checked_at": now_iso(), "reason": "malformed DOI"}}
    try:
        msg = fetcher(d)
    except Exception as e:  # الشبكة/الخدمة: لا نحكم بالفشل، بل بالتعليق
        return {"status": "PENDING", "evidence": {"tool": "TL-CROSSREF", "checked_at": now_iso(), "reason": f"unreachable: {e.__class__.__name__}"}}
    ev = {"tool": "TL-CROSSREF", "checked_at": now_iso(), "response_ref": CROSSREF + d}
    if msg is None:
        return {"status": "FAILED", "evidence": {**ev, "reason": "DOI not found (404)"}}
    title = (msg.get("title") or [""])[0]
    year = None
    for k in ("published-print", "published-online", "issued"):
        parts = (msg.get(k) or {}).get("date-parts") or [[None]]
        if parts[0][0]:
            year = parts[0][0]
            break
    meta = {"Title": title, "Year": year, "Journal": (msg.get("container-title") or [None])[0],
            "Publisher": msg.get("publisher"), "Volume": msg.get("volume"), "Issue": msg.get("issue"),
            "Pages": msg.get("page"), "DOI": d,
            "Author": [" ".join(filter(None, [a.get("given"), a.get("family")])) for a in msg.get("author", [])],
            "Type": msg.get("type")}
    # السحب: علاقات update-to / is-retracted-by أو نوع retraction
    upd = [u.get("type", "") for u in msg.get("update-to", [])] + list((msg.get("relation") or {}).keys())
    if any("retract" in str(u).lower() for u in upd) or "retract" in (title or "").lower()[:12]:
        return {"status": "RETRACTED", "evidence": {**ev, "reason": "retraction relation present"}, "metadata": meta}
    if expected_title:
        sim = title_similarity(expected_title, title)
        ev["match_score"] = round(sim, 3)
        if sim < threshold:
            return {"status": "PARTIAL", "evidence": {**ev, "reason": f"title mismatch ({sim:.2f})"}, "metadata": meta}
    if expected_year and year and int(expected_year) != int(year):
        return {"status": "PARTIAL", "evidence": {**ev, "reason": f"year mismatch {expected_year}≠{year}"}, "metadata": meta}
    return {"status": "VERIFIED", "evidence": ev, "metadata": meta}
