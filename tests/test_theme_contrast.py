import re
from pathlib import Path

import pytest


CSS = (Path(__file__).resolve().parents[1] / "site" / "assets" / "styles.css").read_text(encoding="utf-8")


def variables(selector: str) -> dict[str, str]:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>.*?)\}}", CSS, re.DOTALL)
    assert match, f"CSS block not found: {selector}"
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})\s*;", match.group("body")))


def relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first: str, second: str) -> float:
    light, dark = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


@pytest.mark.parametrize("selector", [":root", 'html[data-theme="dark"]'])
def test_panel_text_pairs_meet_normal_text_contrast(selector: str) -> None:
    theme = variables(selector)
    pairs = [
        ("panel-ink", "panel"),
        ("panel-muted", "panel"),
        ("panel-accent", "panel"),
        ("panel-button-ink", "panel-button"),
        ("success-panel-ink", "success-panel"),
        ("success-panel-muted", "success-panel"),
        ("success-panel-accent", "success-panel"),
    ]

    failures = [
        f"{foreground}/{background}={contrast(theme[foreground], theme[background]):.2f}"
        for foreground, background in pairs
        if contrast(theme[foreground], theme[background]) < 4.5
    ]
    assert not failures, ", ".join(failures)
