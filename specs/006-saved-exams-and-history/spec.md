# Feature specification: Saved exams and usage history

**Folder**: `006-saved-exams-and-history` | **Status**: Implemented | **Created**: 2026-11-14
**Plan**: `plan.md` | **Prerequisite**: 005

## Why

The selection of questions for an exam exists only in memory: closing the app
or switching discipline loses it, and nothing records which questions were
given to which class. Teachers need both to resume work and to avoid repeating
questions with the same students.

## User stories

### US1 — Resume an exam I was building (P1)

**Acceptance scenarios**

1. **Given** questions selected and ordered, **when** I save the exam with a
   name, **then** I can close the app, reopen it, open that exam and find the
   same questions, order, turma and generation options.
2. **Given** unsaved changes to the selection, **when** I close the app or
   switch discipline, **then** I am asked whether to save them.

### US2 — Know where a question was used (P1)

**Acceptance scenarios**

1. **Given** an exam that was generated, **when** I look at one of its
   questions in the search tab, **then** the card shows the exam name, class
   and date of each use.
2. **Given** the search filters, **when** I choose "Nunca usadas" or "Não
   usadas desde <data>", **then** only matching questions are listed.

### US3 — Reuse a past exam (P2)

**Acceptance scenarios**

1. **Given** a saved exam, **when** I duplicate it, **then** I get a new
   editable exam with the same questions and no usage records.
2. **Given** a saved exam, **when** I regenerate it, **then** compatible
   question and alternative orders match the first generation, while content
   and answer keys reflect the current questions.

### US4 — Manage saved exams (P2)

**Acceptance scenarios**

1. **Given** the list of saved exams, **when** I rename or delete one, **then**
   the questions themselves are unaffected.
2. **Given** a question used in a saved exam, **when** I delete the question,
   **then** I am warned which exams contain it.

## Requirements

- **FR-001** An exam is a named, ordered set of questions with its turma and
  generation options, stored in the bank. Documents remain header-free.
- **FR-002** The current selection can be saved as a new exam or over the open one. Spec 012 adds a guarded fresh-draft action that detaches the open exam and resets preparation state.
- **FR-003** Generating documents from an exam records a usage: date, class,
  number of versions.
- **FR-004** Question cards show the usages of the question. Spec 011 replaces the inline presentation with a count and on-demand history; usage records and filters are unchanged.
- **FR-005** Search can filter by never used and by not used since a date.
- **FR-006** Exams can be listed, opened, renamed, duplicated and deleted.
- **FR-007** Regenerating an exam preserves the saved question and alternative orders when compatible. It uses current question content and the current correct answer. If an arrangement is incompatible, the teacher is warned and regeneration is blocked.
- **FR-008** If a question was edited after an exam was generated, opening
  that exam says so.

## Success criteria

- A teacher can interrupt exam preparation and continue another day.
- A teacher can answer "did 2ª série B already see this question?" from the app.

## Out of scope

Student rosters, grades, answer-sheet correction, item statistics.

## Owner decisions

- Classes (turmas) are managed in a list.
- Generated exams use the current question content, rather than frozen copies.
- Every generation automatically records a usage.
- Exports remain header-free; save the exam name, turma and generation options.

## Regeneration after edits

The original ordering is retained, but content and answer keys reflect the current
question. If the saved arrangement no longer fits, warn the teacher and block
regeneration rather than silently changing the arrangement.

## Review-fix acceptance scenarios

- Refreshing exam or class controls retains the selected class. If that class
  was deleted, the selection becomes "Sem turma". Managing another exam does
  not change the open exam's selected class or unsaved settings, and historical
  usage class names remain unchanged.
- Changing answer-key inclusion or placement preserves generated arrangements
  and still blocks incompatible question edits. Cancelling or failing an export
  preserves the previous arrangements and does not record a completed usage.
- When the teacher intentionally changes question selection, order, version
  count or shuffling options, the next successful export establishes new
  arrangements. Cancelling or failing that export retains the previous ones.
