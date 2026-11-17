# Feature specification: Optional source-year range

**Folder**: `008-source-year-range` | **Status**: Draft | **Created**: 2026-11-16
**Fixes**: KD-18 | **Prerequisite**: 007
**Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

## Why

Teachers need to find questions published during a period rather than only
one exact year. The owner's requested example is "Desde: 2022" with no upper
bound: include every question whose source year is 2022 or later. Source year
is distinct from school grade/year and the source-name filter.

## User stories and acceptance scenarios

### US1 — Search with either or both year bounds (P1)

The "Ano da Fonte:" section replaces its single exact-year input with two
labeled text fields, "Desde" and "até". Both are optional.

For questions with source years 2019, 2021, 2022, 2023, 2024 and 2025:

| Desde | até | Included source years |
|---|---|---|
| empty | empty | All, including questions with no valid numeric year |
| 2022 | empty | 2022, 2023, 2024, 2025 |
| empty | 2022 | 2019, 2021, 2022 |
| 2022 | 2024 | 2022, 2023, 2024 |
| 2022 | 2022 | 2022 only |

1. **Given** these bounds, **when** I apply filters or press Enter in either
   year field, **then** those inclusive results appear on page 1, combined
   with the other currently entered search criteria.
2. **Given** a source-year range and a school-year filter, **when** I apply
   them, **then** results satisfy both; grade labels are never compared with
   source-year numbers.
3. **Given** results spanning multiple pages, **when** I navigate, **then**
   both the total and every page reflect the last applied range.
4. **Given** selected questions outside the range, **when** I apply it, **then**
   they remain selected for the exam. Selected-only browsing ignores the range.

### US2 — Understand invalid input without losing the current view (P1)

1. **Given** "Desde: 2024" and "até: 2022", **when** I apply filters,
   **then** I see "O ano em 'Desde' deve ser menor ou igual ao ano em 'até'."
   The app does not silently swap bounds, clear the result set or change page.
2. **Given** an input such as `202x`, `2022.5`, `-2022` or `0`, **when** I
   apply it, **then** I see "Informe um ano inteiro entre 1 e 9999 ou deixe o
   campo vazio." and the previous applied search and selection remain intact.
3. **Given** surrounding whitespace such as ` 2022 `, **when** I apply it,
   **then** it is treated as 2022. Empty/whitespace-only fields are unbounded.

### US3 — Keep legacy year text intact (P1)

1. **Given** stored values `2022`, ` 2022 `, `2022/2023`, `c. 2022`, `s/d`,
   empty and NULL, **when** I search from 2022 to 2022, **then** only the first
   two match. A year is never guessed from a prefix, suffix or interval.
2. **Given** the same rows, **when** I clear both bounds and apply filters,
   **then** all remain findable subject to the other filters. Stored values
   and displayed metadata are unchanged.

## Requirements

- **FR-001** Replace only the exact source-year search input. Do not add an
  additional exact-year control or change registration, source name, school
  year, difficulty, category, text or type controls.
- **FR-002** Each bound is independently optional, inclusive and numeric;
  equal bounds reproduce exact numeric-year search. Proposed valid years are
  positive decimal integers 1–9999; future years are allowed. Whitespace is
  ignored; decimal points, signs and arbitrary text are invalid. Leading zeros
  are interpreted numerically rather than lexicographically.
- **FR-003** Existing stored free text is interpreted for comparison only
  when its entire trimmed value is a valid year under FR-002. Unknown,
  malformed and out-of-range stored years match only when no bound is active.
  No stored year is converted, corrected, rewritten or dropped.
- **FR-004** Validate the whole range before replacing applied filters,
  requesting results or changing selected-only mode. On validation failure,
  retain the current page, result total, mode and selection.
- **FR-005** Range predicates apply before pagination and use identical
  semantics for count and page queries. Query input is parameterized.
- **FR-006** Accessible labels and tooltips identify source year and explain
  that either field may be left empty. Help includes lower-only, upper-only
  and two-bound examples. UI text is Brazilian Portuguese.
- **FR-007** This iteration is read-only and has no migration, new persistent
  column or new dependency. Spec 005's future numeric-storage mapping question
  remains open; range filtering does not require answering it.

## Success criteria

Every table case and scenario above passes, including combined filters and
page boundaries. Automated checks compare database contents before/after a
search and prove that no write statements are issued by range filtering.

## Out of scope

Changing how source years are registered, interpreting approximate/compound
years, offering an unknown-year filter, changing school-year choices,
converting source year to a numeric database column, schema normalization.
