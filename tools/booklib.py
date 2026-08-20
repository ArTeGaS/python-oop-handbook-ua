from __future__ import annotations

import hashlib
import html
import json
import re
import shlex
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(slots=True)
class Block:
    kind: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chapter:
    source_path: Path
    slug: str
    title: str
    order: int
    blocks: list[Block]

    @property
    def output_name(self) -> str:
        return f"{self.slug}.html"


DIRECTIVE_LABELS = {
    "goal": "Результат",
    "focus": "Зараз у фокусі",
    "predict": "Спочатку передбач",
    "note": "Важливо",
    "history": "Коротка історична пауза",
    "warning": "Обережно",
    "practice": "Спробуй зараз",
    "completion": "Доповни готовий приклад",
    "parsons": "Склади код у правильному порядку",
    "recall": "Згадай без підглядання",
    "check": "Швидка перевірка",
    "mistake": "Типова помилка",
    "os": "Різниця між системами",
    "answer": "Показати відповідь",
    "tasks": "Самостійна робота",
}


def load_metadata(root: Path) -> dict[str, Any]:
    return json.loads((root / "book.json").read_text(encoding="utf-8"))


def load_chapters(content_dir: Path) -> list[Chapter]:
    chapters = [parse_chapter(path) for path in sorted(content_dir.glob("*.md"))]
    if not chapters:
        raise ValueError(f"Не знайдено розділів у {content_dir}")
    return chapters


def parse_chapter(path: Path) -> Chapter:
    match = re.match(r"(?P<order>\d+)-(?P<slug>.+)\.md$", path.name)
    if not match:
        raise ValueError(f"Назва розділу має починатися з числа: {path.name}")
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks = parse_blocks(lines)
    title = next(
        (block.data["text"] for block in blocks if block.kind == "heading" and block.data["level"] == 1),
        None,
    )
    if not title:
        raise ValueError(f"У {path.name} немає заголовка першого рівня")
    return Chapter(
        source_path=path,
        slug=f"{int(match.group('order')):02d}-{match.group('slug')}",
        title=title,
        order=int(match.group("order")),
        blocks=blocks,
    )


def parse_blocks(lines: list[str]) -> list[Block]:
    blocks: list[Block] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if not stripped or stripped.startswith("<!--"):
            index += 1
            continue

        if stripped.startswith(":::"):
            header = stripped[3:].strip()
            if not header:
                raise ValueError("Зайвий маркер закриття :::")
            parts = header.split(maxsplit=1)
            directive = parts[0].lower()
            title = parts[1].strip() if len(parts) == 2 else ""
            body: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != ":::" :
                body.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError(f"Не закрито блок :::{directive}")
            if directive == "quiz":
                blocks.append(Block("quiz", parse_quiz(body)))
            elif directive == "trace":
                trace = parse_trace(body)
                trace["title"] = title or "Простеж стан крок за кроком"
                blocks.append(Block("trace", trace))
            else:
                blocks.append(
                    Block(
                        "directive",
                        {
                            "directive": directive,
                            "title": title,
                            "blocks": parse_blocks(body),
                        },
                    )
                )
            index += 1
            continue

        if stripped.startswith("```"):
            info = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index >= len(lines):
                raise ValueError("Не закрито блок коду")
            blocks.append(Block("code", parse_code_info(info, "\n".join(code_lines))))
            index += 1
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            blocks.append(
                Block(
                    "heading",
                    {"level": len(heading.group(1)), "text": heading.group(2).strip()},
                )
            )
            index += 1
            continue

        if stripped in {"---", "***"}:
            blocks.append(Block("rule"))
            index += 1
            continue

        image_match = re.match(r"^!\[(?P<alt>[^]]*)]\((?P<src>[^)]+)\)$", stripped)
        if image_match:
            blocks.append(Block("image", image_match.groupdict()))
            index += 1
            continue

        list_match = re.match(r"^(?P<indent>\s*)(?P<marker>-|\d+\.)\s+(?P<text>.+)$", raw)
        if list_match:
            ordered = list_match.group("marker") != "-"
            items: list[str] = []
            while index < len(lines):
                current = re.match(r"^\s*(?P<marker>-|\d+\.)\s+(?P<text>.+)$", lines[index])
                if not current or (current.group("marker") != "-") != ordered:
                    break
                items.append(current.group("text").strip())
                index += 1
            blocks.append(Block("list", {"ordered": ordered, "items": items}))
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index]
            candidate_stripped = candidate.strip()
            if not candidate_stripped:
                break
            if (
                candidate_stripped.startswith(("#", "```", ":::"))
                or candidate_stripped in {"---", "***"}
                or re.match(r"^\s*(-|\d+\.)\s+", candidate)
                or re.match(r"^!\[[^]]*]\([^)]+\)$", candidate_stripped)
            ):
                break
            paragraph_lines.append(candidate_stripped)
            index += 1
        blocks.append(Block("paragraph", {"text": " ".join(paragraph_lines)}))

    return blocks


def parse_code_info(info: str, code: str) -> dict[str, Any]:
    tokens = shlex.split(info) if info else []
    language = tokens[0].lower() if tokens else "text"
    flags: set[str] = set()
    attributes: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            attributes[key] = value
        else:
            flags.add(token)
    return {
        "language": language,
        "flags": flags,
        "attributes": attributes,
        "code": code,
    }


def parse_quiz(lines: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {"options": []}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        if not separator:
            raise ValueError(f"Невірний рядок quiz: {line}")
        key = key.lower().strip()
        value = value.strip()
        if key == "option":
            values["options"].append(value)
        elif key in {"question", "correct", "explanation"}:
            values[key] = value
        else:
            raise ValueError(f"Невідоме поле quiz: {key}")
    for required in ("question", "correct", "explanation"):
        if not values.get(required):
            raise ValueError(f"У quiz немає поля {required}")
    options = [values["correct"], *values["options"]]
    digest = int(hashlib.sha256(values["question"].encode("utf-8")).hexdigest()[:8], 16)
    shift = digest % len(options)
    options = options[shift:] + options[:shift]
    values["options"] = options
    values["correct_index"] = options.index(values["correct"])
    return values


def parse_trace(lines: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {"steps": []}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        if not separator:
            raise ValueError(f"Невірний рядок trace: {line}")
        key = key.lower().strip()
        value = value.strip()
        if key == "step":
            parts = [part.strip() for part in value.split("|", 2)]
            if len(parts) != 3 or not all(parts):
                raise ValueError(
                    "Крок trace має формат: step: Назва | `код` | пояснення"
                )
            values["steps"].append(
                {"label": parts[0], "code": parts[1], "meaning": parts[2]}
            )
        elif key in {"before", "after", "meaning"}:
            values[key] = value
        else:
            raise ValueError(f"Невідоме поле trace: {key}")
    for required in ("before", "after", "meaning"):
        if not values.get(required):
            raise ValueError(f"У trace немає поля {required}")
    if len(values["steps"]) < 2:
        raise ValueError("У trace має бути щонайменше два кроки")
    return values


def heading_id(text: str) -> str:
    transliteration = str.maketrans(
        {
            "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d",
            "е": "e", "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i",
            "ї": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
            "ь": "", "ю": "iu", "я": "ia", "’": "", "'": "",
        }
    )
    normalized = unicodedata.normalize("NFKD", text.lower()).translate(transliteration)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "section"


def render_inline_html(text: str) -> str:
    placeholders: dict[str, str] = {}

    def hold(rendered: str) -> str:
        token = f"INLINEPLACEHOLDER{len(placeholders)}TOKEN"
        placeholders[token] = rendered
        return token

    text = re.sub(
        r"`([^`]+)`",
        lambda match: hold(f"<code>{html.escape(match.group(1))}</code>"),
        text,
    )
    text = html.escape(text)
    text = re.sub(
        r"\[([^]]+)]\((https?://[^)]+)\)",
        lambda match: hold(
            f'<a href="{html.escape(match.group(2), quote=True)}" target="_blank" rel="noreferrer">'
            f"{match.group(1)}</a>"
        ),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    # A link label can contain an inline-code placeholder. Restore outer
    # placeholders first, then the nested earlier placeholders.
    for token, rendered in reversed(placeholders.items()):
        text = text.replace(token, rendered)
    return text


def render_inline_pdf(text: str) -> str:
    placeholders: dict[str, str] = {}

    def hold(rendered: str) -> str:
        token = f"PDFINLINEPLACEHOLDER{len(placeholders)}TOKEN"
        placeholders[token] = rendered
        return token

    text = re.sub(
        r"`([^`]+)`",
        lambda match: hold(f'<font name="BookCode">{_xml_escape(match.group(1))}</font>'),
        text,
    )
    text = re.sub(
        r"\[([^]]+)]\((https?://[^)]+)\)",
        lambda match: hold(
            f'<link href="{_xml_escape(match.group(2), attribute=True)}" color="#147d7a">'
            f"{_xml_escape(match.group(1))}</link>"
        ),
        text,
    )
    text = _xml_escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    # A link label can contain an inline-code placeholder. Restore outer
    # placeholders first, then the nested earlier placeholders.
    for token, rendered in reversed(placeholders.items()):
        text = text.replace(token, rendered)
    return text


def _xml_escape(value: str, *, attribute: bool = False) -> str:
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if attribute:
        value = value.replace('"', "&quot;")
    return value


def render_blocks_html(blocks: Iterable[Block], chapter_slug: str) -> str:
    heading_counts: dict[str, int] = {}
    task_index = 0
    def render_group(group: Iterable[Block]) -> str:
        nonlocal task_index
        rendered: list[str] = []
        for block in group:
            if block.kind == "heading":
                level = block.data["level"]
                text = block.data["text"]
                base_id = heading_id(text)
                heading_counts[base_id] = heading_counts.get(base_id, 0) + 1
                suffix = "" if heading_counts[base_id] == 1 else f"-{heading_counts[base_id]}"
                anchor = f"{base_id}{suffix}"
                rendered.append(
                    f'<h{level} id="{anchor}">{render_inline_html(text)}'
                    f'<a class="heading-link" href="#{anchor}" aria-label="Посилання на розділ">#</a>'
                    f"</h{level}>"
                )
            elif block.kind == "paragraph":
                rendered.append(f"<p>{render_inline_html(block.data['text'])}</p>")
            elif block.kind == "list":
                tag = "ol" if block.data["ordered"] else "ul"
                items = "".join(f"<li>{render_inline_html(item)}</li>" for item in block.data["items"])
                rendered.append(f"<{tag}>{items}</{tag}>")
            elif block.kind == "code":
                language = block.data["language"]
                attributes = block.data["attributes"]
                label = attributes.get("file") or ("Результат" if language == "output" else language)
                code = html.escape(block.data["code"])
                runnable = "true" if "run" in block.data["flags"] else "false"
                rendered.append(
                    '<div class="code-block">'
                    '<div class="code-toolbar">'
                    f'<span>{html.escape(label)}</span>'
                    '<button class="copy-code" type="button">Копіювати</button>'
                    '</div>'
                    f'<pre data-runnable="{runnable}"><code class="language-{html.escape(language)}">{code}</code></pre>'
                    '</div>'
                )
            elif block.kind == "rule":
                rendered.append("<hr>")
            elif block.kind == "image":
                rendered.append(
                    '<figure>'
                    f'<img src="{html.escape(block.data["src"], quote=True)}" '
                    f'alt="{html.escape(block.data["alt"], quote=True)}" loading="lazy">'
                    f'<figcaption>{html.escape(block.data["alt"])}</figcaption>'
                    '</figure>'
                )
            elif block.kind == "quiz":
                options = "".join(
                    f'<button type="button" class="quiz-option" data-index="{index}">'
                    f"{render_inline_html(option)}</button>"
                    for index, option in enumerate(block.data["options"])
                )
                rendered.append(
                    f'<section class="quiz" data-answer="{block.data["correct_index"]}">'
                    '<div class="callout-label">Перевір себе</div>'
                    f'<p class="quiz-question">{render_inline_html(block.data["question"])}</p>'
                    f'<div class="quiz-options">{options}</div>'
                    f'<p class="quiz-feedback" hidden>{render_inline_html(block.data["explanation"])}</p>'
                    '</section>'
                )
            elif block.kind == "trace":
                steps = "".join(
                    '<li class="trace-step">'
                    f'<span class="trace-step-number">{index}</span>'
                    '<div>'
                    f'<strong>{render_inline_html(step["label"])}</strong>'
                    f'<div class="trace-code">{render_inline_html(step["code"])}</div>'
                    f'<p>{render_inline_html(step["meaning"])}</p>'
                    '</div>'
                    '</li>'
                    for index, step in enumerate(block.data["steps"], 1)
                )
                rendered.append(
                    '<section class="state-trace">'
                    f'<div class="callout-label">{render_inline_html(block.data["title"])}</div>'
                    '<div class="trace-states">'
                    '<div class="trace-state trace-before"><span>До</span>'
                    f'<strong>{render_inline_html(block.data["before"])}</strong></div>'
                    '<div class="trace-state-arrow" aria-hidden="true">→</div>'
                    '<div class="trace-state trace-after"><span>Після</span>'
                    f'<strong>{render_inline_html(block.data["after"])}</strong></div>'
                    '</div>'
                    f'<ol class="trace-steps">{steps}</ol>'
                    f'<p class="trace-meaning"><strong>Що тут важливо:</strong> {render_inline_html(block.data["meaning"])}</p>'
                    '</section>'
                )
            elif block.kind == "directive":
                directive = block.data["directive"]
                title = block.data["title"] or DIRECTIVE_LABELS.get(directive, directive.capitalize())
                inner = render_group(block.data["blocks"])
                if directive == "answer":
                    rendered.append(
                        f'<details class="answer"><summary>{html.escape(title)}</summary><div>{inner}</div></details>'
                    )
                elif directive == "tasks":
                    def replace_task(match: re.Match[str]) -> str:
                        nonlocal task_index
                        task_index += 1
                        return _task_item_html(chapter_slug, task_index, match.group(1))

                    task_html = re.sub(r"<li>(.*?)</li>", replace_task, inner, flags=re.DOTALL)
                    rendered.append(
                        f'<section class="callout callout-tasks"><div class="callout-label">{html.escape(title)}</div>{task_html}</section>'
                    )
                else:
                    rendered.append(
                        f'<section class="callout callout-{html.escape(directive)}">'
                        f'<div class="callout-label">{html.escape(title)}</div>{inner}</section>'
                    )
        return "\n".join(rendered)

    return render_group(blocks)


def _task_item_html(chapter_slug: str, index: int, body: str) -> str:
    task_id = f"{chapter_slug}-task-{index}"
    return (
        '<li class="task-item">'
        f'<label><input class="task-check" type="checkbox" data-task-id="{task_id}">'
        f"<span>{body}</span></label></li>"
    )


def chapter_plain_text(chapter: Chapter) -> str:
    parts: list[str] = [chapter.title]

    def visit(blocks: Iterable[Block]) -> None:
        for block in blocks:
            if block.kind in {"heading", "paragraph"}:
                parts.append(block.data["text"])
            elif block.kind == "list":
                parts.extend(block.data["items"])
            elif block.kind == "code":
                parts.append(block.data["code"])
            elif block.kind == "quiz":
                parts.extend([block.data["question"], block.data["explanation"]])
            elif block.kind == "trace":
                parts.extend(
                    [
                        block.data["title"],
                        block.data["before"],
                        *(
                            text
                            for step in block.data["steps"]
                            for text in (step["label"], step["code"], step["meaning"])
                        ),
                        block.data["after"],
                        block.data["meaning"],
                    ]
                )
            elif block.kind == "directive":
                if block.data["title"]:
                    parts.append(block.data["title"])
                visit(block.data["blocks"])

    visit(chapter.blocks)
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def iter_blocks(blocks: Iterable[Block]) -> Iterable[Block]:
    for block in blocks:
        yield block
        if block.kind == "directive":
            yield from iter_blocks(block.data["blocks"])
