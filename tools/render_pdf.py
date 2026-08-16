from __future__ import annotations

import argparse
from pathlib import Path

import pypdfium2 as pdfium


ROOT = Path(__file__).resolve().parents[1]


def render_pdf(pdf_path: Path, output_dir: Path, pages: list[int] | None, scale: float) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(pdf_path))
    page_numbers = pages if pages is not None else list(range(1, len(document) + 1))
    outputs: list[Path] = []
    for page_number in page_numbers:
        if page_number < 1 or page_number > len(document):
            raise ValueError(f"Сторінки {page_number} немає у PDF з {len(document)} сторінок")
        page = document[page_number - 1]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        output = output_dir / f"page-{page_number:03d}.png"
        image.save(output)
        outputs.append(output)
        page.close()
    document.close()
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Render PDF pages to PNG for visual QA")
    parser.add_argument(
        "pdf",
        nargs="?",
        type=Path,
        default=ROOT / "output" / "pdf" / "python-cherez-obiekty.pdf",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "tmp" / "pdfs" / "rendered")
    parser.add_argument("--pages", help="Comma-separated one-based page numbers")
    parser.add_argument("--scale", type=float, default=1.8)
    args = parser.parse_args()
    pages = [int(value) for value in args.pages.split(",")] if args.pages else None
    outputs = render_pdf(args.pdf.resolve(), args.output.resolve(), pages, args.scale)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
