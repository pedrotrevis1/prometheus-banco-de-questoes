# Feature specification: Paged search results

**Folder**: `007-search-pagination` | **Status**: Draft | **Created**: 2026-11-16
**Fixes**: KD-16 | **Prerequisites**: 001, 002
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

## Why

The owner reports that interacting with tab 2 is slow with approximately
2,500 questions. The current implementation retrieves rich content for all
matches and creates one rich-text card per result. The owner chose a fixed
page size of **50** on 2026-11-16.

## User stories and acceptance scenarios

### US1 — Browse a large bank without rendering the entire bank (P1)

1. **Given** 2,500 matching questions, **when** I open the bank's search view,
   **then** I see the first 50 in ascending ID order and a footer showing
   "Mostrando 1–50 de 2500 questões" and "Página 1 de 50".
2. **Given** that view, **when** I choose page 2, **then** only IDs for matches
   51–100 appear, in the same order, and the card area starts at the top.
3. **Given** 123 matches, **when** I choose page 3, **then** 23 cards appear and
   the footer shows 101–123 of 123. No result is duplicated or omitted.
4. **Given** zero matches, **when** the search completes, **then** I see
   "Nenhuma questão encontrada", a zero total and disabled page controls;
   there is no fictional page of results.

### US2 — Filters and page navigation describe the same result set (P1)

1. **Given** that I am on a later page, **when** I apply filters, **then** the
   result set and count are recomputed and page 1 is shown.
2. **Given** category or school-year matches scattered across the bank,
   **when** I filter, **then** every non-final page contains 50 matches and the
   total counts matches, not rows before those filters.
3. **Given** I edit filter fields without pressing "Filtrar Questões",
   **when** I change page, **then** the last applied filter set remains in
   effect. Applying the edited fields starts a new result set at page 1.

### US3 — Keep an exam selection across pages (P1)

1. **Given** questions selected on pages 1 and 3, **when** I change page or
   apply a filter hiding them, **then** all selected IDs and the global
   selection count are preserved. Returning to a card shows it selected.
2. **Given** 120 selected questions, **when** I choose "Navegar pelas questões
   selecionadas", **then** I browse only those questions in three pages,
   irrespective of the search filters, including any source-year bounds.
3. **Given** selected-only mode, **when** I deselect the last item on its last
   page, **then** the page is clamped to the last remaining valid page. If the
   selection becomes empty, the view shows an empty selected result set until
   I leave that mode; it must not silently display all questions.
4. **Given** selected-only mode, **when** I leave it, **then** page 1 of the
   last applied normal search returns. "Filtrar Questões" applies the form's
   current values, exits selected-only mode and goes to page 1.
5. **Given** selected questions across several pages, **when** I generate an
   exam, **then** it includes all selected questions in the existing exam
   order, not just the visible page.

### US4 — Stay on a valid page as the bank changes (P2)

1. **Given** a change through an existing register/delete action, **when**
   results refresh, **then** the current search is refreshed and the page is
   kept if valid or clamped otherwise; deleted IDs leave the selection.
2. **Given** a different bank is opened, **when** it loads, **then** paging
   starts at page 1, selected-only mode ends, and the selection clears as it
   does today. Revalidate the filter form against the newly opened bank.

## Requirements

- **FR-001** Normal and selected-only results contain at most 50 cards per
  page. There is no page-size selector in this iteration.
- **FR-002** A footer outside the card scroll area provides "Anterior",
  "Próxima", a direct page selector, current/total page counts and result
  range/total. Unavailable actions are disabled; invalid page input cannot
  issue an unbounded query. A single page disables previous/next.
- **FR-003** Paging has explicit stable ascending ID order. Counts and page
  contents use exactly the same effective predicates, including legacy
  school-year and direct category matching. Existing filters keep their
  semantics until another spec changes them.
- **FR-004** Full statements, alternatives and answers are retrieved and
  converted to preview HTML only for the requested page. No retained card or
  rich-content cache grows with pages visited; previous cards are disposed.
- **FR-005** Page state, applied filters, view mode and global selection are
  separate from widget instances. Search validation/query failures display a
  Portuguese error and never leave new counts paired with old page content.
- **FR-006** Page navigation and filtering are read-only. They neither create
  database files nor change schema, stored years, rich text or images.
- **FR-007** Data-safety spec 002's per-card deletion remains in force; exam
  selection is never repurposed as a page/bulk deletion selection.

## Success criteria

- The owner-confirmed page size is 50; all scenarios above pass.
- Automated checks prove full-content rows fetched and live cards are bounded
  by page size after deferred Qt deletion, including after repeated page turns.
- On a documented reference machine with a synthetic 2,500-question bank,
  target median filter/page-to-visible time is at most 1 second and no measured
  interaction exceeds 2 seconds across 10 repetitions. Record the Python/Qt
  versions, content/image sizes, cold and warm times separately; these are
  proposed release targets, not measured results.
- The same measurements on 5,000 synthetic questions confirm that card and
  rich-content payload counts stay bounded. Query scans may still grow.

## Out of scope

Infinite scrolling, virtualized delegates, worker threads, FTS, schema/index
changes, compression, deleting questions to reduce bank size, source-year
range behavior (008), preview resize behavior (009), changing exam order.
