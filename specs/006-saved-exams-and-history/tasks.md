# Tasks: Saved exams and usage history

- [x] Resolve owner decisions and document the plan.
- [x] Add migration and tested persistence for classes, exams and usage history.
- [x] Add tested version arrangement persistence and reconstruction.
- [x] Add exam and class management, save/open and unsaved-change prompts.
- [x] Connect generation to saved arrangements and usage recording.
- [x] Add usage display, filtering and question deletion warnings.
- [x] Verify acceptance, update baseline and roadmap, and run the test suite.

## Ordered review fixes

- [x] Preserve the selected class through exam and class control refreshes; add regression coverage.
- [x] Preserve arrangements across presentation-only changes and unsuccessful exports; test deliberate configuration changes and edited questions.
- [x] Verify review reproductions and the full suite, update acceptance and baseline, and document Git readiness.

## Owner-authorized source release preparation (2026-11-18)

- [x] Create `006-saved-exams-and-history` from the current main commit while preserving all staged, unstaged and untracked implementation work.
- [x] Set the application version to 2.0.0 and update the README, release notes and roadmap.
- [x] Verify the complete source and prepare all intended 005/006 implementation and review fixes for commit, excluding personal databases and generated artifacts. The 354-test suite passed; the complete staged change contains 58 intended source, test and documentation files.

Delivery uses a feature-branch commit and pull request, followed by a merge and
synchronization of local main. The actual commit and pull-request records are
the evidence for those Git operations.

The owner explicitly excluded building the apps from this request. Windows and
macOS packaging and executable acceptance, final release publication and the
release tag remain pending; source preparation does not mark those checks done.
