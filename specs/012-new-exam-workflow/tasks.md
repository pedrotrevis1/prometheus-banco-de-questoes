# Tasks: Start a new exam

**Plan**: [plan.md](plan.md) | **Status**: Done; owner confirmed the visual test and authorized T009 closure

Work in order, one task at a time. Check only after its evidence passes.

- [x] T001 Review constitution/roadmap, 006 and 010 documents, draft/search/order/save code/tests; obtain the owner's full-reset preference; prepare spec, plan, tasks and handoff without implementation.
- [x] T002 Revalidate prerequisites/reset contract; reproduce the missing New workflow with synthetic exams and record current state/actions.
- [x] T003 Characterize draft/default/dirty behavior; extract rules into a small Qt-free domain boundary and adapt callers without behavior changes. Verify close/open/bank-switch guards.
- [x] T004 Add failing core regressions; implement fresh-draft/defaults/search reset, preserving the shared selected-ID set, clearing order and leaving ordinary pending/applied search semantics intact.
- [x] T005 Add failing New/guard UI regressions; implement Nova prova, row layout/enablement, Save/Discard/Cancel sequencing, full reset table, clean snapshot, search navigation and focus.
- [x] T006 Implement/test refresh-error/retry handling, no-bank/empty-bank, invalid old filters, repeated New, derived controls and preserved editor. Verify no stale cards, popup or hidden selection remains.
- [x] T007 Verify named/unnamed Save success/cancel/failure and Discard/Cancel preservation; compare saved tables and run two-exam generation/reopen, proving no arrangement/history leakage or automatic empty-draft save.
- [x] T008 Run targeted and existing saved-exam/search/order/normalization/011 UI checks, then full pytest. Record actual commands/results.
- [x] T009 Verify Windows/macOS visible flows, both themes and representative scaling, keyboard use, toolbar fit and 2ª Série → 3ª Série without restart. The owner confirmed the visual test passed and explicitly authorized closing this task; specific platform coverage is recorded in acceptance.md.
- [x] T010 Write acceptance.md; update BL-043/BL-058, KD-22, 006 lifecycle cross-reference, roadmap/handoff. Mark Done only after acceptance. Do not build, publish, merge or tag under this task list.
