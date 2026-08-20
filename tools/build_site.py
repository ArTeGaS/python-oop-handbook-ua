from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from booklib import Chapter, chapter_plain_text, load_chapters, load_metadata, render_blocks_html


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
SITE_SOURCE = ROOT / "site"
DOCS_DIR = ROOT / "docs"


def build_site() -> list[Chapter]:
    metadata = load_metadata(ROOT)
    chapters = load_chapters(CONTENT_DIR)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    assets_target = DOCS_DIR / "assets"
    shutil.copytree(SITE_SOURCE / "assets", assets_target, dirs_exist_ok=True)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")
    asset_version = build_asset_version()

    sidebar = render_sidebar(chapters, metadata)
    (DOCS_DIR / "index.html").write_text(
        render_page(
            metadata=metadata,
            page_title=metadata["title"],
            description=metadata["description"],
            sidebar=sidebar,
            body=render_home(chapters, metadata),
            active_slug="home",
            body_class="home-page",
            asset_version=asset_version,
        ),
        encoding="utf-8",
    )

    for index, chapter in enumerate(chapters):
        previous_chapter = chapters[index - 1] if index > 0 else None
        next_chapter = chapters[index + 1] if index + 1 < len(chapters) else None
        body = render_chapter(chapter, previous_chapter, next_chapter)
        (DOCS_DIR / chapter.output_name).write_text(
            render_page(
                metadata=metadata,
                page_title=f"{chapter.title} — {metadata['title']}",
                description=chapter_plain_text(chapter)[:190],
                sidebar=sidebar,
                body=body,
                active_slug=chapter.slug,
                body_class="chapter-page",
                asset_version=asset_version,
            ),
            encoding="utf-8",
        )

    search_index = [
        {
            "slug": chapter.slug,
            "title": chapter.title,
            "url": chapter.output_name,
            "text": chapter_plain_text(chapter),
        }
        for chapter in chapters
    ]
    (DOCS_DIR / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DOCS_DIR / "404.html").write_text(
        render_page(
            metadata=metadata,
            page_title=f"Сторінку не знайдено — {metadata['title']}",
            description="Сторінку не знайдено.",
            sidebar=sidebar,
            body=(
                '<section class="empty-state"><p class="eyebrow">Помилка 404</p>'
                '<h1>Такої сторінки немає</h1>'
                '<p>Повернися до змісту або знайди потрібну тему через пошук.</p>'
                '<a class="button primary" href="index.html">До змісту</a></section>'
            ),
            active_slug="",
            body_class="error-page",
            asset_version=asset_version,
        ),
        encoding="utf-8",
    )
    (DOCS_DIR / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n",
        encoding="utf-8",
    )
    return chapters


def build_asset_version() -> str:
    digest = hashlib.sha256()
    for path in sorted((SITE_SOURCE / "assets").glob("*")):
        if path.is_file():
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def render_page(
    *,
    metadata: dict,
    page_title: str,
    description: str,
    sidebar: str,
    body: str,
    active_slug: str,
    body_class: str,
    asset_version: str,
) -> str:
    return f"""<!doctype html>
<html lang="uk" data-active-chapter="{active_slug}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape_attr(description)}">
  <meta name="theme-color" content="#f4f0e8">
  <title>{escape_text(page_title)}</title>
  <link rel="stylesheet" href="assets/styles.css?v={asset_version}">
  <script src="assets/app.js?v={asset_version}" defer></script>
</head>
<body class="{body_class}">
  <a class="skip-link" href="#main-content">До основного тексту</a>
  <header class="mobile-header">
    <button class="icon-button menu-button" type="button" aria-label="Відкрити зміст" aria-expanded="false">Зміст</button>
    <a class="mobile-brand" href="index.html">{escape_text(metadata['title'])}</a>
    <button class="icon-button theme-toggle" type="button" aria-label="Змінити тему">Тема</button>
  </header>
  <div class="app-shell">
{sidebar}
    <main id="main-content" class="main-content" tabindex="-1">
{body}
      <footer class="site-footer">
        <p>{escape_text(metadata['title'])} · українська практична довідка · {escape_text(metadata['edition'])}</p>
        <div class="footer-links">
          <a href="{escape_attr(metadata.get('classic_url', 'classic/index.html'))}">Класичне видання</a>
          <a href="{escape_attr(metadata['repository_url'])}">Відкрити репозиторій</a>
        </div>
      </footer>
    </main>
  </div>
  <div class="search-panel" hidden aria-live="polite">
    <div class="search-panel-inner">
      <button class="search-close" type="button" aria-label="Закрити пошук">×</button>
      <p class="eyebrow">Пошук у довідці</p>
      <div id="search-results" class="search-results"></div>
    </div>
  </div>
</body>
</html>
"""


def render_sidebar(chapters: list[Chapter], metadata: dict) -> str:
    links = []
    for chapter in chapters:
        number = "Початок" if chapter.order == 0 else f"{chapter.order:02d}"
        links.append(
            f'<a class="chapter-link" data-slug="{chapter.slug}" href="{chapter.output_name}">'
            f'<span class="chapter-number">{number}</span>'
            f'<span>{escape_text(chapter.title)}</span>'
            '<span class="chapter-check" aria-hidden="true">✓</span>'
            '</a>'
        )
    return f"""
<aside class="sidebar" aria-label="Зміст">
  <div class="sidebar-top">
    <a class="brand" data-slug="home" href="index.html">
      <span class="brand-mark">Py</span>
      <span><strong>{escape_text(metadata['title'])}</strong><small>{escape_text(metadata['subtitle'])}</small></span>
    </a>
    <button class="icon-button sidebar-close" type="button" aria-label="Закрити зміст">×</button>
    <button class="theme-toggle desktop-theme" type="button">Змінити тему</button>
  </div>
  <label class="search-box">
    <span class="visually-hidden">Пошук</span>
    <input id="chapter-search" type="search" placeholder="Знайти тему…" autocomplete="off">
    <kbd>Ctrl K</kbd>
  </label>
  <div class="progress-card">
    <div><span>Прогрес</span><strong id="progress-label">0 з {len(chapters)}</strong></div>
    <div class="progress-track"><span id="progress-bar"></span></div>
  </div>
  <nav class="chapter-nav">{''.join(links)}</nav>
  <div class="sidebar-actions">
    <a class="button secondary full" href="downloads/{escape_attr(metadata['pdf_filename'])}">Завантажити PDF</a>
    <a class="edition-link" href="{escape_attr(metadata.get('classic_url', 'classic/index.html'))}">Відкрити класичне видання</a>
  </div>
</aside>
"""


def render_home(chapters: list[Chapter], metadata: dict) -> str:
    first = chapters[0]
    cards = []
    for chapter in chapters:
        label = "Вступ" if chapter.order == 0 else f"Розділ {chapter.order:02d}"
        cards.append(
            f'<a class="chapter-card" href="{chapter.output_name}" data-chapter-card="{chapter.slug}">'
            f'<span class="card-label">{label}</span>'
            f'<h2>{escape_text(chapter.title)}</h2>'
            '<span class="card-action">Відкрити <span aria-hidden="true">→</span></span>'
            '</a>'
        )
    return f"""
<section class="hero">
  <div class="hero-copy">
    <p class="eyebrow">Перше офіційне видання · українська практична довідка</p>
    <h1>Python, у якому дані <em>щось означають</em>, а об’єкти <em>щось роблять</em></h1>
    <p class="hero-lead">Від першого <code>.py</code>-файла до збереження даних і тестів. Кожна нова конструкція одразу стає поведінкою маленької програми.</p>
    <div class="hero-actions">
      <a class="button primary" href="{first.output_name}">Почати читати</a>
      <a class="button secondary" href="downloads/{escape_attr(metadata['pdf_filename'])}">PDF-книга</a>
      <a class="button quiet" href="{escape_attr(metadata.get('classic_url', 'classic/index.html'))}">Класичне видання</a>
    </div>
  </div>
  <div class="hero-code" aria-label="Приклад Python-коду">
    <div class="window-bar"><span></span><span></span><span></span><small>robot.py</small></div>
    <pre><code><span class="token-keyword">class</span> <span class="token-class">Robot</span>:
    <span class="token-keyword">def</span> <span class="token-function">say_hello</span>(self):
        print(<span class="token-string">"Привіт! Я вже працюю."</span>)

robot = Robot()
robot.say_hello()</code></pre>
    <div class="terminal-line"><span>›</span> Привіт! Я вже працюю.</div>
  </div>
</section>

<section class="home-section principles">
  <p class="eyebrow">Як тут навчаємось</p>
  <div class="principle-grid">
    <article><span>01</span><h2>Передбач до запуску</h2><p>Спочатку сформулюй очікування, потім порівняй його з реальною поведінкою.</p></article>
    <article><span>02</span><h2>Простеж зміну</h2><p>Стан «до», точні кроки коду і стан «після» показані в одному місці.</p></article>
    <article><span>03</span><h2>Підказки зникають поступово</h2><p>Від готового прикладу переходь через доповнення й зміну до власної програми.</p></article>
    <article><span>04</span><h2>Згадай і перенеси</h2><p>Коротко відтвори правило без підглядання та застосуй його до іншого об’єкта.</p></article>
  </div>
</section>

<section class="home-section">
  <div class="section-heading">
    <div><p class="eyebrow">Повний маршрут</p><h2>Зміст довідки</h2></div>
    <p>{len(chapters) - 1} основних розділів, вступ і наскрізні швидкі перевірки.</p>
  </div>
  <div class="chapter-grid">{''.join(cards)}</div>
</section>

<section class="home-section coverage">
  <div class="coverage-copy">
    <p class="eyebrow">Не прив’язано до одного проєкту</p>
    <h2>Знання, які можна перенести у власну програму</h2>
    <p>Приклади змінюють контекст: робот, герой, інвентар, нотатник, сховище, генератор і тестована модель. Так синтаксис не зливається з однією грою чи одним сюжетом.</p>
  </div>
  <ul class="coverage-list">
    <li><strong>Мова</strong><span>типи, умови, колекції, цикли, функції</span></li>
    <li><strong>ООП</strong><span>класи, стан, поведінка, композиція, успадкування</span></li>
    <li><strong>Надійність</strong><span>traceback, винятки, файли, JSON, тести</span></li>
    <li><strong>Практика</strong><span>VS Code, термінал, модулі, структура папок</span></li>
  </ul>
</section>
"""


def render_chapter(
    chapter: Chapter,
    previous_chapter: Chapter | None,
    next_chapter: Chapter | None,
) -> str:
    label = "Вступ" if chapter.order == 0 else f"Розділ {chapter.order:02d}"
    previous_link = (
        f'<a class="chapter-pager-link previous" href="{previous_chapter.output_name}">'
        f'<span>← Назад</span><strong>{escape_text(previous_chapter.title)}</strong></a>'
        if previous_chapter
        else '<span></span>'
    )
    next_link = (
        f'<a class="chapter-pager-link next" href="{next_chapter.output_name}">'
        f'<span>Далі →</span><strong>{escape_text(next_chapter.title)}</strong></a>'
        if next_chapter
        else '<a class="chapter-pager-link next" href="index.html"><span>До змісту →</span><strong>Усі теми</strong></a>'
    )
    content = render_blocks_html(chapter.blocks, chapter.slug)
    return f"""
<article class="chapter-article" data-chapter="{chapter.slug}">
  <header class="chapter-header">
    <p class="eyebrow">{label}</p>
    <p class="chapter-reading-note">Передбач · запускай · простеж · змінюй · створи</p>
  </header>
  <div class="chapter-body">{content}</div>
  <section class="completion-card">
    <div><p class="eyebrow">Твій прогрес</p><h2>Розділ опрацьовано?</h2><p>Позначай після запуску, пояснення без підглядання й самостійної зміни.</p></div>
    <button class="button primary complete-chapter" type="button" data-chapter-id="{chapter.slug}">Позначити завершеним</button>
  </section>
  <nav class="chapter-pager" aria-label="Сусідні розділи">{previous_link}{next_link}</nav>
</article>
"""


def escape_text(value: str) -> str:
    import html

    return html.escape(str(value))


def escape_attr(value: str) -> str:
    import html

    return html.escape(str(value), quote=True)


if __name__ == "__main__":
    built = build_site()
    print(f"Сайт зібрано: {len(built)} розділів -> {DOCS_DIR}")
