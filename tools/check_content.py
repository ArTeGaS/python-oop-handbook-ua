from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from booklib import Block, Chapter, iter_blocks, load_chapters, load_metadata


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
DOCS_DIR = ROOT / "docs"
REPORTS_DIR = ROOT / "reports"
OUTPUT_PDF_DIR = ROOT / "output" / "pdf"
CLASSIC_DIR = ROOT / "editions" / "classic"

FORBIDDEN_SOURCE_REFERENCES = (
    "matthes",
    "метьюз",
    "метьюза",
    "мєтьюз",
    "ерік мат",
    "eric mat",
)

ATTENTION_ACTIVE_DIRECTIVES = {
    "focus",
    "predict",
    "practice",
    "completion",
    "parsons",
    "check",
    "recall",
    "tasks",
}
ATTENTION_LIMITS = {
    "max_paragraph_words": 70,
    "max_passive_words_between_actions": 450,
    "minimum_active_prompts_per_main_chapter": 7,
    "minimum_reentry_headings_per_main_chapter": 12,
    "long_code_soft_limit_lines": 60,
    "minimum_navigation_comments_in_long_code": 3,
}
NAVIGATION_COMMENT = re.compile(r"^\s*#\s*\d+[.)]\s+\S", re.MULTILINE)


@dataclass
class CheckReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    runnable_blocks: int = 0
    expected_error_blocks: int = 0
    python_blocks: int = 0
    pages: int = 0
    attention_chapters: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "passed": self.passed,
            "metrics": {
                "runnable_code_blocks": self.runnable_blocks,
                "expected_error_blocks": self.expected_error_blocks,
                "python_code_blocks": self.python_blocks,
                "pdf_pages": self.pages,
            },
            "attention": attention_payload(self.attention_chapters),
        }


def check_sources(*, strict: bool) -> tuple[list[Chapter], CheckReport]:
    report = CheckReport()
    metadata = load_metadata(ROOT)
    try:
        chapters = load_chapters(CONTENT_DIR)
    except Exception as error:
        report.errors.append(f"Не вдалося прочитати розділи: {error}")
        return [], report

    if strict and len(chapters) != metadata["expected_chapters"]:
        report.errors.append(
            f"Очікувалося {metadata['expected_chapters']} файлів розділів, знайдено {len(chapters)}"
        )
    elif len(chapters) < metadata["expected_chapters"]:
        report.warnings.append(
            f"Чернетка: {len(chapters)} з {metadata['expected_chapters']} запланованих розділів"
        )
    else:
        report.passed.append(f"Повнота структури: {len(chapters)} розділів")

    seen_slugs: set[str] = set()
    for chapter in chapters:
        if chapter.slug in seen_slugs:
            report.errors.append(f"Повторюється slug {chapter.slug}")
        seen_slugs.add(chapter.slug)
        check_chapter(chapter, report, strict=strict)

    check_forbidden_references(report)
    check_classic_sources(report, strict=strict)
    if not report.errors:
        report.passed.append("Структура й кодові блоки джерел перевірені")
        report.passed.append("Навчальний ритм першого офіційного видання перевірено")
        summary = attention_payload(report.attention_chapters)["book"]
        report.passed.append(
            "Увага пройшла окремий аудит: "
            f"пасивний відрізок до {summary['longest_passive_stretch_words']} слів, "
            f"абзац до {summary['longest_paragraph_words']} слів"
        )
        report.passed.append(
            f"Навмисні помилки відтворені: {report.expected_error_blocks} блоків"
        )
    return chapters, report


def check_chapter(chapter: Chapter, report: CheckReport, *, strict: bool) -> None:
    headings = {
        block.data["text"].strip().lower()
        for block in iter_blocks(chapter.blocks)
        if block.kind == "heading"
    }
    directives = [
        block for block in iter_blocks(chapter.blocks) if block.kind == "directive"
    ]
    quizzes = [block for block in iter_blocks(chapter.blocks) if block.kind == "quiz"]
    code_blocks = [block for block in iter_blocks(chapter.blocks) if block.kind == "code"]
    document_blocks = list(iter_blocks(chapter.blocks))
    check_error_evidence(chapter.blocks, chapter, report)

    if chapter.order > 0:
        required_headings = {
            "що зробимо",
            "майстерня",
            "типова помилка",
            "швидка перевірка",
            "підсумок",
        }
        missing = sorted(required_headings - headings)
        if missing:
            report.errors.append(f"{chapter.source_path.name}: немає секцій {', '.join(missing)}")
        task_blocks = [block for block in directives if block.data["directive"] == "tasks"]
        if not task_blocks:
            report.errors.append(f"{chapter.source_path.name}: немає блоку самостійних завдань")
        elif strict:
            task_items = sum(
                len(inner.data["items"])
                for task_block in task_blocks
                for inner in iter_blocks(task_block.data["blocks"])
                if inner.kind == "list"
            )
            if task_items < 4:
                report.errors.append(
                    f"{chapter.source_path.name}: потрібно щонайменше 4 самостійні завдання, є {task_items}"
                )
        if strict and not quizzes:
            report.errors.append(f"{chapter.source_path.name}: немає інтерактивної самоперевірки")
        directive_names = [block.data["directive"] for block in directives]
        for required in ("focus", "predict", "recall"):
            if directive_names.count(required) != 1:
                report.errors.append(
                    f"{chapter.source_path.name}: потрібен рівно один блок {required}"
                )
        traces = [block for block in document_blocks if block.kind == "trace"]
        if len(traces) != 1:
            report.errors.append(
                f"{chapter.source_path.name}: потрібна рівно одна інтегрована trace-схема"
            )
        bridge_count = sum(name in {"completion", "parsons"} for name in directive_names)
        if bridge_count != 1:
            report.errors.append(
                f"{chapter.source_path.name}: потрібен рівно один проміжний блок completion або parsons"
            )
        check_learning_block_order(chapter, document_blocks, report)

    check_attention(chapter, document_blocks, report, strict=strict)

    runnable_in_chapter = 0
    for number, block in enumerate(code_blocks, 1):
        if block.data["language"] != "python":
            continue
        report.python_blocks += 1
        code = block.data["code"]
        flags = block.data["flags"]
        for line_number, line in enumerate(code.splitlines(), 1):
            if len(line) > 100:
                report.warnings.append(
                    f"{chapter.source_path.name}, код {number}, рядок {line_number}: {len(line)} символів"
                )
        if "fragment" not in flags and "error" not in flags:
            try:
                compile(code, f"{chapter.source_path.name}:code-{number}", "exec")
            except SyntaxError as error:
                report.errors.append(
                    f"{chapter.source_path.name}, код {number}: SyntaxError — {error.msg}"
                )
        if "run" in flags:
            runnable_in_chapter += 1
            report.runnable_blocks += 1
            run_python_block(chapter, number, block, report)
        if "error" in flags:
            report.expected_error_blocks += 1
            run_error_block(chapter, number, block, report)

    if chapter.order > 0 and strict and runnable_in_chapter == 0:
        report.errors.append(f"{chapter.source_path.name}: немає runnable Python-прикладу")


def run_python_block(chapter: Chapter, number: int, block: Block, report: CheckReport) -> None:
    attributes = block.data["attributes"]
    stdin_text = attributes.get("stdin", "").replace("\\n", "\n")
    expected = attributes.get("expect")
    if expected is not None:
        expected = expected.replace("\\n", "\n")
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        with tempfile.TemporaryDirectory(prefix="python-oop-handbook-") as temp_dir:
            result = subprocess.run(
                [sys.executable, "-c", block.data["code"]],
                input=stdin_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8,
                cwd=temp_dir,
                env=environment,
            )
    except subprocess.TimeoutExpired:
        report.errors.append(f"{chapter.source_path.name}, код {number}: перевищено 8 секунд")
        return
    if result.returncode != 0:
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: запуск завершився з {result.returncode}: "
            f"{result.stderr.strip()[:500]}"
        )
        return
    if expected is not None and normalize_output(expected) not in normalize_output(result.stdout):
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: очікуване виведення {expected!r}, отримано {result.stdout!r}"
        )


def check_learning_block_order(
    chapter: Chapter, blocks: list[Block], report: CheckReport
) -> None:
    def first_index(predicate) -> int | None:
        return next((index for index, block in enumerate(blocks) if predicate(block)), None)

    predict = first_index(
        lambda block: block.kind == "directive" and block.data["directive"] == "predict"
    )
    first_run = first_index(
        lambda block: block.kind == "code" and "run" in block.data["flags"]
    )
    trace = first_index(lambda block: block.kind == "trace")
    bridge = first_index(
        lambda block: block.kind == "directive"
        and block.data["directive"] in {"completion", "parsons"}
    )
    mistake_heading = first_index(
        lambda block: block.kind == "heading"
        and block.data["text"].strip().lower() == "типова помилка"
    )
    recall = first_index(
        lambda block: block.kind == "directive" and block.data["directive"] == "recall"
    )
    tasks = first_index(
        lambda block: block.kind == "directive" and block.data["directive"] == "tasks"
    )
    history = first_index(
        lambda block: block.kind == "directive" and block.data["directive"] == "history"
    )

    expected_pairs = [
        (predict, first_run, "predict має стояти перед першим запуском"),
        (first_run, trace, "trace має стояти після першого запуску"),
        (bridge, mistake_heading, "completion/parsons має стояти до типової помилки"),
        (recall, tasks, "recall має стояти до самостійної роботи"),
        (tasks, history, "історична пауза має стояти після самостійної дії"),
    ]
    for earlier, later, message in expected_pairs:
        if earlier is None or later is None or earlier >= later:
            report.errors.append(f"{chapter.source_path.name}: {message}")


def attention_payload(chapters: list[dict]) -> dict:
    main_chapters = [item for item in chapters if item["chapter"] > 0]
    all_passed = bool(chapters) and all(item["passed"] for item in chapters)
    return {
        "status": "pass" if all_passed else "fail",
        "thresholds": ATTENTION_LIMITS,
        "book": {
            "chapters_audited": len(chapters),
            "longest_paragraph_words": max(
                (item["max_paragraph_words"] for item in chapters), default=0
            ),
            "longest_passive_stretch_words": max(
                (item["max_passive_words_between_actions"] for item in chapters),
                default=0,
            ),
            "minimum_active_prompts_in_main_chapter": min(
                (item["active_prompts"] for item in main_chapters), default=0
            ),
            "minimum_reentry_headings_in_main_chapter": min(
                (item["reentry_headings"] for item in main_chapters), default=0
            ),
            "longest_code_block_lines": max(
                (item["max_code_lines"] for item in chapters), default=0
            ),
            "long_code_blocks": sum(
                item["long_code_blocks"] for item in chapters
            ),
            "long_code_blocks_with_navigation": sum(
                item["long_code_blocks_with_navigation"] for item in chapters
            ),
        },
        "chapters": chapters,
    }


def check_attention(
    chapter: Chapter,
    blocks: list[Block],
    report: CheckReport,
    *,
    strict: bool,
) -> None:
    paragraph_words = [
        word_count(block.data["text"])
        for block in blocks
        if block.kind == "paragraph"
    ]
    code_blocks = [block for block in blocks if block.kind == "code"]
    code_lines = [len(block.data["code"].splitlines()) for block in code_blocks]
    long_code_blocks = [
        block
        for block, line_count in zip(code_blocks, code_lines)
        if line_count > ATTENTION_LIMITS["long_code_soft_limit_lines"]
    ]
    long_code_with_navigation = sum(
        len(NAVIGATION_COMMENT.findall(block.data["code"]))
        >= ATTENTION_LIMITS["minimum_navigation_comments_in_long_code"]
        for block in long_code_blocks
    )
    active_prompts = sum(is_attention_action(block) for block in blocks)
    reentry_headings = sum(
        block.kind == "heading" and block.data["level"] >= 2 for block in blocks
    )
    max_passive_words = longest_passive_stretch(blocks)

    failures: list[str] = []
    max_paragraph_words = max(paragraph_words, default=0)
    if max_paragraph_words > ATTENTION_LIMITS["max_paragraph_words"]:
        failures.append(
            f"найдовший абзац має {max_paragraph_words} слів"
        )
    if max_passive_words > ATTENTION_LIMITS["max_passive_words_between_actions"]:
        failures.append(
            f"пасивний відрізок має {max_passive_words} слів без дії учня"
        )
    if chapter.order > 0:
        if active_prompts < ATTENTION_LIMITS["minimum_active_prompts_per_main_chapter"]:
            failures.append(
                f"лише {active_prompts} активних відповідей або дій"
            )
        if reentry_headings < ATTENTION_LIMITS["minimum_reentry_headings_per_main_chapter"]:
            failures.append(
                f"лише {reentry_headings} точок повернення у підзаголовках"
            )
    if long_code_with_navigation != len(long_code_blocks):
        failures.append(
            "довгий код не має щонайменше трьох пронумерованих навігаційних коментарів"
        )

    metrics = {
        "chapter": chapter.order,
        "source": chapter.source_path.name,
        "max_paragraph_words": max_paragraph_words,
        "max_passive_words_between_actions": max_passive_words,
        "active_prompts": active_prompts,
        "reentry_headings": reentry_headings,
        "max_code_lines": max(code_lines, default=0),
        "long_code_blocks": len(long_code_blocks),
        "long_code_blocks_with_navigation": long_code_with_navigation,
        "passed": not failures,
    }
    report.attention_chapters.append(metrics)

    for failure in failures:
        message = f"{chapter.source_path.name}: увага — {failure}"
        if strict:
            report.errors.append(message)
        else:
            report.warnings.append(message)


def longest_passive_stretch(blocks: list[Block]) -> int:
    current = 0
    longest = 0
    for block in blocks:
        if is_attention_action(block):
            longest = max(longest, current)
            current = 0
            continue
        if block.kind == "paragraph":
            current += word_count(block.data["text"])
        elif block.kind == "list":
            current += sum(word_count(item) for item in block.data["items"])
    return max(longest, current)


def is_attention_action(block: Block) -> bool:
    if block.kind in {"quiz", "trace"}:
        return True
    if block.kind == "directive":
        return block.data["directive"] in ATTENTION_ACTIVE_DIRECTIVES
    return block.kind == "code" and bool(
        block.data["flags"] & {"run", "error"}
    )


def word_count(text: str) -> int:
    return len(re.findall(r"[\w’'-]+", text, flags=re.UNICODE))


def check_classic_sources(report: CheckReport, *, strict: bool) -> None:
    metadata_path = CLASSIC_DIR / "edition.json"
    content_dir = CLASSIC_DIR / "content"
    site_dir = CLASSIC_DIR / "site"
    required = [
        metadata_path,
        CLASSIC_DIR / "book.json",
        site_dir / "index.html",
        site_dir / "downloads" / "python-cherez-obiekty.pdf",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        report.errors.append(f"Класичне видання неповне: {', '.join(missing)}")
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    sources = sorted(content_dir.glob("*.md"))
    if len(sources) != metadata["chapter_count"]:
        report.errors.append(
            f"Класичне видання: очікувалося {metadata['chapter_count']} джерел, є {len(sources)}"
        )
    classic_reader = PdfReader(str(site_dir / "downloads" / "python-cherez-obiekty.pdf"))
    if strict and len(classic_reader.pages) != metadata["pdf_page_count"]:
        report.errors.append(
            f"Класичне видання: очікувалося {metadata['pdf_page_count']} сторінок PDF, "
            f"є {len(classic_reader.pages)}"
        )
    if not report.errors:
        report.passed.append(
            f"Класичне видання збережене: {len(sources)} розділів, {len(classic_reader.pages)} сторінки"
        )


def run_error_block(chapter: Chapter, number: int, block: Block, report: CheckReport) -> None:
    attributes = block.data["attributes"]
    expected_error = attributes.get("raises")
    if not expected_error:
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: блок error не має атрибута raises"
        )
        return

    stdin_text = attributes.get("stdin", "").replace("\\n", "\n")
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        with tempfile.TemporaryDirectory(prefix="python-oop-handbook-error-") as temp_dir:
            result = subprocess.run(
                [sys.executable, "-c", block.data["code"]],
                input=stdin_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8,
                cwd=temp_dir,
                env=environment,
            )
    except subprocess.TimeoutExpired:
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: навмисна помилка зависла довше 8 секунд"
        )
        return

    if result.returncode == 0:
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: очікувався {expected_error}, але код завершився успішно"
        )
        return
    if expected_error not in result.stderr:
        report.errors.append(
            f"{chapter.source_path.name}, код {number}: очікувався {expected_error}, отримано "
            f"{result.stderr.strip()[:500]}"
        )


def check_error_evidence(
    blocks: Iterable[Block], chapter: Chapter, report: CheckReport
) -> None:
    block_list = list(blocks)
    for index, block in enumerate(block_list):
        if block.kind == "directive":
            check_error_evidence(block.data["blocks"], chapter, report)
        if not (
            block.kind == "code"
            and block.data["language"] == "python"
            and "error" in block.data["flags"]
        ):
            continue

        following = block_list[index + 1 : index + 3]
        has_visible_output = any(
            candidate.kind == "code"
            and candidate.data["language"] in {"output", "text"}
            for candidate in following
        )
        if not has_visible_output:
            report.errors.append(
                f"{chapter.source_path.name}: після навмисної помилки немає оформленого журналу"
            )


def normalize_output(value: str) -> str:
    return value.replace("\r\n", "\n").strip()


def check_forbidden_references(report: CheckReport) -> None:
    checked_paths = [ROOT / "README.md", *CONTENT_DIR.glob("*.md"), ROOT / "book.json"]
    for path in checked_paths:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_SOURCE_REFERENCES:
            if forbidden in text:
                report.errors.append(f"{path.relative_to(ROOT)}: заборонене посилання на джерело ({forbidden})")


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.lang = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.lang = values.get("lang", "")
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if values.get("id"):
            self.ids.add(values["id"])


def check_built_outputs(report: CheckReport, *, strict: bool) -> None:
    if not DOCS_DIR.exists():
        report.errors.append("Папка docs не створена")
        return
    if strict and not (DOCS_DIR / ".nojekyll").exists():
        report.errors.append("У docs немає .nojekyll для GitHub Pages")
    check_classic_built_copy(report)
    html_files = sorted(DOCS_DIR.glob("*.html"))
    if not html_files:
        report.errors.append("У docs немає HTML-сторінок")
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        parser = LinkCollector()
        parser.feed(text)
        if parser.lang != "uk":
            report.errors.append(f"{path.name}: html lang має бути uk")
        lowered = text.lower()
        if "inlineplaceholder" in lowered:
            report.errors.append(f"{path.name}: у HTML лишився службовий placeholder")
        for forbidden in FORBIDDEN_SOURCE_REFERENCES:
            if forbidden in lowered:
                report.errors.append(f"{path.name}: у зібраному HTML є заборонене слово {forbidden}")
        for href in parser.links:
            if href.startswith(("http://", "https://", "mailto:", "#", "javascript:")):
                continue
            target, _, anchor = href.partition("#")
            target_path = DOCS_DIR / (target or path.name)
            if not target_path.exists():
                if strict or not href.startswith("downloads/"):
                    report.errors.append(f"{path.name}: битий локальний лінк {href}")
                continue
            if anchor and target_path.suffix == ".html":
                target_parser = LinkCollector()
                target_parser.feed(target_path.read_text(encoding="utf-8"))
                if anchor not in target_parser.ids:
                    report.errors.append(f"{path.name}: немає якоря {href}")

    app_js = DOCS_DIR / "assets" / "app.js"
    if app_js.exists():
        node = shutil_which("node")
        if node:
            result = subprocess.run([node, "--check", str(app_js)], capture_output=True, text=True)
            if result.returncode != 0:
                report.errors.append(f"app.js: помилка синтаксису: {result.stderr.strip()}")
            else:
                report.passed.append("JavaScript пройшов node --check")
        else:
            report.warnings.append("Node.js не знайдено; app.js не перевірено через node --check")

    metadata = load_metadata(ROOT)
    pdf_path = OUTPUT_PDF_DIR / metadata["pdf_filename"]
    download_path = DOCS_DIR / "downloads" / metadata["pdf_filename"]
    if not pdf_path.exists():
        report.errors.append("Фінальний PDF не створено")
        return
    if not download_path.exists():
        report.errors.append("PDF не скопійовано в docs/downloads")
        return
    if sha256(pdf_path) != sha256(download_path):
        report.errors.append("PDF у output і docs/downloads відрізняються")
    reader = PdfReader(str(pdf_path))
    report.pages = len(reader.pages)
    if strict and report.pages < 40:
        report.errors.append(f"PDF виглядає неповним: лише {report.pages} сторінок")
    extracted = "\n".join((page.extract_text() or "") for page in reader.pages).lower()
    if "inlineplaceholder" in extracted:
        report.errors.append("У PDF лишився службовий placeholder")
    for forbidden in FORBIDDEN_SOURCE_REFERENCES:
        if forbidden in extracted:
            report.errors.append(f"У PDF є заборонене посилання на джерело ({forbidden})")
    report.passed.append(f"PDF читається: {report.pages} сторінок, копії ідентичні")
    check_pytest_suites(report, strict=strict)


def check_classic_built_copy(report: CheckReport) -> None:
    frozen_site = CLASSIC_DIR / "site"
    published_site = DOCS_DIR / "classic"
    pairs = [
        (frozen_site / "index.html", published_site / "index.html"),
        (
            frozen_site / "downloads" / "python-cherez-obiekty.pdf",
            published_site / "downloads" / "python-cherez-obiekty.pdf",
        ),
    ]
    for source, target in pairs:
        if not source.exists() or not target.exists():
            report.errors.append(
                f"Класична копія для сайту відсутня: {target.relative_to(ROOT)}"
            )
            return
        if sha256(source) != sha256(target):
            report.errors.append(
                f"Класична копія не збігається з архівом: {target.relative_to(ROOT)}"
            )
            return
    report.passed.append("Класичне видання доступне у docs/classic і збігається з архівом")


def check_pytest_suites(report: CheckReport, *, strict: bool) -> None:
    python_path = (
        ROOT / ".venv" / "Scripts" / "python.exe"
        if os.name == "nt"
        else ROOT / ".venv" / "bin" / "python"
    )
    if not python_path.exists():
        message = "Dev-середовище pytest не знайдено; встанови requirements-dev.txt"
        if strict:
            report.errors.append(message)
        else:
            report.warnings.append(message)
        return

    suites = [
        (ROOT, [str(ROOT / "tests")], "тести збірки"),
        (
            ROOT / "examples" / "pytest_demo",
            [],
            "навчальний pytest-набір",
        ),
    ]
    for cwd, arguments, label in suites:
        command = [str(python_path), "-m", "pytest", "-q", *arguments]
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        if result.returncode != 0:
            details = (result.stdout + "\n" + result.stderr).strip()[-1000:]
            report.errors.append(f"{label}: pytest завершився з помилкою: {details}")
        else:
            summary = result.stdout.strip().splitlines()[-1]
            report.passed.append(f"{label}: {summary}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shutil_which(command: str) -> str | None:
    import shutil

    return shutil.which(command)


def write_report(report: CheckReport, *, strict: bool) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = report.as_dict()
    payload["mode"] = "strict" if strict else "draft"
    path = REPORTS_DIR / "verification.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


if __name__ == "__main__":
    strict = "--draft" not in sys.argv
    _, result = check_sources(strict=strict)
    if DOCS_DIR.exists():
        check_built_outputs(result, strict=strict)
    path = write_report(result, strict=strict)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    print(f"Звіт: {path}")
    raise SystemExit(0 if result.ok else 1)
