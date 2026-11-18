# Tasks: Paged search results

**Plan**: [plan.md](plan.md) | **Status**: In progress

Do tasks in order, one at a time. Mark a task only after its validation
passes. The owner marked platform checks complete on 2026-11-17.

- [x] T001 Read the handoff, constitution and roadmap; verify 001/002 implementation is merged and reconcile package paths and the owner’s bulk-delete decision. Windows verification and release tasks remain pending by owner direction.
- [x] T002 Extract existing search filtering/query and selection-view state into domain/storage modules without behavior changes; add characterization tests for every existing filter, category token boundaries, legacy school-year JSON and selected-only bypass. Keep the widget as a delegate.
- [x] T003 Add failing pure pagination/state tests for 0/1/49/50/51/123 results, invalid pages, applied filters, mode transitions and global selection. Sparse IDs and ordering are covered in the storage tasks.
- [x] T004 Implement the pure fixed-50 page/state contract and connection-local legacy matching functions; verify the tests from T002/T003 and no Qt imports in domain/storage.
- [x] T005 Add failing in-memory storage tests for identical count/page predicates, scattered category/school-year matches, combined filters, bounded payload rows and selection sets beyond the connection's parameter limit.
- [x] T006 Implement count and bounded ordered queries under the existing read-transaction conventions; make T005 pass and compare concatenated pages with the complete expected ID list.
- [x] T007 Add the Portuguese footer with previous/next, direct page selection, page count and range; wire only thin delegates and atomically display successful page results. Add an offscreen regression that fails when all cards are rendered or a failed query mismatches content/count.
- [x] T008 Wire all apply/mode/selection/bank/write refresh paths, card disposal and scroll reset. Verify hidden selections, last-page deletion/deselection, empty selected mode, no accidental selection signals, and unchanged all-selected-ID export.
- [x] T009 Measure synthetic 2,500- and 5,000-question datasets with long HTML and images; record reference environment, cold/warm query and render times, card/payload counts, and repeated-page lifecycle results. Profile and revise the plan if the acceptance target is missed.
- [x] T010 Automated tests, an offscreen multi-page exam check, Help, baseline, architecture and roadmap are updated. The owner confirmed Windows and macOS functionality and marked platform checks complete on 2026-11-17.

## Review follow-up

- [x] R001 Reproduce the invalid schema benchmark, use current migrations, surface errors, validate every page and rerun rich/light measurements.
