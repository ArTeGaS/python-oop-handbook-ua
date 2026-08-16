from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_pdf import build_pdf
from build_site import build_site
from check_content import check_built_outputs, check_sources, write_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the website and PDF from shared Ukrainian content")
    parser.add_argument("--draft", action="store_true", help="Allow missing planned chapters during authoring")
    parser.add_argument("--skip-pdf", action="store_true", help="Build only the static website")
    args = parser.parse_args()
    strict = not args.draft

    _, report = check_sources(strict=strict)
    if report.errors:
        report_path = write_report(report, strict=strict)
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        print(f"Звіт: {report_path}")
        raise SystemExit(1)

    chapters = build_site()
    print(f"Сайт: {len(chapters)} розділів")
    if not args.skip_pdf:
        pdf_path = build_pdf()
        print(f"PDF: {pdf_path}")

    check_built_outputs(report, strict=strict and not args.skip_pdf)
    report_path = write_report(report, strict=strict)
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    print(f"Звіт: {report_path}")
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
