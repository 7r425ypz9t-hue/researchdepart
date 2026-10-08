"""تصدير النصوص إلى Word بالهوية البصرية (اتجاه من اليمين، Noto Naskh Arabic، عناوين زرقاء وخط ذهبي).

clean=True يحذف وسوم الادعاءات ومعرّفات الوحدات من نسخة القراءة؛ النسخة الأصلية (Markdown) تبقى بوسومها.
"""
from __future__ import annotations
import io
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

BLUE, GOLD = RGBColor(0x1F, 0x4E, 0x79), RGBColor(0xB8, 0x86, 0x0B)
FONT = "Noto Naskh Arabic"
TAGS = re.compile(r"\[(?:FACT|EBI|INTERP|HYP|AUTHOR)\]\s?")
NEEDS = re.compile(r"\[NEEDS-EVIDENCE(?::[^\]]*)?\]")   # يبقى ظاهراً للمؤلف بعلامة عربية: موضع يحتاج توثيقاً


def _rtl(par, align="both"):
    ppr = par._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    ppr.append(bidi)
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), align)
    ppr.append(jc)


def _run(par, text, size=14, bold=False, color=None):
    r = par.add_run(text)
    r.font.name, r.font.size, r.bold = FONT, Pt(size), bold
    if color:
        r.font.color.rgb = color
    rpr = r._r.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for k in ("w:ascii", "w:hAnsi", "w:cs"):
        fonts.set(qn(k), FONT)
    rtl = OxmlElement("w:rtl")
    rpr.append(rtl)
    szcs = OxmlElement("w:szCs")
    szcs.set(qn("w:val"), str(size * 2))
    rpr.append(szcs)
    if bold:
        rpr.append(OxmlElement("w:bCs"))
    return r


def _inline(par, text, size):
    """**غامق** داخل الفقرة."""
    for i, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if chunk:
            _run(par, chunk, size=size, bold=bool(i % 2))


def to_docx(markdown: str, title: str | None = None, clean: bool = True) -> bytes:
    if clean:
        markdown = TAGS.sub("", markdown)
        markdown = NEEDS.sub(" ⟨يحتاج توثيقاً⟩", markdown)
        markdown = re.sub(r"(?: ⟨يحتاج توثيقاً⟩)+", " ⟨يحتاج توثيقاً⟩", markdown)
        markdown = re.sub(r"\A---\n.*?\n---\n", "", markdown, flags=re.S)
        markdown = re.sub(r"\[@SRC-\d+[^\]]*\]", "", markdown)
    doc = Document()
    sec = doc.sections[0]
    sec.right_to_left = True
    st = doc.styles["Normal"]
    st.font.name, st.font.size = FONT, Pt(14)
    if title:
        p = doc.add_paragraph()
        _rtl(p, "center")
        _run(p, title, size=24, bold=True, color=BLUE)
        line = doc.add_paragraph()
        _rtl(line, "center")
        _run(line, "━━━━━━━━", size=12, color=GOLD)
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
            _run(p, m.group(2).strip(), size={1: 20, 2: 17, 3: 15}.get(level, 14), bold=True, color=BLUE)
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
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
