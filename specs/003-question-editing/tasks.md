# Tasks: Question editing

Complete tasks in order and mark each only after its verification passes.

- [x] T001 Add migration 1 → 2 for a nullable last-modified timestamp; test legacy preservation, automatic backup and failure rollback with temporary fixtures.
- [x] T002 Extract question validation, serialization and persistence into tested Qt-free domain/storage modules, preserving registration behavior and rich HTML.
- [x] T003 Add tested edit/duplicate state, dirty snapshots, timestamp updates and missing-category handling.
- [x] T004 Add card actions and registration edit/duplicate/cancel flows; preserve selection, filters and unchanged rich content; add offscreen regression tests.
- [x] T005 Protect unsaved forms on editing another question, switching discipline and closing; add offscreen tests for cancellation and confirmation.
- [x] T006 Route toolbar formatting and equations to the last focused supported editor; add offscreen tests for statement, alternatives and expected answers.
- [x] T007 Display last-modified time on cards and verify migrated legacy and newly saved questions.
- [x] T008 Verify rich content and images survive an unchanged edit and export; run the full suite and update baseline, help, architecture and roadmap.
- [ ] T009 The owner checked question editing on macOS and reported it worked. Other manual macOS flows, Windows and theme checks remain pending.

## Ordered review follow-up

- [x] R001 Reproduce and fix edit-session state across successful, failed and cancelled bank changes; cover switch, create, link and remove flows.
- [x] R002 Reproduce and fix transaction leakage after failed question writes and commits; cover insert, update and retained UI form state.
- [x] R003 Reproduce and correct the 007 pagination benchmark, then rerun rich and light datasets.
- [x] R004 Verify and correct the baseline toolbar description.
