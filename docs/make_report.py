# -*- coding: utf-8 -*-
"""Пояснительная записка курсового проекта «Пси-Эксперт» с полями Word."""

import os
from copy import deepcopy

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor, Twips
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "Пояснительная_записка_Пси-Эксперт.docx")
FONT = "Times New Roman"

TOPIC = "Разработка веб-сайта психологического центра «Пси-Эксперт»"


class C:
    def __init__(self):
        self.chapter = 0
        self.fig = 0
        self.tbl = 0
        self.bid = 10

    def start_chapter(self):
        self.chapter += 1
        self.fig = 0
        self.tbl = 0

    def take_fig(self):
        self.fig += 1
        return f"{self.chapter}.{self.fig}"

    def peek_fig(self):
        return f"{self.chapter}.{self.fig + 1}"

    def take_tbl(self):
        self.tbl += 1
        return f"{self.chapter}.{self.tbl}"

    def peek_tbl(self):
        return f"{self.chapter}.{self.tbl + 1}"

    def next_id(self):
        self.bid += 1
        return self.bid


N = C()


def _rpr(size=14, bold=False, italic=False, color=None):
    rPr = OxmlElement("w:rPr")
    fonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), FONT)
    rPr.append(fonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(size * 2)))
    sz2 = OxmlElement("w:szCs")
    sz2.set(qn("w:val"), str(int(size * 2)))
    rPr.append(sz)
    rPr.append(sz2)
    if bold:
        rPr.append(OxmlElement("w:b"))
        rPr.append(OxmlElement("w:bCs"))
    if italic:
        rPr.append(OxmlElement("w:i"))
        rPr.append(OxmlElement("w:iCs"))
    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rPr.append(c)
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "ru-RU")
    lang.set(qn("w:eastAsia"), "ru-RU")
    rPr.append(lang)
    return rPr


def add_text(p, text, size=14, bold=False, italic=False):
    r = OxmlElement("w:r")
    r.append(_rpr(size, bold, italic))
    t = OxmlElement("w:t")
    if text[:1].isspace() or text[-1:].isspace():
        t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    p._p.append(r)


def add_field(p, instr, cached, size=14, bold=False):
    def fld(kind, dirty=False):
        r = OxmlElement("w:r")
        r.append(_rpr(size, bold))
        fc = OxmlElement("w:fldChar")
        fc.set(qn("w:fldCharType"), kind)
        if dirty:
            fc.set(qn("w:dirty"), "true")
        r.append(fc)
        return r

    p._p.append(fld("begin", True))
    r = OxmlElement("w:r")
    r.append(_rpr(size, bold))
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr if instr.startswith(" ") else " " + instr + " "
    r.append(it)
    p._p.append(r)
    p._p.append(fld("separate"))
    add_text(p, cached, size=size, bold=bold)
    p._p.append(fld("end"))


def bookmark(p, name, bid, where="start"):
    tag = "w:bookmarkStart" if where == "start" else "w:bookmarkEnd"
    el = OxmlElement(tag)
    el.set(qn("w:id"), str(bid))
    if where == "start":
        el.set(qn("w:name"), name)
    p._p.append(el)


def P(doc, align="justify", indent=True, before=0, after=0, size_line=1.5,
      keep_next=False, style=None):
    p = doc.add_paragraph()
    if style:
        p.style = style
    p.alignment = {
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "left": WD_ALIGN_PARAGRAPH.LEFT,
    }[align]
    pf = p.paragraph_format
    pf.line_spacing = size_line
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.first_line_indent = Cm(1) if indent else Cm(0)
    pf.keep_with_next = keep_next
    # drop the empty run python-docx inserts
    for child in list(p._p):
        if child.tag == qn("w:r"):
            p._p.remove(child)
    return p


def rich(doc, parts, **kwargs):
    size = kwargs.pop("size", 14)
    p = P(doc, **kwargs)
    for part in parts:
        if isinstance(part, str):
            add_text(p, part, size=size)
        elif part[0] == "b":
            add_text(p, part[1], size=size, bold=True)
        elif part[0] == "i":
            add_text(p, part[1], size=size, italic=True)
        elif part[0] == "ref":
            add_field(p, f" REF {part[1]} \\h ", part[2], size=size)
        elif part[0] == "cite":
            add_text(p, "[", size=size)
            add_field(p, f" REF lit_{part[1]} \\h ", str(part[1]), size=size)
            add_text(p, "]", size=size)
    return p


def body(doc, text):
    return rich(doc, [text])


def item(doc, text):
    p = P(doc, align="justify", indent=False, before=0, after=2)
    p.paragraph_format.left_indent = Cm(1.25)
    add_text(p, "– " + text)
    return p


def force_heading_run(p, size):
    for r in p.runs:
        rPr = r._element.get_or_add_rPr()
        for child in list(rPr):
            if child.tag == qn("w:rFonts"):
                rPr.remove(child)
        rPr.insert(0, _rpr(size, bold=True).find(qn("w:rFonts")))
        # full rPr replacement keeps bold/size/color without theme
        for child in list(rPr):
            rPr.remove(child)
        for child in _rpr(size, bold=True):
            rPr.append(child)


def h1(doc, text):
    N.start_chapter()
    p = doc.add_heading(". " + text, level=1)
    force_heading_run(p, 16)
    return p


def h2(doc, text):
    p = doc.add_heading(". " + text, level=2)
    force_heading_run(p, 14)
    return p


def h3(doc, text):
    p = doc.add_heading(". " + text, level=3)
    force_heading_run(p, 14)
    return p


def plain_heading(doc, text):
    p = doc.add_paragraph(text, style="РазделБезНомера")
    return p


def _number_runs(p, chapter, local, bookmark_name, size=14):
    bid = N.next_id()
    bookmark(p, bookmark_name, bid, "start")
    add_field(p, " STYLEREF 1 \\s ", str(chapter), size=size)
    add_text(p, ".", size=size)
    add_field(p, f" SEQ {'Fig' if bookmark_name.startswith('fig') else 'Tbl'} \\* ARABIC \\s 1 ", str(local), size=size)
    bookmark(p, bookmark_name, bid, "end")


def figure(doc, key, filename, title, max_w=16.0):
    label = N.take_fig()
    chapter, local = label.split(".")
    path = os.path.join(IMG, filename)
    with Image.open(path) as im:
        wpx, hpx = im.size
    width_cm = max_w
    height_cm = width_cm * hpx / wpx
    if height_cm > 18.4:
        height_cm = 18.4
        width_cm = height_cm * wpx / hpx
    pic_p = P(doc, align="center", indent=False, before=8, after=0, keep_next=True)
    run = pic_p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    cap = P(doc, align="center", indent=False, before=4, after=10)
    add_text(cap, "Рис. ")
    _number_runs(cap, chapter, local, "fig_" + key)
    add_text(cap, ". " + title)
    return label


def table_caption(doc, key, title):
    label = N.take_tbl()
    chapter, local = label.split(".")
    cap = P(doc, align="right", indent=False, before=10, after=0, keep_next=True)
    add_text(cap, "Таблица ")
    _number_runs(cap, chapter, local, "tbl_" + key)
    title_p = P(doc, align="center", indent=False, before=0, after=4, keep_next=True)
    add_text(title_p, title)
    return label


def shade(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_cell_text(cell, text, bold=False, center=False, size=12):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    pf.line_spacing = 1.0
    # clear run
    for child in list(p._p):
        if child.tag == qn("w:r"):
            p._p.remove(child)
    add_text(p, text, size=size, bold=bold)
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for edge, val in (("top", "40"), ("bottom", "40"), ("left", "60"), ("right", "60")):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:w"), val)
        node.set(qn("w:type"), "dxa")
        mar.append(node)
    tcPr.append(mar)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl = table._tbl
    tblPr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), "5000")
    tblW.set(qn("w:type"), "pct")
    # header repeat
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    trPr.append(tblHeader)
    usable = 17.0
    if widths is None:
        widths = [usable / len(headers)] * len(headers)
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        set_cell_text(cell, h, bold=True, center=True)
        shade(cell, "E7E1D6")
        cell.width = Cm(widths[i])
    for r_i, row in enumerate(rows):
        for c_i, value in enumerate(row):
            cell = table.rows[r_i + 1].cells[c_i]
            set_cell_text(cell, value, center=(c_i == 0 and len(value) < 18))
            if r_i % 2 == 1:
                shade(cell, "F7F5F1")
            cell.width = Cm(widths[c_i])
    # grid columns
    grid = tbl.find(qn("w:tblGrid"))
    if grid is not None:
        for i, child in enumerate(list(grid)):
            if i < len(widths):
                child.set(qn("w:w"), str(int(widths[i] * 567)))
    gap = P(doc, indent=False, before=2, after=2)
    return table


def set_run_font_on_style(style, size_pt, bold=None, italic=None):
    style.font.name = FONT
    style.font.size = Pt(size_pt)
    if bold is not None:
        style.font.bold = bold
    if italic is not None:
        style.font.italic = italic
    rPr = style.element.get_or_add_rPr()
    fonts = rPr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rPr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), FONT)
    lang = rPr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rPr.append(lang)
    lang.set(qn("w:val"), "ru-RU")


def style_paragraph(style, *, before=0, after=8, line=1.15, align="left",
                    first=0, page_break=False, keep_next=True, keep_together=True, outline=None):
    pf = style.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = line
    pf.first_line_indent = Cm(first)
    pf.page_break_before = page_break
    pf.keep_with_next = keep_next
    pf.keep_together = keep_together
    style.paragraph_format.alignment = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }[align]
    if outline is not None:
        pPr = style.element.get_or_add_pPr()
        ol = pPr.find(qn("w:outlineLvl"))
        if ol is None:
            ol = OxmlElement("w:outlineLvl")
            pPr.append(ol)
        ol.set(qn("w:val"), str(outline))


def attach_numbering(style, ilvl, num_id="10"):
    pPr = style.element.get_or_add_pPr()
    old = pPr.find(qn("w:numPr"))
    if old is not None:
        pPr.remove(old)
    numPr = OxmlElement("w:numPr")
    il = OxmlElement("w:ilvl")
    il.set(qn("w:val"), str(ilvl))
    nid = OxmlElement("w:numId")
    nid.set(qn("w:val"), num_id)
    numPr.append(il)
    numPr.append(nid)
    # numbering should be first child of pPr for Word
    pPr.insert(0, numPr)


def ensure_numbering(doc):
    numbering = doc.part.numbering_part._element

    def lvl(ilvl, text, size_half_points):
        node = OxmlElement("w:lvl")
        node.set(qn("w:ilvl"), str(ilvl))
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        fmt = OxmlElement("w:numFmt")
        fmt.set(qn("w:val"), "decimal")
        txt = OxmlElement("w:lvlText")
        txt.set(qn("w:val"), text)
        jc = OxmlElement("w:lvlJc")
        jc.set(qn("w:val"), "left")
        suff = OxmlElement("w:suff")
        suff.set(qn("w:val"), "nothing")
        pPr = OxmlElement("w:pPr")
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), "0")
        ind.set(qn("w:firstLine"), "0")
        pPr.append(ind)
        rPr = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts")
        for attr in ("w:ascii", "w:hAnsi", "w:cs"):
            fonts.set(qn(attr), FONT)
        rPr.append(fonts)
        rPr.append(OxmlElement("w:b"))
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(size_half_points))
        rPr.append(sz)
        node.extend([start, fmt, txt, jc, suff, pPr, rPr])
        return node

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), "10")
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "multilevel")
    abstract.append(multi)
    abstract.append(lvl(0, "%1", 32))
    abstract.append(lvl(1, "%1.%2", 28))
    abstract.append(lvl(2, "%1.%2.%3", 28))
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), "10")
    absId = OxmlElement("w:abstractNumId")
    absId.set(qn("w:val"), "10")
    num.append(absId)
    numbering.append(abstract)
    numbering.append(num)


def configure_styles(doc):
    normal = doc.styles["Normal"]
    set_run_font_on_style(normal, 14, bold=False, italic=False)
    style_paragraph(normal, before=0, after=0, line=1.5, align="justify",
                    first=1.0, page_break=False, keep_next=False, keep_together=False, outline=None)
    normal.font.color.rgb = RGBColor(0, 0, 0)

    h = doc.styles["Heading 1"]
    set_run_font_on_style(h, 16, bold=True, italic=False)
    style_paragraph(h, before=0, after=12, line=1.5, align="left",
                    first=0, page_break=True, keep_next=True, outline=0)
    h.font.color.rgb = RGBColor(0, 0, 0)
    attach_numbering(h, 0)

    h = doc.styles["Heading 2"]
    set_run_font_on_style(h, 14, bold=True, italic=False)
    style_paragraph(h, before=16, after=8, line=1.5, align="left",
                    first=0, page_break=False, keep_next=True, outline=1)
    h.font.color.rgb = RGBColor(0, 0, 0)
    attach_numbering(h, 1)

    h = doc.styles["Heading 3"]
    set_run_font_on_style(h, 14, bold=True, italic=False)
    style_paragraph(h, before=12, after=6, line=1.5, align="left",
                    first=0, page_break=False, keep_next=True, outline=2)
    h.font.color.rgb = RGBColor(0, 0, 0)
    attach_numbering(h, 2)

    plain = doc.styles.add_style("РазделБезНомера", 1)
    set_run_font_on_style(plain, 16, bold=True, italic=False)
    style_paragraph(plain, before=0, after=12, line=1.5, align="left",
                    first=0, page_break=True, keep_next=True, outline=0)
    plain.font.color.rgb = RGBColor(0, 0, 0)
    _strip_theme_fonts(doc)


def _strip_theme_fonts(doc):
    """Тема Word подменяет Times New Roman, если в стиле остался asciiTheme."""
    styles = doc.styles.element
    for rFonts in styles.iter(qn("w:rFonts")):
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
            if rFonts.get(qn(attr)) is not None:
                del rFonts.attrib[qn(attr)]
        if rFonts.get(qn("w:ascii")) is None:
            for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                rFonts.set(qn(attr), FONT)
    # связанные знаковые стили заголовков — чёрные, без синего Accent
    sizes = {"Heading1Char": "32", "Heading2Char": "28", "Heading3Char": "28"}
    for style in styles.findall(qn("w:style")):
        sid = style.get(qn("w:styleId"))
        if sid not in sizes:
            continue
        rPr = style.find(qn("w:rPr"))
        if rPr is None:
            rPr = OxmlElement("w:rPr")
            style.append(rPr)
        for tag in ("w:color", "w:sz", "w:szCs"):
            node = rPr.find(qn(tag))
            if node is not None:
                rPr.remove(node)
        color = OxmlElement("w:color")
        color.set(qn("w:val"), "000000")
        rPr.append(color)
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), sizes[sid])
        sz2 = OxmlElement("w:szCs")
        sz2.set(qn("w:val"), sizes[sid])
        rPr.append(sz)
        rPr.append(sz2)
    defaults = styles.find(qn("w:docDefaults"))
    if defaults is None:
        defaults = OxmlElement("w:docDefaults")
        styles.insert(0, defaults)
    rPrDefault = defaults.find(qn("w:rPrDefault"))
    if rPrDefault is None:
        rPrDefault = OxmlElement("w:rPrDefault")
        defaults.append(rPrDefault)
    rPr = rPrDefault.find(qn("w:rPr"))
    if rPr is None:
        rPr = OxmlElement("w:rPr")
        rPrDefault.append(rPr)
    # replace fonts
    old = rPr.find(qn("w:rFonts"))
    if old is not None:
        rPr.remove(old)
    rPr.insert(0, _rpr(14).find(qn("w:rFonts")))
    if rPr.find(qn("w:sz")) is None:
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), "28")
        rPr.append(sz)
        sz2 = OxmlElement("w:szCs")
        sz2.set(qn("w:val"), "28")
        rPr.append(sz2)


def setup_section(doc):
    sec = doc.sections[0]
    sec.page_width = Mm(210)
    sec.page_height = Mm(297)
    sec.top_margin = Cm(3)
    sec.bottom_margin = Cm(2)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(1.5)
    sec.header_distance = Cm(1.0)
    sec.footer_distance = Cm(0.8)
    sec.different_first_page_header_footer = True

    header = sec.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    hp.paragraph_format.first_line_indent = Cm(0)
    hp.paragraph_format.space_before = Pt(0)
    hp.paragraph_format.space_after = Pt(0)
    for child in list(hp._p):
        if child.tag == qn("w:r"):
            hp._p.remove(child)
    add_text(hp, TOPIC, size=12, italic=True)
    # bottom border of header
    pPr = hp._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "1A6B62")
    pBdr.append(bottom)
    pPr.append(pBdr)

    fp = sec.first_page_header.paragraphs[0]
    fp.text = ""

    footer = sec.footer
    footer.is_linked_to_previous = False
    fpager = footer.paragraphs[0]
    fpager.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fpager.paragraph_format.first_line_indent = Cm(0)
    for child in list(fpager._p):
        if child.tag == qn("w:r"):
            fpager._p.remove(child)
    add_field(fpager, " PAGE ", "2", size=12)
    sec.first_page_footer.paragraphs[0].text = ""

    settings = doc.settings.element
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    settings.append(upd)


def title_page(doc):
    lines = [
        (14, False, "Министерство науки и высшего образования Российской Федерации"),
        (14, False, "Государственное бюджетное образовательное учреждение высшего образования"),
        (14, True, "Псковский государственный университет"),
        (14, False, "Передовая инженерная школа гибридных технологий в станкостроении Союзного государства"),
    ]
    for i, (size, bold, text) in enumerate(lines):
        p = P(doc, align="center", indent=False, before=0, after=2)
        add_text(p, text, size=size, bold=bold)
    for _ in range(3):
        P(doc, align="center", indent=False, before=0, after=0)
    p = P(doc, align="center", indent=False, before=18, after=4)
    add_text(p, "Курсовой проект", size=20, bold=True)
    p = P(doc, align="center", indent=False, before=2, after=2)
    add_text(p, "по дисциплине «Веб-программирование»", size=16)
    p = P(doc, align="center", indent=False, before=8, after=2)
    add_text(p, "на тему: " + TOPIC, size=16, bold=True)
    for _ in range(4):
        P(doc, align="center", indent=False)
    block = [
        "Выполнил студент",
        "группы 0434-03:",
        "Чуров А.А.",
        "Проверил преподаватель:",
        "Бруттан Ю. В.",
    ]
    for text in block:
        p = P(doc, align="right", indent=False, before=0, after=2)
        add_text(p, text, size=14, bold=(text.startswith("Чуров") or text.startswith("Бруттан")))
    for _ in range(3):
        P(doc, align="center", indent=False)
    p = P(doc, align="center", indent=False, before=12, after=0)
    add_text(p, "Псков", size=14)
    p = P(doc, align="center", indent=False, before=0, after=0)
    add_text(p, "2026", size=14)


TOC_LINES = [
    (0, "1.", "Техническое задание", "3"),
    (1, "1.1.", "Название проекта. Назначение веб-сайта", "3"),
    (1, "1.2.", "Требования к веб-сайту", "4"),
    (2, "1.2.1.", "Функциональные требования", "4"),
    (2, "1.2.2.", "Информационные требования", "6"),
    (0, "2.", "Проектирование веб-сайта", "8"),
    (1, "2.1.", "Проектирование карты сайта", "8"),
    (1, "2.2.", "Проектирование базы данных веб-сайта", "11"),
    (2, "2.2.1.", "Структура базы данных", "11"),
    (2, "2.2.2.", "Описание таблиц базы данных", "12"),
    (1, "2.3.", "Проектирование шаблонов веб-страниц сайта", "16"),
    (0, "3.", "Разработка модулей веб-сайта", "22"),
    (1, "3.1.", "Разработка модуля оформления заказа", "22"),
    (1, "3.2.", "Разработка модуля управления заказами зарегистрированных пользователей", "24"),
    (1, "3.3.", "Разработка модуля управления пользователями", "25"),
    (1, "3.4.", "Разработка модуля управления каталогом", "27"),
    (1, "3.5.", "Разработка модуля управления новостями", "28"),
    (0, "", "Вывод", "30"),
    (0, "", "Список литературы", "31"),
]


def contents(doc):
    p = P(doc, align="center", indent=False, before=0, after=12)
    p.paragraph_format.page_break_before = True
    add_text(p, "Содержание", size=16, bold=True)

    # field begins in its own paragraph and spans the cached entries
    start = P(doc, align="left", indent=False, before=0, after=0, size_line=1.5)
    r = OxmlElement("w:r")
    r.append(_rpr(14))
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "begin")
    fc.set(qn("w:dirty"), "true")
    r.append(fc)
    start._p.append(r)
    r = OxmlElement("w:r")
    r.append(_rpr(14))
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = ' TOC \\o "1-3" \\h \\z \\u '
    r.append(it)
    start._p.append(r)
    r = OxmlElement("w:r")
    r.append(_rpr(14))
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "separate")
    r.append(fc)
    start._p.append(r)

    paras = [start]
    for level, num, title, page in TOC_LINES:
        if paras[0] is start and start._p.find(qn("w:r")) is not None and len(paras) == 1 and not any(
            c.tag == qn("w:t") for c in start._p.iter()
        ):
            host = start
        else:
            host = P(doc, align="left", indent=False, before=1, after=1, size_line=1.5)
            paras.append(host)
        # first entry goes into the paragraph that already holds separate
        if host is not start or any(c.tag == qn("w:t") for c in start._p.iter()):
            if host is start:
                pass
        left = {0: 0, 1: 0.75, 2: 1.5}[level]
        host.paragraph_format.left_indent = Cm(left)
        tabs = host.paragraph_format.tab_stops
        tabs.add_tab_stop(Cm(16.2), alignment=WD_ALIGN_PARAGRAPH.RIGHT, leader=2)  # may fail
        label = (num + " " if num else "") + title
        add_text(host, label, size=14, bold=(level == 0))
        add_text(host, "\t" + page, size=14)
    # The loop above is messy if the first paragraph logic is wrong.
    # Rebuild cleanly below if we detect we put nothing. We'll instead
    # construct TOC in a simpler second pass by not using this function's loop.
    return


def contents_clean(doc):
    """Содержание: поле TOC, результат кэширован построчно."""
    title = P(doc, align="center", indent=False, before=0, after=12)
    title.paragraph_format.page_break_before = True
    add_text(title, "Содержание", size=16, bold=True)

    entries = []
    for idx, (level, num, name, page) in enumerate(TOC_LINES):
        p = P(doc, align="left", indent=False, before=1, after=1, size_line=1.5)
        p.paragraph_format.left_indent = Cm({0: 0, 1: 0.75, 2: 1.5}[level])
        pPr = p._p.get_or_add_pPr()
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "right")
        tab.set(qn("w:leader"), "dot")
        tab.set(qn("w:pos"), "9639")  # ~17 cm from left margin in twips (17*567)
        tabs.append(tab)
        pPr.append(tabs)
        if idx == 0:
            r = OxmlElement("w:r")
            r.append(_rpr(14, bold=True))
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), "begin")
            fc.set(qn("w:dirty"), "true")
            r.append(fc)
            p._p.append(r)
            r = OxmlElement("w:r")
            r.append(_rpr(14))
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = ' TOC \\o "1-3" \\h \\z \\u '
            r.append(it)
            p._p.append(r)
            r = OxmlElement("w:r")
            r.append(_rpr(14))
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), "separate")
            r.append(fc)
            p._p.append(r)
        add_text(p, ((num + " ") if num else "") + name, size=14, bold=(level == 0))
        r = OxmlElement("w:r")
        r.append(_rpr(14))
        r.append(OxmlElement("w:tab"))
        p._p.append(r)
        add_text(p, page, size=14)
        entries.append(p)
    last = entries[-1]
    r = OxmlElement("w:r")
    r.append(_rpr(14))
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "end")
    r.append(fc)
    last._p.append(r)


def section_tz(doc):
    h1(doc, "Техническое задание")
    h2(doc, "Название проекта. Назначение веб-сайта")
    body(doc, "Название проекта — веб-сайт психологического центра «Пси-Эксперт».")
    rich(doc, [
        "Сайт предназначен для Первого Псковского профессионального психологического центра «Пси-Эксперт». "
        "Центр оказывает взрослым консультации, терапию и кризисную поддержку, работает с тревогой, депрессией и отношениями. "
        "Назначение сайта — показать услуги, новости и полезные видео, принять запись зарегистрированного клиента "
        "и дать сотрудникам средство вести эту запись. Сведения об услугах, пользователях и новостях "
        "хранятся в базе данных и выводятся на страницы, оформленные одной таблицей стилей ",
        ("cite", 2),
        ". Правила разработки и состав отчёта приняты по учебно-методическому пособию ",
        ("cite", 4),
        ".",
    ])
    body(doc,
         "Проект выполнен на языке Python с библиотекой Django 4.2 и СУБД SQLite. "
         "Страницы собраны шаблонами Django, оформление — собственный файл CSS. "
         "Отдельный клиентский каркас (React и аналоги) не используется: страница формируется на сервере. "
         "Решение открывается в Visual Studio 2022: файл psi-exp.sln, стартовый файл manage.py, "
         "модуль настроек PsiExpert.settings, запуск — Django launcher клавишей F5. "
         "Наполнение каталога, новостей и видео загружается командой python manage.py seed.")
    body(doc,
         "Заказчик учебной работы — преподаватель дисциплины «Веб-программирование». "
         "Исполнитель — студент группы 0434-03 Чуров А. А. Год выполнения — 2026.")

    h2(doc, "Требования к веб-сайту")
    body(doc,
         "Требуется сайт организации с элементами электронной коммерции: каталог услуг, корзина записи и заказы. "
         "На всех страницах доступно одно и то же меню. Оформление общее: спокойный тёмный текст, "
         "бирюзовый акцент, бумажный фон, логотип центра, фотографии и карточки услуг. "
         "Доступ к данным зависит от роли посетителя. Ролей четыре: гость, клиент, менеджер, администратор. "
         "Работа ведётся со взрослыми от 18 лет. Дети, подростки, зависимости и психиатрические диагнозы в каталог не входят.")

    h3(doc, "Функциональные требования")
    body(doc, "Гость не проходит аутентификацию и может только смотреть открытые страницы и завести учётную запись клиента.")
    item(doc, "Смотреть главную страницу: название, логотип, аннотацию, три последние новости и переход в каталог.")
    item(doc, "Смотреть страницу «О центре»: формат работы и границы запросов.")
    item(doc, "Смотреть каталог трёх категорий и карточку выбранной услуги.")
    item(doc, "Смотреть список новостей и текст одной новости.")
    item(doc, "Смотреть страницу «Полезные материалы» с видео.")
    item(doc, "Смотреть контакты центра и сведения о разработчике.")
    item(doc, "Зарегистрироваться и войти. Корзина, заказы и панель администратора гостю закрыты.")

    body(doc, "Клиент — зарегистрированный посетитель. Ему доступны все открытые страницы и операции со своей записью.")
    item(doc, "Положить услугу в корзину, изменить количество (не больше 8) и убрать позицию.")
    item(doc, "Оформить запись: телефон, способ связи и необязательный комментарий. После записи корзина очищается.")
    item(doc, "Открыть «Мои заказы» и увидеть состав, сумму и статус каждой своей записи.")
    item(doc, "Изменить телефон, способ связи и комментарий либо удалить запись, пока статус «Новая» или «В работе».")
    item(doc, "Выйти из сессии. Чужие записи и панель администратора клиенту недоступны.")

    body(doc, "Менеджер ведёт записи клиентов и не пользуется корзиной.")
    item(doc, "Смотреть открытые страницы сайта.")
    item(doc, "Открыть страницу «Заказы» со всеми записями: состав, сумма, телефон, способ связи, комментарий.")
    item(doc, "Назначить статус: «Новая», «В работе», «Проведена» или «Отменена».")
    item(doc, "Не имеет корзины и не открывает панель администратора.")

    body(doc, "Администратор управляет наполнением после входа. Учётная запись администратора создаётся заранее и через сайт не удаляется.")
    item(doc, "Добавлять, изменять и удалять категории. Повтор названия, в том числе с другим регистром букв, отклоняется.")
    item(doc, "Добавлять, изменять и удалять услуги: категория, стоимость, описание, длительность, метод, изображение, признак доступности.")
    item(doc, "Добавлять, изменять и удалять новости: заголовок, текст, дата публикации.")
    item(doc, "Добавлять, изменять и удалять видео полезных материалов.")
    item(doc, "Регистрировать пользователя с ролью «Менеджер».")
    item(doc, "Удалять пользователей с ролью «Клиент» или «Менеджер». Удаление администратора запрещено.")
    item(doc, "Дополнительно доступна стандартная панель Django по адресу /admin/ с теми же данными.")

    body(doc,
         "Для проверки ролей в учебную базу записаны учётные записи: "
         "администратор — admin / PsiAdmin!26; менеджер — manager / PsiManager!26; "
         "клиент — client / PsiClient!26. Пароли показаны на странице входа, потому что база демонстрационная.")

    h3(doc, "Информационные требования")
    rich(doc, [
        "Информационные элементы и их атрибуты сведены в таблицу ",
        ("ref", "tbl_elements", N.peek_tbl()),
        ". Каталог иерархический: не меньше трёх категорий и пяти наименований в каждой. "
        "В поставке три категории — «Индивидуальная терапия», «Специальные методы», «Форматы консультаций» — и пятнадцать услуг. "
        "Страница «Полезные материалы» добавлена по теме центра: видео лежат отдельно от новостей и читаются из базы.",
    ])
    table_caption(doc, "elements", "Информационные элементы сайта")
    add_table(
        doc,
        ["Элемент", "Атрибуты", "Кто видит"],
        [
            ["Главная", "Название, логотип, аннотация, три категории, три последние новости", "Все роли"],
            ["О центре", "Формат сессий, длительность, границы запросов", "Все роли"],
            ["Новости", "Заголовок, текст, дата публикации. Список по убыванию даты", "Все роли"],
            ["Контакты", "Телефон, WhatsApp, Telegram, город, часы, сведения о разработчике", "Все роли"],
            ["Каталог", "Категория: название, описание, порядок. Услуга: изображение, название, стоимость, длительность, метод, описание", "Все роли"],
            ["Карточка услуги", "Те же атрибуты услуги и другие услуги той же категории", "Все роли"],
            ["Полезные материалы", "Название, описание, видеофайл", "Все роли"],
            ["Корзина", "Услуга, количество, сумма строки, итог", "Клиент"],
            ["Мои заказы", "Номер, дата, статус, телефон, способ связи, комментарий, позиции, сумма", "Клиент, только свои"],
            ["Заказы", "Те же атрибуты записи плюс учётная запись клиента", "Менеджер"],
            ["Регистрация", "Логин, имя, фамилия, почта, телефон, пароль", "Гость"],
            ["Панель", "Категории, услуги, новости, видео, пользователи и их роли", "Администратор"],
        ],
        widths=[3.4, 9.1, 4.5],
    )
    body(doc,
         "Навигация на каждой странице содержит пункты «Главная», «О центре», «Каталог», «Новости», "
         "«Полезные материалы», «Контакты». "
         "Гость видит «Вход» и «Регистрация». Клиент — «Корзина», «Мои заказы» и «Выход». "
         "Менеджер — «Заказы» и «Выход». Администратор — «Панель» и «Выход». "
         "Подвал повторяет имя центра, город и строку о разработчике.")
    body(doc,
         "Главная страница содержит название «Пси-Эксперт», подзаголовок о первом Псковском профессиональном "
         "психологическом центре, логотип, краткую аннотацию и ровно три последние новости. "
         "Каталог собирается выборкой из базы: внутри категории выводятся её услуги, переход по адресу категории "
         "оставляет одну ветвь иерархии. Страница «Контакты» содержит телефон +7 (911) 377-88-11, "
         "WhatsApp и Telegram @viva0stress, указание «г. Псков, очно и онлайн», часы записи "
         "и сведения о разработчике: Чуров А. А., группа 0434-03.")


def section_design(doc):
    h1(doc, "Проектирование веб-сайта")
    h2(doc, "Проектирование карты сайта")
    body(doc,
         "Карта сайта показывает, какие страницы открыты каждой роли. Общий ствол один: главная страница "
         "ведёт в раздел о центре, новости, контакты, каталог и полезные материалы. Дальше маршруты расходятся. "
         "Каталог — иерархия: категория, затем карточка услуги. Служебные страницы нарисованы только у той роли, "
         "которая имеет на них право. Так карта совпадает с проверками в представлениях, а не только с пунктами меню.")
    rich(doc, [
        "Карта гостя приведена на рисунке ",
        ("ref", "fig_guest", N.peek_fig()),
        ". Гость доходит до каталога и трёх категорий, открывает карточку услуги, новости, видео и контакты, "
        "а также формы входа и регистрации. Корзины на этой карте нет.",
    ])
    figure(doc, "guest", "Карта_сайта_гость.png", "Карта сайта для роли «Гость»", 15.6)
    rich(doc, [
        "Карта клиента приведена на рисунке ",
        ("ref", "fig_client", N.peek_fig()),
        ". К открытым страницам добавляются корзина (изменение количества и удаление позиции), "
        "оформление заказа и «Мои заказы» с просмотром, изменением и удалением. Вместо входа показан выход.",
    ])
    figure(doc, "client", "Карта_сайта_клиент.png", "Карта сайта для роли «Клиент»", 15.6)
    rich(doc, [
        "Карта менеджера приведена на рисунке ",
        ("ref", "fig_manager", N.peek_fig()),
        ". Менеджер смотрит витрину и открывает единственную служебную ветвь — заказы клиентов: "
        "просмотр состава и смена статуса.",
    ])
    figure(doc, "manager", "Карта_сайта_менеджер.png", "Карта сайта для роли «Менеджер»", 15.6)
    rich(doc, [
        "Карта администратора приведена на рисунке ",
        ("ref", "fig_admin", N.peek_fig()),
        ". К витрине добавляется панель с пятью разделами: категории, услуги, новости, видео и пользователи. "
        "Именно здесь выполняются функции удалённого управления наполнением.",
    ])
    figure(doc, "admin", "Карта_сайта_администратор.png", "Карта сайта для роли «Администратор»", 15.6)

    h2(doc, "Проектирование базы данных веб-сайта")
    h3(doc, "Структура базы данных")
    rich(doc, [
        "Данные хранит файл SQLite. Схема прикладных таблиц показана на рисунке ",
        ("ref", "fig_er", N.peek_fig()),
        ". Пользователь Django (USER) связан с профилем роли один к одному, с корзиной один к одному "
        "и с заказами один ко многим. Категория связана с услугами один ко многим, удаление категории при живых услугах запрещено. "
        "Позиция корзины ссылается на корзину и на услугу. Позиция заказа ссылается на заказ обязательно, "
        "а на услугу — необязательно: если услугу снимут с каталога, в записи останутся название и цена. "
        "Новости и полезные видео самостоятельны и связей с заказом не имеют.",
    ])
    figure(doc, "er", "Схема_базы_данных.png", "Схема базы данных", 16.4)
    body(doc,
         "Служебные таблицы Django (сессии, права, журнал администратора) на схеме не показаны: "
         "прикладная логика их не читает напрямую. Роль хранится не флагом is_staff, а полем profile.role, "
         "чтобы клиент, менеджер и администратор различались явно. Уникальность названия категории "
         "держит поле name_key — название, приведённое к одному регистру. Обычное сравнение SQLite "
         "не складывает русские буквы «В» и «в», поэтому проверка сделана в модели и в форме до записи.")

    h3(doc, "Описание таблиц базы данных")
    body(doc, "Ниже приведена структура таблиц, которые наполняют страницы. Имена полей совпадают со столбцами SQLite.")

    specs = [
        ("user", "Структура таблицы USER (auth_user)",
         "Таблица учётных записей. Пароль хранится только в виде хеша Django.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["username", "VARCHAR(150)", "UNIQUE, NOT NULL", "Логин"],
             ["password", "VARCHAR(128)", "NOT NULL", "Хеш пароля"],
             ["email", "VARCHAR(254)", "—", "Почта"],
             ["first_name", "VARCHAR(150)", "—", "Имя"],
             ["last_name", "VARCHAR(150)", "—", "Фамилия"],
             ["is_active", "BOOLEAN", "NOT NULL", "Учётная запись включена"],
             ["is_staff", "BOOLEAN", "NOT NULL", "Доступ в /admin/"],
             ["is_superuser", "BOOLEAN", "NOT NULL", "Полные права Django"],
             ["date_joined", "DATETIME", "NOT NULL", "Дата регистрации"],
         ],
         [3.4, 3.6, 3.8, 6.2]),
        ("profile", "Структура таблицы PROFILE (app_profile)",
         "Профиль дополняет пользователя ролью и телефоном. При регистрации сигнал создаёт профиль с ролью «Клиент».",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["user_id", "INTEGER", "FK, UNIQUE, CASCADE", "Ссылка на USER"],
             ["role", "VARCHAR(20)", "NOT NULL", "client, manager или admin"],
             ["phone", "VARCHAR(20)", "пустое допускается", "Телефон"],
         ],
         [3.2, 3.6, 4.2, 6.0]),
        ("category", "Структура таблицы CATEGORY (app_category)",
         "Категория каталога. Поле name_key не редактируется вручную: его записывает модель из названия.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["name", "VARCHAR(120)", "NOT NULL", "Название на витрине"],
             ["name_key", "VARCHAR(120)", "UNIQUE, NOT NULL", "Название без учёта регистра"],
             ["slug", "VARCHAR(140)", "UNIQUE, NOT NULL", "Адрес категории"],
             ["description", "TEXT", "пустое допускается", "Пояснение в каталоге"],
             ["position", "INTEGER", "NOT NULL", "Порядок вывода"],
         ],
         [3.3, 3.4, 4.2, 6.1]),
        ("product", "Структура таблицы SERVICE (app_service)",
         "Услуга каталога. Категорию удалить нельзя, пока на неё ссылается хотя бы одна строка (ON DELETE PROTECT).",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["category_id", "INTEGER", "FK, PROTECT, NOT NULL", "Категория"],
             ["name", "VARCHAR(200)", "NOT NULL", "Название"],
             ["price", "DECIMAL(10,2)", "NOT NULL", "Стоимость, руб."],
             ["duration", "VARCHAR(80)", "NOT NULL", "Длительность"],
             ["method", "VARCHAR(160)", "пустое допускается", "Метод"],
             ["description", "TEXT", "NOT NULL", "Описание"],
             ["image", "VARCHAR(100)", "пустое допускается", "Файл в media/services"],
             ["available", "BOOLEAN", "NOT NULL", "Открыта для записи"],
             ["created_at", "DATETIME", "NOT NULL", "Дата добавления"],
         ],
         [3.4, 4.2, 4.0, 5.4]),
        ("news", "Структура таблицы NEWS (app_news)",
         "Новость организации. Список на сайте сортируется по published_at по убыванию.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["title", "VARCHAR(200)", "NOT NULL", "Заголовок"],
             ["text", "TEXT", "NOT NULL", "Текст"],
             ["published_at", "DATETIME", "NOT NULL", "Дата публикации"],
         ],
         [3.4, 3.6, 4.0, 6.0]),
        ("cart", "Структура таблицы CART (app_cart)",
         "Одна корзина на пользователя. Создаётся при первом добавлении услуги.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["user_id", "INTEGER", "FK, UNIQUE, CASCADE", "Владелец"],
             ["created_at", "DATETIME", "NOT NULL", "Момент создания"],
         ],
         [3.2, 4.4, 4.4, 5.0]),
        ("citem", "Структура таблицы CART_ITEM (app_cartitem)",
         "Позиция корзины. Пара «корзина + услуга» уникальна: повторное добавление увеличивает количество.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["cart_id", "INTEGER", "FK, CASCADE, NOT NULL", "Корзина"],
             ["service_id", "INTEGER", "FK, CASCADE, NOT NULL", "Услуга"],
             ["quantity", "INTEGER", "NOT NULL, по умолчанию 1", "Количество"],
         ],
         [3.2, 4.6, 4.6, 4.6]),
        ("order", "Структура таблицы ORDER (app_order)",
         "Запись клиента. Статус принимает значения new, in_progress, done, cancelled.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Номер записи"],
             ["user_id", "INTEGER", "FK, CASCADE, NOT NULL", "Клиент"],
             ["created_at", "DATETIME", "NOT NULL", "Дата создания"],
             ["status", "VARCHAR(20)", "NOT NULL", "Статус"],
             ["total", "DECIMAL(12,2)", "NOT NULL", "Сумма на момент записи"],
             ["phone", "VARCHAR(20)", "NOT NULL", "Телефон"],
             ["contact", "VARCHAR(200)", "NOT NULL", "Как связаться"],
             ["comment", "TEXT", "пустое допускается", "Комментарий клиента"],
         ],
         [3.3, 3.6, 4.2, 5.9]),
        ("oitem", "Структура таблицы ORDER_ITEM (app_orderitem)",
         "Строка записи. service_name и price копируются из каталога, чтобы история не зависела от будущей правки стоимости.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["order_id", "INTEGER", "FK, CASCADE, NOT NULL", "Запись"],
             ["service_id", "INTEGER", "FK, SET NULL", "Услуга, если ещё есть в каталоге"],
             ["service_name", "VARCHAR(200)", "NOT NULL", "Название на момент записи"],
             ["quantity", "INTEGER", "NOT NULL", "Количество"],
             ["price", "DECIMAL(10,2)", "NOT NULL", "Цена на момент записи"],
         ],
         [3.4, 3.6, 4.4, 5.6]),
        ("video", "Структура таблицы MATERIAL_VIDEO (app_materialvideo)",
         "Ролик раздела «Полезные материалы». Файл лежит в media/videos.",
         ["Поле", "Тип", "Ограничения", "Назначение"],
         [
             ["id", "INTEGER", "PK", "Идентификатор"],
             ["title", "VARCHAR(200)", "NOT NULL", "Название"],
             ["description", "TEXT", "NOT NULL", "Описание"],
             ["video", "VARCHAR(100)", "NOT NULL", "Видеофайл"],
             ["created_at", "DATETIME", "NOT NULL", "Дата загрузки"],
         ],
         [3.2, 3.4, 4.2, 6.2]),
    ]
    for key, title, lead, headers, rows, widths in specs:
        rich(doc, [
            lead + " Состав полей — таблица ",
            ("ref", "tbl_" + key, N.peek_tbl()),
            ".",
        ])
        table_caption(doc, key, title)
        add_table(doc, headers, rows, widths)

    h2(doc, "Проектирование шаблонов веб-страниц сайта")
    body(doc,
         "Все страницы собраны от одного каркаса: шапка с логотипом и меню, основная колонка, подвал. "
         "Ширина колонки ограничена, на узком экране меню прокручивается по горизонтали и не ломает шапку. "
         "Ниже — эскизы основных шаблонов. Это схема блоков, а не снимок готовой вёрстки: размеры и отступы задаёт CSS.")
    templates = [
        ("home", "Шаблон_главная.png", "Шаблон главной страницы",
         "На рисунке {n} показан шаблон главной страницы. Верхний блок — название «Пси-Эксперт», аннотация и кнопка «Смотреть каталог». "
         "Дальше три карточки категорий и три последние новости. Подвал есть и здесь, и на остальных эскизах."),
        ("catalog", "Шаблон_каталог.png", "Шаблон страницы каталога",
         "На рисунке {n} показан каталог. Переключатели категорий стоят под заголовком. Для каждой категории выводится описание и ряд карточек: изображение, название, стоимость, кнопка «В корзину». Следующая категория повторяет тот же блок."),
        ("product", "Шаблон_карточка_услуги.png", "Шаблон карточки услуги",
         "На рисунке {n} показана карточка. Слева изображение, справа категория, название, стоимость, описание, длительность, метод и кнопка «В корзину». Над карточкой — путь «Каталог / категория»."),
        ("news", "Шаблон_новости.png", "Шаблон страницы новостей",
         "На рисунке {n} показан список новостей. Каждая запись содержит дату, заголовок и текст. Порядок — от новой к старой. Отдельная страница одной новости повторяет ту же запись крупнее."),
        ("video", "Шаблон_видео.png", "Шаблон страницы полезных материалов",
         "На рисунке {n} показана страница «Полезные материалы». Ролик встроен плеером, под ним название и описание. Следующий ролик идёт таким же блоком."),
        ("contacts", "Шаблон_контакты.png", "Шаблон страницы контактов",
         "На рисунке {n} показаны контакты. Левая колонка — телефон, мессенджеры, город и часы записи. Правая — разработчик сайта, группа и стек."),
        ("cart", "Шаблон_корзина.png", "Шаблон страницы корзины",
         "На рисунке {n} показана корзина клиента. Строка позиции содержит услугу, категорию, количество, сумму и удаление. Снизу — итог и кнопка «Оформить запись». Гость и менеджер этот шаблон не открывают."),
        ("myorders", "Шаблон_мои_заказы.png", "Шаблон страницы «Мои заказы»",
         "На рисунке {n} показана история записей клиента. Карточка собирает номер, статус, дату, сумму, телефон, способ связи и состав. Кнопки «Изменить» и «Удалить» выводятся только для статусов, которые клиенту ещё можно менять."),
        ("mgr", "Шаблон_заказы_менеджера.png", "Шаблон страницы заказов менеджера",
         "На рисунке {n} показан список, который видит менеджер. К данным записи добавлен клиент и список статусов с кнопкой «Сохранить статус»."),
        ("reg", "Шаблон_регистрация.png", "Шаблон страницы регистрации",
         "На рисунке {n} показана форма регистрации: логин, имя, фамилия, почта, телефон, пароль и повтор пароля. Рядом ссылка на вход, если учётная запись уже есть."),
        ("panel", "Шаблон_панель.png", "Шаблон панели администратора",
         "На рисунке {n} показана панель. Верхние вкладки — обзор, категории, услуги, новости, видео, пользователи. Обзор даёт счётчики. Остальные вкладки — список с добавлением, изменением и удалением. В категориях форма не принимает занятое название. Во вкладке пользователей — создание менеджера и удаление клиента или менеджера."),
    ]
    for key, filename, caption, text in templates:
        # text uses {n} placeholder replaced by peek
        n = N.peek_fig()
        rich(doc, _split_fig(text.format(n=n), n, "fig_" + key))
        figure(doc, key, filename, caption, 15.2)


def _split_fig(text, label, bookmark):
    """Replace the first occurrence of the figure number with a REF field."""
    token = label
    idx = text.find(token)
    if idx < 0:
        return [text]
    return [text[:idx], ("ref", bookmark, label), text[idx + len(token):]]


def section_modules(doc):
    h1(doc, "Разработка модулей веб-сайта")
    rich(doc, [
        "Алгоритмы модулей вычерчены по ГОСТ 19.701-90 ",
        ("cite", 5),
        ". Используются терминатор «начало» и «конец», процесс, решение, данные с ручного ввода, "
        "дисплей и запоминающее устройство прямого доступа. Линии идут сверху вниз и слева направо, "
        "ветвь «да/нет» подписана у линии. Схема одного модуля открывается «началом» и закрывается «концом».",
    ])

    h2(doc, "Разработка модуля оформления заказа")
    rich(doc, [
        "Модуль проводит клиента от витрины до записи заказа. Блок-схема приведена на рисунке ",
        ("ref", "fig_order", N.peek_fig()),
        ". Каталог показывает услуги из базы. Посетитель выбирает услугу. Если он не клиент, "
        "выводится страница входа и сценарий для этой попытки заканчивается: гостя не пускают в корзину, "
        "менеджеру и администратору корзина тоже закрыта. Клиент добавляет позицию. "
        "Повтор той же услуги увеличивает количество, а не создаёт вторую строку.",
    ])
    figure(doc, "order", "Блок-схема_оформление_заказа.png", "Блок-схема модуля оформления заказа", 13.2)
    body(doc,
         "Дальше клиент решает, оформлять заказ сейчас или вернуться в каталог. При оформлении выводится корзина. "
         "Пустая корзина останавливает сценарий сообщением. Иначе клиент вводит телефон, способ связи и комментарий. "
         "Незаполненные обязательные поля возвращают к форме. Верные данные записываются в ORDER и ORDER_ITEM: "
         "в строку копируются название и цена. Корзина очищается, телефон при необходимости сохраняется в профиль, "
         "на экран выводится номер записи. Статус новой записи — «Новая».")

    h2(doc, "Разработка модуля управления заказами зарегистрированных пользователей")
    rich(doc, [
        "Модуль разделён по роли. Блок-схема приведена на рисунке ",
        ("ref", "fig_orders", N.peek_fig()),
        ". Иная роль, кроме клиента и менеджера, получает отказ. "
        "Менеджер видит все заказы, вводит новый статус и записывает его. Состав заказа менеджер не переписывает: "
        "цену и количество фиксирует клиент в момент покупки.",
    ])
    figure(doc, "orders", "Блок-схема_управление_заказами.png",
           "Блок-схема модуля управления заказами", 15.4)
    rich(doc, [
        "Клиент видит только свои заказы. Действие «изменить» открывает ввод телефона, способа связи и комментария "
        "и сохраняет ту же запись. Действие «удалить» сначала проверяет статус. "
        "Соответствие статусов и прав приведено в таблице ",
        ("ref", "tbl_status", N.peek_tbl()),
        ". Выполненный и отменённый заказ клиент уже не меняет и не удаляет: на экран выводится запрет. "
        "Удаление заказа каскадно удаляет его позиции.",
    ])
    table_caption(doc, "status", "Статусы заказа и право клиента изменить запись")
    add_table(
        doc,
        ["Статус", "Код", "Клиент может изменить или удалить", "Кто назначает"],
        [
            ["Новая", "new", "Да", "Система при создании"],
            ["В работе", "in_progress", "Да", "Менеджер"],
            ["Проведена", "done", "Нет", "Менеджер"],
            ["Отменена", "cancelled", "Нет", "Менеджер"],
        ],
        widths=[4.0, 3.6, 5.6, 3.8],
    )

    h2(doc, "Разработка модуля управления пользователями")
    rich(doc, [
        "Модуль закрывает регистрацию, вход и действия администратора с учётными записями. "
        "Блок-схема приведена на рисунке ",
        ("ref", "fig_users", N.peek_fig()),
        ". Регистрация принимает логин, почту, пароль и имя. Повтор логина или слабый пароль возвращает к форме. "
        "Успех создаёт USER и профиль с ролью «Клиент», затем открывает сессию. "
        "Вход сверяет учётные данные. Ошибка показывается без уточнения, какое поле неверно. "
        "Верный пароль открывает сессию, а меню уже зависит от роли профиля.",
    ])
    figure(doc, "users", "Блок-схема_управление_пользователями.png",
           "Блок-схема модуля управления пользователями", 15.2)
    body(doc,
         "Ветка «Управление» доступна только администратору. Он вводит данные менеджера, и создаётся пользователь с ролью «Менеджер». "
         "Отдельное решение — удаление. Удаляются только клиент и менеджер. Попытка удалить администратора отклоняется. "
         "Вместе с пользователем каскадно уходят профиль, корзина и заказы. "
         "Самого себя администратор через эту форму не удаляет: в списке его строка без кнопки удаления.")

    h2(doc, "Разработка модуля управления каталогом")
    rich(doc, [
        "Модуль показывает каталог всем ролям и даёт администратору менять категории и услуги. "
        "Блок-схема приведена на рисунке ",
        ("ref", "fig_catalog", N.peek_fig()),
        ". Если пользователь не администратор, модуль только выводит категории и услуги из базы и завершается. "
        "Администратор выбирает операцию над категорией или над услугой.",
    ])
    figure(doc, "catalog", "Блок-схема_управление_каталогом.png",
           "Блок-схема модуля управления каталогом", 14.2)
    body(doc,
         "Для категории вводится название. Перед записью оно сравнивается с name_key существующих категорий. "
         "Совпадение, в том числе «Индивидуальная терапия» и «индивидуальная терапия», даёт сообщение «Категория с таким названием уже существует» "
         "и не создаёт вторую строку. Новая категория получает адрес (slug) из названия. "
         "Удаление категории возможно, только если в ней не осталось услуг: внешний ключ услуги защищает категорию от удаления. "
         "Иначе выводится отказ с просьбой сначала убрать услуги.")
    body(doc,
         "Для услуги вводятся карточка и изображение, затем строка пишется в выбранную категорию. "
         "Удаление услуги не стирает уже оформленные записи: в ORDER_ITEM название и цена свои, "
         "а ссылка на услугу обнуляется. Каталог при этом больше эту услугу не показывает.")

    h2(doc, "Разработка модуля управления новостями")
    rich(doc, [
        "Модуль отдаёт новости читателю и правит их в панели администратора. "
        "Блок-схема приведена на рисунке ",
        ("ref", "fig_news", N.peek_fig()),
        ". Читатель любой роли получает список по убыванию даты и может открыть одну новость. "
        "На главной из этого же списка берутся три верхние записи.",
    ])
    figure(doc, "news", "Блок-схема_управление_новостями.png",
           "Блок-схема модуля управления новостями", 14.0)
    body(doc,
         "Администратор выбирает добавление, изменение или удаление. Добавление — ввод заголовка, текста и даты, затем запись. "
         "Изменение выбирает существующую новость и обновляет те же поля. "
         "Удаление запрашивает подтверждение: отказ возвращает к списку, согласие удаляет запись. "
         "Отдельной модерации комментариев нет: комментарии к новостям в техническое задание не входили.")


def section_end(doc):
    plain_heading(doc, "Вывод")
    rich(doc, [
        "В ходе курсового проекта разработан веб-сайт психологического центра «Пси-Эксперт». "
        "Сайт реализован на Python и Django, страницы оформлены общей таблицей стилей, "
        "а услуги, новости, пользователи, записи и полезные видео читаются из базы SQLite ",
        ("cite", 1),
        ". Сделаны четыре роли. Гость смотрит сайт и регистрируется. Клиент собирает корзину и ведёт свои записи, "
        "пока менеджер не закрыл их статусом. Менеджер меняет статусы. Администратор через веб-панель "
        "ведёт каталог и новости, заводит менеджеров и удаляет клиентов и менеджеров.",
    ])
    body(doc,
         "Каталог содержит три требуемые категории и по пять услуг в каждой. "
         "Повтор названия категории не записывается. Главная страница показывает центр, логотип, аннотацию "
         "и три последние новости. Отдельная страница собрана из полезных видео. "
         "Меню присутствует на всех страницах и зависит от роли.")
    rich(doc, [
        "Спроектированы карты сайта для четырёх ролей, схема базы и шаблоны страниц. "
        "Для пяти модулей методички построены блок-схемы по ГОСТ 19.701-90 ",
        ("cite", 5),
        ". Проверка ролей, уникальности категории, корзины и смены статуса заказа покрыта автоматическими тестами Django. "
        "Сайт можно показать преподавателю локально командой python manage.py runserver "
        "после python manage.py migrate и python manage.py seed.",
    ])

    plain_heading(doc, "Список литературы")
    sources = [
        "Форсье Дж., Биссекс П., Чан У. Django: разработка веб-приложений на Python / пер. с англ. А. Киселева. М.: Символ-Плюс, 2013. 451 с.",
        "Дронов В. А. Django 2.1. Практика создания веб-сайтов на Python. СПб.: БХВ-Петербург, 2019. 672 с.",
        "Фрэйн Б. HTML5 и CSS3. Разработка сайтов для любых браузеров и устройств / пер. с англ. В. Черника. СПб.: Питер, 2014. 298 с.",
        "Антонов И. В., Бруттан Ю. В. Веб-программирование: учебно-методическое пособие. Псков: Псковский государственный университет, 2017. 72 с.",
        "ГОСТ 19.701-90. Единая система программной документации. Схемы алгоритмов, программ, данных и систем. Обозначения условные и правила выполнения. М.: Стандартинформ, 2010.",
    ]
    for i, text in enumerate(sources, start=1):
        p = P(doc, align="justify", indent=False, before=2, after=2)
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        bid = N.next_id()
        bookmark(p, f"lit_{i}", bid, "start")
        add_text(p, str(i))
        bookmark(p, f"lit_{i}", bid, "end")
        add_text(p, ". " + text)


def build():
    doc = Document()
    ensure_numbering(doc)
    configure_styles(doc)
    setup_section(doc)
    core = doc.core_properties
    core.author = "Чуров А. А."
    core.title = TOPIC
    core.subject = "Курсовой проект по дисциплине «Веб-программирование»"
    core.category = "Пояснительная записка"
    core.language = "ru-RU"
    title_page(doc)
    contents_clean(doc)
    section_tz(doc)
    section_design(doc)
    section_modules(doc)
    section_end(doc)
    doc.save(OUT)
    print(OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    build()
