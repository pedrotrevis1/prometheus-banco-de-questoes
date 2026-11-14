# Roadmap

Last updated: 2026-11-14

Order matters: each iteration assumes the previous ones are done.

| # | Spec | Goal | Depends on | Status |
|---|---|---|---|---|
| 000 | [baseline](../specs/000-baseline/spec.md) | Document the released v1.1 behavior | — | Done |
| 001 | [project-foundation](../specs/001-project-foundation/spec.md) | Make the project buildable, testable and versioned, with no behavior change | — | Draft |
| 002 | [data-safety](../specs/002-data-safety/spec.md) | Remove every known way to lose or misplace a question bank | 001 | Draft |
| 003 | [question-editing](../specs/003-question-editing/spec.md) | Edit and duplicate existing questions | 002 | Draft |
| 004 | [exam-document-quality](../specs/004-exam-document-quality/spec.md) | Header, version labels, faithful images, chosen order | 001 | Draft |
| 005 | [schema-normalization](../specs/005-schema-normalization/spec.md) | Relational categories and alternatives, real text search | 002, 003 | Draft |
| 006 | [saved-exams-and-history](../specs/006-saved-exams-and-history/spec.md) | Save exams, see where each question was used | 005 | Draft |

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

## Suggested releases

| Release | Contents |
|---|---|
| v1.2.0 | 001 + 002 |
| v1.3.0 | 003 + 004 |
| v2.0.0 | 005 (schema change) + 006 |

## Backlog (no spec yet)

- Paged or lazily rendered search results for large banks.
- Import/export of question packs to share between colleagues.
- Real equation support (fractions, roots) exported as Word equations.
- More question types (true/false, matching, numeric).
- Persist the chosen theme between sessions.
- Preserve tables and lists from pasted content in the exported exam.
