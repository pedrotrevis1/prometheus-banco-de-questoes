# Feature specification: Visible preview resizing and card reflow

**Folder**: `010-preview-visible-resize` | **Status**: Done | **Created**: 2026-11-18
**Fixes**: KD-20 | **Prerequisite**: 009 implementation
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)
**Evidence**: [reproduction.md](reproduction.md)

## Why

The owner supplied a screen recording showing that question-preview resizing
is still broken after 009 was marked Done. Dragging the lower-right preview
handle downward changes its scrollbar, but does not provide the corresponding
visible reading space. The preview is clipped at the containing card's lower
edge, while the beginning of the next card stays almost stationary.

009 addressed unbounded heights and automatic fitting overriding manual drags.
Its completed tasks are historical evidence of that work, not proof that this
newly recorded symptom is fixed. This follow-up requires actual visible growth
and enclosing layout reflow as well as bounded internal geometry. The root
cause has not been established; do not assume that the sizing policy is wrong
or that the recording was produced by this exact source revision.

## User stories and acceptance scenarios

### US1 — Gain reading space by dragging the preview (P1)

1. **Given** a long preview and a second question card below it, with room
   below the preview's current height cap, **when** I drag the lower-right
   handle downward by a modest amount and release, **then** the visible text
   viewport grows by the permitted amount, additional content becomes visible
   without scrolling inside the preview, and the containing card grows to
   enclose the preview and handle. Nothing is clipped by the card or overlaps
   the next card.
2. **Given** that growth, **when** the results scroll position and window
   width stay unchanged, **then** the next card's top moves downward by the
   containing card's height increase, with the existing inter-card spacing
   preserved. Both increases must be positive; zero movement is not success.
3. **Given** a manually enlarged preview, **when** I drag upward within its
   bounds, **then** visible reading space and containing-card height decrease
   together, the next card moves upward accordingly, and the handle remains
   reachable at the preview's lower-right edge.
4. **Given** repeated drag events, **when** layout and document callbacks
   settle during and after the gesture, **then** visible geometry remains
   consistent with the selected height, without later snap-back or cropping.

### US2 — Preserve the constraints established by 009 (P1)

1. **Given** a drag toward either limit, **when** the limit is reached,
   **then** the preview stops at the existing minimum/viewport-derived cap.
   Content beyond the visible preview remains reachable through its scrollbar.
2. **Given** compact, expanded or manually sized previews, **when** I resize,
   toggle "Ler enunciado" / "Ocultar", or resize the application window,
   **then** 009's sizing precedence, toggle reset and viewport clamping remain
   intact, with the containing card always enclosing the effective preview.
3. **Given** a preview drag, **when** I release outside the handle or the
   mouse grab is cancelled, **then** dragging stops. The main window, filter
   sidebar, tab bar, selection header and page footer do not grow or shift as
   a consequence of the preview drag; the results do not scroll unexpectedly.

### US3 — Keep search and other handles working (P2)

1. **Given** multiple cards on a 50-result page, including questions with
   usage history, **when** I resize one preview, **then** every card retains
   readable metadata and controls, selection and paging work as before, and
   rich text, alternatives, answers and images are unchanged.
2. **Given** the shared resize helpers, **when** I resize registration
   editors or category trees, **then** their existing behavior is preserved.
3. **Given** light/dark themes on macOS and Windows, **when** I drag the
   preview's visible handle using a real pointer, **then** visible resizing
   and card reflow work on both platforms. Record unverified combinations as
   pending rather than extrapolating from an offscreen test.

## Requirements

- **FR-001** Reproduce the recorded clipping/no-reflow symptom in an isolated
  synthetic fixture and capture a failing regression before changing behavior.
  Record the running source/build and distinguish a source defect from a stale
  executable. If reproduction fails, document attempts and ask the owner for
  missing conditions; do not declare the issue fixed or invent a diagnosis.
- **FR-002** A permitted resize changes the actually visible text viewport,
  not only widget height, scrollbar range or sizing-state values. The card
  must enclose the preview and its handle throughout settled layout states.
- **FR-003** Card growth/shrinkage propagates through the results layout;
  adjacent cards neither overlap nor hide the resized preview. Reflow preserves
  normal spacing and respects 009's outer-geometry and scroll constraints.
- **FR-004** The regression must require positive visible growth below the
  cap, matching enclosing-card growth and subsequent-card displacement, then
  verify the inverse on shrink. Assertions where both measured changes can
  equal zero cannot establish successful resizing.
- **FR-005** Retain 009's 60-logical-pixel manual minimum, stable viewport cap,
  compact/expanded/manual precedence, release cleanup and non-persistent sizes.
  Geometry operations never write to a question bank or alter exported content.
- **FR-006** Completion requires a before/after geometry record and visible
  platform validation of this symptom. Preserve the new acceptance evidence
  separately from 009's historical reproduction.

## Success criteria

A regression fails on the reproduced pre-fix layout and passes after the fix.
The owner's gesture visibly reveals more question content, with matching card
reflow, in a synthetic equivalent of the recording. The 009 invariants and
search/paging/shared-handle checks pass. All acceptance scenarios have recorded
results; missing platform checks remain explicit and prevent a Done claim.

## Out of scope

Implementing a fix in this documentation change; removing handles; redesigning
cards; changing stored data, schema, exports or content formatting; persisting
sizes; changing 009's sizing limits without a spec amendment; unrelated UI work.
