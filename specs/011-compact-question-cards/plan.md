# Implementation plan: Compact question cards and usage history

**Spec**: [spec.md](spec.md) | **Status**: Done | **Created**: 2026-11-18

## Entry and source evidence

Use branch `011-compact-question-cards`. Revalidate the checkout and prerequisite
implementations, then start at the next unchecked task. Work sequentially. This
plan authorizes no application implementation in the current documentation task.

| Location | Observation / intended work |
|---|---|
| `prometheus/app.py::QuestionCard.__init__` | One plain-text CardLabel concatenates all metadata and full usage text; buttons and checkbox occupy the same horizontal row |
| `LIGHT_THEME`, `DARK_THEME`, `windows_theme` | Both base themes emphasize the entire label; Windows adds its own selectors, which also need local overrides |
| `ExamGeneratorApp.load_questions` | Calls question_usages and formats every page card's complete history immediately |
| `domain/usage_history.py::format_usage_history` | Produces a semicolon-separated string of exam, class and date |
| `domain/card_data.py` | Named card-data boundary; suitable for presentation-neutral metadata |
| `storage/saved_exams.py::question_usages` | Read-only rows ordered by usage timestamp descending, then usage ID descending |
| `QuestionCard._preview_geometry` | Reads header layout size hint as preview chrome; header changes can regress viewport caps |
| `tests/ui/test_saved_exams_ui.py::test_usage_filter_card_and_delete_warning` | Requires full history in a label; replace that assertion with count plus on-demand details, retaining filter/deletion checks |

Paths above are relative to `prometheus/` unless otherwise stated. The screenshot
matches construction/styling choices, but no visible run was performed during
planning. Do not claim measured speed or compactness yet.

## Design and implementation boundary

1. Extract metadata fallback/field construction out of QuestionCard before
   altering it. Extend the card-data boundary or add a small Qt-free
   `prometheus/domain/card_metadata.py`. Return structured labels/values,
   rather than concatenated HTML. Test missing values, multiple segments,
   all years and literal markup characters outside Qt.
2. Extend `domain/usage_history.py` with count labels and structured history
   entries. Preserve existing date/fallback behavior. UI escapes at the rendering
   boundary if rich labels are used. Prefer separate bold labels/regular values.
3. Add a page-scoped aggregate, e.g. `storage.saved_exams.question_usage_counts`,
   accepting displayed IDs (at most 50). One parameterized grouped SELECT returns
   counts, with zero defaults for requested IDs lacking rows. Count usage records,
   never sum version_count or count distinct exams. Keep existing detail ordering.
   Use the current connection/schema; no stored counters or migration.
4. Pass structured metadata, counts and a read-only history-request callback
   into cards. Replace usage_text at call sites/fixtures; no database lookup
   belongs in QuestionCard. Controller/storage supplies details on demand.
5. Build metadata rows beside a top-aligned narrow column: selection first,
   then expand/edit/duplicate. Size buttons with font metrics/size hints and
   compact local padding. Scope object names/QSS to cards in base themes and
   the Windows override. Avoid a large competing background panel. Use a simple
   below-metadata fallback when side-by-side minimum widths cannot fit; keep
   any new width decision calculation outside the widget, with Qt-free tests.
6. Add a small Qt popup adapter with a scroll area/list, wrapping entries,
   screen-bound geometry, hover handoff, click/keyboard activation, dismissal
   and focus restoration. Qt events/focus/geometry stay in the adapter; entry
   formatting and count semantics stay in the domain. Use existing Qt screen
   and style facilities; do not build a new tooltip framework.
7. Re-read details on each fresh opening, not every pointer movement; close and
   release the popup on card disposal/bank change. Refresh counts via existing
   result refresh after generation/deletion. Errors are visible and retryable;
   failure is not cached as empty history. For aggregate failure, retain the
   previous consistent page and use the existing search error path, not false
   zero counts. A zero count needs no detail read to show its empty message.

Do not redesign preview policy. Recheck `_preview_geometry` after wrapping and
fallback and when expand appears/disappears. Qt layout is UI adaptation; new
presentation/state rules must not be added inside widget classes.

## Verification

Use in-memory SQLite and synthetic content with isolated app config. Never
open a personal bank or use the owner's normal configuration. No `.db` file is
needed. Characterize affected code before extraction; demonstrate failing
behavior regressions before implementing the requested changes.

- Domain: fields/fallbacks, literal markup, multiple segments, dates, count
  labels and independent structured entries.
- Storage: repeated generations of one exam on the same date; several versions
  count once; zero uses; page subset isolation; stable ordering; save/duplicate
  and cancelled/failed export add no uses; deletion retains existing semantics.
  Compare each aggregate count to detail length.
- UI: no detail reads before inspection; one aggregate per result page; no
  other-page prefetch; errors/retry/disposal/bank switching. Use stable object
  names instead of the first QLabel found in a card.
- Geometry: identical metadata with 2/1,000 uses; long names/unbroken strings;
  narrow/default/wide widths, including a 640-logical-pixel standalone card and
  below-column-fit fallback; keyboard access; screen-edge popup placement and
  scrolling to the oldest use.
- Integration: selection across pages/filters, selected-only, edit/duplicate,
  answers/images; rerun 009/010 visible growth, containment, shrinkage and
  next-card reflow with both header modes.

Run targeted tests, existing saved-exam/pagination/preview regressions, then full
pytest. Record actual commands/results. Visually inspect synthetic UI on
Windows/macOS, light/dark and representative display scaling: real hover,
popup scrolling, keyboard inspection and preview dragging. Save before/after
evidence. Offscreen results do not establish native acceptance.

## Delivery and constitution check

Write `acceptance.md` with fixtures, environment, tests, measurements and pending
checks. With implementation, update BL-042/KD-21, the 006 presentation
cross-reference and roadmap. Preserve 006's historical completed tasks; 011
supersedes only its inline-history presentation. No data-model/release change.

| Principle | Compliance |
|---|---|
| I / II | Read-only queries, synthetic in-memory tests, offline, no migration or personal bank writes |
| III | Question, answer key and export content preserved |
| IV | Draft spec precedes implementation; baseline changes with actual delivery |
| V | Extract changed formatting first; domain/storage rules tested outside Qt; adapters stay thin |
| VI / VII | Existing dependencies; scoped layout; Portuguese UI, English code/docs |

## Complexity tracking

No exception requested. A scrollable popup is justified because an unbounded
native tooltip cannot expose long history reliably. Bulk counts plus deferred
details replace eager histories without adding caching infrastructure.
