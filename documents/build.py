#!/usr/bin/env python3
"""Build the three T12 DOCX documents from content/approved.json."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Mm, Pt, RGBColor


FONT = "Malgun Gothic"
# A4 210mm에서 좌우 여백을 뺀 본문 폭. 날짜를 오른쪽 끝에 세울 때 기준이 된다.
PAGE_MARGIN = Inches(0.75)
BODY_WIDTH = Mm(210) - PAGE_MARGIN * 2
LABEL_INDENT = Inches(0.52)
# 기술 분류 이름은 길이가 제각각이라 값을 한 칸에 세워야 이름과 목록이 구분된다.
SKILL_LABEL_WIDTH = Inches(1.2)
INK = "1C1917"
MUTED = "57534E"
BLUE = "1D4ED8"
LINE = "D9D9D9"
PALE = "F5F7FA"
MAX_TABLE_WIDTH = Inches(6.5)


def set_cell_shading(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=120, start=140, bottom=120, end=140) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table) -> None:
    properties = table._tbl.tblPr
    borders = properties.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = borders.find(qn(f"w:{edge}"))
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:color"), LINE)


def set_repeat_table_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    properties.append(repeat)


def validate_document_layout(path: Path) -> None:
    document = Document(path)
    for section_index, section in enumerate(document.sections, start=1):
        if (
            abs(section.page_width - Mm(210)) > 1000
            or abs(section.page_height - Mm(297)) > 1000
        ):
            raise ValueError(f"A4 용지 크기 검사 실패: 섹션 {section_index}")

    body_width = min(
        section.page_width - section.left_margin - section.right_margin
        for section in document.sections
    )
    allowed_width = min(body_width, MAX_TABLE_WIDTH)
    for table_index, table in enumerate(document.tables, start=1):
        widths = [column.width for column in table.columns]
        if any(width is None for width in widths):
            raise ValueError(f"표 열 너비가 지정되지 않았습니다: 표 {table_index}")
        table_width = sum(int(width) for width in widths if width is not None)
        if table_width > allowed_width:
            raise ValueError(
                f"표 너비가 본문 폭을 넘습니다: 표 {table_index} "
                f"{table_width / Inches(1):.2f}in > {allowed_width / Inches(1):.2f}in"
            )


def save_document(document: Document, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)
    validate_document_layout(output)


def set_run_font(run, size: float | None = None, bold: bool | None = None, color: str | None = None) -> None:
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_hyperlink(paragraph, text: str, url: str) -> None:
    relationship_id = paragraph.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)
    run_element = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), BLUE)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), FONT)
    fonts.set(qn("w:hAnsi"), FONT)
    fonts.set(qn("w:eastAsia"), FONT)
    properties.extend((fonts, color, underline))
    run_element.append(properties)
    text_element = OxmlElement("w:t")
    text_element.text = text
    run_element.append(text_element)
    hyperlink.append(run_element)
    paragraph._p.append(hyperlink)


def base_document(
    title: str, name: str, subtitle: str | None = None, links: list[dict] | None = None
) -> Document:
    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = PAGE_MARGIN
    section.right_margin = PAGE_MARGIN

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(10.8)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    style_specs = {
        "Title": (25, 700, 0, 16),
        "Heading 1": (15, 700, 18, 8),
        "Heading 2": (12, 700, 12, 5),
    }
    for style_name, (size, _weight, before, after) in style_specs.items():
        style = styles[style_name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string("000000")
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True
        if style_name == "Title":
            paragraph_properties = style._element.get_or_add_pPr()
            border = paragraph_properties.find(qn("w:pBdr"))
            if border is not None:
                paragraph_properties.remove(border)

    # 이름을 가장 크게 두고 문서 종류를 오른쪽에 작게 붙인다. 그 아래 한 줄에 직무와 확인
    # 링크를 모으고 강조색 선으로 닫는다. 해외 이력서의 머리글 구성을 그대로 따랐다.
    header = document.add_paragraph()
    header.paragraph_format.space_after = Pt(3)
    header.paragraph_format.keep_with_next = True
    header.paragraph_format.tab_stops.add_tab_stop(BODY_WIDTH, WD_TAB_ALIGNMENT.RIGHT)
    name_run = header.add_run(name)
    set_run_font(name_run, 23, True, INK)
    kind_run = header.add_run(f"\t{title}")
    set_run_font(kind_run, 11, True, MUTED)

    meta = document.add_paragraph()
    meta.paragraph_format.space_after = Pt(12)
    meta.paragraph_format.keep_with_next = True
    if subtitle:
        role_run = meta.add_run(subtitle)
        set_run_font(role_run, 10.5, True, MUTED)
    for link in links or []:
        if meta.runs or link is not (links or [])[0]:
            separator = meta.add_run("   ·   ")
            set_run_font(separator, 10.5, False, MUTED)
        add_hyperlink(meta, link["label"], link["href"])
    set_bottom_border(meta, color=BLUE, size=10)

    document.core_properties.title = f"{name} {title}"
    document.core_properties.author = name
    return document


def text(value: object, draft: bool, label: str = "확정 필요") -> str:
    if value is not None and value != "" and value != []:
        return str(value)
    if draft:
        return label
    raise ValueError(label)


def add_intro(document: Document, body: str) -> None:
    paragraph = document.add_paragraph(body)
    paragraph.paragraph_format.space_after = Pt(14)
    for run in paragraph.runs:
        set_run_font(run, 11.2)


def add_label_value(document: Document, label: str, value: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(3)
    label_run = paragraph.add_run(f"{label}  ")
    set_run_font(label_run, 10.5, True, MUTED)
    value_run = paragraph.add_run(value)
    set_run_font(value_run, 10.5)


def add_highlights(document: Document, items: list[str]) -> None:
    for item in items:
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(5)
        paragraph.paragraph_format.left_indent = Inches(0.16)
        paragraph.paragraph_format.first_line_indent = Inches(-0.16)
        marker = paragraph.add_run("· ")
        set_run_font(marker, 10.5, True, BLUE)
        run = paragraph.add_run(item)
        set_run_font(run, 10.5)


def set_bottom_border(paragraph, color: str = LINE, size: int = 6) -> None:
    properties = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    borders.append(bottom)
    properties.append(borders)


def add_section(document: Document, title: str) -> None:
    """절 제목과 그 아래 가는 선. 해외 이력서가 절을 나누는 가장 흔한 방식이다."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(15)
    paragraph.paragraph_format.space_after = Pt(7)
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run(title)
    set_run_font(run, 11.5, True, INK)
    set_bottom_border(paragraph)


def add_entry(document: Document, title: str, period: str | None) -> None:
    """항목 제목과 기간. 날짜는 줄 앞이 아니라 오른쪽 끝에 세운다."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.tab_stops.add_tab_stop(BODY_WIDTH, WD_TAB_ALIGNMENT.RIGHT)
    run = paragraph.add_run(title)
    set_run_font(run, 11, True, INK)
    if period:
        tail = paragraph.add_run(f"\t{period}")
        set_run_font(tail, 10, False, MUTED)


def add_line(document: Document, label: str, value: str, keep: bool = True) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.left_indent = LABEL_INDENT
    paragraph.paragraph_format.first_line_indent = -LABEL_INDENT
    paragraph.paragraph_format.keep_with_next = keep
    label_run = paragraph.add_run(f"{label}  ")
    set_run_font(label_run, 10, True, MUTED)
    value_run = paragraph.add_run(value)
    set_run_font(value_run, 10)


def add_skill_line(document: Document, label: str, value: str) -> None:
    """분류 이름과 목록을 두 칸으로 세운다. 이름 안의 가운뎃점이 목록 구분과 섞이지 않게 한다."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.left_indent = SKILL_LABEL_WIDTH
    paragraph.paragraph_format.first_line_indent = -SKILL_LABEL_WIDTH
    paragraph.paragraph_format.tab_stops.add_tab_stop(SKILL_LABEL_WIDTH, WD_TAB_ALIGNMENT.LEFT)
    label_run = paragraph.add_run(f"{label}	")
    set_run_font(label_run, 10, True, MUTED)
    value_run = paragraph.add_run(value)
    set_run_font(value_run, 10)


def add_links(document: Document, links: list[dict] | None, keep: bool = False) -> None:
    """확인 링크를 한 줄에 모은다. 줄이 늘어지지 않게 하려는 목적도 있다."""
    if not links:
        return
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = keep
    for index, link in enumerate(links):
        if index:
            separator = paragraph.add_run("   ·   ")
            set_run_font(separator, 10, False, MUTED)
        add_hyperlink(paragraph, link["label"], link["href"])


def style_header_row(row) -> None:
    set_repeat_table_header(row)
    for cell in row.cells:
        set_cell_shading(cell, BLUE)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                set_run_font(run, 9.5, True, "FFFFFF")


def header_links(profile: dict, draft: bool) -> list[dict]:
    """머리글 한 줄에 모을 연락 수단과 공개 주소."""
    links = []
    contact = profile.get("contact")
    if contact and contact.get("href"):
        links.append(contact)
    elif not draft:
        raise ValueError("공개 연락 수단 확정 필요")
    site = profile.get("site")
    if site and site.get("href"):
        links.append(site)
    return links


# ---------------------------------------------------------------------------
# 같은 내용을 DOCX와 웹 페이지로 쓴다. 세 문서의 조립 순서는 아래 build_* 한 곳에만 있고,
# 쓰는 쪽(Writer)만 바꿔 끼운다. 그래서 웹 문서와 DOCX가 다른 말을 할 수 없다.
# ---------------------------------------------------------------------------


class DocxWriter:
    """위 add_* 함수를 그대로 부른다. 웹 페이지를 더하기 전의 DOCX와 본문이 같다."""

    def __init__(self) -> None:
        self.document: Document | None = None

    def header(self, kind: str, name: str, subtitle: str, links: list[dict]) -> None:
        self.document = base_document(kind, name, subtitle, links)

    def intro(self, body: str) -> None:
        add_intro(self.document, body)

    def section(self, title: str) -> None:
        add_section(self.document, title)

    def highlights(self, items: list[str]) -> None:
        add_highlights(self.document, items)

    def skill(self, label: str, value: str) -> None:
        add_skill_line(self.document, label, value)

    def entry(self, title: str, period: str | None) -> None:
        add_entry(self.document, title, period)

    def line(self, label: str, value: str, keep: bool = True) -> None:
        add_line(self.document, label, value, keep=keep)

    def links(self, links: list[dict] | None) -> None:
        add_links(self.document, links)

    def summary(self, body: str) -> None:
        paragraph = self.document.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(3)
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.keep_with_next = True
        run = paragraph.add_run(body)
        set_run_font(run, 11, True, BLUE)

    def body(self, body: str) -> None:
        paragraph = self.document.add_paragraph(body)
        # 세 장면과 마지막 문장이 한 쪽에 들어가도록 본문만 조금 좁게 짠다.
        paragraph.paragraph_format.space_after = Pt(7)
        paragraph.paragraph_format.line_spacing = 1.16
        for run in paragraph.runs:
            set_run_font(run, 10.5)

    def closing(self, body: str) -> None:
        paragraph = self.document.add_paragraph(body)
        for run in paragraph.runs:
            set_run_font(run, 11, True)

    def save(self, output: Path) -> None:
        save_document(self.document, output)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


class HtmlWriter:
    """같은 호출을 웹 페이지 본문으로 옮긴다. 쪽 나눔 대신 절과 항목을 HTML 구조로 둔다."""

    def __init__(self, page: dict) -> None:
        self.page = page
        self.parts: list[str] = []
        self.in_section = False
        self.in_entry = False

    def _close_entry(self) -> None:
        if self.in_entry:
            self.parts.append("        </article>")
            self.in_entry = False

    def _close_section(self) -> None:
        self._close_entry()
        if self.in_section:
            self.parts.append("      </section>")
            self.in_section = False

    def header(self, kind: str, name: str, subtitle: str, links: list[dict]) -> None:
        link_html = "".join(
            f' <span aria-hidden="true">·</span> <a href="{esc(link["href"])}">{esc(link["label"])}</a>'
            for link in links
        )
        self.parts.append(
            "      <header class=\"doc-head\">\n"
            f"        <h1><span class=\"doc-name\">{esc(name)}</span> <span class=\"doc-kind\">{esc(kind)}</span></h1>\n"
            f"        <p class=\"doc-meta\"><strong>{esc(subtitle)}</strong>{link_html}</p>\n"
            "      </header>"
        )

    def intro(self, body: str) -> None:
        self.parts.append(f'      <p class="doc-intro">{esc(body)}</p>')

    def section(self, title: str) -> None:
        self._close_section()
        self.parts.append(f'      <section class="doc-section">\n        <h2>{esc(title)}</h2>')
        self.in_section = True

    def highlights(self, items: list[str]) -> None:
        rows = "".join(f"<li>{esc(item)}</li>" for item in items)
        self.parts.append(f'        <ul class="doc-highlights">{rows}</ul>')

    def skill(self, label: str, value: str) -> None:
        self.parts.append(
            f'        <p class="doc-skill"><span class="doc-label">{esc(label)}</span><span>{esc(value)}</span></p>'
        )

    def entry(self, title: str, period: str | None) -> None:
        self._close_entry()
        period_html = f'<span class="doc-period">{esc(period)}</span>' if period else ""
        # 절 안의 항목은 h3, 절 없이 바로 이어지는 항목(자기소개서 장면, 경력기술서 항목)은 h2다.
        level = "h3" if self.in_section else "h2"
        self.parts.append(
            f'        <article class="doc-entry">\n          <div class="doc-entry-head"><{level}>{esc(title)}</{level}>{period_html}</div>'
        )
        self.in_entry = True

    def line(self, label: str, value: str, keep: bool = True) -> None:
        self.parts.append(
            f'          <p class="doc-line"><span class="doc-label">{esc(label)}</span><span>{esc(value)}</span></p>'
        )

    def links(self, links: list[dict] | None) -> None:
        if not links:
            return
        items = "".join(f'<a href="{esc(link["href"])}">{esc(link["label"])}</a>' for link in links)
        self.parts.append(f'          <p class="doc-links">{items}</p>')

    def summary(self, body: str) -> None:
        self.parts.append(f'          <p class="doc-summary">{esc(body)}</p>')

    def body(self, body: str) -> None:
        self.parts.append(f'          <p class="doc-body">{esc(body)}</p>')

    def closing(self, body: str) -> None:
        self.parts.append(f'        <p class="doc-closing">{esc(body)}</p>')

    def save(self, output: Path) -> None:
        self._close_section()
        page = self.page
        nav = "".join(
            f'<a href="{esc(item["href"])}"'
            + (' aria-current="page"' if item.get("current") else "")
            + f'>{esc(item["label"])}</a>'
            for item in page["nav"]
        )
        downloads = "".join(
            f'<a href="{esc(item["href"])}">{esc(item["label"])}</a>' for item in page["downloads"]
        )
        body = "\n".join(self.parts)
        document = (
            "<!doctype html>\n"
            f"<html lang=\"{esc(page['lang'])}\">\n"
            "<head>\n"
            "  <meta charset=\"utf-8\">\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"  <title>{esc(page['title'])}</title>\n"
            f"  <meta name=\"description\" content=\"{esc(page['description'])}\">\n"
            "  <meta name=\"color-scheme\" content=\"light dark\">\n"
            "  <link rel=\"icon\" href=\"favicon.svg\" type=\"image/svg+xml\">\n"
            f"  <link rel=\"stylesheet\" href=\"document.css?v={esc(page['assetVersion'])}\">\n"
            "</head>\n"
            "<body>\n"
            f"  <a class=\"skip-link\" href=\"#doc\">{esc(page['skip'])}</a>\n"
            "  <div class=\"doc-bar\">\n"
            f"    <a class=\"doc-back\" href=\"./\">{esc(page['back'])}</a>\n"
            f"    <nav class=\"doc-tabs\" aria-label=\"{esc(page['navLabel'])}\">{nav}</nav>\n"
            f"    <p class=\"doc-downloads\">{downloads}</p>\n"
            "  </div>\n"
            "  <main id=\"doc\" class=\"doc\">\n"
            f"{body}\n"
            "  </main>\n"
            "</body>\n"
            "</html>\n"
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document, encoding="utf-8", newline="\n")


KO_LABELS = {
    "resume": "이력서",
    "highlights": "핵심 역량",
    "skills": "기술",
    "projects": "프로젝트와 연구",
    "otherWork": "그 외 작업",
    "education": "교육",
    "role": "역할",
    "scope": "담당",
    "result": "결과",
    "stack": "기술",
    "institution": "기관",
    "details": "내용",
}


def build_resume(data: dict[str, object], writer, draft: bool, labels: dict[str, str] = KO_LABELS) -> None:
    profile = data["profile"]
    writer.header(
        labels.get("documentTitle", labels["resume"]),
        profile["name"],
        profile["role"],
        header_links(profile, draft),
    )
    writer.intro(profile["direction"])

    highlights = profile.get("highlights") or []
    if highlights:
        writer.section(labels["highlights"])
        writer.highlights(highlights)

    # 기술은 표 대신 줄로 적는다. 채용 시스템이 표를 잘못 읽는 일이 있고 줄 수도 아낀다.
    writer.section(labels["skills"])
    for category, items in (profile.get("technologies") or {}).items():
        writer.skill(category, " · ".join(items))

    # 이력서는 두 쪽을 넘기지 않는다. 앞선 작업은 자세히, 나머지는 한 덩어리로 줄여 싣는다.
    experience = data["experience"]
    detailed = [item for item in experience if item.get("resumeDetail", "full") != "compact"]
    compact = [item for item in experience if item.get("resumeDetail") == "compact"]

    writer.section(labels["projects"])
    for item in detailed:
        writer.entry(
            text(item.get("title"), draft, "세 번째 항목 확정 필요"),
            text(item.get("period"), draft),
        )
        writer.line(labels["role"], text(item.get("role"), draft))
        if item.get("scope"):
            writer.line(labels["scope"], item["scope"])
        writer.line(labels["result"], text(item.get("result"), draft))
        writer.line(
            labels["stack"],
            text(" · ".join(item.get("technologies") or []), draft),
            keep=bool(item.get("links")),
        )
        writer.links(item.get("links"))

    if compact:
        writer.section(labels["otherWork"])
        for item in compact:
            writer.entry(text(item.get("title"), draft), text(item.get("period"), draft))
            writer.line(labels["result"], text(item.get("result"), draft), keep=bool(item.get("links")))
            writer.links(item.get("links"))

    writer.section(labels["education"])
    for item in profile.get("education") or []:
        writer.entry(item["name"], item["period"])
        if item.get("org"):
            writer.line(labels["institution"], item["org"], keep=bool(item.get("detail")))
        if item.get("detail"):
            writer.line(labels["details"], item["detail"], keep=False)


def build_personal_statement(data: dict[str, object], writer, draft: bool) -> None:
    profile = data["profile"]
    story = data["story"]
    writer.header("자기소개서", profile["name"], profile["role"], header_links(profile, draft))
    writer.intro(
        text(
            story.get("firstSentence"),
            draft,
            "첫 문장은 제출자가 직접 작성한 뒤 이 자리에 들어갑니다.",
        )
    )
    for segment in story["segments"]:
        writer.entry(
            text(segment.get("statementTitle"), draft, f"{segment['stage']}의 자기소개서 제목"),
            f"{segment['period']}  ·  {segment['ability']}",
        )
        writer.summary(segment["summary"])
        writer.body(segment["body"])

    writer.section("앞으로의 방향")
    writer.closing(
        text(
            story.get("lastSentence"),
            draft,
            "마지막 문장은 제출자가 직접 작성한 뒤 이 자리에 들어갑니다.",
        )
    )


def build_career_description(data: dict[str, object], writer, draft: bool) -> None:
    profile = data["profile"]
    writer.header("경력기술서", profile["name"], profile["role"], header_links(profile, draft))
    writer.intro(
        "프로젝트마다 맡은 역할과 담당 범위, 상황에서 판단과 행동을 거쳐 결과에 이른 과정을"
        " 확인 가능한 사실로 정리했습니다."
    )

    for item in data["experience"]:
        writer.entry(
            text(item.get("title"), draft, "세 번째 항목 확정 필요"),
            text(item.get("period"), draft),
        )
        writer.line("역할", text(item.get("role"), draft))
        if item.get("scope"):
            writer.line("담당", item["scope"])
        writer.line("능력", text(item.get("ability"), draft))
        # 표 대신 줄로 적는다. 판단을 따로 보여 주는 편이 면접에서 이어 말하기 좋다.
        for label, field in (
            ("상황", "situation"),
            ("판단", "rationale"),
            ("행동", "action"),
            ("결과", "result"),
        ):
            value = item.get(field)
            if field == "rationale" and not value:
                continue
            writer.line(label, text(value, draft))
        writer.line(
            "기술",
            text(" · ".join(item.get("technologies") or []), draft),
            keep=bool(item.get("links")),
        )
        writer.links(item.get("links"))


def localize(data: dict[str, object], english: dict[str, object]) -> dict[str, object]:
    """영문 이력서 자료. 기간·링크 주소·항목 순서는 한국어 원본을 쓰고 문장만 바꾼다."""
    localized = copy.deepcopy(data)
    profile = localized["profile"]
    source = english["profile"]
    for key in ("name", "role", "direction", "highlights", "technologies"):
        profile[key] = source[key]
    if profile.get("contact"):
        profile["contact"]["label"] = source["contact"]
    if profile.get("site"):
        profile["site"]["label"] = source["site"]
    missing = [item["id"] for item in localized["experience"] if item["id"] not in english["experience"]]
    if missing:
        raise ValueError(f"영문 번역이 없는 경력 항목: {', '.join(missing)}")
    for item in localized["experience"]:
        words = english["experience"][item["id"]]
        for key in ("title", "role", "scope", "result"):
            if key in words:
                item[key] = words[key]
        labels = words.get("links") or []
        if len(labels) != len(item.get("links") or []):
            raise ValueError(f"영문 링크 이름 수가 다릅니다: {item['id']}")
        for link, label in zip(item.get("links") or [], labels):
            link["label"] = label
    education = english["education"]
    if len(education) != len(profile.get("education") or []):
        raise ValueError("영문 교육 항목 수가 한국어와 다릅니다")
    profile["education"] = education
    return localized


# (파일 이름, 웹 페이지, 탭 이름)
DOCUMENT_PAGES = (
    ("resume-kim-myeongjun", "resume.html", "이력서"),
    ("personal-statement-kim-myeongjun", "personal-statement.html", "자기소개서"),
    ("career-description-kim-myeongjun", "career-description.html", "경력기술서"),
)
ENGLISH_RESUME = ("resume-kim-myeongjun-en", "resume-en.html", "English")


def asset_version(site_dir: Path) -> str:
    css = site_dir / "document.css"
    return hashlib.sha256(css.read_bytes()).hexdigest()[:12] if css.exists() else "0"


def page_context(name: str, page: str, title: str, description: str, lang: str, site_dir: Path) -> dict:
    english = lang == "en"
    return {
        "lang": lang,
        "title": title,
        "description": description,
        "assetVersion": asset_version(site_dir),
        "skip": "Skip to the document" if english else "문서 본문으로 바로 가기",
        "back": "← Portfolio (Korean)" if english else "← 김명준 소개로",
        "navLabel": "Documents" if english else "문서",
        "nav": [
            {"href": tab_page, "label": label, "current": tab_page == page}
            for _, tab_page, label in (*DOCUMENT_PAGES, ENGLISH_RESUME)
        ],
        "downloads": [
            {"href": f"files/{name}.pdf", "label": "PDF"},
            {"href": f"files/{name}.docx", "label": "DOCX"},
        ],
    }


def build_all(
    data: dict, english: dict | None, docx_dir: Path, site_dir: Path | None, draft: bool, only: str
) -> int:
    profile = data["profile"]
    builders = {
        "resume-kim-myeongjun": lambda writer: build_resume(data, writer, draft),
        "personal-statement-kim-myeongjun": lambda writer: build_personal_statement(data, writer, draft),
        "career-description-kim-myeongjun": lambda writer: build_career_description(data, writer, draft),
    }
    count = 0
    for name, page, label in DOCUMENT_PAGES:
        if only not in {"all", name.replace("-kim-myeongjun", "")}:
            continue
        writer = DocxWriter()
        builders[name](writer)
        writer.save(docx_dir / f"{name}.docx")
        count += 1
        if site_dir:
            context = page_context(
                name,
                page,
                f"{profile['name']} {label}",
                f"{profile['name']}의 {label}. 같은 내용을 PDF와 DOCX로도 내려받을 수 있습니다.",
                "ko",
                site_dir,
            )
            web = HtmlWriter(context)
            builders[name](web)
            web.save(site_dir / page)

    if english is not None and only in {"all", "resume"}:
        name, page, _ = ENGLISH_RESUME
        localized = localize(data, english)
        labels = {**KO_LABELS, **english["labels"]}
        writer = DocxWriter()
        build_resume(localized, writer, draft, labels)
        writer.save(docx_dir / f"{name}.docx")
        count += 1
        if site_dir:
            context = page_context(
                name,
                page,
                f"{localized['profile']['name']} — Résumé",
                f"Résumé of {localized['profile']['name']}. Also available as PDF and DOCX.",
                "en",
                site_dir,
            )
            web = HtmlWriter(context)
            build_resume(localized, web, draft, labels)
            web.save(site_dir / page)
    return count


def main() -> int:
    base = Path(__file__).resolve().parent
    published = (base.parent / "docs" / "files").resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, default=base.parent / "content" / "approved.json")
    parser.add_argument("--english", type=Path, default=base.parent / "content" / "approved.en.json")
    parser.add_argument("--output-dir", type=Path, default=published)
    parser.add_argument("--draft", action="store_true")
    parser.add_argument(
        "--only",
        choices=("all", "resume", "personal-statement", "career-description"),
        default="all",
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.content.read_text(encoding="utf-8"))
        if data.get("draft") and not args.draft:
            raise ValueError("approved.json이 draft 상태입니다. 최종 문서 생성을 중단합니다.")
        english = (
            json.loads(args.english.read_text(encoding="utf-8")) if args.english.exists() else None
        )
        output_dir = args.output_dir.resolve()
        # 웹 문서는 공개 문서를 만들 때만 사이트 폴더(docs/)에 함께 쓴다. 초안은 DOCX만 만든다.
        site_dir = output_dir.parent if output_dir == published else None
        count = build_all(data, english, output_dir, site_dir, args.draft, args.only)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    pages = " and web pages" if site_dir else ""
    print(f"PASS: {count} DOCX file{'s' if count != 1 else ''}{pages} in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
