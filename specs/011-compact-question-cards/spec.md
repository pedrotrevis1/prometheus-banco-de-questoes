# Feature specification: Compact question cards and usage history

**Folder**: `011-compact-question-cards` | **Status**: Done; owner accepted remaining unperformed native checks | **Created**: 2026-11-18
**Prerequisites**: 006 usage history, 007 pagination, 009/010 preview sizing
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)
**Handoff**: [card-and-new-exam-workflow.md](../../docs/card-and-new-exam-workflow.md)

## Why

The owner's first screenshot shows metadata competing with a horizontal row
of large buttons. Every metadata value is bold and blue on a green panel,
making field boundaries hard to scan. Every recorded use is appended to the
same panel, so the header grows indefinitely as the question is reused.

Organize metadata into readable rows, stack compact actions, and show only a
usage count in the card. Reveal the existing history on demand. This changes
the presentation contract of 006 US2/FR-004, retaining its history and filter
semantics. The screenshot is owner evidence; no runtime measurement or visual
acceptance is claimed by this planning change.

## Proposed visual contract

Illustrative content; wrapping depends on available width:

```text
Questão #1                                          [ ] Selecionar
Segmento / Série: Ensino Médio — 1ª, 2ª e 3ª Série    [Ler enunciado]
Dificuldade: Médio    Tipo: Múltipla Escolha         [Editar       ]
Assuntos: 2ª Lei de Mendel (Segregação Independente)  [Duplicar     ]
Fonte: Não informada    Ano da fonte: Não informado
Última alteração: 17/11/2026 15:31    Usos: 2
----------------------------------------------------------------
Existing statement / alternatives / answer preview
                                                 [resize handle]
```

Use a prominent question identifier, bold field labels and regular values. The owner requested a light green metadata background in light mode and the app’s dark green surface in dark mode, with readable text; the usage control and history popup follow the current theme (2026-11-18).
Secondary metadata uses a readable secondary color; the entire panel is no
longer a saturated bold block. Preserve explicit labels for difficulty, type
and source year. Keep all metadata available without opening the preview.
The school-year value above is illustrative: preserve the current formatter's
complete classifications, including multiple segments and segment-only data.

## User stories and acceptance scenarios

### US1 — Scan metadata and reach actions (P1)

1. **Given** an ordinary card, **when** it is displayed, **then** ID, segment
   and school years, difficulty, type, subjects, source, source year and
   last-modified time are readable in labeled rows. Labels are emphasized;
   values are regular weight. Source year is distinguishable from school year.
2. **Given** long subjects, sources, or several school years/segments,
   **when** the card becomes narrower, **then** values wrap without overlapping
   actions or being silently omitted. Literal `<`, `>`, `&` and quotes remain
   literal text. Missing-value fallbacks retain their current meaning.
3. **Given** the action area, **when** I use the card, **then** selection is
   visible at the top of one narrow action column, followed vertically by
   "Ler enunciado" / "Ocultar", "Editar" and "Duplicar". Buttons share a
   compact width and retain visible Portuguese labels and keyboard focus.
4. **Given** a short preview, **when** its expand action is unnecessary,
   **then** that button remains hidden as today and leaves no empty button slot.
   At widths insufficient for the two columns, actions move below metadata;
   they never squeeze metadata into an unreadable sliver or widen the window.

### US2 — Understand usage without a growing card (P1)

1. **Given** 0, 1, 2 or 1,000 completed generations containing a question,
   **when** I view its card, **then** it shows respectively "Usos: 0",
   "Usos: 1", "Usos: 2" or "Usos: 1000". Exam names, classes and dates are
   absent from the resting card. Increasing history does not add header rows.
2. **Given** one completed generation with several versions, **when** I view
   the count, **then** it adds one use, regardless of its version count. A
   second generation of the same exam adds another use, even on the same date.
   Saving, opening, duplicating, cancelling or failing an export adds no use.
3. **Given** recorded uses, **when** I hover over "Usos: N", **then** a small
   popup shows one entry per use with date, exam name and class, newest first,
   retaining stable ordering for ties. Missing class displays "Sem turma".
   Dates use `dd/MM/yyyy`, retaining the recorded date as in existing history.
4. **Given** no recorded use, **when** I inspect the count, **then** the popup
   says "Nenhum uso registrado." A legacy path without history support shows
   "Usos: não disponível", rather than asserting that the question was unused.
5. **Given** lengthy history or long names, **when** I inspect it, **then** the
   popup stays within the screen, wraps names and provides scrolling to every
   entry. Moving the pointer into it permits reading/scrolling without closing
   it. Its size does not change the card or preview.
6. **Given** keyboard navigation, **when** I activate the focused usage control
   with Enter/Space, **then** I can read/scroll the same history and close it
   with Escape. Clicking the count also keeps the popup open for inspection.
   A transient hover popup closes when the pointer leaves both surfaces; an
   activated popup closes with Escape or an outside click and restores focus.
7. **Given** a history-read error, **when** I request details, **then** I see
   "Não foi possível carregar o histórico de usos." I can retry; the app
   neither silently substitutes an empty history nor changes the stored data.

### US3 — Preserve the working search and preview (P1)

1. **Given** normal or selected-only search across multiple pages, **when** I
   select, expand, resize, edit or duplicate a question, **then** the existing
   behavior, global selection and 50-card limit remain intact.
2. **Given** a long preview and another card below, **when** I resize it,
   **then** visible preview growth/shrinkage, card containment and next-card
   reflow still satisfy 009/010. The new header participates in size calculation.
3. **Given** successful generation, exam deletion or bank switching through
   existing actions, **when** cards next refresh or details reopen, **then**
   usage information reflects the current bank. No previous-bank popup survives
   card disposal. Deleting an exam retains 006's existing removal of its usages.

## Requirements

- **FR-001** Implement the labeled hierarchy and compact action column above
  in light/dark themes on Windows and macOS. Compactness comes from layout and
  local spacing, with readable platform typography and pointer targets.
- **FR-002** Render metadata as data, never as unescaped rich-text markup.
  Do not change question HTML, correct-answer highlighting or exported content.
- **FR-003** A use means an existing completed-generation usage record linked
  to the question, not an exam, version, selected question or exported filename.
  Count and detail queries must describe the same records.
- **FR-004** Load counts for the displayed page without retrieving its full
  histories. Load details only when requested, scoped to that question. Do not
  preload histories for the whole bank or retain an unbounded cross-page cache.
- **FR-005** All recorded history remains available in the bounded popup;
  avoid a screen-sized native tooltip containing a single unbroken string.
  Accessible names/descriptions expose the count and its inspection action.
- **FR-006** Usage reads and UI interactions are read-only. No schema migration,
  stored counter, backfill, new dependency or changed usage-filter semantics.
- **FR-007** Preserve preview sizing, card disposal, search/paging and existing
  edit/duplicate/selection callbacks. No general application theme redesign.

## Success criteria and scope

The illustrated hierarchy and all scenarios pass; cards with otherwise identical
metadata and 2 versus 1,000 uses have the same settled header height at the same
width. Tests verify accurate counts, deferred history reads, escaped text,
bounded geometry and preserved preview reflow. Record actual visible checks on
Windows/macOS, both themes and representative scaling in `acceptance.md`.
The owner authorized closing T008 with unperformed checks recorded in acceptance.md; offscreen tests are not native acceptance.

Out of scope: new usage analytics, historical content snapshots, changing when
usages are recorded/deleted, preview redesign, global font reduction, and the
new-exam action (012). The implementation is complete; the owner accepted closure with unperformed native checks recorded in [acceptance.md](acceptance.md).
