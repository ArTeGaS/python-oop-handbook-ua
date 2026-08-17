from pathlib import Path
import sys


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from build_site import build_asset_version, render_page


def test_render_page_versions_css_and_javascript() -> None:
    html = render_page(
        metadata={"title": "Test", "edition": "2026", "repository_url": "https://example.com"},
        page_title="Test",
        description="Test",
        sidebar="",
        body="",
        active_slug="home",
        body_class="home-page",
        asset_version="abc123",
    )

    assert 'href="assets/styles.css?v=abc123"' in html
    assert 'src="assets/app.js?v=abc123"' in html


def test_asset_version_is_stable_and_content_derived() -> None:
    version = build_asset_version()

    assert len(version) == 12
    assert version == build_asset_version()
    assert all(character in "0123456789abcdef" for character in version)
