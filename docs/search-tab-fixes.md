# Search tab fixes: handoff for implementation agents

**Prepared**: 2026-11-16 | **Status**: 007–009 implementations in progress; platform checks pending

Start here when continuing the owner's three reported problems in "Buscar e
Selecionar Questões". Read `AGENTS.md`, [constitution.md](constitution.md),
[roadmap.md](roadmap.md) and [glossary.md](glossary.md) first. Documents and code
are English; application labels and messages are Brazilian Portuguese.

## Owner decisions and proposed details

The owner confirmed **50 questions per page** and confirmed that the resize
problem happens in a **question card's statement preview**. The requested
source-year filter has two independently optional, inclusive bounds: "Desde"
and "até". "Desde: 2022" includes 2022 and later years. This changes source
year (`ano_origem`), not school year (`ano_sugerido`).

Pagination state transitions, invalid-year handling and resize constraints
below describe the draft acceptance rules. Pagination is implemented and has
synthetic offscreen measurements; platform verification remains pending.
Source-year ranges and the reproduced preview-resize issue are implemented; platform checks remain pending.

## Documents and sequence

| Order | Work | Read together |
|---|---|---|
| Prerequisite | Foundation, then data safety | Existing specs 001 and 002, including their plans, tasks and unresolved owner questions |
| 1 | Bound query payloads and cards; preserve selection | [007 spec](../specs/007-search-pagination/spec.md), [plan](../specs/007-search-pagination/plan.md), [tasks](../specs/007-search-pagination/tasks.md) |
| 2 | Replace exact source year with inclusive optional bounds | [008 spec](../specs/008-source-year-range/spec.md), [plan](../specs/008-source-year-range/plan.md), [tasks](../specs/008-source-year-range/tasks.md) |
| 3 | Reproduce and fix preview resize instability | [009 spec](../specs/009-preview-resize/spec.md), [plan](../specs/009-preview-resize/plan.md), [tasks](../specs/009-preview-resize/tasks.md) |

This sequence follows the merged 001/002 implementation; Windows verification
and release work remain pending. The code is now in the `prometheus/` package
and has an automated test suite. The owner chose to retain bulk deletion using the global selection, including
questions hidden by filters or pages. The help text should make that clear.

## Evidence from the current source

Line numbers are navigation aids for the 2026-11-16 checkout; search for method
names after foundation moves the file.

| Location in `Prometheus1.1.py` | Observation |
|---|---|
| `load_questions`, approximately 3021–3129 | Fetches all matching rich-text columns with `fetchall()`, then filters school years and categories in Python, then constructs every `QuestionCard` |
| `QuestionCard.__init__`, approximately 1272–1336 | Creates a `QTextEdit`, loads HTML and formats its full document for every card |
| `setup_tab_search`, approximately 2812–2985 | Two scroll areas; result footer is outside the card scroll content |
| `load_questions`, approximately 3068–3070 | Exact `ano_origem = ?` comparison |
| `QuestionCard._fit_initial_preview` / `toggle_expansion` | Automatic document sizing and expand/collapse both set a fixed preview height |
| `VerticalResizeHandle.mouseMoveEvent`, approximately 1400 | Adds each pointer delta to the current owner height, with a minimum but no maximum |
| `VerticalResizeMixin` | Shares the handle with registration editors and category trees; regressions can affect other tabs |

The likely main performance cost is creating and laying out thousands of rich
text documents, potentially containing images. This is an inference from the
code, not a measured diagnosis. The resize root cause is still unverified.

## Why pagination first

Use numbered pages with 50 cards and fetch full content for the current page.
Do not fetch every rich-text row and merely hide or slice the widgets. Apply
**all** filters before counting and paging: the existing category/school-year
post-filtering would otherwise produce short pages and incorrect totals.

| Alternative | Assessment for this change |
|---|---|
| 50 cards plus bounded queries | Recommended; reuses cards and supports direct page navigation |
| 100 cards | Twice as many rich-text previews; owner chose 50 |
| Infinite scrolling / "Carregar mais" | Retaining previous cards eventually recreates the same growth; different navigation than requested |
| Virtualized Qt model/view | Consider only if measured results still miss the target; richer delegate and resize work makes it a larger change |
| Background loading | Consider only after profiling the bounded approach; it adds connection/thread and stale-result handling |
| Indexes / full-text search | Could improve particular queries; cannot remove the cost of thousands of widgets. Schema/search normalization belongs to 005 |

There is no new dependency, schema migration, database cleanup or question
limit. All questions remain accessible. Card count, payload count, query time
and GUI time must be measured separately before claiming the slowdown fixed.

## Instructions to paste into a future chat

> Continue the search-tab fixes documented in `docs/search-tab-fixes.md`.
> Read AGENTS.md, the constitution, roadmap and the applicable spec/plan/tasks.
> Reconcile the current checkout with the documented prerequisites and owner
> decisions. Work on the next eligible unchecked task, one at a time and in
> order; check it only after its tests/checks pass. Do not guess an existing
> [NEEDS CLARIFICATION] answer. Keep domain/storage logic outside widgets.
> Use in-memory SQLite fixtures and synthetic content; never launch the normal
> app against the owner's configuration or alter a personal bank for testing.
> Update the baseline when behavior actually changes, and report completed
> task IDs, test results, remaining work and any blocker for the next chat.

For an individual issue, add: "Continue spec 007", "Continue spec 008" or
"Continue spec 009". These agents should run sequentially because the changes
share the search controller, query path and preview widgets.

## Review record

- [x] Read the constitution, roadmap and first unfinished iteration's spec/plan/tasks.
- [x] Inspect search, selection, year storage and resize code without opening a bank.
- [x] Record the owner's page-size and affected-widget answers.
- [x] Prepare three Draft specs with plans, ordered tasks and regression criteria.
- [x] Reconcile prerequisites and owner decisions; 007 implementation is in progress.
- [ ] Run automated tests, GUI checks and performance measurements during implementation.
