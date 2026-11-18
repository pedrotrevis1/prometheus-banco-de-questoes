# Acceptance: saved exams and history

**Review status:** The confirmed class-selection and arrangement-preservation
issues pass the independent reproductions and permanent regression tests.

Automated verification covers saving and opening exam selections and options,
managed classes, the save/discard/cancel decision, duplication without usage,
recorded usages, inclusive date filtering, deletion warnings, regeneration with
current content and answer keys, incompatible arrangements, edited or missing
questions, and backup-protected migration from schema 5. The full pytest suite
runs offscreen and does not establish Windows or macOS desktop acceptance.

Platform checks and the v2.0.0 build and release remain separate follow-up work.

## Review-fix verification

- All four independent review reproductions pass against the working tree.
- Permanent tests cover multiple classes, no class, exam management, class
  deletion and retained usage names; presentation changes and current answers;
  incompatible edits; cancelled and failed exports; legacy arrangements; and
  intentional configuration changes.
- The full suite passed: 354 tests, using synthetic test banks and offscreen Qt.
- Initial Git inspection found merge `35f6b97` contains only a
  `.gitignore` change relative to its first parent. The 005 implementation is
  still staged, while 006 and review-fix work includes unstaged and untracked
  files. Both must be included when preparing an eventual commit.

## Source release preparation

The owner authorized committing, pushing and merging all reviewed 005/006
work, including the fixes, and then explicitly excluded app builds. The
`006-saved-exams-and-history` source-preparation branch includes the complete
implementation and version 2.0.0, rather than relying on the incomplete earlier
merge. The full suite was rerun before committing: 354 tests passed. Windows/macOS packaging and
executable acceptance, release publication and the release tag remain pending.
