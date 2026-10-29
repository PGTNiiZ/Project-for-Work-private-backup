"""Render the Thai Identity Resolution report and its PNG figures as a PDF."""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF


REPORT_DIR = Path(__file__).resolve().parent
SOURCE = REPORT_DIR / "PROJECT_REPORT_TH.md"
OUTPUT = REPORT_DIR / "PROJECT_REPORT_TH.pdf"
THAI_FONT = Path("/System/Library/Fonts/Supplemental/Thonburi.ttc")


class ReportPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Thonburi", size=8)
        self.set_text_color(90, 105, 118)
        self.cell(0, 5, f"Identity Resolution Pipeline | {self.page_no()}", align="C")


def plain_text(value: str) -> str:
    """Remove Markdown syntax while retaining human-readable labels and equations."""
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = value.replace("**", "").replace("`", "")
    return value.replace("$", "").replace("→", "->").strip()


def write_paragraph(pdf: ReportPDF, text: str, *, size: float = 10.3, indent: float = 0) -> None:
    pdf.set_font("Thonburi", size=size)
    pdf.set_text_color(24, 35, 46)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(pdf.epw - indent, 5.8, plain_text(text))
    pdf.ln(1.5)


def write_table(pdf: ReportPDF, rows: list[list[str]]) -> None:
    column_count = max(len(row) for row in rows)
    widths = [pdf.epw / column_count] * column_count
    for row_index, values in enumerate(rows):
        values = values + [""] * (column_count - len(values))
        cell_text = [plain_text(value) for value in values]
        line_count = max(1, max(len(value) // 28 + 1 for value in cell_text))
        height = max(6.5, min(30, line_count * 4.4))
        if pdf.get_y() + height > pdf.page_break_trigger:
            pdf.add_page()
        fill = (23, 50, 77) if row_index == 0 else ((242, 246, 248) if row_index % 2 == 0 else (255, 255, 255))
        text_color = (255, 255, 255) if row_index == 0 else (24, 35, 46)
        pdf.set_fill_color(*fill)
        pdf.set_draw_color(185, 198, 208)
        pdf.set_text_color(*text_color)
        pdf.set_font("Thonburi", size=7.3)
        start_x, start_y = pdf.get_x(), pdf.get_y()
        for column, value in enumerate(cell_text):
            x = start_x + sum(widths[:column])
            pdf.rect(x, start_y, widths[column], height, style="DF")
            pdf.set_xy(x + 1.3, start_y + 1)
            pdf.multi_cell(widths[column] - 2.6, 3.7, value, new_x="RIGHT", new_y="TOP")
        pdf.set_xy(start_x, start_y + height)
    pdf.ln(2)


def write_image(pdf: ReportPDF, image_path: Path, alt_text: str) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"Report image not found: {image_path}")
    if image_path.name == "00_end_to_end_architecture.png":
        pdf.add_page(orientation="P")
        pdf.image(str(image_path), x=22, y=12, h=245)
        pdf.set_y(260)
        pdf.set_font("Thonburi", size=8)
        pdf.set_text_color(90, 105, 118)
        pdf.multi_cell(pdf.epw, 4.5, alt_text, align="C")
        pdf.add_page()
        return
    if pdf.get_y() > 145:
        pdf.add_page()
    pdf.image(str(image_path), x=pdf.l_margin, w=pdf.epw)
    pdf.set_font("Thonburi", size=8)
    pdf.set_text_color(90, 105, 118)
    pdf.multi_cell(pdf.epw, 4.5, alt_text, align="C")
    pdf.ln(2)


def render_pdf() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Report not found: {SOURCE}")
    if not THAI_FONT.exists():
        raise FileNotFoundError(f"Thai font not found: {THAI_FONT}")

    pdf = ReportPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(14, 14, 14)
    pdf.add_font("Thonburi", style="", fname=str(THAI_FONT))
    pdf.add_page()
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line.strip())
        heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if image_match:
            write_image(pdf, REPORT_DIR / image_match.group(2), image_match.group(1))
        elif heading_match:
            level = len(heading_match.group(1))
            if level == 1 and pdf.page_no() > 1:
                pdf.add_page()
            pdf.set_font("Thonburi", size={1: 19, 2: 14.5, 3: 12}[level])
            pdf.set_text_color(*(23, 50, 77) if level < 3 else (40, 120, 181))
            pdf.multi_cell(pdf.epw, 8, plain_text(heading_match.group(2)))
            pdf.ln(2)
        elif line.startswith("|") and index + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}", lines[index + 1]):
            table_rows = [[cell.strip() for cell in line.strip().strip("|").split("|")]]
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                table_rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            write_table(pdf, table_rows)
            continue
        elif line.startswith("```"):
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code_lines.append(lines[index])
                index += 1
            pdf.set_fill_color(242, 246, 248)
            pdf.set_text_color(24, 35, 46)
            pdf.set_font("Thonburi", size=7.5)
            pdf.multi_cell(pdf.epw, 4, "\n".join(code_lines), fill=True)
            pdf.ln(2)
        elif line.strip() == "$$":
            equation: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "$$":
                equation.append(lines[index])
                index += 1
            pdf.set_fill_color(242, 246, 248)
            pdf.set_text_color(24, 35, 46)
            pdf.set_font("Thonburi", size=9)
            pdf.multi_cell(pdf.epw, 5, "\n".join(equation), align="C", fill=True)
            pdf.ln(2)
        elif line.strip() and line.strip() != "---":
            bullet = re.match(r"^(?:[-*]|\d+\.)\s+(.+)$", line)
            write_paragraph(pdf, ("• " if bullet else "") + (bullet.group(1) if bullet else line), indent=3 if bullet else 0)
        index += 1
    pdf.output(str(OUTPUT))
    print(f"PDF written to {OUTPUT}")


if __name__ == "__main__":
    render_pdf()