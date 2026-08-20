from pathlib import Path
import sys

from reportlab.lib.units import mm
from reportlab.platypus import CondPageBreak, KeepTogether, Paragraph

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from booklib import Block, Chapter
from build_pdf import blocks_to_flowables, make_styles, register_fonts


register_fonts()


def chapter() -> Chapter:
    return Chapter(
        source_path=Path("content/example.md"),
        slug="example",
        title="Example",
        order=1,
        blocks=[],
    )


def test_section_heading_reserves_room_for_following_content() -> None:
    flowables = blocks_to_flowables(
        [
            Block("heading", {"level": 2, "text": "Підсумок"}),
            Block("paragraph", {"text": "Перший рядок підсумку."}),
        ],
        make_styles(),
        chapter(),
    )

    assert isinstance(flowables[0], CondPageBreak)
    assert isinstance(flowables[1], KeepTogether)
    assert isinstance(flowables[1]._content[0], Paragraph)
    assert flowables[1]._content[0].getKeepWithNext()


def test_final_summary_stays_together_with_list_and_references() -> None:
    flowables = blocks_to_flowables(
        [
            Block("heading", {"level": 2, "text": "Підсумок"}),
            Block(
                "list",
                {
                    "ordered": False,
                    "items": ["Перший висновок.", "Другий висновок."],
                },
            ),
            Block("paragraph", {"text": "Офіційні орієнтири: Python."}),
        ],
        make_styles(),
        chapter(),
    )

    assert isinstance(flowables[0], CondPageBreak)
    assert isinstance(flowables[1], KeepTogether)
    assert len(flowables[1]._content) == 3


def test_lead_in_paragraph_stays_with_code_block() -> None:
    flowables = blocks_to_flowables(
        [
            Block("paragraph", {"text": "Запусти команду:"}),
            Block(
                "code",
                {
                    "language": "powershell",
                    "code": "python robot.py",
                    "attributes": {},
                },
            ),
        ],
        make_styles(),
        chapter(),
    )

    assert isinstance(flowables[0], Paragraph)
    assert flowables[0].keepWithNext


def test_complex_callout_header_stays_with_first_content_block() -> None:
    flowables = blocks_to_flowables(
        [
            Block(
                "directive",
                {
                    "directive": "practice",
                    "title": "Побач два об'єкти",
                    "blocks": [
                        Block("paragraph", {"text": "Додай ще одного робота."}),
                        Block(
                            "code",
                            {
                                "language": "python",
                                "code": "first_robot = Robot()",
                                "attributes": {},
                            },
                        ),
                    ],
                },
            )
        ],
        make_styles(),
        chapter(),
    )

    assert isinstance(flowables[0], KeepTogether)
    assert len(flowables[0]._content) == 3


def test_tasks_section_reserves_room_for_actual_tasks() -> None:
    flowables = blocks_to_flowables(
        [
            Block("heading", {"level": 2, "text": "Самостійна робота"}),
            Block("paragraph", {"text": "Виконуй завдання по одному."}),
            Block(
                "directive",
                {
                    "directive": "tasks",
                    "title": "",
                    "blocks": [
                        Block(
                            "list",
                            {"ordered": False, "items": ["Перше завдання", "Друге завдання"]},
                        )
                    ],
                },
            ),
        ],
        make_styles(),
        chapter(),
    )

    assert isinstance(flowables[0], CondPageBreak)
    assert flowables[0].height >= 110 * mm
    assert isinstance(flowables[1], Paragraph)
    assert flowables[1].keepWithNext is True
