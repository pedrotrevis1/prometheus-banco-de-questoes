# Tasks: Paged search results

**Plan**: [plan.md](plan.md) | **Status**: Draft

Do tasks in order, one at a time. All boxes are implementation work; none was
completed by the planning-only change. Mark a task only after its validation
passes. Record actual test commands/results for the next agent.

- [ ] T001 Read the handoff, constitution and current roadmap; verify completion of 001/002, resolve their outstanding markers with the owner through their own tasks, and reconcile package paths. Do not mark this task done merely because plans exist.
- [ ] T002 Extract existing search filtering/query and selection-view state into domain/storage modules without behavior changes; add characterization tests for every existing filter, category token boundaries, legacy school-year JSON and selected-only bypass. Keep the widget as a delegate.
- [ ] T003 Add failing pagination/state tests for 0/1/49/50/51/123 results, sparse IDs, invalid pages, stable ordering, applied-vs-edited filters, mode transitions and global selection across pages.
- [ ] T004 Implement the pure fixed-50 page/state contract and connection-local legacy matching functions; verify the tests from T002/T003 and no Qt imports in domain/storage.
- [ ] T005 Add failing in-memory storage tests for identical count/page predicates, scattered category/school-year matches, combined filters, bounded payload rows and selection sets beyond the connection's parameter limit.
- [ ] T006 Implement count and bounded ordered queries under the existing read-transaction conventions; make T005 pass and compare concatenated pages with the complete expected ID list.
- [ ] T007 Add the Portuguese footer with previous/next, direct page selection, page count and range; wire only thin delegates and atomically display successful page results. Add an offscreen regression that fails when all cards are rendered or a failed query mismatches content/count.
- [ ] T008 Wire all apply/mode/selection/bank/write refresh paths, card disposal and scroll reset. Verify hidden selections, last-page deletion/deselection, empty selected mode, no accidental selection signals, and unchanged all-selected-ID export.
- [ ] T009 Measure synthetic 2,500- and 5,000-question datasets with long HTML and images; record reference environment, cold/warm query and render times, card/payload counts, and repeated-page lifecycle results. Profile and revise the plan if the acceptance target is missed.
- [ ] T010 Run applicable tests and manual Windows/macOS, theme, page navigation and multi-page exam checks; update Help, BL-041/043/044, KD-16, architecture and roadmap to the behavior actually delivered. Do not claim unperformed platform checks passed.
