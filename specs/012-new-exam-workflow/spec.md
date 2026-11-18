# Feature specification: Start a new exam

**Folder**: `012-new-exam-workflow` | **Status**: Draft | **Created**: 2026-11-18
**Prerequisites**: 006 saved exams; 007/008 search state; execute after 011
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)
**Handoff**: [card-and-new-exam-workflow.md](../../docs/card-and-new-exam-workflow.md)

## Why and owner decision

The third tab offers open/save/save-as/rename/duplicate/delete, but no action
to detach from the current exam and start an empty selection. The owner reports
having to restart between preparing a 2ª Série exam and a new 3ª Série exam.

On 2026-11-18 the owner chose: **start completely fresh**, with empty selection,
"Sem turma", default generation options and search filters, returning to search.
Unsaved changes offer Save/Discard/Cancel; existing saved exams are preserved.

## User stories and acceptance scenarios

### US1 — Begin another exam without restarting (P1)

1. **Given** an open bank and an unchanged saved exam, **when** I click
   "Nova prova" in the third tab, **then** the app starts a fresh unnamed
   draft without a discard prompt, switches to "Buscar e Selecionar Questões"
   and shows the unfiltered first page with no selected questions.
2. **Given** questions selected across hidden filters/pages or selected-only
   browsing, **when** the transition is authorized, **then** every selected ID
   and the exam order are cleared, selected-only mode ends and its toggle resets.
   No hidden selection survives for a later export or bulk deletion.
3. **Given** that I generated an exam for 2ª Série, **when** I start a new
   exam, select a 3ª Série filter and different questions, and save/generate it,
   **then** it is a separate named exam. The earlier exam can be reopened with
   its saved questions, settings, arrangements and usage history intact.

### US2 — Protect unsaved work (P1)

1. **Given** a new or existing draft with changes to questions, order, class
   or generation settings, **when** I click "Nova prova", **then** a prompt
   identifies that unsaved changes to the current exam will be replaced and
   offers "Salvar", "Descartar" and "Cancelar"; Save is the default.
2. **Given** that prompt, **when** I choose Save, **then** the existing save
   workflow completes before resetting. A saved exam is updated; an unnamed
   draft requests a name. A successful save is followed by the fresh draft.
3. **Given** Save, **when** I cancel naming or saving fails, **then** the new
   exam does not start. Selection/order/options/class/filters/view and the
   current exam identity remain available; an error is reported on failure.
4. **Given** that prompt, **when** I choose Discard, **then** only the current
   in-memory exam changes are discarded. Its last saved state and all usage
   records remain. Choosing Cancel preserves the whole current view and draft.
5. **Given** an unchanged or already fresh draft, **when** I click "Nova prova"
   repeatedly, **then** there is no unnecessary save prompt, new saved row or
   usage record. Fresh defaults are still applied, including edited filters.

### US3 — Reset all related controls consistently (P1)

1. **Given** any exam options and applied or unsubmitted filter edits,
   **when** a new exam starts, **then** both form values and effective search
   state match the reset table below. Invalid old year-range text does not
   prevent the reset. Search starts at the top of page 1, or its normal empty
   result state if the bank contains no questions.
2. **Given** a fresh draft, **when** I return to the third tab, **then** it
   displays "Prova aberta: nova prova (não salva)", no question-order entries,
   the default settings and "Sem turma". The saved-exam picker's selection is
   empty until I choose an exam to open; the picker never identifies the draft.
3. **Given** a fresh draft with no further edits, **when** I close or switch
   banks, **then** no unsaved-exam prompt appears solely because of the reset.
   Selecting questions or changing settings makes the draft dirty normally.
4. **Given** no open bank, **when** the third tab is shown, **then** "Nova prova"
   is disabled. It does not create a bank or reopen the last bank.

## Reset contract

| State | Fresh value |
|---|---|
| Open saved-exam ID | None; the next Save cannot overwrite the earlier exam |
| Selected questions and explicit order | Empty, including hidden pages/filters |
| Saved-exam picker | No selected exam; existing entries remain available |
| Class | "Sem turma"; managed classes remain in storage |
| Multiple versions | Off; effective export count 1 |
| Version-count control | 2, disabled while multiple versions is off (current startup default) |
| Shuffle questions / alternatives | Both off; enabled state follows existing multiple-version behavior |
| Include answer key | On |
| Separate answer-key file | Off; enabled states consistent with answer inclusion |
| Category checkboxes, including "Sem categoria" | All unchecked, meaning no category restriction |
| Category-tree search text | Empty; previously hidden category nodes visible again |
| Statement-text / source search | Empty |
| Source-year lower / upper bounds | Both empty |
| Difficulty / school year / question type | Only each respective "Todas" / "Todos" option checked |
| Usage filter / date | "Todas"; date reset to today's local date and disabled |
| Applied search and pending filter values | Same unrestricted defaults, even after invalid pending input |
| Selected-only flag and toggle | False, normal label, disabled with zero selection |
| Page and result scroll | First page, top; normal zero-result footer if empty |
| Selection count / selection-dependent actions | Zero; browse-selected and bulk-delete disabled |
| Dirty snapshot | Equals the fully initialized new draft |
| Active tab / focus | Search tab; focus statement-text search field |

The current bank, discipline, theme, question editor contents and managed
categories/classes are preserved. "Start fresh" concerns exam preparation and
search filters; it does not restart the app or discard an edited question.
Preview heights follow their existing non-persistent lifetime when cards reload.

## Requirements

- **FR-001** Expose a visible "Nova prova" action in the third tab, separate
  from "Duplicar" and "Salvar como". Keep saved-exam actions reachable without
  extending an already crowded single row: use a separate draft action row
  and, where needed, two rows for existing saved-exam controls.
- **FR-002** Run the unsaved-work guard before mutating any draft, search or UI
  state. Preserve existing close/bank-switch/open guards. A successful Save may
  write through existing persistence; the reset itself is in-memory/read-only.
- **FR-003** Apply the complete reset contract together. Do not reset only the
  visible checkboxes or current page. Shared selection references must remain
  consistent with domain search state.
- **FR-004** Clearing current exam identity prevents reuse of earlier
  arrangements. Save/generation use existing naming, validation and history
  rules; only a successful later generation records new usage.
- **FR-005** Reset never deletes/rewrites saved exams, questions, classes,
  usages, arrangements, output documents or database files. Discarding dirty
  work identifies what is discarded and requires the explicit Discard choice.
- **FR-006** If the post-reset result refresh fails, report the error and keep
  the new draft empty with a coherent empty/error result area and retry action.
  Do not retain old selected cards/counts or silently restore the old exam.
  A successful save before that error remains saved.
- **FR-007** No migration, new dependency, automatic empty-draft save, usage
  entry, document generation or new database creation on "Nova prova".

## Success criteria and scope

All scenarios pass, including Save success/cancel/failure, Discard, Cancel,
hidden selections, pending invalid filters, empty bank, no bank and repeated
reset. The owner can complete the 2ª Série → 3ª Série workflow without a restart
and reopen both saved exams. Record core/UI tests and visible native checks in
`acceptance.md`.

Out of scope: multiple simultaneously open drafts, autosave/recovery, templates,
changing existing save/duplicate/delete semantics, rewriting export logic and
resetting question registration. This is a planning proposal; only the stated
reset preference has been explicitly confirmed by the owner so far.
