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

FORBIDDEN_SOURCE_REFERENCES = (
    "matthes",
    "метьюз",
    "метьюза",
    "мєтьюз",
    "ерік мат",
    "eric mat",
)


@dataclass
class CheckReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)
    runnable_blocks: int = 0
    expected_error_blocks: int = 0
    python_blocks: int = 0
    pages: int = 0

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
    if not report.errors:
        report.passed.append("Структура й кодові блоки джерел перевірені")
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
