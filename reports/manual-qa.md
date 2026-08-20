# First Official Edition - Final QA and Release Report

Date: 2026-08-20
Scope: the published Ukrainian OOP-first handbook, its optional frozen Classic Edition, the generated PDFs, the local site, and the live GitHub Pages deployment.

## Release identity

- Repository: `https://github.com/ArTeGaS/python-oop-handbook-ua`
- Public site: `https://artegas.github.io/python-oop-handbook-ua/`
- Pages source: `main:/docs`, HTTPS enforced.
- Official-edition commit: `3edc6a2` (`Підготовлено перше офіційне видання`).
- PDF pagination commit: `c19902b` (`Збалансовано завершення розділів у PDF`).
- The live Pages deployment was verified as built from exact commit `c19902b727d23e8c467fe6eadc76654c8f49b1f0` before this report-only update.
- This report changes no file under `docs/`. A fresh exact-HEAD Pages check is performed after the report commit; GitHub's deployment record is the non-self-referential source of truth for that commit.

## Reference and editorial boundary

- The subject map follows the third-edition pre-project learning scope and its companion material, but the handbook text, examples, object model, exercises, explanations, and chapter structure are original Ukrainian work.
- No page-number references to the source book are used.
- The game, web, and data-project half is intentionally excluded.
- The former edition is preserved as an optional, visibly labelled Classic Edition instead of being silently overwritten.
- `editorial/edition-1-system.md` is the consistency contract for chapter rhythm, attention, traces, fading, media choice, error progression, and history placement.

## Automated build gate

- Command: `.\.venv\Scripts\python.exe tools\build.py`
- Result: pass with zero reported errors and zero warnings.
- Sources: 18 chapters, 357 Python code blocks, 133 runnable examples, and 19 intentional error examples.
- Tests: 19 build tests passed; 7 educational pytest tests passed.
- Official PDF: 225 pages.
- Classic PDF: 204 pages.
- Official PDF SHA-256: `49851B0DEAA529E1A963623116E55AC8ADF26DA1AB19AA88A1AC113CB0F9B8B8`.
- Classic PDF SHA-256: `5A52E53BDB734489BA25C6A045E9BA5193C095191425ED33C0309B9ABBE29CB7`.
- Each output PDF and its `docs/downloads/` copy are byte-identical.
- Detailed machine-readable evidence: `reports/verification.json`.

## Attention gate

Attention was treated as an independent acceptance criterion, not as a screenshot count.

- Longest paragraph: 54 words (limit 70).
- Longest passive stretch between learner actions: 383 words (limit 450).
- Minimum active prompts in a main chapter: 9 (minimum 7).
- Minimum re-entry headings in a main chapter: 15 (minimum 12).
- Long code blocks: 2; both contain at least 3 navigation comments.
- Every main chapter includes prediction, running, an integrated trace, completion or Parsons reconstruction, retrieval, a quiz, and independent transfer work.
- Every main chapter places its short history pause after useful practice.

## Full offline PDF review

- Freshly rendered all 225 pages to images under `tmp/pdfs/final-offline-full-2026-08-20`.
- Reviewed all pages visually in 15 contact sheets, then rechecked suspect pages individually.
- A real pagination defect was found during the second-from-start review: final `Підсумок` sections could split into sparse tails on pages 139, 152, and 165.
- The renderer now groups each final summary section with `KeepTogether`; a dedicated pagination regression test was added. The three pages now contain complete summary sections.
- No clipping, overlap, broken glyph, black box, corrupt figure, unintended blank page, or horizontally overflowing content was found.
- Programmatic audit confirmed one A4 page size, 225 nonblank pages, all 18 chapter titles, required `.py`/VS Code/parameter/argument/platform/independent-work phrases, no placeholder markers, and 9,757 Ukrainian-specific letters.
- The lowest-text pages were manually reviewed; their whitespace is intentional cover, transition, or complete-section spacing rather than missing content.

## Full local-site review

- Crawled 40 HTML pages: 18 main chapters, 18 Classic chapters, and supporting pages.
- Checked 47 unique local URLs, 1,954 references, and 880 anchors; errors: none.
- Rendered all 36 main/Classic chapter pages at desktop and mobile widths; failures: none.
- Verified the required semantic learning blocks in chapters 01-17.
- Manually verified search, chapter navigation, Classic navigation, correct and incorrect quiz feedback, code copy, task persistence after reload, theme persistence, mobile menu, the real VS Code figure, and the custom 404 page.
- The local QA server was stopped and its port was confirmed closed.

## Full live-site and online-PDF review

- Repeated the 40-page crawl against the public Pages URL with the same 47 URLs, 1,954 references, and 880 anchor checks; errors: none.
- Compared all 53 published files with verified local `docs/`: every file matched. Text comparison normalized CRLF/LF only; PDFs and PNGs matched byte-for-byte.
- Rendered all 36 live chapter pages at desktop and mobile widths; failures and semantic-block failures: none.
- Repeated live search and navigation, mobile menu, code copy and clipboard content, wrong-answer feedback, task persistence, theme persistence, and the custom 404 flow.
- Verified the missing-page response as HTTP 404 with the expected Ukrainian title.
- Opened the public official PDF in the browser viewer: title `Python через об'єкти`, page count 225, and cover rendering were correct.
- Direct page-number automation in the browser's native PDF viewer was unreliable. This is covered by the complete offline 225-page render plus the exact byte hash of the live PDF; it is not treated as a product failure.

## Manual learner workflow through VS Code and Computer Use

- Opened the exact `PythonCours` project folder in the installed VS Code application through the normal **File -> Open Folder** dialog.
- Opened `examples/pytest_demo/chapter01_manual_robot.py` and ran it using the visible **Run Python File** control, not by entering a shell command.
- VS Code selected the project `.venv` (`Python 3.12.13`) and printed the expected visible result: `Привіт! Я Робі.`
- Opened `content/03-metody-parametry-i-povernennia.md` through Quick Open and inspected it in Markdown Preview.
- Visually confirmed the OOP context, the separate method-definition parameter and call-site argument, runnable code, independent tasks, the history pause after practice, and the complete final summary.
- The single Problems marker belongs to the intentional `robot_missing_colon.py` error demonstration and is not a defect in the runnable example or published artifact.

## Screenshot and platform policy

- One real Windows VS Code screenshot is used where interface location is the learning target: the shared **Run Python File** control.
- Screenshots are not used for syntax, state flow, terminal commands, or text that learners may need to copy.
- No macOS or Linux screenshot was fabricated. Windows, macOS, and Linux differences are shown explicitly with platform-labelled commands and paths.
- The image has Ukrainian alternative text, a visible caption, natural size 1135 x 290, and no overflow at desktop or 390 x 844 mobile width.
- Evidence captures: `reports/visual-qa/site-ch01-vscode-desktop.png` and `reports/visual-qa/site-ch01-vscode-mobile.png`.

## Objective completion matrix

| Requirement | Final evidence | Status |
| --- | --- | --- |
| Original Ukrainian text with no Matthes page references | Original OOP-first sources; source page numbers are not used | Proven |
| Preserve the former version | 18 frozen Classic sources, 204-page Classic PDF, and matching `docs/classic/` site | Proven |
| Teach pre-project Python through OOP from the beginning | Chapter 1 creates `Robot` and an object before the language surface expands | Proven |
| Exclude editor-installation and project-half walkthroughs | The handbook starts from an opened VS Code folder and ends at testing, debugging, style, and syntax map | Proven |
| Explain `.py`, editor/terminal launch, and platform differences | Chapter 1 treats `.py` as text and separates Windows, macOS, and Linux commands; later path chapters continue the distinction | Proven |
| Distinguish parameter and argument | Chapter 3 separates definition/call sites and includes a four-stage binding/state trace | Proven |
| Interleave theory and practice | Prediction-run-trace-fade-retrieve-transfer rhythm is enforced in every main chapter | Proven |
| Use realistic error progression | 19 executed intentional-error blocks plus a Typical Error section in every main chapter | Proven |
| Treat attention independently | Source metrics, 225-page visual review, desktop/mobile review, and re-entry structure all pass | Proven |
| Choose screenshots by learning value | One focused real VS Code screenshot; code and platform differences remain selectable text | Proven |
| Keep site and PDF synchronized | One `content/` source, matching live/local files, and identical PDF hashes | Proven |
| Publish through the `ArTeGaS` account | Correct authenticated owner, public repository, Pages source, live URLs, and exact deployment commit verified | Proven |

## Final release state

- Active GitHub account during publication: `ArTeGaS`; `ArTeGaS-2` remained inactive.
- Upstream divergence before this report-only commit: `0 0`.
- The only remaining worktree entry is the pre-existing untracked prototype `output/pdf/prototyp-formatu-do-pislia.pdf`; it was excluded from every commit and left untouched.
- No known defect remains in the published site or either published PDF.
