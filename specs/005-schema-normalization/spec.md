# Feature specification: Schema normalization and real search

**Folder**: `005-schema-normalization` | **Status**: Verified | **Created**: 2026-11-14
**Fixes**: KD-12, KD-13, KD-14, KD-15 | **Plan**: [plan.md](plan.md)
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
4. **Given** a question classified by a known segment without a school year,
   **when** its bank is upgraded, **then** the segment remains visible without
   inventing a year. Unmappable classification values appear in the upgrade report.

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
4. **Given** checked categories and an active edit or duplication, **when** a
   category is created, renamed or moved, **then** checked IDs and unsaved form
   content remain intact. Deleting categories removes only deleted IDs from the
   checked and applied filters without selecting replacements.

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

- Upgrade of the owner's real banks verified by an automated comparison of
  every original question's IDs, rich content, alternatives, answers, category
  links and classification before and after migration, including generated
  exam and answer-key content. Combine this with owner-led visual checks of a
  varied sample of rendered cards and documents in Word. Explain intentional
  test edits and every reported unmappable value; do not treat them as silent
  migration changes.
- KD-12 to KD-15 cannot be reproduced.
- Search over 2,000 questions returns in under one second.

Final verification results are recorded in [acceptance.md](acceptance.md).

## Out of scope

New question types; saved exams (spec 006); result paging and source-year range
implementation (specs 007 and 008). If those land first, preserve their
behavior while adapting their storage queries/tests to the normalized schema.

## Owner decisions (2026-11-18)

- Keep Fundamental II (6º–9º) and Médio (1ª–3ª Série) as the available years.
- A question may belong to more than one segment.
- Convert source years to numbers and preserve unmappable text separately.
- Compatibility with v1.x executables may be broken; warn the user before upgrading.
- On 2026-11-18, the owner chose to store segments independently of years, so a
  segment can be preserved even when no school year is recorded.
- On 2026-11-18, the owner approved exhaustive automated bank comparison plus
  representative manual card and Word checks for final acceptance, replacing
  a manual visual comparison of every question.
