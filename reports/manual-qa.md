# First Official Edition — Manual QA

Date: 2026-08-17
Scope: local first-official-edition site and PDF; no commit, push, or public deployment.

## Automated gate

- Command: `.\.venv\Scripts\python.exe tools\build.py`
- Result: pass, with zero reported errors and zero warnings.
- Sources: 18 chapters, 357 Python code blocks, 133 runnable examples, 19 intentional error examples.
- Tests: 18 build tests passed; 7 educational pytest tests passed.
- PDF: 225 pages; the output PDF and the site download copy are byte-identical.
- Detailed machine-readable evidence: `reports/verification.json`.

## Attention gate

Attention was treated as an independent success criterion, not as a screenshot count.

- Longest paragraph: 54 words (limit 70).
- Longest passive stretch between actions: 383 words (limit 450).
- Minimum active prompts in a main chapter: 9 (minimum 7).
- Minimum re-entry headings in a main chapter: 15 (minimum 12).
- Long code blocks: 2; both contain at least 3 navigation comments.
- Every main chapter includes prediction, tracing, completion/faded guidance, Parsons reconstruction, and retrieval prompts.

## PDF visual review

- Rendered and visually reviewed all 225 pages in eight contact sheets.
- Re-rendered selected pages at larger size after pagination fixes: chapter 1 pages 17–25, chapter 3 pages 36–38, chapter 10 pages 119–122, pytest pages 192–193, and ending pages 224–225.
- Verified that prediction prompts remain with the first meaningful code segment, complex directive headers remain with their content, and figures remain with captions.
- No blank, corrupt, clipped, or horizontally overflowing page was found.
- Intentional whitespace remains on a few ending/transition pages (notably pages 17 and 225) where preserving a complete visual or chapter boundary is clearer than filling the page.

## Site user-flow review

Previously completed user-style checks were repeated or preserved after the final rebuild:

- Home page, chapter navigation, classic-edition link, search navigation, code copy, quiz interaction, task persistence, chapter-progress persistence, light/dark theme, desktop layout, and 390 x 844 mobile layout.
- The chapter 1 VS Code figure loads from the built site at its natural size of 1135 x 290, has Ukrainian alternative text and a visible caption, and creates no horizontal overflow at 1280 x 720 or 390 x 844.
- Mobile rendered image width: approximately 339 px within the available content width.
- Browser console after the final chapter 1 check: no messages.
- Evidence captures: `reports/visual-qa/site-ch01-vscode-desktop.png` and `reports/visual-qa/site-ch01-vscode-mobile.png`.

## Screenshot and platform policy

- The VS Code screenshot was captured from the real Windows application through manual GUI interaction, then cropped to one focused learning target: the shared **Run Python File** control.
- Screenshots are used only when interface location or visual state is itself the learning target. Ordinary code, output, state changes, and platform commands remain selectable code or text.
- No macOS or Linux screenshot was fabricated. Their differences are stated in text/code, with Windows, macOS, and Linux commands separated where relevant.
- The original VS Code project window was restored after the clean capture window was closed.

## Objective completion matrix

| Requirement | Current-state evidence | Local status |
| --- | --- | --- |
| Keep the former version as an optional Classic Edition | `editions/classic/` contains 18 frozen sources and its 204-page PDF; `docs/classic/` matches the frozen copy | Proven |
| First official edition is OOP-first | Chapter 1 creates `Robot` and an object before expanding the rest of Python; `book.json` identifies edition `official-1` | Proven |
| Cover the pre-project learning scope only | The 18-source book ends with testing, debugging, style, and the syntax map; no game/web/data project half is included | Proven |
| Do not add editor-installation walkthroughs | Chapter 1 explicitly starts from an already opened VS Code folder | Proven |
| Explain `.py`, editor launch, terminal launch, and platform differences | Chapter 1 explains that `.py` is plain text, shows VS Code launch, and separates Windows/macOS/Linux commands; chapters 10 and 13 continue the platform-specific path and environment guidance | Proven |
| Make parameter and argument visibly distinct | Chapter 3 separates definition and call sites, compares repeated calls, provides a four-stage binding trace, and uses a completion task with different blanks | Proven |
| Use a prediction-run-observe-explain rhythm | The strict checker proves exactly one prediction before the first run and one integrated trace after it in every main chapter | Proven |
| Replace weak arrow chains with integrated state traces | All 17 main chapters contain one trace with before state, numbered code steps, after state, and a meaning statement; HTML and PDF have dedicated trace renderers | Proven |
| Fade guidance before blank-page work | Nine chapters use completion tasks and eight use Parsons reconstruction; every main chapter then ends with independent transfer tasks | Proven |
| Use retrieval and spaced return points | Every main chapter has one recall block and one interactive quiz; attention metrics also count re-entry headings and active prompts | Proven |
| Progress realistic errors | The edition contains 19 executed intentional-error blocks plus a Typical Error section in every main chapter, progressing from syntax/naming to files, persistence, tests, and semantic defects | Proven |
| Keep history light and after practice | Every main chapter has one history pause after the independent-task block; ordering is enforced by the strict checker | Proven |
| Treat attention as an independent acceptance criterion | Source metrics pass; all 225 PDF pages and desktop/mobile site layouts were also visually reviewed | Proven |
| Use screenshots only when the interface is the lesson | One real, tightly cropped Windows VS Code screenshot identifies Run Python File; code/state/platform differences remain text or selectable code | Proven |
| Keep site and PDF as two renderings of one book | Both are generated from the same `content/` sources; the two official PDF copies have the same SHA-256 hash | Proven |
| Publish the official edition on `ArTeGaS` GitHub Pages | Correct account, remote, public repository, and Pages source are verified; the commit and push are not yet authorized | Pending external action |

## Release boundary

The local artifacts are ready for review. Git history and the public GitHub Pages site were not changed because publication to the `ArTeGaS` account requires explicit authorization.

- `git diff --check`: exit 0. Git emitted line-ending normalization advisories for generated files, but found no whitespace errors.
- Upstream divergence before publication: `0 0`.
- The pre-existing untracked prototype `output/pdf/prototyp-formatu-do-pislia.pdf` was left untouched.
- The temporary local QA browser tab and HTTP server were closed after the checks.

## GitHub Pages preflight

- GitHub CLI: 2.86.0.
- Active authenticated account: `ArTeGaS`; `ArTeGaS-2` is authenticated but inactive.
- Remote: `https://github.com/ArTeGaS/python-oop-handbook-ua.git` for fetch and push.
- Repository: public, default branch `main`.
- Pages: built and public at `https://artegas.github.io/python-oop-handbook-ua/`, sourced from `main:/docs`, with HTTPS enforced.
- The current public page was opened as a user and loaded without horizontal overflow. It is still the pre-release edition: it has no Classic Edition link and no new attention introduction. This is the expected boundary before the pending commit and push.
