from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Flowable,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents

from booklib import (
    Block,
    Chapter,
    DIRECTIVE_LABELS,
    heading_id,
    load_chapters,
    load_metadata,
    render_inline_pdf,
)


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
OUTPUT_DIR = ROOT / "output" / "pdf"
DOWNLOAD_DIR = ROOT / "docs" / "downloads"

PAPER = colors.HexColor("#F4F0E8")
SURFACE = colors.HexColor("#FFFDF8")
INK = colors.HexColor("#18232D")
INK_SOFT = colors.HexColor("#52606B")
LINE = colors.HexColor("#D7D0C4")
NAVY = colors.HexColor("#18354A")
TEAL = colors.HexColor("#147D7A")
TEAL_SOFT = colors.HexColor("#D9EFEB")
CORAL = colors.HexColor("#E66A4E")
CORAL_SOFT = colors.HexColor("#FAE4DC")
YELLOW_SOFT = colors.HexColor("#FFF2C8")
GREEN = colors.HexColor("#2F7D56")
GREEN_SOFT = colors.HexColor("#DFEEE4")
DANGER = colors.HexColor("#A33E35")
DANGER_SOFT = colors.HexColor("#F8DFDC")
CODE_BG = colors.HexColor("#13232F")
CODE_TEXT = colors.HexColor("#E9F0F4")


class BookDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, *, metadata: dict, **kwargs):
        super().__init__(filename, **kwargs)
        self.metadata = metadata
        content_frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="content",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="cover", frames=[content_frame], onPage=self.draw_cover_page),
                PageTemplate(id="body", frames=[content_frame], onPage=self.draw_body_page),
            ]
        )

    def afterFlowable(self, flowable: Flowable) -> None:
        if isinstance(flowable, Paragraph) and getattr(flowable, "toc_level", None) is not None:
            level = flowable.toc_level
            text = flowable.getPlainText()
            key = getattr(flowable, "bookmark_name", heading_id(text))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            self.notify("TOCEntry", (level, text, self.page, key))

    def draw_cover_page(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canvas.setFillColor(CORAL)
        canvas.circle(A4[0] - 28 * mm, A4[1] - 24 * mm, 11 * mm, stroke=0, fill=1)
        canvas.setFillColor(TEAL)
        canvas.circle(23 * mm, 24 * mm, 6 * mm, stroke=0, fill=1)
        canvas.restoreState()

    def draw_body_page(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFillColor(SURFACE)
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, A4[1] - 15 * mm, A4[0] - doc.rightMargin, A4[1] - 15 * mm)
        canvas.setFont("BookSans", 8)
        canvas.setFillColor(INK_SOFT)
        canvas.drawString(doc.leftMargin, A4[1] - 11.5 * mm, self.metadata["title"])
        canvas.drawRightString(A4[0] - doc.rightMargin, 11 * mm, str(canvas.getPageNumber()))
        canvas.restoreState()


def register_fonts() -> None:
    candidates = [
        {
            "regular": Path(r"C:\Windows\Fonts\segoeui.ttf"),
            "bold": Path(r"C:\Windows\Fonts\segoeuib.ttf"),
            "italic": Path(r"C:\Windows\Fonts\segoeuii.ttf"),
            "bold_italic": Path(r"C:\Windows\Fonts\seguisbi.ttf"),
            "code": Path(r"C:\Windows\Fonts\consola.ttf"),
            "code_bold": Path(r"C:\Windows\Fonts\consolab.ttf"),
        },
        {
            "regular": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            "bold": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            "italic": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
            "bold_italic": Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
            "code": Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
            "code_bold": Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
        },
        {
            "regular": Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            "bold": Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            "italic": Path("/System/Library/Fonts/Supplemental/Arial Italic.ttf"),
            "bold_italic": Path("/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf"),
            "code": Path("/System/Library/Fonts/SFNSMono.ttf"),
            "code_bold": Path("/System/Library/Fonts/SFNSMono.ttf"),
        },
    ]
    font_set = next(
        (
            item
            for item in candidates
            if all(item[key].exists() for key in ("regular", "bold", "italic", "code", "code_bold"))
        ),
        None,
    )
    if font_set is None:
        raise RuntimeError("Не знайдено Unicode-шрифтів для українського PDF")

    pdfmetrics.registerFont(TTFont("BookSans", str(font_set["regular"])))
    pdfmetrics.registerFont(TTFont("BookSans-Bold", str(font_set["bold"])))
    pdfmetrics.registerFont(TTFont("BookSans-Italic", str(font_set["italic"])))
    pdfmetrics.registerFont(TTFont("BookSans-BoldItalic", str(font_set.get("bold_italic", font_set["bold"]))))
    pdfmetrics.registerFont(TTFont("BookCode", str(font_set["code"])))
    pdfmetrics.registerFont(TTFont("BookCode-Bold", str(font_set["code_bold"])))
    pdfmetrics.registerFontFamily(
        "BookSans",
        normal="BookSans",
        bold="BookSans-Bold",
        italic="BookSans-Italic",
        boldItalic="BookSans-BoldItalic",
    )
    pdfmetrics.registerFontFamily(
        "BookCode",
        normal="BookCode",
        bold="BookCode-Bold",
        italic="BookCode",
        boldItalic="BookCode-Bold",
    )


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="BookSans-Bold",
            fontSize=35,
            leading=38,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=9 * mm,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="BookSans",
            fontSize=16,
            leading=22,
            textColor=INK_SOFT,
            alignment=TA_LEFT,
        ),
        "cover_label": ParagraphStyle(
            "CoverLabel",
            parent=base["Normal"],
            fontName="BookSans-Bold",
            fontSize=9,
            leading=12,
            textColor=CORAL,
            tracking=1.2,
            spaceAfter=5 * mm,
        ),
        "h1": ParagraphStyle(
            "Heading1Book",
            parent=base["Heading1"],
            fontName="BookSans-Bold",
            fontSize=25,
            leading=28,
            textColor=NAVY,
            spaceBefore=3 * mm,
            spaceAfter=7 * mm,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "Heading2Book",
            parent=base["Heading2"],
            fontName="BookSans-Bold",
            fontSize=17,
            leading=21,
            textColor=NAVY,
            spaceBefore=9 * mm,
            spaceAfter=3.5 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3Book",
            parent=base["Heading3"],
            fontName="BookSans-Bold",
            fontSize=12.5,
            leading=16,
            textColor=NAVY,
            spaceBefore=6 * mm,
            spaceAfter=2.5 * mm,
            keepWithNext=True,
        ),
        "h4": ParagraphStyle(
            "Heading4Book",
            parent=base["Heading4"],
            fontName="BookSans-Bold",
            fontSize=10.5,
            leading=14,
            textColor=INK,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "BodyBook",
            parent=base["BodyText"],
            fontName="BookSans",
            fontSize=9.65,
            leading=14.2,
            textColor=INK,
            spaceAfter=3.3 * mm,
            allowWidows=0,
            allowOrphans=0,
        ),
        "small": ParagraphStyle(
            "SmallBook",
            parent=base["BodyText"],
            fontName="BookSans",
            fontSize=8.2,
            leading=11.5,
            textColor=INK_SOFT,
        ),
        "label": ParagraphStyle(
            "LabelBook",
            parent=base["BodyText"],
            fontName="BookSans-Bold",
            fontSize=7.4,
            leading=9,
            textColor=TEAL,
            spaceAfter=2 * mm,
        ),
        "code_label": ParagraphStyle(
            "CodeLabel",
            parent=base["BodyText"],
            fontName="BookCode",
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor("#9FB0B9"),
        ),
        "code": ParagraphStyle(
            "CodeBook",
            parent=base["Code"],
            fontName="BookCode",
            fontSize=7.15,
            leading=10.1,
            textColor=CODE_TEXT,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "toc_title": ParagraphStyle(
            "TocTitle",
            parent=base["Heading1"],
            fontName="BookSans-Bold",
            fontSize=24,
            leading=28,
            textColor=NAVY,
            spaceAfter=7 * mm,
        ),
        "chapter_label": ParagraphStyle(
            "ChapterLabel",
            parent=base["Normal"],
            fontName="BookSans-Bold",
            fontSize=8,
            leading=10,
            textColor=CORAL,
            spaceAfter=3 * mm,
        ),
    }


def build_pdf() -> Path:
    register_fonts()
    metadata = load_metadata(ROOT)
    chapters = load_chapters(CONTENT_DIR)
    styles = make_styles()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / metadata["pdf_filename"]

    document = BookDocTemplate(
        str(output_path),
        metadata=metadata,
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=19 * mm,
        title=metadata["title"],
        subject=metadata["description"],
        creator="Python через об’єкти — build pipeline",
    )
    story: list[Flowable] = []
    story.extend(build_cover(metadata, styles))
    story.extend(build_toc(styles))
    for chapter in chapters:
        story.append(PageBreak())
        label = "ВСТУП" if chapter.order == 0 else f"РОЗДІЛ {chapter.order:02d}"
        story.append(Paragraph(label, styles["chapter_label"]))
        story.extend(blocks_to_flowables(chapter.blocks, styles, chapter))

    document.multiBuild(story)
    shutil.copy2(output_path, DOWNLOAD_DIR / metadata["pdf_filename"])
    return output_path


def build_cover(metadata: dict, styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    return [
        Spacer(1, 36 * mm),
        Paragraph("ПРАКТИЧНА ДОВІДКА ДЛЯ ПОЧАТКІВЦІВ", styles["cover_label"]),
        Paragraph(metadata["title"], styles["cover_title"]),
        Paragraph(metadata["subtitle"], styles["cover_subtitle"]),
        Spacer(1, 22 * mm),
        Table(
            [[Paragraph(
                "Від першого <font name=\"BookCode\">.py</font>-файла до об’єктів, файлів, помилок і тестів. "
                "Спочатку передбачаємо результат, потім запускаємо, простежуємо стан, поступово прибираємо "
                "підказки й переносимо знання у власну програму.",
                styles["body"],
            )]],
            colWidths=[128 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
                    ("BOX", (0, 0), (-1, -1), 0.8, LINE),
                    ("LINEBEFORE", (0, 0), (0, -1), 4, TEAL),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 6 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                ]
            ),
        ),
        Spacer(1, 36 * mm),
        Paragraph(metadata["edition"], styles["cover_label"]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Попередня версія збережена на сайті як класичне видання.",
            styles["small"],
        ),
        NextPageTemplate("body"),
        PageBreak(),
    ]


def build_toc(styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="BookSans-Bold",
            fontSize=10,
            leading=14,
            textColor=INK,
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=2.5 * mm,
        ),
        ParagraphStyle(
            "TOC2",
            fontName="BookSans",
            fontSize=8.5,
            leading=12,
            textColor=INK_SOFT,
            leftIndent=7 * mm,
            firstLineIndent=0,
            spaceBefore=1 * mm,
        ),
    ]
    return [Paragraph("Зміст", styles["toc_title"]), toc]


def blocks_to_flowables(
    blocks: Iterable[Block],
    styles: dict[str, ParagraphStyle],
    chapter: Chapter,
) -> list[Flowable]:
    flowables: list[Flowable] = []
    heading_serial = 0
    block_list = list(blocks)
    for block_index, block in enumerate(block_list):
        next_block = block_list[block_index + 1] if block_index + 1 < len(block_list) else None
        if block.kind == "heading":
            level = block.data["level"]
            style = styles[f"h{level}"]
            if level >= 2:
                minimum_following_space = {2: 32, 3: 27, 4: 23}.get(level, 23)
                nearby_blocks = block_list[block_index + 1 : block_index + 4]
                if level == 2 and any(
                    nearby.kind == "directive"
                    and nearby.data.get("directive") == "tasks"
                    for nearby in nearby_blocks
                ):
                    minimum_following_space = 110
                flowables.append(CondPageBreak(minimum_following_space * mm))
            paragraph = Paragraph(render_inline_pdf(block.data["text"]), style)
            if level >= 2:
                paragraph.keepWithNext = True
            if level <= 2:
                heading_serial += 1
                paragraph.toc_level = 0 if level == 1 else 1
                paragraph.bookmark_name = f"{chapter.slug}-{heading_serial}-{heading_id(block.data['text'])}"
            flowables.append(paragraph)
        elif block.kind == "paragraph":
            paragraph = Paragraph(render_inline_pdf(block.data["text"]), styles["body"])
            if next_block is not None and next_block.kind in {"code", "list", "quiz", "trace", "directive"}:
                paragraph.keepWithNext = True
            flowables.append(paragraph)
        elif block.kind == "list":
            items = [
                ListItem(Paragraph(render_inline_pdf(item), styles["body"]), leftIndent=3 * mm)
                for item in block.data["items"]
            ]
            list_options = {
                "bulletType": "1" if block.data["ordered"] else "bullet",
                "leftIndent": 7 * mm,
                "bulletFontName": "BookSans",
                "bulletFontSize": 8,
                "bulletColor": TEAL,
                "spaceAfter": 3 * mm,
            }
            if block.data["ordered"]:
                list_options["start"] = "1"
            else:
                list_options["bulletChar"] = "•"
            flowables.append(ListFlowable(items, **list_options))
        elif block.kind == "code":
            label = block.data["attributes"].get("file") or (
                "Результат" if block.data["language"] == "output" else block.data["language"]
            )
            code_lines = block.data["code"].splitlines() or [""]
            previous_block = block_list[block_index - 1] if block_index > 0 else None
            follows_prediction = (
                previous_block is not None
                and previous_block.kind == "directive"
                and previous_block.data.get("directive") == "predict"
            )
            first_chunk_size = 16 if follows_prediction and len(code_lines) > 22 else 22
            code_chunks = [code_lines[:first_chunk_size]]
            code_chunks.extend(
                code_lines[start : start + 22]
                for start in range(first_chunk_size, len(code_lines), 22)
            )
            for chunk_index, chunk in enumerate(code_chunks):
                chunk_label = label if chunk_index == 0 else f"{label} · продовження"
                flowables.append(code_table(chunk_label, "\n".join(chunk), styles))
        elif block.kind == "rule":
            flowables.append(Spacer(1, 4 * mm))
        elif block.kind == "image":
            image_path = resolve_image(block.data["src"])
            if image_path.exists():
                image = Image(str(image_path))
                image._restrictSize(160 * mm, 105 * mm)
                flowables.extend(
                    [
                        Spacer(1, 3 * mm),
                        KeepTogether(
                            [
                                image,
                                Paragraph(render_inline_pdf(block.data["alt"]), styles["small"]),
                            ]
                        ),
                        Spacer(1, 3 * mm),
                    ]
                )
        elif block.kind == "quiz":
            quiz_flowables: list[Flowable] = [
                Paragraph("ПЕРЕВІР СЕБЕ", styles["label"]),
                Paragraph(render_inline_pdf(block.data["question"]), styles["body"]),
            ]
            quiz_flowables.append(
                ListFlowable(
                    [ListItem(Paragraph(render_inline_pdf(option), styles["body"])) for option in block.data["options"]],
                    bulletType="bullet",
                    leftIndent=7 * mm,
                    bulletColor=CORAL,
                )
            )
            quiz_flowables.append(
                Paragraph(
                    f"<b>Відповідь:</b> {render_inline_pdf(block.data['correct'])}<br/>{render_inline_pdf(block.data['explanation'])}",
                    styles["small"],
                )
            )
            flowables.append(callout_table(quiz_flowables, CORAL, SURFACE))
        elif block.kind == "trace":
            flowables.append(trace_table(block.data, styles))
        elif block.kind == "directive":
            directive = block.data["directive"]
            title = block.data["title"] or DIRECTIVE_LABELS.get(directive, directive.capitalize())
            border, background = directive_colors(directive)
            nested_blocks = list(block.data["blocks"])
            is_complex = (
                directive in {"os", "tasks"}
                or any(item.kind == "code" for item in _walk_blocks(nested_blocks))
                or len(list(_walk_blocks(nested_blocks))) > 5
            )
            inner = blocks_to_flowables(nested_blocks, styles, chapter)
            if is_complex:
                header = callout_header(title, border, background, styles)
                if inner:
                    prefix: list[Flowable] = []
                    prefix_size = 0
                    while prefix_size < len(inner) and len(prefix) < 2:
                        item = inner[prefix_size]
                        prefix_size += 1
                        if isinstance(item, CondPageBreak):
                            continue
                        prefix.append(item)
                    flowables.append(KeepTogether([header, *prefix]))
                    flowables.extend(inner[prefix_size:])
                else:
                    flowables.append(header)
                flowables.append(Spacer(1, 3 * mm))
            else:
                callout = callout_table(
                    [Paragraph(render_inline_pdf(title.upper()), styles["label"]), *inner],
                    border,
                    background,
                )
                if directive == "predict":
                    callout.keepWithNext = True
                flowables.append(callout)
    return flowables


def directive_colors(directive: str):
    return {
        "goal": (TEAL, TEAL_SOFT),
        "focus": (TEAL, TEAL_SOFT),
        "predict": (colors.HexColor("#D89A25"), YELLOW_SOFT),
        "practice": (colors.HexColor("#D89A25"), YELLOW_SOFT),
        "completion": (GREEN, GREEN_SOFT),
        "parsons": (GREEN, GREEN_SOFT),
        "recall": (CORAL, CORAL_SOFT),
        "check": (colors.HexColor("#D89A25"), YELLOW_SOFT),
        "tasks": (colors.HexColor("#D89A25"), YELLOW_SOFT),
        "warning": (DANGER, DANGER_SOFT),
        "mistake": (DANGER, DANGER_SOFT),
        "os": (CORAL, CORAL_SOFT),
        "answer": (GREEN, GREEN_SOFT),
        "history": (NAVY, SURFACE),
    }.get(directive, (TEAL, SURFACE))


def trace_table(data: dict, styles: dict[str, ParagraphStyle]) -> Table:
    state_table = Table(
        [[
            Paragraph(
                f'<font color="#52606b">ДО</font><br/><b>{render_inline_pdf(data["before"])}</b>',
                styles["body"],
            ),
            Paragraph("→", styles["h3"]),
            Paragraph(
                f'<font color="#2f7d56">ПІСЛЯ</font><br/><b>{render_inline_pdf(data["after"])}</b>',
                styles["body"],
            ),
        ]],
        colWidths=[69 * mm, 10 * mm, 69 * mm],
        hAlign="LEFT",
    )
    state_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), PAPER),
                ("BACKGROUND", (2, 0), (2, 0), GREEN_SOFT),
                ("BOX", (0, 0), (0, 0), 0.5, LINE),
                ("BOX", (2, 0), (2, 0), 0.5, LINE),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )

    step_rows = []
    for index, step in enumerate(data["steps"], 1):
        step_rows.append(
            [
                Paragraph(f"<b>{index}</b>", styles["body"]),
                Paragraph(f"<b>{render_inline_pdf(step['label'])}</b>", styles["small"]),
                Paragraph(render_inline_pdf(step["code"]), styles["small"]),
                Paragraph(render_inline_pdf(step["meaning"]), styles["small"]),
            ]
        )
    steps_table = Table(
        step_rows,
        colWidths=[9 * mm, 28 * mm, 43 * mm, 68 * mm],
        hAlign="LEFT",
        repeatRows=0,
    )
    steps_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), TEAL_SOFT),
                ("TEXTCOLOR", (0, 0), (0, -1), TEAL),
                ("GRID", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    return callout_table(
        [
            Paragraph(render_inline_pdf(data["title"].upper()), styles["label"]),
            state_table,
            Spacer(1, 3 * mm),
            steps_table,
            Spacer(1, 2 * mm),
            Paragraph(
                f'<b>Що тут важливо:</b> {render_inline_pdf(data["meaning"])}',
                styles["small"],
            ),
        ],
        TEAL,
        SURFACE,
    )


def callout_table(flowables: list[Flowable], border, background) -> Table:
    table = Table([[flowables]], colWidths=[None], hAlign="LEFT", splitByRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    table.spaceBefore = 3 * mm
    table.spaceAfter = 4 * mm
    return table


def code_table(label: str, code: str, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [
            [Paragraph(render_inline_pdf(label), styles["code_label"])],
            [XPreformatted(_escape_code(code), styles["code"])],
        ],
        colWidths=[None],
        hAlign="LEFT",
        splitByRow=0,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E1C25")),
                ("BACKGROUND", (0, 1), (-1, 1), CODE_BG),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#29414F")),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#29414F")),
                ("LEFTPADDING", (0, 0), (-1, 0), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, 0), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, 0), 2.1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2.1 * mm),
                ("LEFTPADDING", (0, 1), (-1, 1), 4 * mm),
                ("RIGHTPADDING", (0, 1), (-1, 1), 4 * mm),
                ("TOPPADDING", (0, 1), (-1, 1), 3.5 * mm),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 3.5 * mm),
            ]
        )
    )
    table.spaceBefore = 2.5 * mm
    table.spaceAfter = 4 * mm
    return table


def callout_header(title: str, border, background, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [[Paragraph(render_inline_pdf(title.upper()), styles["label"])]],
        colWidths=[None],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, border),
                ("LEFTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ]
        )
    )
    table.spaceBefore = 3 * mm
    table.spaceAfter = 3 * mm
    return table


def _walk_blocks(blocks: Iterable[Block]) -> Iterable[Block]:
    for block in blocks:
        yield block
        if block.kind == "directive":
            yield from _walk_blocks(block.data["blocks"])


def resolve_image(source: str) -> Path:
    source_path = Path(source)
    for candidate in (ROOT / source_path, ROOT / "site" / source_path, ROOT / "content" / source_path):
        if candidate.exists():
            return candidate
    return ROOT / source_path


def _escape_code(code: str) -> str:
    return code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    path = build_pdf()
    print(f"PDF зібрано: {path}")
