"""تصدير النصوص إلى Word بالهوية البصرية (اتجاه من اليمين، Noto Naskh Arabic، عناوين بلون الإدارة وخط ذهبي).

clean=True نسخة القراءة: تُحذف وسوم التصنيف، وتُترجم مواضع النقص والقرار إلى العربية بين قوسين.
clean=False نسخة المراجعة: كل الوسوم بالعربية بين قوسين. وفي الحالين تُنقّى العلامات المائية الظاهرة والمخفية
(runtime/rkpos/sanitize.py)، والأصل (Markdown) يبقى بوسومه المعيارية.
"""
from __future__ import annotations
import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from . import footnotes as FN, sanitize

BLUE, GOLD = RGBColor(0x1F, 0x4E, 0x79), RGBColor(0xB8, 0x86, 0x0B)
FONT = "Noto Naskh Arabic"


def _rtl(par, align="both"):
    ppr = par._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    ppr.append(bidi)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), {"start": "both", "center": "center", "both": "both"}[align])
    ppr.append(jc)


def _run(par, text, size=14, bold=False, color=None):
    """مقطع نصي بخط عربي واتجاه من اليمين؛ تُدرج عناصر الخصائص في مواضعها من المخطط (يرفض Word الترتيب الخاطئ)."""
    r = par.add_run(text)
    r.font.name, r.font.size, r.bold = FONT, Pt(size), bold
    if color:
        r.font.color.rgb = color
    rpr = r._r.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(k), FONT)
    if bold:
        rpr.find(qn("w:b")).addnext(OxmlElement("w:bCs"))
    szcs = OxmlElement("w:szCs")
    szcs.set(qn("w:val"), str(size * 2))
    rpr.find(qn("w:sz")).addnext(szcs)
    rpr.append(OxmlElement("w:rtl"))
    return r


def _segments(text: str) -> list[tuple]:
    """تقطيع السطر: الغامق (**…**)، وما بين الأقواس مع الأقواس نفسها (يُلوَّن بالأحمر)، ومواضع الحواشي."""
    segs, buf, bold, depth, i = [], [], False, 0, 0

    def flush(red: bool):
        if buf:
            segs.append(("t", "".join(buf), bold, red))
            buf.clear()
    while i < len(text):
        if text.startswith("**", i):
            flush(depth > 0)
            bold = not bold
            i += 2
            continue
        c = text[i]
        if c == FN.PH_OPEN and (j := text.find(FN.PH_CLOSE, i)) > i:
            flush(depth > 0)
            segs.append(("n", int(text[i + 1:j])))
            i = j + 1
            continue
        if c == "(":
            flush(depth > 0)
            depth += 1
        buf.append(c)
        if c == ")" and depth:
            flush(True)
            depth -= 1
        i += 1
    flush(depth > 0)
    return segs


def _note_ref(par, n: int, footnote_text: bool = False):
    """علامة الحاشية المرفوعة: في المتن تحيل إلى الحاشية n، وفي نص الحاشية رقمها."""
    r = par.add_run()
    rpr = r._r.get_or_add_rPr()
    va = OxmlElement("w:vertAlign")
    va.set(qn("w:val"), "superscript")
    rpr.append(va)
    rpr.append(OxmlElement("w:rtl"))
    if footnote_text:
        r._r.append(OxmlElement("w:footnoteRef"))
    else:
        ref = OxmlElement("w:footnoteReference")
        ref.set(qn("w:id"), str(n))
        r._r.append(ref)


def _inline(par, text, size, color=None, bold=False):
    """الغامق، والأقواس وما بينها بالأحمر، ومواضع الحواشي."""
    for seg in _segments(text):
        if seg[0] == "n":
            _note_ref(par, seg[1])
        else:
            _run(par, seg[1], size=size, bold=bold or seg[2], color=_red() if seg[3] else color)


def _red() -> RGBColor:
    return _rgb((sanitize.cfg().get("typography") or {}).get("brackets_color", "#FF0000"))


FOOTNOTES_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
def _separators(indent_twips: int) -> str:
    """الخط الفاصل بين المتن والحاشية: خط مفرد يبدأ من اليمين ويمتد إلى نصف عرض النص.
    الفقرة هنا من اليسار إلى اليمين عمداً، فتكون المسافة البادئة اليسرى يساراً بلا التباس، ويقع الخط في النصف الأيمن."""
    p = ('<w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="8" w:space="1" w:color="000000"/></w:pBdr>'
         f'<w:spacing w:before="120" w:after="0" w:line="240" w:lineRule="auto"/><w:ind w:left="{indent_twips}"/></w:pPr>'
         '<w:r><w:rPr><w:sz w:val="4"/><w:szCs w:val="4"/></w:rPr><w:t xml:space="preserve"> </w:t></w:r></w:p>')
    return (f'<w:footnote w:type="separator" w:id="-1">{p}</w:footnote>'
            f'<w:footnote w:type="continuationSeparator" w:id="0">{p}</w:footnote>')


def _footnotes_xml(notes: list[str], text_width_twips: int = 8640) -> bytes:
    """جزء الحواشي: كل حاشية فقرة من اليمين بخط أصغر، والأقواس فيها بالأحمر كذلك."""
    from lxml import etree
    tmp = Document()
    items = []
    for n, note in enumerate(notes, 1):
        p = tmp.add_paragraph()
        _rtl(p, "both")
        p.paragraph_format.space_after = Pt(0)
        _note_ref(p, n, footnote_text=True)
        _run(p, " ", size=11)
        _inline(p, note, 11)
        xml = etree.tostring(p._p, encoding="unicode")
        xml = re.sub(r'\sxmlns:\w+="[^"]*"', "", xml)
        items.append(f'<w:footnote w:id="{n}">{xml}</w:footnote>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:footnotes {FOOTNOTES_NS}>'
            f'{_separators(_sep_indent(text_width_twips))}{"".join(items)}</w:footnotes>').encode("utf-8")


def _sep_indent(text_width_twips: int) -> int:
    share = float((sanitize.cfg().get("typography") or {}).get("footnote_separator", 0.5))
    return int(text_width_twips * (1 - max(0.05, min(share, 1.0))))


def _attach_footnotes(data: bytes, notes: list[str], text_width_twips: int = 8640) -> bytes:
    """يضيف جزء الحواشي إلى الحزمة مع علاقته ونوع محتواه وإعداد الفواصل."""
    import zipfile
    src = zipfile.ZipFile(io.BytesIO(data))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for item in src.infolist():
            body = src.read(item.filename)
            if item.filename == "word/_rels/document.xml.rels":
                body = body.replace(b"</Relationships>", b'<Relationship Id="rIdFootnotes" Type="http://schemas.openxmlformats.org/'
                                    b'officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/></Relationships>')
            elif item.filename == "[Content_Types].xml":
                body = body.replace(b"</Types>", b'<Override PartName="/word/footnotes.xml" ContentType="application/'
                                    b'vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml"/></Types>')
            elif item.filename == "word/settings.xml":
                body = body.replace(b"<w:compat>", b'<w:footnotePr><w:footnote w:id="-1"/><w:footnote w:id="0"/>'
                                    b"</w:footnotePr><w:compat>", 1)
            out.writestr(item, body)
        out.writestr("word/footnotes.xml", _footnotes_xml(notes, text_width_twips))
    return buf.getvalue()


def _rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def to_docx(markdown: str, title: str | None = None, clean: bool = True, theme: dict | None = None,
            author: str = "", sources: list[dict] | None = None) -> bytes:
    """theme: ألوان الإدارة من نظام التصميم المركزي (primary للعناوين، accent للخط الفاصل).
    sources: سجل المصادر لبناء نصوص الحواشي؛ والاستشهادات تصير حواشي مرقّمة أسفل الصفحة."""
    blue = _rgb(theme["primary"]) if theme else BLUE
    gold = _rgb(theme["accent"]) if theme else GOLD
    notes: list[str] = []
    if (sanitize.cfg().get("typography") or {}).get("footnotes", True):
        markdown, notes = FN.collect(markdown, sources)
    markdown, _ = sanitize.clean(markdown, "reading" if clean else "tagged")
    if title:   # لا يتكرر العنوان إن كان النص يبدأ به
        markdown = re.sub(rf"\A#\s+{re.escape(title.strip())}\s*\n", "", markdown.lstrip())
    doc = Document()
    sec = doc.sections[0]
    sec.right_to_left = True
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(14)
    if title:
        p = doc.add_paragraph()
        _rtl(p, "center")
        _run(p, title, size=24, bold=True, color=blue)
        line = doc.add_paragraph()
        _rtl(line, "center")
        _run(line, "━━━━━━━━", size=12, color=gold)
    for block in re.split(r"\n\s*\n", markdown.strip()):
        block = block.strip()
        if not block or block.startswith(("```", "===")):
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", block)
        if m:
            level = len(m.group(1))
            p = doc.add_paragraph()
            _rtl(p, "start")
            p.paragraph_format.space_before = Pt(14)
            _inline(p, m.group(2).strip(), {1: 20, 2: 17, 3: 15}.get(level, 14), color=blue, bold=True)
            continue
        for line in block.split("\n"):
            line = line.rstrip()
            if not line:
                continue
            bullet = re.match(r"^\s*[-*•]\s+(.*)", line)
            p = doc.add_paragraph()
            _rtl(p, "both")
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.4
            _inline(p, ("• " + bullet.group(1)) if bullet else line, 14)
    sanitize.scrub_docx(doc, author=author, title=title or "")
    buf = io.BytesIO()
    doc.save(buf)
    data = sanitize.scrub_package(buf.getvalue())
    width = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)     # EMU ← twips
    return _attach_footnotes(data, notes, width) if notes else data
