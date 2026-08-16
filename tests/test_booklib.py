from tools.booklib import render_inline_html, render_inline_pdf


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
