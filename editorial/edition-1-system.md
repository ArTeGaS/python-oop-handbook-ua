# Edition 1 learning system

This file is the consistency contract for the main edition. The frozen classic edition lives in `editions/classic/`.

## Invariants

1. Preserve the subject scope and OOP-first route. Improve how a learner acts on the material, not what the book fundamentally teaches.
2. The book is the primary artifact. The website renders the same semantic blocks and may only add quiet affordances such as revealing an answer or saving progress.
3. Every chapter keeps one visible result, runnable code, realistic errors, a quick check, independent work, and a short history pause.
4. Attention is an acceptance criterion across prose, code, visuals, tasks, and pacing.
5. If a later editorial solution is better, apply the same solution to all earlier chapters where the same teaching situation appears.

## Required chapter rhythm

Every main chapter uses these stages without turning every paragraph into a worksheet:

1. `goal`: the visible result and chapter outcome.
2. `focus`: one primary action and a short re-entry anchor.
3. `predict`: a concrete prediction before an important run.
4. runnable example and explanation.
5. `trace`: an integrated state/value/process trace placed next to the example it explains.
6. `completion` or `parsons`: one intermediate task between reading and blank-page coding.
7. realistic error progression appropriate to the learner's current level.
8. `recall`: a short closed-book retrieval prompt.
9. independent transfer tasks in at least two contexts.
10. a detachable history pause after useful action, never before the first visible result.

## Attention gate

A fragment passes only when all statements are true:

- The learner can identify the next action from the heading and first sentence.
- One panel has one dominant purpose.
- A stopped learner can resume from a numbered step, state label, filename, or explicit prompt.
- Related explanation and visual evidence are adjacent; the learner does not have to mentally merge distant sources.
- Decorative material does not compete with code or the current action.
- Long code is segmented at meaningful boundaries and followed by an observable result.
- Active responses appear regularly: predict, trace, explain, modify, recall, or make.

The "identify in a few seconds" check is an editorial heuristic, not a medical or scientific threshold.

Attention is audited independently from the media choice. The strict build records, for every chapter:

- the longest paragraph;
- the longest passive stretch between learner actions;
- the number of active prompts and re-entry headings;
- the longest code block;
- whether every code block over 60 lines has at least three numbered navigation comments.

The current acceptance limits are source-level guardrails, not claims about a universal human attention span. Visual density, contrast, cropping, page breaks, and mobile layout still require a real rendered review.

## Trace design

Do not use a bare arrow chain as the only explanation. A trace must show:

- an explicit **before** state;
- numbered steps with the exact code fragment and its meaning;
- an explicit **after** state;
- a short sentence naming the concept being distinguished.

For parameter/argument examples, the trace must separately show the call-site argument, the method-definition parameter, Python's binding, and the resulting state change.

## Guidance fading

Use the ladder:

1. complete worked example;
2. one missing or reordered part;
3. a small modification with an expected result;
4. independent work in a familiar context;
5. transfer to another object or domain.

Do not keep full guidance after the learner has demonstrated the same operation twice.

## Visual media decision

- Use a code block when exact characters, syntax, logic, comparison, or value flow is the object of learning.
- Use a tightly cropped VS Code screenshot when interface location or visible editor state is the object of learning.
- Use a stable two- or three-frame screenshot sequence only when a GUI action changes state in a way prose cannot show clearly.
- One screenshot communicates one assertion. Crop unrelated tabs, sidebars, terminals, and notifications.
- Screenshots may show only VS Code elements that are common across Windows, macOS, and Linux.
- Platform-specific commands and paths use text/code panels. Do not fabricate macOS or Linux screenshots.
- Every image needs an informative caption and must remain legible in the printed PDF.

## Error progression

- Early chapters: local syntax, indentation, naming, and missing-argument errors.
- Middle chapters: type, index, key, state, and control-flow errors.
- Later chapters: file, dependency, exception-boundary, persistence, test, and semantic defects.
- A deliberate error is always followed by the visible message, a reading cue, and a corrected or recoverable path.

## History and optional context

- Place the history block after practice or independent action.
- Keep it short and independently skippable.
- Never hide a required definition, command, or test criterion inside a history block.
- Do not add portraits or decorative images unless they explain the active concept.

## Verification contract

- Source checker enforces required semantic blocks in all main chapters.
- Every runnable and deliberate-error block is executed.
- Main and classic site/PDF links are checked.
- PDF is rendered to images and inspected at chapter transitions and representative dense pages.
- The site is checked at desktop and mobile widths, in light and dark themes.
- No commit, push, or public deployment happens without Viktor's explicit approval.
