import io
import logging
import re
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from backend.prompts import extract_chapter_title


logger = logging.getLogger(__name__)


def _approved_chapters(chapters: list[dict]) -> list[dict]:
    return sorted(
        [chapter for chapter in chapters if chapter.get("status") == "approved"],
        key=lambda chapter: chapter["chapter_number"],
    )


def _clean_inline_markdown(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"^okay,?\s+here(?:'|’)s.*?$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"^do you want me to.*?$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"^write the chapter now:.*?$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"^editor feedback:.*?$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"`{1,3}", "", cleaned)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("—", "--")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _clean_paragraphs(text: str) -> list[str]:
    cleaned = _clean_inline_markdown(text)
    if not cleaned:
        return []
    paragraphs = []
    for block in re.split(r"\n\s*\n", cleaned):
        block = block.strip()
        if not block:
            continue
        if block.lower().startswith("summary:"):
            continue
        block = re.sub(r"^[*-]\s+", "", block)
        paragraphs.append(block)
    return paragraphs


def _chapter_title(outline: dict, chapter: dict) -> str:
    title = extract_chapter_title(outline.get("content", ""), chapter["chapter_number"]).strip()
    title = re.sub(r"^chapter\s+\d+\s*[:.-]\s*", "", title, flags=re.IGNORECASE).strip()
    return title or f"Chapter {chapter['chapter_number']}"


def _chapter_entries(outline: dict, chapters: list[dict]) -> list[tuple[int, str]]:
    return [
        (chapter["chapter_number"], _chapter_title(outline, chapter))
        for chapter in _approved_chapters(chapters)
    ]


def _set_book_margins(section):
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.95)
    section.right_margin = Inches(0.95)


def compile_to_docx(book: dict, outline: dict, chapters: list[dict]) -> bytes:
    try:
        document = Document()
        _set_book_margins(document.sections[0])

        styles = document.styles
        normal_style = styles["Normal"]
        normal_style.font.name = "Garamond"
        normal_style.font.size = Pt(12)

        title_style = styles["Title"]
        title_style.font.name = "Garamond"
        title_style.font.size = Pt(26)

        heading_style = styles["Heading 1"]
        heading_style.font.name = "Garamond"
        heading_style.font.size = Pt(18)

        subtitle_style = styles["Subtitle"] if "Subtitle" in styles else styles["Intense Quote"]
        subtitle_style.font.name = "Garamond"

        approved_chapters = _approved_chapters(chapters)
        chapter_entries = _chapter_entries(outline, approved_chapters)
        generated_on = datetime.now(UTC).strftime("%B %d, %Y")
        author_name = (book.get("author") or "AutoBook").strip()

        title_paragraph = document.add_paragraph(style="Title")
        title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_paragraph.add_run(book["title"].strip())

        author_paragraph = document.add_paragraph()
        author_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_run = author_paragraph.add_run(f"by {author_name}")
        author_run.italic = True
        author_run.font.name = "Garamond"
        author_run.font.size = Pt(14)

        generated_paragraph = document.add_paragraph()
        generated_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        generated_run = generated_paragraph.add_run(f"Prepared {generated_on}")
        generated_run.font.name = "Garamond"
        generated_run.font.size = Pt(10)

        document.add_page_break()

        toc_heading = document.add_paragraph(style="Heading 1")
        toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        toc_heading.add_run("Contents")

        for chapter_number, chapter_title in chapter_entries:
            entry = document.add_paragraph()
            entry.paragraph_format.space_after = Pt(8)
            entry.paragraph_format.left_indent = Inches(0.2)
            run = entry.add_run(f"Chapter {chapter_number}")
            run.bold = True
            run.font.name = "Garamond"
            run.font.size = Pt(12)
            title_run = entry.add_run(f"  {chapter_title}")
            title_run.font.name = "Garamond"
            title_run.font.size = Pt(12)

        for chapter in approved_chapters:
            document.add_section(WD_SECTION_START.NEW_PAGE)
            section = document.sections[-1]
            _set_book_margins(section)

            header = section.header.paragraphs[0]
            header.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_run = header.add_run(book["title"].strip())
            header_run.font.name = "Garamond"
            header_run.font.size = Pt(9)

            chapter_heading = document.add_paragraph(style="Heading 1")
            chapter_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            chapter_heading.paragraph_format.space_before = Pt(42)
            chapter_heading.paragraph_format.space_after = Pt(8)
            chapter_heading.add_run(f"Chapter {chapter['chapter_number']}")

            chapter_title = _chapter_title(outline, chapter)
            title_paragraph = document.add_paragraph()
            title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            title_paragraph.paragraph_format.space_after = Pt(26)
            title_run = title_paragraph.add_run(chapter_title)
            title_run.font.name = "Garamond"
            title_run.font.size = Pt(14)
            title_run.italic = True

            for paragraph in _clean_paragraphs(chapter.get("content", "")):
                body = document.add_paragraph()
                body.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                body.paragraph_format.first_line_indent = Inches(0.3)
                body.paragraph_format.line_spacing = 1.35
                body.paragraph_format.space_after = Pt(10)
                run = body.add_run(paragraph)
                run.font.name = "Garamond"
                run.font.size = Pt(12)

        output = io.BytesIO()
        document.save(output)
        return output.getvalue()
    except Exception as exc:
        logger.error("DOCX compilation failed: %s", exc, exc_info=True)
        raise


def compile_to_pdf(book: dict, outline: dict, chapters: list[dict]) -> bytes:
    try:
        output = io.BytesIO()
        approved_chapters = _approved_chapters(chapters)
        chapter_entries = _chapter_entries(outline, approved_chapters)
        generated_on = datetime.now(UTC).strftime("%B %d, %Y")
        author_name = (book.get("author") or "AutoBook").strip()

        document = SimpleDocTemplate(
            output,
            pagesize=LETTER,
            leftMargin=0.9 * inch,
            rightMargin=0.9 * inch,
            topMargin=0.9 * inch,
            bottomMargin=0.8 * inch,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "BookTitle",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=26,
            leading=32,
            alignment=TA_CENTER,
            spaceAfter=18,
        )
        subtitle_style = ParagraphStyle(
            "BookSubtitle",
            parent=styles["BodyText"],
            fontName="Times-Italic",
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading1"],
            fontName="Times-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=18,
        )
        chapter_number_style = ParagraphStyle(
            "ChapterNumber",
            parent=styles["Heading1"],
            fontName="Times-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=8,
            spaceBefore=28,
        )
        chapter_title_style = ParagraphStyle(
            "ChapterTitle",
            parent=styles["BodyText"],
            fontName="Times-Italic",
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=22,
        )
        body_style = ParagraphStyle(
            "BodyCopy",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            firstLineIndent=18,
            spaceAfter=10,
        )
        toc_style = ParagraphStyle(
            "TOCEntry",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=12,
            leading=16,
            leftIndent=18,
            spaceAfter=8,
        )

        story = [
            Spacer(1, 2.0 * inch),
            Paragraph(escape(book["title"].strip()), title_style),
            Paragraph(escape(f"by {author_name}"), subtitle_style),
            Paragraph(escape(f"Prepared {generated_on}"), ParagraphStyle(
                "GeneratedOn",
                parent=styles["BodyText"],
                fontName="Times-Roman",
                fontSize=10,
                leading=14,
                alignment=TA_CENTER,
            )),
            PageBreak(),
            Paragraph("Contents", section_style),
        ]

        for chapter_number, chapter_title in chapter_entries:
            story.append(
                Paragraph(
                    escape(f"Chapter {chapter_number}  {chapter_title}"),
                    toc_style,
                )
            )

        for chapter in approved_chapters:
            story.append(PageBreak())
            story.append(Paragraph(f"Chapter {chapter['chapter_number']}", chapter_number_style))
            story.append(Paragraph(escape(_chapter_title(outline, chapter)), chapter_title_style))

            for paragraph in _clean_paragraphs(chapter.get("content", "")):
                story.append(Paragraph(escape(paragraph).replace("\n", "<br/>"), body_style))

        def draw_page_chrome(canvas, doc):
            if canvas.getPageNumber() <= 1:
                return
            canvas.saveState()
            canvas.setFont("Times-Roman", 9)
            canvas.drawCentredString(LETTER[0] / 2.0, 0.55 * inch, book["title"].strip())
            canvas.drawRightString(LETTER[0] - 0.9 * inch, 0.55 * inch, str(canvas.getPageNumber()))
            canvas.restoreState()

        document.build(story, onFirstPage=draw_page_chrome, onLaterPages=draw_page_chrome)
        return output.getvalue()
    except Exception as exc:
        logger.error("PDF compilation failed: %s", exc, exc_info=True)
        raise
