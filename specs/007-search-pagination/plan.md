# Implementation plan: Paged search results

**Spec**: [spec.md](spec.md) | **Status**: In progress | **Created**: 2026-11-16

## Prerequisite and scope check

The 001 and 002 implementation is merged; their Windows verification and
release tasks remain pending. The owner authorized continuing with those
checks deferred. The owner chose to retain the existing bulk deletion behavior.
Paths below describe the post-foundation package. The current source
anchors are `load_questions`, `QuestionCard`, `setup_tab_search`,
`toggle_selected_question_view`, `show_filtered_questions`,
`toggle_question_selection` and existing bank/register/delete refresh paths.

Extract the search behavior unchanged and characterize it before adding
paging. Avoid a general UI rewrite. Domain/storage decisions go outside Qt;
widgets only collect inputs, request a page and render results.

## Proposed modules and responsibilities

| Module | Responsibility |
|---|---|
| `prometheus/domain/search.py` | Immutable applied filters, normal/selected view state, page calculations and transitions; direct category token matching and legacy school-year matching |
| `prometheus/storage/search.py` | Parameterized predicates, count and bounded page reads; named question records rather than new positional dependencies |
| Existing app/search UI module | Form snapshot on Apply, thin event handlers, pager widgets, card creation/disposal and Portuguese errors |
| `tests/domain/test_search.py` | Characterization plus state, total-page and boundary rules without Qt |
| `tests/storage/test_search.py` | In-memory query correctness and payload-bound tests |
| `tests/ui/test_search_pagination.py` | Offscreen page/selection/footer integration with injected test data |

Names are suggestions; extend existing equivalents if earlier iterations
already introduced them. Use the standard library, sqlite3, pytest and
PySide6 already selected by the project; no extra dependency is needed.

## Query strategy

1. Preserve today's text-over-HTML, source casefold, direct category matching,
   difficulty/type and legacy school-year semantics. Do not implement spec
   005's broader search semantics accidentally.
2. Move the existing Python category/school-year predicates into pure tested
   functions. Register them as connection-local SQLite functions where the
   legacy schema cannot express the same semantics simply. The connection
   already registers a `CASEFOLD` function; reuse that convention. No database
   schema or file changes are required.
3. Build one effective WHERE clause and parameter list. Use it for `COUNT(*)`
   and for the page SELECT. Read counts and content from one consistent read
   snapshot using the storage layer's transaction conventions.
4. Clamp the requested page, then SELECT the explicit required columns with
   `ORDER BY id ASC LIMIT ? OFFSET ?`. Bind values. Do not LIMIT first and then
   discard category/school-year nonmatches in Python. Do not fetch all rich
   text and slice it in memory. Count queries may scan stored text but must
   not transfer every rich document to the UI.
5. Selected-only queries use the global ID set and the same paging contract,
   bypassing normal filters. Empty selection is an immediate empty result,
   never an omitted restriction. Respect SQLite's actual bind-variable limit
   for large selections; use bounded ID chunks and merge sorted matching IDs
   before fetching only the page payload if necessary. Do not require a new
   persistent table or assume a fixed SQLite build limit.

`LIMIT/OFFSET` is sufficient for the reported bank size and direct page jumps.
Do not introduce keyset pagination unless a later measurement justifies a
spec/plan revision. Reassess predicates against the new model when 005 lands.

## UI and state flow

- Store an immutable applied-filter snapshot. Navigating pages must not read
  half-edited form values. Keep one bank-scoped set of selected IDs, independent
  of cards. Constructing a checked card must not emit a selection mutation.
- Keep the pager below `scroll_area`, outside `scroll_content`; selection
  count stays global. Render footer data and the new card list together only
  after a successful query. Retain the prior consistent view if a query fails.
- Dispose of old cards/signals/queued work when replacing a page. Qt
  `deleteLater()` needs an event-loop turn; tests should account for it rather
  than hiding an accumulating cache. Avoid duplicate loads caused by nested
  selected-view toggles or page selector signals while populating controls.
- Apply/page/mode changes scroll results to the top. Same-page selection
  changes do not rebuild normal results. Selected-only deselection refreshes
  and clamps the page. A last deselection remains an explicitly empty selected
  view, with a working way to return to normal search.
- Invalidate/recount on an existing successful write, not on every checkbox
  change in normal mode. Opening another bank clears cached query state and
  retains no foreign-bank IDs. Preserve existing bank filter behavior while
  revalidating category choices.
- Exam generation must continue reading all selected IDs, not the page records.
  Coordinate refresh with the existing bulk-delete path retained by 002.

## Validation and performance evidence

Use `sqlite3.connect(":memory:")`, all current migrations, and synthetic rows; never open or populate
the owner's bank. The benchmark fails on alerts or incorrect counts, page IDs or live-card counts. Test 0/1/49/50/51/123/2500 results, nonexistent page requests,
sparse IDs, scattered category/year matches, legacy school-year JSON,
casefolded sources, multiple filter combinations, large selected sets, page
turns with edited-but-unapplied form text, hidden selections, empty selected
mode and last-page deletion/deselection. Compare the full ordered result IDs
with concatenated pages. Cover errors and bank switching.

Use a small injected search-tab fixture, not the normal application startup,
which reads user configuration and may create a default bank. Offscreen Qt
checks may use `PySide6.QtTest` and pytest without adding pytest-qt. Assert
bounded full-record reads and card lifecycle in addition to correct labels.
Regression tests must fail against the extracted unpaged behavior.

Record query, HTML preparation, card construction/layout and end-to-end GUI
times separately with `time.perf_counter()`. Include long prompts, alternatives
and embedded synthetic images, plus a lightweight dataset. Do not use a flaky
wall-clock limit as a unit test. If the bounded version misses the spec target,
profile first and revise this plan before adding threads, caches or indexes.

Manual checks cover Windows (primary), macOS, light/dark themes, selection
across pages and a generated exam containing questions from several pages.

## Constitution check

| Principle | Compliance |
|---|---|
| I / II | Read-only searches; in-memory test banks; offline; no migration or data rewrite |
| III | All selected questions remain in export; errors remain visible |
| IV | Draft spec precedes code; update BL-041/043/044 and KD-16 when implemented |
| V | Extract query/state logic first, cover with tests; Qt only renders and handles events |
| VI / VII | No new dependency; Portuguese controls; English code/docs |

## Complexity tracking

Connection-local matching functions are needed to preserve the legacy token
and JSON formats without migration. Applying LIMIT before the existing Python
post-filters was rejected because it gives incorrect pages and counts. Revisit
these functions after schema normalization; do not create an abstraction layer
for hypothetical future stores.
