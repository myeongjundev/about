#!/usr/bin/env python3
"""Build the three T12 DOCX documents from content/approved.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


FONT = "Malgun Gothic"
INK = "1C1917"
MUTED = "57534E"
BLUE = "1D4ED8"
LINE = "D9D9D9"
PALE = "F5F7FA"


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


def base_document(title: str, name: str) -> Document:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)

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

    title_paragraph = document.add_paragraph(style="Title")
    title_paragraph.add_run(title)
    subtitle = document.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(14)
    run = subtitle.add_run(name)
    set_run_font(run, 11, True, MUTED)

    document.core_properties.title = title
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


def style_header_row(row) -> None:
    set_repeat_table_header(row)
    for cell in row.cells:
        set_cell_shading(cell, BLUE)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                set_run_font(run, 9.5, True, "FFFFFF")


def build_resume(data: dict[str, object], output: Path, draft: bool) -> None:
    profile = data["profile"]
    document = base_document("김명준 이력서", profile["name"])
    add_intro(document, profile["direction"])

    document.add_heading("연락", level=1)
    contact = profile.get("contact")
    add_label_value(document, "연락 수단", text(contact.get("label") if contact else None, draft))
    if contact and contact.get("href"):
        paragraph = document.add_paragraph()
        add_hyperlink(paragraph, contact.get("label") or "연락 링크", contact["href"])

    document.add_heading("교육", level=1)
    for item in profile.get("education") or []:
        paragraph = document.add_paragraph()
        run = paragraph.add_run(item["name"])
        set_run_font(run, 11, True)
        paragraph.add_run(f"  {item['period']}")

    document.add_heading("기술", level=1)
    table = document.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(1.45)
    table.columns[1].width = Inches(5.25)
    table.rows[0].cells[0].text = "영역"
    table.rows[0].cells[1].text = "사용 기술"
    style_header_row(table.rows[0])
    for index, (category, items) in enumerate(profile.get("technologies", {}).items()):
        cells = table.add_row().cells
        cells[0].text = category
        cells[1].text = " · ".join(items)
        if index % 2:
            for cell in cells:
                set_cell_shading(cell, PALE)
        for cell in cells:
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    set_run_font(run, 10)
    set_table_borders(table)

    document.add_heading("프로젝트와 연구", level=1)
    for item in data["experience"]:
        document.add_heading(text(item.get("title"), draft, "세 번째 항목 확정 필요"), level=2)
        add_label_value(document, "기간", text(item.get("period"), draft))
        add_label_value(document, "역할", text(item.get("role"), draft))
        add_label_value(document, "핵심 결과", text(item.get("result"), draft))
        technologies = text(" · ".join(item.get("technologies") or []), draft)
        add_label_value(document, "기술", technologies)
        for link in item.get("links") or []:
            paragraph = document.add_paragraph()
            add_hyperlink(paragraph, link["label"], link["href"])

    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def build_personal_statement(data: dict[str, object], output: Path, draft: bool) -> None:
    profile = data["profile"]
    story = data["story"]
    document = base_document("김명준 자기소개서", profile["name"])
    add_intro(
        document,
        text(
            story.get("firstSentence"),
            draft,
            "첫 문장은 제출자가 직접 작성한 뒤 이 자리에 들어갑니다.",
        ),
    )
    for segment in story["segments"]:
        document.add_heading(
            text(segment.get("statementTitle"), draft, f"{segment['stage']}의 자기소개서 제목"),
            level=1,
        )
        meta = document.add_paragraph()
        meta.paragraph_format.space_after = Pt(5)
        meta_run = meta.add_run(f"{segment['period']}  ·  {segment['ability']}")
        set_run_font(meta_run, 9.8, True, BLUE)
        summary = document.add_paragraph()
        run = summary.add_run(segment["summary"])
        set_run_font(run, 11.5, True)
        body = document.add_paragraph(segment["body"])
        body.paragraph_format.space_after = Pt(12)
    document.add_heading("앞으로의 방향", level=1)
    closing = document.add_paragraph(
        text(
            story.get("lastSentence"),
            draft,
            "마지막 문장은 제출자가 직접 작성한 뒤 이 자리에 들어갑니다.",
        )
    )
    closing.paragraph_format.space_before = Pt(14)
    for run in closing.runs:
        set_run_font(run, 11.2, True)
    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def build_career_description(data: dict[str, object], output: Path, draft: bool) -> None:
    profile = data["profile"]
    document = base_document("김명준 경력기술서", profile["name"])
    add_intro(document, "프로젝트마다 맡은 역할과 상황, 행동, 결과를 확인 가능한 사실로 정리했습니다.")

    for item in data["experience"]:
        document.add_heading(text(item.get("title"), draft, "세 번째 항목 확정 필요"), level=1)
        add_label_value(document, "기간", text(item.get("period"), draft))
        add_label_value(document, "역할", text(item.get("role"), draft))
        add_label_value(document, "능력", text(item.get("ability"), draft))

        table = document.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table.columns[0].width = Inches(1.0)
        table.columns[1].width = Inches(5.7)
        table.rows[0].cells[0].text = "구분"
        table.rows[0].cells[1].text = "내용"
        style_header_row(table.rows[0])
        for index, (label, field) in enumerate((('상황', 'situation'), ('행동', 'action'), ('결과', 'result'))):
            cells = table.add_row().cells
            cells[0].text = label
            cells[1].text = text(item.get(field), draft)
            if index % 2:
                for cell in cells:
                    set_cell_shading(cell, PALE)
            for cell in cells:
                set_cell_margins(cell, top=150, bottom=150)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        set_run_font(run, 10)
            for run in cells[0].paragraphs[0].runs:
                set_run_font(run, 10, True, MUTED)
        set_table_borders(table)

        technology = document.add_paragraph()
        technology.paragraph_format.space_before = Pt(6)
        run = technology.add_run("기술  ")
        set_run_font(run, 10, True, MUTED)
        run = technology.add_run(text(" · ".join(item.get("technologies") or []), draft))
        set_run_font(run, 10)
        for link in item.get("links") or []:
            paragraph = document.add_paragraph()
            add_hyperlink(paragraph, link["label"], link["href"])

    output.parent.mkdir(parents=True, exist_ok=True)
    document.save(output)


def main() -> int:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", type=Path, default=base.parent / "content" / "approved.json")
    parser.add_argument("--output-dir", type=Path, default=base.parent / "docs" / "files")
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
        output_dir = args.output_dir.resolve()
        if args.only in {"all", "resume"}:
            build_resume(data, output_dir / "resume-kim-myeongjun.docx", args.draft)
        if args.only in {"all", "personal-statement"}:
            build_personal_statement(
                data, output_dir / "personal-statement-kim-myeongjun.docx", args.draft
            )
        if args.only in {"all", "career-description"}:
            build_career_description(
                data, output_dir / "career-description-kim-myeongjun.docx", args.draft
            )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    count = 3 if args.only == "all" else 1
    print(f"PASS: {count} DOCX file{'s' if count != 1 else ''} in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
