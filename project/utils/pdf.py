from html import escape
from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_pdf_bytes(text: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    for line in text.splitlines():
        safe_line = escape(line) or " "
        content.append(Paragraph(safe_line, styles["Normal"]))
        content.append(Spacer(1, 10))

    document.build(content)
    return buffer.getvalue()
