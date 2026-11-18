# Roadmap

Last updated: 2026-11-17

Follow the dependencies and the ordered tasks within each iteration. The first
unfinished iteration is 001, currently in progress.
New planning documents do not mean that prerequisites have been implemented.

| # | Spec | Goal | Depends on | Status |
|---|---|---|---|---|
| 000 | [baseline](../specs/000-baseline/spec.md) | Document the released v1.1 behavior | — | Done |
| 001 | [project-foundation](../specs/001-project-foundation/spec.md) | Make the project buildable, testable and versioned, with no behavior change | — | In progress (platform checks complete; T004 open) |
| 002 | [data-safety](../specs/002-data-safety/spec.md) | Reduce ways to lose or misplace a question bank | 001 foundation | Done |
| 003 | [question-editing](../specs/003-question-editing/spec.md) | Edit and duplicate existing questions | 002 | Done |
| 004 | [exam-document-quality](../specs/004-exam-document-quality/spec.md) | Version labels, faithful images, chosen order and answer keys | 001 | Done |
| 005 | [schema-normalization](../specs/005-schema-normalization/spec.md) | Relational categories and alternatives, real text search | 002, 003 | Draft |
| 006 | [saved-exams-and-history](../specs/006-saved-exams-and-history/spec.md) | Save exams, see where each question was used | 005 | Draft |
| 007 | [search-pagination](../specs/007-search-pagination/spec.md) | Browse 50 question cards per page with bounded content reads and persistent selection | 001, 002 | Done |
| 008 | [source-year-range](../specs/008-source-year-range/spec.md) | Optional inclusive "Desde" / "até" source-year filtering without rewriting legacy values | 007 | Done |
| 009 | [preview-resize](../specs/009-preview-resize/spec.md) | Reproduce and fix question-preview resizing without stretching the outer UI | 008 (execution sequence) | Done |

## Owner-requested search fixes (2026-11-16)

The owner requested plans for these three issues and confirmed 50 results per
page and that the resize symptom concerns a question-card preview. Specs
007–009 are implemented with platform checks complete. See
[the agent handoff](search-tab-fixes.md).

Proposed next priority after 001/002: **007 → 008 → 009**, before the broader
feature work in 003–006. Their higher numbers identify new specs, not a need
to wait for 006. This sequence is implemented; 005 and 006 remain Draft. The owner chose to retain the existing bulk deletion behavior, including
selected questions hidden by a filter.

007/008 do not require 005's schema normalization: paging uses the existing
schema and year ranges interpret stored text without a migration. When 005 is
implemented, preserve these public contracts and adapt their query tests.

## Why this order

- **001 before 002.** The safety fixes must ship with tests (constitution V),
  and today nothing can be tested without launching the GUI. 001 is small and
  changes no behavior.
- **002 before everything else that writes data.** It introduces schema
  versioning and automatic backups, which every later migration relies on.
- **003 before 005.** Editing is the most-missed feature and is cheap on the
  current schema; 005 then migrates one well-understood write path.
- **004 is independent** of 002/003 and can be done in parallel or earlier if
  exam output matters more to the owner.

## Planned release

| Release | Contents |
|---|---|
| v2.0.0 | Implemented work in 001–004 and 007–009, plus 005 (schema change) and 006 |

The owner skipped the previously suggested v1.2.0 and v1.3.0 releases and plans
to implement 005 and 006 before building v2.0.0. The version bump, build and tag
for v2.0.0 remain future release work.

On 2026-11-17, the owner confirmed that the implemented functionality works on
Windows and macOS and requested that all platform checks be marked complete.
The owner also verified the exported files in Word, noting unusual formatting
when exporting tables; its cause remains unconfirmed. Release work remains open.

## Backlog (no spec yet)

- Import/export of question packs to share between colleagues.
- Real equation support (fractions, roots) exported as Word equations.
- More question types (true/false, matching, numeric).
- Persist the chosen theme between sessions.
- Preserve tables and lists from pasted content in the exported exam.
