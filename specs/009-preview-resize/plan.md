# Implementation plan: Stable question-preview resizing

**Spec**: [spec.md](spec.md) | **Status**: Done historically; visible-resize follow-up in [010](../010-preview-visible-resize/plan.md) | **Created**: 2026-11-16

## Investigation before a fix

The owner's affected control is confirmed; the exact failure mechanism is not.
Current anchors are `QuestionCard`, `_fit_initial_preview`, `toggle_expansion`,
`VerticalResizeHandle`, `VerticalResizeMixin` and the two scroll containers in
`setup_tab_search`. Locate their equivalents after 007/008.

Static observations to test, not assumed causes:

- The shared handle incrementally adds pointer movement to `owner.height()`;
  a concurrent auto-fit can alter that base between mouse events.
- The handle has only a minimum. Each `setFixedHeight()` also raises the
  preview's minimum height, which can affect enclosing layout size hints.
- `_fit_initial_preview` responds to document size, calls `setTextWidth` and
  sets fixed heights. Its expanded branch runs even after a manual drag.
- Appearance/disappearance of inner/outer scrollbars changes available width,
  which reflows rich text and may trigger more document-size notifications.
- The card preview's handle is inserted as its own layout row while the
  shared mixin overlays its handles. Check ownership and movement in each
  case before changing parenting or event routing.

Use an injected tab/card fixture and synthetic content. Do not instantiate the
normal application startup against the owner's data directory. Record the
platform, Qt/Python versions, theme, window size, content, expansion state,
scroll position and exact press/move/release sequence that triggers the issue.
Record top-level, viewport, sidebar, card and preview geometry before/during/
after a drag. An observation such as "later cards moved down" alone does not
prove a bug; that movement is necessary when one card becomes taller.

Qt explains that a QScrollArea's child/layout size policies influence sizing;
see [QScrollArea: Size Hints and Layouts](https://doc.qt.io/qt-6/qscrollarea.html#size-hints-and-layouts).
Its [QAbstractScrollArea documentation](https://doc.qt.io/qt-6/qabstractscrollarea.html#detailed-description)
also describes scrollbar-related viewport changes. These support the areas
to investigate, not a conclusion about this app's root cause. Check behavior
against the project's pinned PySide6 version rather than upgrading Qt as a fix.

## Intended implementation boundary

Extract the sizing/state policy first into pure functions or a small state
object, for example `prometheus/domain/preview.py`. Inputs are plain numbers
and modes: starting pointer/height, current pointer, content height, viewport
height, card chrome height and compact/expanded/manual state. Qt geometry,
signals, timers and events stay in the UI adapter; no PySide imports in domain.

Use the press-time height and global pointer Y as an immutable drag origin:
`start_height + current_global_y - start_global_y`, clamped to the current
bounds. A preview cap is based on the **result viewport**, minus measured card
chrome, never the growing scroll content. Automatic compact fitting retains
the existing short-content behavior and 150-pixel ceiling; expanded fitting
retains the existing 300-pixel ceiling, both clamped to available space.
Manual sizing can use the viewport-based cap. An explicit expand/collapse
resets to that mode's automatic height; a new drag takes manual precedence.

After reproduction, make the smallest verified Qt/layout change needed so
the outer scroll viewport can contain a tall child without forcing the main
window's minimum height upward. Check size policies, size-adjust policies,
layout constraints and stable scroll anchoring using recorded geometries.
Do not freeze the entire main window size or change every size policy blindly.
Document callbacks must be idempotent and guarded against recursive reentry;
apply a geometry update only when the effective target changes. Avoid an
unbounded zero-delay timer chain as a workaround.

The event adapter must end a drag on release/cancellation, including releases
outside the handle and loss of the active widget. Avoid leaving stale callbacks
targeting cards disposed during a page turn. Keep preview-specific caps and
mode rules out of registration editors and category trees, even if their event
adapter is shared. Extract any changed sizing calculation before changing it;
widgets handle Qt operations only.

## Validation

- First capture a failure against the current/extracted implementation. Use
  offscreen Qt/QTest for reproducible geometry/event tests and a visible manual
  run for the owner's visual symptom. If no failure appears, get missing
  reproduction conditions from the owner before choosing a speculative fix.
- Pure policy tests cover stable drag origin under external intermediate
  heights, lower/upper clamps, expanded-to-manual precedence, explicit toggle
  reset, external viewport shrink, repeated identical notifications and tiny
  viewports. These run without Qt.
- UI tests verify that a large drag changes one preview, leaves top-level,
  sidebar, selection header and footer geometry stable, and keeps later-card
  displacement equal to the affected card's height change. Check release
  outside the handle, multiple events and scrollbar-induced reflow. Use an
  event-loop settling criterion rather than arbitrary long sleeps.
- Exercise short/long statements, five alternatives, essay answers, large
  synthetic images, 1/50 cards, top/middle/bottom scroll positions, and initial,
  expanded and manually resized states. Verify content is reachable through
  preview scrollbars at the cap and no unintended page scroll jump occurs.
- Recheck registration and tree handles because `VerticalResizeHandle` is
  shared. Run applicable 007/008 tests to catch pager/viewport interactions.
- Manually validate Windows and macOS, both themes and different scale factors.
  An offscreen pass alone cannot establish that the visual symptom is resolved
  on an untested platform; record missing checks explicitly.

## Constitution check

| Principle | Compliance |
|---|---|
| I / II | Synthetic fixtures only; geometry has no database writes; offline |
| III | No change to stored/exported question content |
| IV | Reproduction and spec precede a fix; update BL-042 and KD-19 when delivered |
| V | Changed sizing logic extracted before modification; failing regression required |
| VI / VII | No new dependency or broad rewrite; existing Portuguese controls retained |

## Complexity tracking

No exception is requested. The resize adapter may require a small refactor
because the current shared helper combines pointer events and sizing policy.
Do not introduce a general layout engine or persist preview geometry.
