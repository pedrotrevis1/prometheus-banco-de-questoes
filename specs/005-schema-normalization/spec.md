# Feature specification: Schema normalization and real search

**Folder**: `005-schema-normalization` | **Status**: Draft | **Created**: 2026-11-14
**Fixes**: KD-12, KD-13, KD-14, KD-15 | **Plan**: to be written when this iteration starts
**Prerequisites**: 002 (versioned migrations, automatic backup), 003 (single write path for questions)

## Why

Several user-visible limits come from how data is stored: categories are names
inside a text field, alternatives are five fixed columns, labels are stored as
data, and search runs over HTML. This iteration changes the storage so those
limits can be removed, and removes them.

This is the only iteration that rewrites existing data. It is released as v2.0.

## User stories

### US1 — My existing bank is upgraded without loss (P1)

**Acceptance scenarios**

1. **Given** a v1.x bank, **when** I open it with v2.0, **then** it is backed
   up, upgraded, and every question shows the same content, categories,
   classification and answer as before.
2. **Given** a question whose category list contains a name that no longer
   exists, **when** the bank is upgraded, **then** the question is kept and the
   orphan names are listed in an upgrade report.
3. **Given** an upgraded bank, **when** it is opened with v1.x, **then** the old
   app refuses it or the user is warned in advance that it will not work.

### US2 — Filtering by a category includes its subcategories (P1)

**Acceptance scenarios**

1. **Given** a question tagged only "Mitose", a child of "Citologia", **when** I
   filter by "Citologia", **then** the question is found.

### US3 — Categories can be reorganized (P1)

**Acceptance scenarios**

1. **Given** a category, **when** I rename it, **then** all its questions show
   the new name.
2. **Given** a category, **when** I move it under another parent, **then** it
   keeps its questions and subcategories.
3. **Given** two different parents, **when** I create a child named
   "Introdução" under each, **then** both are accepted.

### US4 — Text search finds what I typed (P1)

**Acceptance scenarios**

1. **Given** a statement containing "Revolução **Francesa**" with formatting,
   **when** I search "revolucao francesa", **then** the question is found.
2. **Given** the word only appears in an alternative, **when** I search it,
   **then** the question is found.
3. **Given** I search "span" or "font", **when** no question contains those
   words as text, **then** nothing is found.

### US5 — Multiple-choice questions with fewer than five alternatives (P2)

**Acceptance scenarios**

1. **Given** a new multiple-choice question, **when** I fill four alternatives
   and mark one correct, **then** it is saved and exported with A–D.

## Requirements

- **FR-001** Questions and categories are linked by identifier, many-to-many,
  with referential integrity.
- **FR-002** Category names are unique among siblings, not globally.
- **FR-003** Categories can be renamed and moved; a category cannot be moved
  under itself or its descendants.
- **FR-004** Deleting a category keeps its questions; a question left with no
  category remains findable through an "Sem categoria" filter.
- **FR-005** A category filter matches the category and all its descendants.
- **FR-006** Alternatives are stored as an ordered list per question; a
  multiple-choice question has between 2 and 5, exactly one correct.
- **FR-007** Type, difficulty, segment and school year are stored as stable
  codes; labels exist only in the UI.
- **FR-008** Each question stores a plain-text rendering of its statement and
  alternatives, kept in sync on every save, used for search.
- **FR-009** Text search ignores case and accents and covers statement,
  alternatives and expected answer.
- **FR-010** Questions record creation and last-modification time.
- **FR-011** The upgrade is one atomic migration preceded by an automatic
  backup, and produces a report of anything it could not map.
- **FR-012** Export and search no longer depend on column positions.

## Target data model (conceptual)

| Entity | Key attributes |
|---|---|
| Question | id, type code, difficulty code, segment code, statement (rich), statement text, expected answer (rich), source, source year, created at, updated at |
| School year (per question) | question, year code |
| Alternative | question, position, content (rich), is correct |
| Category | id, name, parent |
| Question–Category | question, category |

Physical design (table and column names, indexes, whether full-text search
uses SQLite FTS5) belongs in the plan.

## Success criteria

- Upgrade of the owner's real banks verified by comparing, per question, the
  rendered card and the exported document before and after.
- KD-12 to KD-15 cannot be reproduced.
- Search over 2,000 questions returns in under one second.

## Out of scope

New question types; saved exams (spec 006); result paging and source-year range
implementation (specs 007 and 008). If those land first, preserve their
behavior while adapting their storage queries/tests to the normalized schema.

## Open questions

- [NEEDS CLARIFICATION: Which segments and years should exist? Today only
  Fundamental II (6º–9º) and Médio. Candidates: Fundamental I (1º–5º), Ensino
  Superior, a free "Outro".]
- [NEEDS CLARIFICATION: May one question belong to more than one segment (e.g.
  9º Ano and 1ª Série)?]
- [NEEDS CLARIFICATION: Should `source year` become a numeric stored value in
  this migration, and how should existing free-text values map? Spec 008 now
  proposes range filtering without changing storage; this numeric-storage
  decision remains unresolved and is not required for those filters.]
- [NEEDS CLARIFICATION: Is breaking compatibility with the v1.x executable
  acceptable (US1 scenario 3)?]
