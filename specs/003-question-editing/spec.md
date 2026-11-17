# Feature specification: Question editing

**Folder**: `003-question-editing` | **Status**: In progress | **Created**: 2026-11-14
**Fixes**: KD-07 | **Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

## Why

A saved question cannot be changed. A typo, a wrong answer key or a missing
category means deleting and retyping the whole question, images included.

## User stories

### US1 — Correct an existing question (P1)

**Acceptance scenarios**

1. **Given** a question card, **when** I choose "Editar", **then** the
   registration tab opens with every field filled from that question (type,
   difficulty, segment, school years, source, source year, categories,
   statement with formatting and images, alternatives, correct answer or
   expected answer) and the tab clearly shows it is editing question N.
2. **Given** edit mode, **when** I change fields and save, **then** the same
   question (same ID) is updated, validation is the same as for a new
   question, and the search results show the new content.
3. **Given** edit mode, **when** I choose "Cancelar edição", **then** nothing is
   saved and the form returns to new-question mode.
4. **Given** a question selected for the exam, **when** I edit it, **then** it
   stays selected.
5. **Given** a saved edit, **when** the card is displayed, **then** it shows
   when the question was last modified. Legacy questions without a known
   modification time show that the time is unavailable.

### US2 — Not lose work by accident (P1)

**Acceptance scenarios**

1. **Given** unsaved changes in the form (new or editing), **when** I start
   editing another question, switch discipline or close the app, **then** I am
   asked whether to discard them.

### US3 — Create a variant from an existing question (P2)

**Acceptance scenarios**

1. **Given** a question card, **when** I choose "Duplicar", **then** the form
   opens in new-question mode pre-filled with that question's content, and
   saving creates a new question with a new ID.

### US4 — Format alternatives like the statement (P3)

**Acceptance scenarios**

1. **Given** the cursor in an alternative or in the expected answer, **when** I
   use the formatting toolbar or insert an equation, **then** it applies to
   that field.

## Requirements

- **FR-001** Every question can be opened for editing from its card.
- **FR-002** Saving in edit mode updates the existing record; the ID is preserved.
- **FR-003** Edit mode is visually distinct and can be cancelled.
- **FR-004** Changing the type of a question while editing follows the same
  rules as for a new question; content of fields that no longer apply is
  discarded only on save.
- **FR-005** A category that no longer exists is ignored when loading, and the
  user is told which names were dropped.
- **FR-006** Unsaved form changes are protected by a discard confirmation.
- **FR-007** A question can be duplicated into a new, unsaved question.
- **FR-008** Loading and re-saving a question without changes leaves its
  rendered content and its exported exam output unchanged.
- **FR-009** Record and show a last-modified timestamp on each question card.
  Existing questions keep an unknown value until edited; new questions and
  saved edits receive the current timestamp.
- **FR-010** The existing formatting toolbar and equation insertion work on
  the focused statement, alternative, or expected-answer editor.

## Success criteria

- Fixing a typo in a statement takes under 30 seconds from the search tab.
- Round trip (FR-008) verified on questions with images, formatting and equations.

## Out of scope

Edit history or versions of a question; bulk editing (e.g. recategorizing many
questions at once); new question types.

## Owner decisions

- Record and show when a question was last modified.
- Include formatting and equation insertion for alternatives and expected answers.
