"""الإحالات في الهامش: تحويل الاستشهادات داخل النص إلى حواشٍ مرقّمة أسفل الصفحة.

يُلتقط نوعان من الاستشهاد:
- مفتاح المصدر المسجل: [@SRC-000123] أو [@SRC-000123, p. 45; @SRC-000124]؛ ويُبنى نص الحاشية من سجل المصادر
  بالحقول المسجلة وحدها (صفر تلفيق)، وما لم يُتحقق منه يُعلَّم.
- الاستشهاد بالمؤلف والسنة: (بورديو، 1986، ص 12) أو (Bourdieu, 1986, p. 12)؛ ويُطابَق بسجل المصادر إن وُجد،
  وإلا نُقل نص الاستشهاد نفسه إلى الحاشية.
التكرار: «المرجع نفسه» للحاشية التالية مباشرة، والصيغة المختصرة لما سبق ذكره.
يحل محل كل استشهاد علامة موضعية (PH_OPEN رقم PH_CLOSE) يحوّلها المُصدِّر إلى حاشية Word، والقارئ إلى رقم مرفوع.
"""
from __future__ import annotations
import re
from pathlib import Path

PH_OPEN, PH_CLOSE = "", ""
PH_RE = re.compile(f"{PH_OPEN}(\\d+){PH_CLOSE}")
KEY_RE = re.compile(r"\s*\[((?:\s*;?\s*-?@SRC-\d{1,6}[^;\]]*)+)\]")
ONE_KEY = re.compile(r"-?@(SRC-\d{1,6})\s*[,،]?\s*(.*)")
YEAR = r"(?:1[5-9]\d{2}|20\d{2}|د\.\s?ت)[a-zأ-ي]?"
LOCATOR = r"(?:\s*[,،:]\s*(?:(?:ص{1,2}|pp?)\.?\s*)?[\d٠-٩][\d٠-٩\-–]*)?"
ONE_CITE = rf"[^()\[\];؛]*?[A-Za-zء-ي][^()\[\];؛]*?[,،]\s*{YEAR}{LOCATOR}"
AY_RE = re.compile(rf"\s*\(({ONE_CITE}(?:\s*[;؛]\s*{ONE_CITE})*)\)")


def project_sources(pid: str | None) -> list[dict]:
    """سجل مصادر المشروع ثم السجل العام."""
    from .paths import PROJECTS
    from .verify import sources as SV
    recs = SV.load(PROJECTS / pid / "research/sources.jsonl") if pid else []
    return recs + SV.load()


def _locator(loc: str) -> str:
    loc = (loc or "").strip().strip("،,").strip()
    loc = re.sub(r"^pp?\.\s*", "ص ", loc)
    return loc


def _authors(src: dict) -> list[str]:
    a = src.get("Author") or []
    return [a] if isinstance(a, str) else [x for x in a if x]


def reference(src: dict) -> str:
    """نص الحاشية الكامل من الحقول المسجلة وحدها."""
    parts = []
    if _authors(src):
        parts.append("، ".join(_authors(src)))
    title = (src.get("Title") or "").strip()
    if title:
        parts.append(f"«{title}»" if src.get("Journal") else title)
    if src.get("Journal"):
        j = src["Journal"]
        if src.get("Volume"):
            j += f"، مج {src['Volume']}"
        if src.get("Issue"):
            j += f"، ع {src['Issue']}"
        parts.append(j)
    if src.get("Publisher"):
        parts.append(src["Publisher"])
    if src.get("Year"):
        parts.append(str(src["Year"]))
    if src.get("Pages"):
        parts.append(f"ص {src['Pages']}")
    if src.get("DOI"):
        parts.append(f"doi:{src['DOI']}")
    elif src.get("URL"):
        parts.append(src["URL"])
    text = "، ".join(parts)
    if src.get("Verification_Status") not in (None, "VERIFIED"):
        text += " (لم يُتحقق منه بعد)"
    return text


def _short(src: dict) -> str:
    a = _authors(src)
    name = a[0].split(",")[0].split("،")[0].strip() if a else ""
    title = " ".join((src.get("Title") or "").split()[:4])
    return "، ".join(x for x in (name, title) if x)


def _match(cite: str, sources: list[dict]) -> dict | None:
    """مطابقة استشهاد المؤلف والسنة بسجل المصادر (اسم العائلة الأول والسنة)."""
    m = re.match(rf"\s*(.+?)[,،]\s*({YEAR})", cite)
    if not m:
        return None
    name = re.split(r"\s+(?:و|and|&|et al\.?|وآخرون)\s*", m.group(1).strip())[0].strip()
    year = m.group(2)[:4]
    for s in sources:
        if str(s.get("Year") or "") == year and any(name and name in au for au in _authors(s)):
            return s
    return None


def collect(text: str, sources: list[dict] | None = None) -> tuple[str, list[str]]:
    """يستبدل كل استشهاد بعلامة موضعية مرقّمة، ويعيد نصوص الحواشي بالترتيب."""
    idx = {s.get("Source_ID"): s for s in (sources or [])}
    notes: list[str] = []
    seen: set[str] = set()
    last: list[str | None] = [None]

    def add(key: str | None, full: str, short: str, loc: str) -> str:
        loc = _locator(loc)
        if key and key == last[0]:
            body = "المرجع نفسه" + (f"، {loc}" if loc else "")
        elif key and key in seen:
            body = short + (f"، {loc}" if loc else "")
        else:
            body = full + (f"، {loc}" if loc else "")
        if key:
            seen.add(key)
        last[0] = key
        notes.append(body.rstrip("،. ") + ".")
        return f"{PH_OPEN}{len(notes)}{PH_CLOSE}"

    def keys(m: re.Match) -> str:
        out = ""
        for part in re.split(r"\s*;\s*", m.group(1)):
            k = ONE_KEY.match(part.strip())
            if not k:
                continue
            sid, loc = k.group(1), k.group(2)
            s = idx.get(sid)
            if s:
                out += add(sid, reference(s), _short(s), loc)
            else:
                out += add(sid, f"مصدر برقم القيد {sid} لم تُستكمل بياناته في سجل المصادر (يحتاج توثيقاً)", sid, loc)
        return out

    def author_year(m: re.Match) -> str:
        out = ""
        for cite in re.split(r"\s*[;؛]\s*", m.group(1)):
            s = _match(cite, sources or [])
            loc_m = re.search(rf"{YEAR}({LOCATOR})\s*$", cite)
            loc = loc_m.group(1) if loc_m else ""
            if s:
                out += add(s.get("Source_ID"), reference(s), _short(s), loc)
            else:
                base = cite[: loc_m.start(1)] if loc_m and loc else cite
                out += add("AY:" + base.strip(), base.strip(), base.strip(), loc)
        return out

    # مرور واحد بترتيب الورود في النص، فتتسلسل أرقام الحواشي كما يقرؤها القارئ
    hits = sorted([(m.start(), m.end(), keys, m) for m in KEY_RE.finditer(text)] +
                  [(m.start(), m.end(), author_year, m) for m in AY_RE.finditer(text)], key=lambda x: x[0])
    out, pos = [], 0
    for start, end, fn, m in hits:
        if start < pos:
            continue
        out.append(text[pos:start])
        out.append(fn(m))
        pos = end
    out.append(text[pos:])
    return "".join(out), notes


def to_superscript(text: str) -> str:
    """للقارئ: العلامة الموضعية رقمٌ مرفوع."""
    sup = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    return PH_RE.sub(lambda m: m.group(1).translate(sup), text)


def reading_text(text: str, sources: list[dict] | None = None) -> str:
    """نص القراءة المنقّى مع الحواشي مجموعة في آخره تحت «الإحالات»."""
    from . import sanitize
    body, notes = collect(text, sources)
    body = to_superscript(sanitize.clean(body)[0])
    if notes:
        body = body.rstrip() + "\n\n## الإحالات\n\n" + "\n".join(f"{i}. {n}" for i, n in enumerate(notes, 1)) + "\n"
    return body


def pid_of(path: Path) -> str | None:
    from .paths import PROJECTS
    try:
        return path.resolve().relative_to(PROJECTS.resolve()).parts[0]
    except (ValueError, IndexError):
        return None
