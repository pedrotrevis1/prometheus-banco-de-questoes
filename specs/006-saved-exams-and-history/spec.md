# Feature specification: Saved exams and usage history

**Folder**: `006-saved-exams-and-history` | **Status**: Draft | **Created**: 2026-11-14
**Plan**: to be written when this iteration starts | **Prerequisite**: 005

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
   same questions, order and header fields.
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
2. **Given** a saved exam, **when** I regenerate it, **then** I get the same
   versions (same orders and answer keys) as the first time.

### US4 — Manage saved exams (P2)

**Acceptance scenarios**

1. **Given** the list of saved exams, **when** I rename or delete one, **then**
   the questions themselves are unaffected.
2. **Given** a question used in a saved exam, **when** I delete the question,
   **then** I am warned which exams contain it.

## Requirements

- **FR-001** An exam is a named, ordered set of questions with its header
  fields and generation options, stored in the bank.
- **FR-002** The current selection can be saved as a new exam or over the open one.
- **FR-003** Generating documents from an exam records a usage: date, class,
  number of versions.
- **FR-004** Question cards show the usages of the question.
- **FR-005** Search can filter by never used and by not used since a date.
- **FR-006** Exams can be listed, opened, renamed, duplicated and deleted.
- **FR-007** Regenerating an exam reproduces its versions exactly.
- **FR-008** If a question was edited after an exam was generated, opening
  that exam says so.

## Success criteria

- A teacher can interrupt exam preparation and continue another day.
- A teacher can answer "did 2ª série B already see this question?" from the app.

## Out of scope

Student rosters, grades, answer-sheet correction, item statistics.

## Open questions

- [NEEDS CLARIFICATION: Is "class" (turma) a free-text field on the exam, or a
  managed list?]
- [NEEDS CLARIFICATION: Should a generated exam keep a frozen copy of each
  question's content, so later edits never change a past exam? This costs
  storage but makes FR-007 hold after edits.]
- [NEEDS CLARIFICATION: Should a usage be recorded automatically on every
  generation, or only when the teacher marks the exam as "aplicada"?]
