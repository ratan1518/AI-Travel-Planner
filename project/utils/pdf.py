from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#1F4E79"),
        spaceAfter=8,
    )
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#16324F"),
        spaceAfter=14,
    )
    content = []

    for line in text.splitlines():
        safe_line = escape(line) or " "
        stripped = line.strip()

        if stripped.startswith("# "):
            content.append(Paragraph(escape(stripped[2:]), title_style))
            content.append(Spacer(1, 10))
        elif stripped.startswith("## "):
            content.append(Paragraph(escape(stripped[3:]), heading_style))
            content.append(Spacer(1, 6))
        elif stripped.startswith("### "):
            content.append(Paragraph(escape(stripped[4:]), styles["Heading3"]))
            content.append(Spacer(1, 4))
        elif stripped.startswith("- "):
            content.append(Paragraph(f"&bull; {escape(stripped[2:])}", styles["Normal"]))
            content.append(Spacer(1, 4))
        elif stripped:
            content.append(Paragraph(safe_line, styles["Normal"]))
            content.append(Spacer(1, 8))
        else:
            content.append(Spacer(1, 6))

    document.build(content)
    return buffer.getvalue()
