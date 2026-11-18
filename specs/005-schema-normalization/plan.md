# Implementation plan: Schema normalization

**Spec**: [spec.md](spec.md) | **Status**: Complete | **Prerequisites**: 001–003, 007–008

## Approach

Upgrade banks from schema version 3 in one transaction following the existing
automatic backup, after an explicit incompatibility warning. Preserve question
IDs, rich content, category hierarchy, question order, and all original values
that cannot be mapped. Surface a report identifying affected questions and values.
Do not proceed when the migration or backup fails. A new bank starts directly on
the current schema without a migration warning.

The normalized model has questions with stable kind and difficulty codes,
independent question–segment records, question–year records with segment and year codes, ordered alternatives with a
correct flag, categories keyed by ID, and question–category links. Source years
use an integer when the existing strict range parser accepts them; retain original
text separately so unmappable values and formatting are not lost. Preserve any
unknown legacy values in migration data and report them, rather than guessing.
Store creation and modification timestamps without inventing historical dates.
Use a plain-text search representation generated from rich content with the
standard library; normalize case and accents at query time. Use explicit column
names and named records at storage boundaries, including export.

Category sibling uniqueness, moves, descendant filtering, and deletion semantics
belong in tested storage/domain functions. Connect the UI to these functions and
add selection of both supported segments and two to five alternatives. Preserve
pagination, source-year range filtering, selection and export behavior from
007/008. Adapt callers together with the migration so an intermediate schema is
never presented as a finished implementation.

## Ordered work and verification

See [tasks.md](tasks.md). Tests use temporary banks only, never an owner's bank.
Exercise successful and failed migrations, backup and warning behavior, legacy
values and orphan categories, hierarchy operations, save/search/export and
pagination. Validate acceptance scenarios, then update the baseline and roadmap.
Final acceptance combines an automated comparison of every original question
in the owner's before/after bank copies with owner-led visual card and Word
checks on representative questions. Read the personal banks through SQLite
read-only connections; do not migrate or write to them during verification.
Compare generated exam and answer-key content, and explain intentional test
edits separately from migration differences.

The review follow-up adds schema version 5 through the existing backup and
transaction mechanism. Populate segment records from current normalized years;
for schema-4 questions with no years, recover a known segment from the retained
legacy row. Preserve the raw legacy data, report unmappable classifications, and
do not infer a year. Schema-4 questions with current year assignments use those
current assignments rather than potentially stale archived classification.

## Constitution check

| Principle | Implementation |
|---|---|
| I Data safety | Backup, warning, transactional migration and lossless reporting; no implicit database creation or deletion. |
| II Offline | No network access or service dependency. |
| III Faithful export | Preserve rich content and verify generated exams and keys. |
| IV Spec first | Owner decisions recorded in spec; baseline updated with behavior changes. |
| V Testable core | Domain, storage and export rules are independently tested; UI coordinates them. |
| VI Simplicity | Standard library and existing dependencies only. |
| VII Languages | Stable stored codes; Brazilian Portuguese interface. |

## Risks

Legacy data may contain malformed or unknown values. Preserve and report them;
do not infer a value or silently discard it. SQLite foreign-key handling and
rollback need explicit tests. Old executables may still open a new schema, so
the pre-upgrade warning is required even if the new schema also impedes them.
