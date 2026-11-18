# Implementation plan: Visible preview resizing and card reflow

**Spec**: [spec.md](spec.md) | **Status**: Done | **Created**: 2026-11-18

## Entry conditions and scope

This change prepares documentation only. The implementing agent begins at T002
in [tasks.md](tasks.md), revalidates this plan against its checkout, and works
one task at a time. Read the constitution, roadmap, 009 spec/plan/tasks and this
spec's reproduction first. Use branch `010-preview-visible-resize` for the fix.
No new dependency, migration or question-bank modification is planned.

## Investigate the visible failure before choosing a fix

Inspect `QuestionCard` construction, `_set_preview_height`, `_preview_geometry`,
`_fit_initial_preview`, `move_preview_drag` and `toggle_expansion` in
`prometheus/app.py`; `VerticalResizeHandle`; the result `QScrollArea`,
`scroll_content` and `scroll_layout` in `setup_tab_search`/`load_questions`;
`prometheus/domain/preview.py`; and `tests/ui/test_preview_resize.py`.

Recreate the video with synthetic multiple-choice content and at least two
cards. Vary header wrapping and saved-exam usage rows, which affect card chrome.
Keep the existing essay fixture as a comparison. Confirm the running revision
before concluding that this checkout reproduces the recording. Never launch
normal startup against the owner's configuration or open a personal bank.

Trace geometry from text viewport through preview, handle, card, result content
and result viewport. Check geometry invalidation, cached size hints, minimum
sizes, size policies, layout constraints and any ancestor clipping. Treat these
as hypotheses until measurements identify the cause. Verify the parent after
the handle is inserted into the card layout rather than inferring ownership
from its constructor alone. Do not select a particular Qt workaround in advance.

Record the measurements listed in [reproduction.md](reproduction.md) across
several movement events and after release. If this fails to reproduce, retain
the attempts, ask for the missing build or conditions and leave implementation
blocked on that information; do not substitute a different resize defect.

## Regression design

Before fixing the UI, add a test that fails on the observed layout defect.
Start below the viewport cap, explicitly assert enough headroom, and drag by a
small positive displacement (for example 60 logical pixels). Wait for bounded
event-loop/layout settling, then require all of the following:

- Actual preview and text viewport height increase by the permitted amount.
- The visible intersection of the text viewport with its ancestors increases;
  the preview and handle remain inside the containing card's contents rectangle.
- Containing-card height increases with the preview, preserving measured chrome.
- The next card's top moves by that positive card-height increase, preserving
  inter-card spacing and result-scroll position. Measure in result-content
  coordinates, and separately check global geometry for unintended scrolling.
- A subsequent upward drag reverses the changes; repeated callbacks and release
  do not snap back or reintroduce clipping. Stored/displayed content is unchanged.

Retain the existing reflow assertion but strengthen it so a zero/zero equality
cannot pass. Tests of scrollbar ranges or `view_panel.height()` alone are
insufficient. Test both compact and expanded starts, repeated drags, scrollbar
transitions, and top/middle/bottom result positions. Include a visible synthetic
run using real pointer input, since direct synthetic mouse-event delivery does
not establish that the visible grip works on a native window.

## Implementation boundary

Preserve `PreviewSizing` unless reproduction demonstrates a policy defect.
Keep pointer handling, Qt signals, measurement and geometry application in thin
UI adapters. Extract existing calculations before changing them; any new sizing
or state logic belongs in `prometheus/domain/preview.py` with Qt-free tests.
Do not add domain rules or a new sizing algorithm inside a widget class.

Apply the smallest measured layout fix that makes the enclosing card and result
layout honor the effective preview height. Keep the handle visible and reachable
at the lower-right edge. Do not force a fixed top-level window size, reserve an
oversized static card, add arbitrary padding, disable scrolling or add endless
timer-based relayout loops. Document the proven cause and why the fix addresses
both growth and shrinkage. No spec amendment to 009's limits is planned.

## Validation and delivery

Run the new failure before and after the fix, then the preview policy/UI tests,
relevant search-pagination/source-year tests and full pytest suite. Use isolated
configuration and in-memory or spec-authorized temporary fixtures; do not
create, overwrite or delete any personal `.db` file. Verify text, alternatives,
images, usage metadata, selection/paging and shared editor/tree handles.

Record a visible macOS before/after demonstration matching the owner's gesture,
then Windows verification, both themes and representative display scaling.
Record pending checks explicitly; offscreen success or 009's previous owner
sign-off cannot stand in for this verification. Write `acceptance.md` with
environment, measurements, regression/test results and platform results.
Only after implementation and acceptance update BL-042/KD-20, roadmap, handoff
and release notes as applicable; do not describe this draft as delivered.

## Constitution check

| Principle | Compliance |
|---|---|
| I / II | Synthetic isolated fixtures, offline operation, no personal bank writes or migrations |
| III | Geometry-only scope; preserve question and export content |
| IV | New spec and acceptance precede code; baseline now records the existing defect and is updated again with delivery |
| V | Failing visible-geometry regression first; new policy outside widgets with tests; UI limited to Qt adaptation |
| VI / VII | No dependency or broad redesign; existing Brazilian Portuguese UI retained; documents/code in English |

## Complexity tracking

No exception requested. A domain refactor is needed only if policy changes are
shown necessary; a measured Qt layout fix does not justify a new layout engine.
