# Tasks: Schema normalization

**Plan**: [plan.md](plan.md). Work in order and check each task when complete.

- [x] T001 Define and test stable codes, lossless legacy mapping, source-year conversion and plain-text search normalization.
- [x] T002 Implement and test the atomic normalized schema migration, preserving all legacy values and producing an upgrade report.
- [x] T003 Add and test the pre-upgrade warning, backup and report presentation in the bank-opening workflow.
- [x] T004 Implement and test category hierarchy operations, sibling uniqueness, descendant filtering and uncategorized questions.
- [x] T005 Implement and test normalized question reads and writes, multiple segments, two to five alternatives and timestamps.
- [x] T006 Adapt and test paginated search, accent-insensitive plain-text matching and source-year ranges.
- [x] T007 Adapt and test exam reads and export with named fields and variable alternatives.
- [x] T008 Connect category and question editing controls to the tested core, including multiple segments and alternative counts.
- [x] T009 Verify acceptance scenarios and regression suite; update the baseline and roadmap. The 317-test suite passed, including offscreen normalized workflows and search over 2,000 questions. On 2026-11-18, exhaustive read-only comparison of all 2,597 original biology questions and their generated exam/answer-key content passed, alongside the owner's manual card and Word checks. The owner confirmed the one edited original question; the only unmappable value was preserved and reported. See [acceptance.md](acceptance.md).

## Review follow-up (2026-11-18)

Reproduced on the current checkout: a segment-only legacy question loses its
displayed segment without a report; renaming a selected category clears both
checked form categories; normalized card data is a padded positional tuple;
the pagination and data-safety UI characterization suites run on schema 3.

- [x] T010 Add failing offscreen regressions and preserve checked category IDs and edit state across tree rebuilds, including search filters and deletions.
- [x] T011 Add a failing regression and replace normalized positional card data with a named record while isolating legacy compatibility.
- [x] T012 Extend schema-4 production regression coverage for pagination, selection, failure handling, editing, bank switching, and exports with two to five alternatives.
- [x] T013 After the owner decides how to represent segment-only classification, add failing regressions and implement lossless forward migration and recovery of schema-4 banks, including reporting and rollback.
- [x] T014 Update the baseline and plans as necessary, verify migration and export integrity, and run the complete suite. Leave real-bank and Word verification pending. The suite passed 317 tests on 2026-11-18.

Final acceptance followed T014: the owner approved exhaustive automated bank
comparison plus representative manual card and Word checks, and T009 is now
complete. The historical pending-verification note in T014 describes that
earlier checkpoint, not the current status.
