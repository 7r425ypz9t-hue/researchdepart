"""تنقية المخرج واللغة البشرية المحكمة (SKL-CLEANOUT وSKL-HUMANLANG).

- الوسوم والملاحظات الإنجليزية تُستبدل بترجمتها العربية بين قوسين؛ والنص الإنجليزي الحر داخل الملاحظات يُحذف
  من نسخة القراءة ويُذكر في تقرير التنقية (لا يُترجم آلياً تخميناً).
- العلامات المائية المخفية (محارف غير مرئية ومسافات شاذة وبصمة مكتبة Word) والظاهرة (علامات التشغيل والمعرّفات
  الداخلية) تُزال.
- مقياس اللغة البشرية: لوازم الصياغة الآلية والشَّرطة الطويلة والملاحظات الإنجليزية لكل ألف كلمة.
الأصل المحفوظ يبقى بوسومه المعيارية (تقرؤها أدوات الفحص)، والتنقية طبقة عرض وتصدير، إلا المحارف الخفية فتُزال من الأصل.
"""
from __future__ import annotations
import re
from functools import lru_cache

from .paths import CONFIG
from . import registry as R

TAG_RE = re.compile(r"\[(?P<tag>[A-Z][A-Z-]{1,20})(?:\s*[—–:\-]\s*(?P<body>[^\]\n]*))?\]")
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
ARABIC = re.compile(r"[ء-ي]")


@lru_cache(maxsize=1)
def cfg() -> dict:
    return R.load_yaml(CONFIG / "output_quality.yaml")


@lru_cache(maxsize=1)
def _hidden_re() -> re.Pattern:
    w = cfg()["watermarks"]
    cls = "".join(f"\\U{a:08X}-\\U{b:08X}" for a, b in w["invisible_ranges"])
    return re.compile(f"[{cls}]")


@lru_cache(maxsize=1)
def _spaces_re() -> re.Pattern:
    return re.compile("[" + "".join(f"\\U{c:08X}" for c in cfg()["watermarks"]["odd_spaces"]) + "]")


def hidden(text: str) -> tuple[str, int]:
    """يحذف المحارف غير المرئية ويوحّد المسافات الشاذة؛ ويعيد عدد ما أُزيل."""
    text, n1 = _hidden_re().subn("", text)
    text, n2 = _spaces_re().subn(" ", text)
    return text, n1 + n2


def _phrases(body: str) -> str:
    for en, ar in cfg()["phrases"].items():
        body = re.sub(rf"\b{re.escape(en)}\b", ar, body, flags=re.I)
    return body


def _english_only(body: str) -> bool:
    return bool(LATIN_WORD.search(body)) and not ARABIC.search(body)


def notes(text: str, mode: str = "reading") -> tuple[str, dict]:
    """الوسوم والملاحظات ← العربية بين قوسين. mode: reading (القراءة) أو tagged (المراجعة بكل الوسوم)."""
    table = cfg()["notes"]
    rep = {"translated": 0, "dropped": 0, "english_removed": []}

    def sub(m: re.Match) -> str:
        tag, body = m.group("tag"), (m.group("body") or "").strip()
        spec = table.get(tag)
        if not spec:
            if _english_only(tag + " " + body):     # وسم إنجليزي غير معروف: يُحذف ويُذكر
                rep["english_removed"].append(m.group(0))
                return ""
            return m.group(0)
        if mode == "reading" and spec["reading"] == "drop":
            rep["dropped"] += 1
            return ""
        body = _phrases(body) if body else ""
        if body and LATIN_WORD.search(re.sub(r"\([^)]*\)", "", body)):   # بقي نص إنجليزي حر: لا تخمين في ترجمته
            rep["english_removed"].append(body)
            body = ""
        rep["translated"] += 1
        return f"({spec['ar']}: {body})" if body else f"({spec['ar']})"

    text = TAG_RE.sub(sub, text)
    for en, ar in cfg()["section_labels"].items():   # عناوين أقسام الوكيل
        text = re.sub(rf"(?m)^(\s*#*\s*\**){en}(\**)\s*:", rf"\g<1>{ar}\g<2>:", text)
    return text, rep


def visible(text: str) -> tuple[str, int]:
    """علامات التشغيل والمعرّفات الداخلية والترويسة التقنية."""
    n = 0
    text, k = re.subn(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    n += k
    for p in cfg()["watermarks"]["visible_patterns"]:
        text, k = re.subn(p, "", text)
        n += k
    text, k = re.subn(r"⟨([^⟩]*)⟩", r"(\1)", text)
    return text, n + k


def _tidy(text: str) -> str:
    text = re.sub(r"(\((?:يحتاج توثيقاً|يحتاج إحالة)\))(?:\s*\1)+", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +([.،؛:,؟!)])", r"\1", text)
    text = re.sub(r"\( +", "(", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def clean(text: str, mode: str = "reading") -> tuple[str, dict]:
    """التنقية الكاملة لنص يُعرض أو يُصدَّر؛ ويعيد تقريراً بما أُزيل وتُرجم."""
    text, nh = hidden(text)
    text, nv = visible(text)
    text, rep = notes(text, mode)
    rep.update({"hidden_chars": nh, "visible_marks": nv})
    return _tidy(text), rep


def source(text: str) -> str:
    """تنقية الأصل المحفوظ: المحارف الخفية وحدها (الوسوم المعيارية تبقى لأدوات الفحص)."""
    return hidden(text)[0]


# ------------------------------------------------------------------ اللغة البشرية
def latin_notes(text: str) -> list[str]:
    out = []
    for m in TAG_RE.finditer(text):
        body = m.group("body") or ""
        if m.group("tag") not in cfg()["notes"] or (body and _english_only(_phrases(body))):
            out.append(m.group(0))
    out += [m.group(0) for m in re.finditer(r"\[(?![A-Z][A-Z-]{1,20}[\]—–:\-\s])(?!@)[^\]\n]*[A-Za-z]{3,}[^\]\n]*\]", text)]
    return out


def humanlang_report(text: str) -> dict:
    """لوازم الصياغة الآلية لكل ألف كلمة، مع ما تجاوز حدّه والعبارات الواقعة."""
    words = max(len(re.findall(r"[ء-ي]+", text)), 1)
    out, flags, hits = {}, [], {}
    for name, c in cfg()["human_language"]["checks"].items():
        if name == "latin_notes":
            found = latin_notes(text)
            n = len(found)
            if found:
                hits[name] = found[:5]
        else:
            found = [p for p in c.get("patterns", []) if p in text]
            n = sum(text.count(p) for p in c.get("patterns", [])) + sum(text.count(ch) for ch in c.get("chars", []))
            if found:
                hits[name] = found[:8]
        per_k = round(1000 * n / words, 2) if name != "latin_notes" else n
        out[name] = per_k
        if per_k > c["max"]:
            flags.append(name)
    return {"per_1k": out, "flags": flags, "hits": hits, "ok": not flags}


def rules() -> list[str]:
    return cfg()["human_language"]["rules"]


# ------------------------------------------------------------------ ملف Word
def scrub_docx(doc, author: str = "", title: str = "") -> None:
    """يمحو بصمة المكتبة من خصائص الملف ويثبّت اسم المؤلف والعنوان."""
    from datetime import datetime, timezone
    cp = doc.core_properties
    now = datetime.now(timezone.utc).replace(microsecond=0)
    cp.author = cp.last_modified_by = author or ""
    cp.title = title or ""
    cp.comments = cp.keywords = cp.subject = cp.category = cp.content_status = cp.identifier = cp.version = ""
    cp.revision = 1
    cp.created = cp.modified = now


APP_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
           'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><DocSecurity>0</DocSecurity></Properties>')


def scrub_package(data: bytes) -> bytes:
    """تنقية حزمة Word بعد حفظها: صورة المعاينة المصغّرة الموروثة من القالب، واسم التطبيق المولِّد،
    ومعرّفات جلسات التحرير (rsid) التي تبقى بصمة للقالب في كل ملف."""
    import io
    import zipfile
    src = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            name = item.filename
            if name == "docProps/thumbnail.jpeg":
                continue
            body = src.read(name)
            if name == "docProps/app.xml":
                body = APP_XML.encode("utf-8")
            elif name == "_rels/.rels":
                body = re.sub(rb'<Relationship [^>]*metadata/thumbnail[^>]*/>', b"", body)
            elif name.startswith("word/") and name.endswith(".xml"):
                body = re.sub(rb'\s+w:rsid\w*="[0-9A-Fa-f]+"', b"", body)
                body = re.sub(rb"<w:rsids>.*?</w:rsids>", b"", body, flags=re.S)
                body = re.sub(rb"\s*<w:rsid [^>]*/>", b"", body)
                body = re.sub(rb"<w:savePreviewPicture/>", b"", body)
            out.writestr(item, body)
    return buf.getvalue()
