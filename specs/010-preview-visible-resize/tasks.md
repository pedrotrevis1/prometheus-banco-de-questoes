# Tasks: Visible preview resizing and card reflow

**Plan**: [plan.md](plan.md) | **Status**: Done; owner confirmed all scenarios checked

Work in order, one task at a time. Mark only after its evidence/checks pass.
The owner confirmed that all scenarios were checked.

- [x] T001 Review the constitution, roadmap, current iteration and 009 documents/code/tests; inspect the supplied movie; preserve representative frames and owner reproduction; prepare this spec/plan/tasks and link the open defect in baseline/roadmap/handoff. No runtime reproduction or fix claimed.
- [x] T002 Revalidate the checkout and running app revision; reproduce the same clipping/stationary-next-card symptom with isolated synthetic multiple-choice cards. Record environment and before/during/after/settled geometry. If not reproduced, document attempts and ask for missing conditions before continuing.
- [x] T003 Add and demonstrate a failing regression requiring positive visible-viewport growth below the cap, complete preview/handle containment, positive enclosing-card growth, matching next-card movement and inverse shrinkage. Strengthen the existing zero/zero reflow assertion.
- [x] T004 Establish the measured cause; extract any existing sizing/state calculation that must change into the Qt-free domain module, with characterization tests. Record why the chosen implementation boundary complies with the thin-UI rule; retain policy unchanged if only layout adaptation is needed.
- [x] T005 Implement the smallest evidence-backed fix; pass T003 and any policy tests, preserving 009 bounds, automatic/manual precedence, handle/release behavior, content and outer geometry.
- [x] T006 Verify repeated drags, compact/expanded/manual starts, reflow callbacks, header/usage variations, text/alternatives/images, 1/50 cards, scrolled results, page disposal and shared editor/tree handles. Run applicable 007/008/009 tests and the full suite; record results.
- [x] T007 Verify the visible gesture with real pointer input on macOS and Windows, light/dark themes and representative scaling; save synthetic before/after evidence. Keep missing checks pending and do not infer success from the old sign-off or offscreen assertions.
- [x] T008 Write acceptance.md with root cause, failing/passing regression evidence, geometry and platform results; reconcile BL-042/KD-20, 009 follow-up links, roadmap, handoff and release notes where relevant. Mark Done only when acceptance is complete.
