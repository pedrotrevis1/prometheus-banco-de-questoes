# Feature specification: Stable question-preview resizing

**Folder**: `009-preview-resize` | **Status**: In progress | **Created**: 2026-11-16
**Fixes**: KD-19 | **Prerequisite**: 008 (planned execution sequence)
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

## Why

The owner reports that dragging a preview's corner makes the interface appear
to stretch downward, and confirmed that the affected control is the statement
preview inside a tab-2 question card. The root cause and exact visual motion
have not been reproduced. This spec defines the intended stable behavior;
the implementation must first capture a failing regression.

## User stories and acceptance scenarios

### US1 — Resize one preview within the search results (P1)

1. **Given** several question cards in a normally sized window, **when** I
   drag one card's preview handle down/up, **then** only that preview changes
   height, with the containing card and cards below it moving by the necessary
   layout amount. The main window, tab bar, filter sidebar, selection header
   and page footer do not grow or move as a consequence of the drag.
2. **Given** one fixed drag displacement, **when** document layout/scrollbars
   update during the drag, **then** the preview follows that displacement
   without runaway growth, oscillation, extra jumps or pointer drift.
3. **Given** a preview at either size limit, **when** I keep dragging,
   **then** the preview remains within its bounds and the outer application
   does not expand. Remaining question content is accessible by scrolling
   inside the preview, including long text, alternatives and embedded images.
4. **Given** an active drag, **when** I release the mouse outside the handle,
   **then** resizing stops. Subsequent mouse movement without a new press
   cannot change the preview height.

### US2 — Automatic layout respects manual resizing (P1)

1. **Given** a manually resized preview, **when** text reflows or its document
   emits a size notification, **then** the manual height is retained within
   the current bounds; automatic fitting cannot take control back.
2. **Given** an unmodified preview, **when** its first layout completes,
   **then** it fits short content or uses the existing compact height of at
   most 150 logical pixels for longer content, subject to the available space.
3. **Given** a long preview, **when** I use "Ler enunciado" / "Ocultar",
   **then** expansion/collapse works predictably and neither state causes the
   outer interface to grow. An explicit toggle resets any manual height to
   that mode's automatic size; a later drag takes manual control again.
4. **Given** manual or expanded content, **when** I shrink the application
   window, **then** the preview clamps to the new available space and all
   content remains reachable. Enlarging the window does not unexpectedly
   restore an old oversized manual height.

### US3 — Keep existing controls and pagination usable (P2)

1. **Given** a resized card, **when** I select it or navigate pages, **then**
   selection and footer behavior follow 007. Returning to a recreated card
   may restore its default preview size; size persistence is not required.
2. **Given** registration text editors and resizable category trees, **when**
   I use their handles, **then** their existing resize behavior still works.
3. **Given** light/dark themes, **when** I use the handle or preview scrollbars,
   **then** both remain visible and operable on Windows and macOS.

## Requirements

- **FR-001** Establish and document an actual reproduction and failing test
  before calling the defect fixed. If it cannot be reproduced, report the
  attempted cases and ask the owner for the missing reproduction conditions;
  do not substitute a guessed diagnosis.
- **FR-002** A drag changes preview height only. It cannot request a resize
  of the top-level window or propagate an unbounded minimum size through the
  result container. Local card reflow and changes in result scroll range are
  expected; arbitrary auto-scrolling of the whole page is not.
- **FR-003** Resize bounds include a minimum of 60 logical pixels for manual
  drags and an upper limit based on the stable result viewport's available
  height, allowing for the card's non-preview controls. On very small windows,
  the minimum wins and the result area can scroll. The maximum must not be
  derived from a container whose height grows with that same preview.
- **FR-004** Manual drag, compact automatic fit and expanded automatic fit
  have an explicit precedence. Automatic fitting is idempotent, does not
  reenter indefinitely and cannot overwrite manual height except to clamp
  it after an external viewport resize.
- **FR-005** Preserve rich text, images, read-only preview behavior, selection
  and export. Geometry changes never write to a bank.

## Success criteria

The reproduced failure has a regression that fails before the fix and passes
after it. The scenarios above pass with short/long text, images, repeated
up/down drags, scrolling during a drag, compact/expanded/manual states and
multiple cards. Top-level geometry stays unchanged unless the user resizes the
application window itself.

## Out of scope

Removing resize controls, changing editor content/export, persisting preview
size, redesigning all cards, fixing unrelated layout issues, claiming a root
cause based on static code inspection alone.
