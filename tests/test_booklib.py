from tools.booklib import parse_blocks, render_blocks_html, render_inline_html, render_inline_pdf


def test_html_restores_inline_code_inside_link() -> None:
    rendered = render_inline_html("[`logging`](https://docs.python.org/3/library/logging.html)")

    assert "INLINEPLACEHOLDER" not in rendered
    assert "<code>logging</code>" in rendered
    assert rendered.startswith('<a href="https://docs.python.org/3/library/logging.html"')


def test_pdf_restores_inline_code_inside_link() -> None:
    rendered = render_inline_pdf("[`logging`](https://docs.python.org/3/library/logging.html)")

    assert "PDFINLINEPLACEHOLDER" not in rendered
    assert '<font name="BookCode">logging</font>' in rendered
    assert rendered.startswith('<link href="https://docs.python.org/3/library/logging.html"')


def test_trace_parses_required_states_and_steps() -> None:
    blocks = parse_blocks(
        [
            ":::trace Лікування героя",
            "before: `self.health = 70`",
            "step: Виклик | `hero.heal(15)` | `15` є аргументом.",
            "step: Зіставлення | `amount = 15` | `amount` є параметром.",
            "after: `self.health = 85`",
            "meaning: Аргумент передає значення параметру.",
            ":::",
        ]
    )

    assert len(blocks) == 1
    assert blocks[0].kind == "trace"
    assert blocks[0].data["title"] == "Лікування героя"
    assert len(blocks[0].data["steps"]) == 2


def test_trace_renders_integrated_html_structure() -> None:
    blocks = parse_blocks(
        [
            ":::trace Лікування героя",
            "before: `self.health = 70`",
            "step: Виклик | `hero.heal(15)` | `15` є аргументом.",
            "step: Зіставлення | `amount = 15` | `amount` є параметром.",
            "after: `self.health = 85`",
            "meaning: Аргумент передає значення параметру.",
            ":::",
        ]
    )

    rendered = render_blocks_html(blocks, "03-metody")

    assert 'class="state-trace"' in rendered
    assert "trace-before" in rendered
    assert '<code>hero.heal(15)</code>' in rendered
    assert "trace-after" in rendered
