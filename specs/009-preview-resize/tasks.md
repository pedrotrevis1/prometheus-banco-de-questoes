# Tasks: Stable question-preview resizing

**Plan**: [plan.md](plan.md) | **Status**: In progress

Do tasks in order, one at a time; mark only after validation. The owner confirmed the growth affects the card/page content in either preview state; synthetic reproduction is recorded separately.

- [x] T001 Read the handoff, spec/plan and preceding iteration results; 008 is implemented and owner-checked on macOS, with Windows and detailed platform checks pending. Located shared resize callers.
- [x] T002 Build an isolated in-memory/synthetic search-tab fixture; reproduce the symptom and record exact environment, event sequence and geometry evidence. If it cannot be reproduced, ask the owner for the missing conditions and keep this task unchecked.
- [x] T003 Add an automated geometry/event regression that fails against the reproduced implementation; distinguish normal card reflow from outer-window/sidebar/footer growth or unintended scrolling.
- [x] T004 Extract existing sizing/state calculations unchanged into a Qt-free domain module with characterization tests; retain only event, measurement and geometry operations in the UI adapter.
- [x] T005 Add failing policy tests for drag origin, minimum/viewport cap, compact/expanded/manual precedence, repeated notifications and external viewport shrink; implement the spec's policy and pass them.
- [x] T006 Apply the smallest evidence-backed layout/event fix, including idempotent auto-fit, manual precedence and drag cleanup; make T003 pass without freezing the main-window size or changing rich content.
- [x] T007 Run offscreen scenarios for 1/50 cards, short/long/image content, inner/outer scrollbar transitions, outside release, page disposal and shared registration/tree handles; run applicable 007/008 regressions.
- [ ] T008 Manually verify the reported symptom on Windows/macOS and light/dark themes with repeated drags and window resizing; record actual coverage and root-cause evidence rather than inferring platform success.
- [x] T009 Update BL-042, KD-19, architecture and roadmap to the behavior delivered; document test results, reproduction and any remaining limitation for the next chat.
