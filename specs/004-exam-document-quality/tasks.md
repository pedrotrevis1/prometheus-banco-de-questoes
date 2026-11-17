# Tasks: Exam document quality

Work in order; mark each task only when its verification passes.

- [x] T001 Add backup-protected schema 2 → 3 migration for the persistent keep-alternative-order flag; test legacy rows, backup and rollback.
- [x] T002 Add the flag to tested question data/persistence and registration/edit/duplicate UI, preserving existing data.
- [x] T003 Extract and test version generation, chosen order, answer remapping, protected questions and pairwise distinctness.
- [x] T004 Extract image preflight and rendering into export code; test supported/missing/remote images, question IDs, proportional dimensions and explicit warning before output.
- [x] T005 Handle locally readable pasted images and warn about unsupported ones; test using synthetic Qt clipboard data without network access.
- [x] T006 Extract and test DOCX construction: chosen order, numbered versions, matching answer keys, page numbers, separate answer file and no school header.
- [x] T007 Wire generation UI for question order, preflight, distinct versions and separate keys; ensure overwrite confirmation and partial-failure reporting.
- [x] T008 Verify integrated output, edit/duplicate/selection and existing regressions; update help, baseline, architecture and roadmap.
- [ ] T009 Manual macOS, Windows and Word checks remain pending; automated tests use synthetic content and offscreen Qt.

## Ordered review follow-up

- [x] R001 Reproduce and fix exact pasted image source replacement, including clipboard-to-DOCX regression.
- [x] R002 Reproduce and fix visually identical version detection, including publication and answer-key checks.
- [x] R003 Reproduce and fix stored image height handling and proportional sizing, using the owner's width-precedence decision.
- [x] R004 Update baseline and run the complete suite; record remaining visual and platform checks. The suite passed 237 tests; macOS Quick Look rendered a synthetic exam and separate key for visual inspection. Interactive Word and Windows checks remain pending (T009).
