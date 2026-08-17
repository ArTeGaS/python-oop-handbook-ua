from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from booklib import Block, Chapter
from check_content import CheckReport, check_error_evidence, run_error_block


def chapter() -> Chapter:
    return Chapter(Path("content/example.md"), "example", "Example", 1, [])


def error_block(*, raises: str = "ValueError") -> Block:
    return Block(
        "code",
        {
            "language": "python",
            "code": "raise ValueError('boom')",
            "flags": {"error"},
            "attributes": {"raises": raises},
        },
    )


def output_block() -> Block:
    return Block(
        "code",
        {
            "language": "output",
            "code": "ValueError: boom",
            "flags": set(),
            "attributes": {},
        },
    )


def test_expected_error_is_executed_and_matches_type() -> None:
    report = CheckReport()

    run_error_block(chapter(), 1, error_block(), report)

    assert report.errors == []


def test_error_block_requires_visible_output_nearby() -> None:
    report = CheckReport()

    check_error_evidence([error_block()], chapter(), report)

    assert report.errors


def test_error_block_accepts_formatted_output() -> None:
    report = CheckReport()

    check_error_evidence([error_block(), output_block()], chapter(), report)

    assert report.errors == []
