from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from booklib import Block, Chapter
from check_content import (
    ATTENTION_LIMITS,
    CheckReport,
    attention_payload,
    check_attention,
)


def intro_chapter() -> Chapter:
    return Chapter(
        source_path=Path("00-intro.md"),
        slug="00-intro",
        title="Вступ",
        order=0,
        blocks=[],
    )


def test_attention_payload_records_a_compact_fragment() -> None:
    report = CheckReport()
    blocks = [
        Block("paragraph", {"text": "Коротке пояснення."}),
        Block(
            "directive",
            {"directive": "practice", "title": "Дія", "blocks": []},
        ),
    ]

    check_attention(intro_chapter(), blocks, report, strict=True)

    payload = attention_payload(report.attention_chapters)
    assert report.errors == []
    assert payload["status"] == "pass"
    assert payload["book"]["chapters_audited"] == 1


def test_attention_rejects_a_long_passive_stretch() -> None:
    report = CheckReport()
    too_many_words = " ".join(
        "слово"
        for _ in range(
            ATTENTION_LIMITS["max_passive_words_between_actions"] + 1
        )
    )

    check_attention(
        intro_chapter(),
        [Block("paragraph", {"text": too_many_words})],
        report,
        strict=True,
    )

    assert any("пасивний відрізок" in error for error in report.errors)
    assert report.attention_chapters[0]["passed"] is False


def test_long_code_needs_numbered_navigation_comments() -> None:
    report = CheckReport()
    long_code = "\n".join(
        ["# 1. Модель", "# 2. Керування", "# 3. Запуск"]
        + ["value = 1"]
        * (ATTENTION_LIMITS["long_code_soft_limit_lines"] - 2)
    )
    block = Block(
        "code",
        {
            "language": "python",
            "flags": {"run"},
            "attributes": {},
            "code": long_code,
        },
    )

    check_attention(intro_chapter(), [block], report, strict=True)

    assert report.errors == []
    assert report.attention_chapters[0]["long_code_blocks"] == 1
    assert report.attention_chapters[0]["long_code_blocks_with_navigation"] == 1
