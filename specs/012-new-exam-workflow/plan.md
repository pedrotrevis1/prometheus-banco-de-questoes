# Implementation plan: Start a new exam

**Spec**: [spec.md](spec.md) | **Status**: Done | **Created**: 2026-11-18

## Entry and existing boundaries

Use branch `012-new-exam-workflow` after 011 acceptance to avoid concurrent edits
to shared `app.py` and saved-exam UI tests. This is integration ordering; a new
exam does not technically depend on the card redesign. Revalidate the checkout
and begin at the next unchecked task.

| Location | Relevant behavior |
|---|---|
| `app.py::setup_tab_generate` | One picker plus six buttons; no New action; content maximum width 880 |
| `exam_draft` | Collects order/class/six settings; synchronizing order currently has a side effect |
| `confirm_save_exam` | Draft/snapshot comparison and Save/Discard/Cancel inside the widget |
| `save_current_exam`, `open_saved_exam` | Existing save/name/error and restore adapters to preserve |
| Initialization / `init_db` | Defaults and partial resets exist; do not call bank lifecycle code for New |
| `domain/search.py::SearchViewState` | Owns selected-ID set, applied filters, mode and page |
| `domain/exam_order.py::ExamOrder` | Explicit order; synchronization removes stale IDs and appends new IDs |
| `current_search_filters`, `show_filtered_questions`, `load_questions` | Pending vs applied filters, validation and rendering; ordinary query failure retains old cards |
| `update_multi_version_controls`, `refresh_exam_order`, `on_exam_tab_changed` | Derived enabled states and order display |
| `generate_word_doc` | Saves a new/dirty exam before export; gets arrangements by open_exam_id |

`self.selected_ids` aliases `self.search_view.selected_ids`. Replacing only one
set leaves stale selection. Clearing current-page checkboxes is insufficient.
Calling `init_db` also changes bank lifecycle and registration unnecessarily.

## Extract and test before adding the transition

Introduce a small Qt-free `prometheus/domain/exam_session.py` (or a small existing
domain extension) for generation defaults, a fresh draft value, dirty comparison
and the decision to proceed after Save/Discard/Cancel and a save result. Use
ordinary values/enums/dataclasses as useful, not a general workflow framework.
Domain code does not show dialogs or call Qt/storage.

Characterize existing dirty/save guard and defaults first. Extract relevant
rules from `exam_draft`/`confirm_save_exam` before changing them; adapt current
close/open/bank-switch callers without changing behavior. Keep widget reads,
dialogs and existing save calls in thin adapters. Cover `ExamOrder.synchronize`
side effects; do not rely on a draft getter to initialize state by accident.

Share the tested option defaults between startup and New where practical. Add
a tested search reset operation to SearchViewState: clear the existing ID set
in place, exit selected-only, set unrestricted filters and page 1. Use the
normalized or supported legacy filter type appropriate to the bank. Preserve
ordinary filtering/paging's selection-retention behavior.

## Thin UI transition

1. Add `btn_new_exam` / "Nova prova" to a draft action row above saved-exam
   controls. Keep picker/Open together, with save/management on another row if
   needed; do not widen 880-width content to fit a seventh button. Enable only
   with an eligible open bank; recheck bank open/close/failure.
2. Get the domain dirty decision. If dirty, show an explicit current-exam
   save/discard prompt. Use the existing save adapter if requested; proceed only
   on success. Cancel/failed Save returns before identity/filter/mode/page/focus
   changes. Name cancellation is a cancelled save, not permission to reset.
3. Apply fresh domain state: clear shared selection in place and order, detach
   open_exam_id, set class None, apply defaults and set picker index -1 while
   preserving entries. The picker is navigation, never open-draft identity.
4. Reset every form value in the spec table and applied filters. Block relevant
   group/tree signals, then update derived enablement once. Clear category-tree
   text filtering and reveal nodes without changing stored categories. Do not
   parse invalid old year text. Use today's local date for the inactive date
   control; inject a date into pure defaults if needed for testing.
5. Update zero count, browse toggle/text/enablement, bulk-delete enablement,
   order list and fresh-draft label. Recompute a clean snapshot after defaults
   settle. Signal callbacks must not dirty/save an empty draft.
6. Refresh unrestricted page 1, reset scroll and move focus to statement search.
   For no matches show the ordinary empty footer. On refresh failure dispose
   old cards and show a Portuguese empty/error area with explicit retry wired
   to default search. Handle load_questions' old-page retention: that behavior
   suits paging failure, not an authorized and completed new-draft reset.

Retain the zero-selection export guard; it may remain enabled and explain that
questions must be selected. New never automatically saves. A second New is
harmless while still resetting edited filters.

## Verification

Use in-memory SQLite and isolated temporary config as existing saved-exam UI
fixtures do. All data is synthetic. No `.db` file is needed; never exercise
this workflow against the owner's bank/config.

Core tests cover defaults, independent fresh state, dirty changes in each
field, all prompt results, failed/cancelled Save, in-place selection clearing,
order clearing, selected-only exit and unrestricted effective filters. Prefer
meaningful behavior assertions over one test per private helper.

UI/storage integration covers:

- Clean saved exam; dirty named/unnamed drafts; Save success/failure/name cancel;
  Discard/Cancel. Verify the prompt precedes reset and failed Save preserves
  stored last-good state and the current editable draft.
- Multiple pages/hidden selections, selected-only, modified order/class/options.
  Check the full table against both domain and visible state, then clean close.
- Invalid pending year bounds, category text-hidden nodes/restrictions,
  usage/date filters and no results. Reset bypasses obsolete validation and
  restores all "Todos" controls, default effective predicates and first page.
- Compare saved exams/questions, classes, versions, usages and link tables
  before/after clean New or Discard: unchanged. Save may update only the
  explicitly saved exam through its existing contract.
- Generate shuffled/multiple-version A; New; select/save/generate B; reopen
  both. Distinct IDs and independent order/class/options; A keeps arrangements
  and history, B has no use before successful export. Repeated New adds no rows.
- No bank, empty bank, repeated resets, refresh error/retry, preserved editor,
  and picker choice without opening. Keep Open/Save as/Duplicate and existing
  close/bank-switch guards working. Inspect popup disposal/cleared checks from 011.

Run targeted core/New UI tests, existing saved-exam/search/order/normalization
checks, then full pytest; record actual commands/results. Visually verify on
Windows/macOS, both themes and representative scaling: toolbar fit, keyboard
order and the full 2ª Série → 3ª Série workflow without restart. Missing native
checks remain pending, not inferred from offscreen tests or prior sign-off.

## Delivery and constitution check

Write `acceptance.md`. With implementation update BL-043/BL-058, close KD-22,
cross-reference 006's extended lifecycle, and update roadmap/handoff. Do not
claim implementation acceptance in this documentation change.

| Principle | Compliance |
|---|---|
| I | Save/discard/cancel before loss; reset preserves saved data/files |
| II / III | Offline; existing export and arrangement rules retained |
| IV | Spec first; baseline updates accompany delivered behavior |
| V | Extract dirty/default rules first; fresh-state rules tested outside widgets; Qt applies state |
| VI / VII | No dependency/migration/global rewrite; Portuguese UI, English code/docs |

## Complexity tracking

No exception requested. One small domain boundary and existing search/order
objects suffice. Multiple-draft management, undo and autosave are outside scope;
do not refactor every saved-exam operation to implement New.
