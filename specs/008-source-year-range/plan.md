# Implementation plan: Optional source-year range

**Spec**: [spec.md](spec.md) | **Status**: Draft | **Created**: 2026-11-16

## Approach

Extend 007's applied-filter object and storage predicate builder. In the
current monolith, the anchors are `txt_search_source_year` inside
`setup_tab_search`, the exact `ano_origem = ?` condition in `load_questions`
and the search paragraph in `show_help`. Find their post-extraction equivalents
first. Avoid adding a second search path inside the main-window class.

## Domain and storage changes

- Add a pure `prometheus/domain/source_years.py` (or extend an equivalent)
  that parses an optional bound and an entire stored value, returns an integer
  or no comparable year, and validates lower <= upper. The rules are explicit
  in the spec: trimmed ASCII decimal digits, value 1–9999, no guessed prefix.
  Invalid user input produces a structured validation error; invalid stored
  metadata produces no comparable value, not a runtime search failure.
- Add `source_year_from` and `source_year_to` optional integers to 007's
  immutable filter model. Validate before committing the applied-filter
  snapshot or changing view mode/page. Do not cap to the current calendar year.
- Keep `ano_origem` as TEXT. Register a connection-local conversion function
  backed by the same tested parser. It returns an integer or SQL NULL. Compare
  numerically with parameterized `>= ?` / `<= ?` only for supplied bounds.
  With no bounds, omit both conditions so unknown-year questions remain visible.
- Do not use `CAST(ano_origem AS INTEGER)` alone: SQLite accepts an integer
  prefix of strings such as `2022/2023`. This would invent a source year.
  Do not use lexical text comparison or a partial digit-pattern test.
- Count and page queries reuse the same predicate builder. Selected-only mode
  bypasses both year predicates just as it bypasses the other search filters.
- Respect storage connection ownership introduced by 002/007. Do not open a
  new bank connection, create an index or update the schema for this feature.

## UI changes

Replace the single exact-year QLineEdit with two QLineEdits under the existing
"Ano da Fonte:" heading. Add visible "Desde" / "até" labels, associate them
with their inputs for accessibility, and show examples in tooltips. Keep the
filter sidebar usable at smaller window sizes. Either input's Enter signal
uses the same Apply action as "Filtrar Questões".

The handler gathers raw strings, calls the domain validator, translates its
error code to the Portuguese spec message, and focuses the relevant input.
It commits the entire new filter snapshot only after validation. No parsing
rule, SQL expression or selection mutation belongs in this widget handler.

Update Help in the same behavior change: remove the statement that the source
year must correspond exactly to the stored text; explain inclusive bounds and
equal bounds for an exact numeric year. Registration Help remains unchanged.

## Validation

Use plain pytest for domain tables covering empty/whitespace, lower-only,
upper-only, equal/inverted bounds, limits 1/9999, 0/10000, signs, decimal
fractions, Unicode non-ASCII digits, leading zeros and very long digit input.
Reject invalid input safely without relying on unlimited integer conversion.

Use in-memory SQLite for numeric comparisons, trimmed legacy strings,
NULL/empty/malformed values, combined source/category/school-year filters and
more than 50 matches across page boundaries. Assert the ordered IDs and totals
match the spec, that searches issue no writes and leave all raw values intact.

Offscreen UI integration verifies labels, Enter from either field, one Apply
request per action, page reset only for a valid Apply, selected-only mode
unchanged after invalid Apply, edited-vs-applied bounds during page navigation,
and persistence of hidden selected IDs. Use the injected fixture from 007.
Tests must fail against the former exact-equality search.

## Constitution check

| Principle | Compliance |
|---|---|
| I / II | Read-only interpretation; no database file creation or data rewrite; offline |
| III | Selection and generated exams remain independent of visibility |
| IV | Spec before behavior; update BL-040 and KD-18 when implemented |
| V | Parsing/validation in domain; query predicates in storage; regression tests |
| VI / VII | Existing dependencies only; Portuguese input/help/error text |

## Complexity tracking and reference

A small connection-local conversion function avoids a migration and shares the
same parsing rules with validation. Direct casting is simpler but incorrect
for existing free text; numeric storage remains a separate spec 005 decision.
SQLite documents this prefix conversion behavior in its
[CAST expression reference](https://www.sqlite.org/lang_expr.html#castexpr).
