# Plan: Saved exams and usage history

Extend the normalized bank with a forward migration for managed classes, saved
exam settings and ordered questions, generated arrangements and usage records.
Use the existing backup-before-migration workflow. Keep persistence and version
reconstruction outside Qt and cover them with automated tests. Add thin UI
controls for exam and class management, saving and opening, generation, usage
display and filtering. Verify the acceptance scenarios and update the baseline.

Review fixes preserve class selection when refreshing controls and distinguish
answer-key presentation from arrangement-affecting settings. Retain the last
successful arrangements until a replacement export succeeds; keep that decision
and storage logic outside widgets, with synthetic-bank regression tests.

## Constitution check

Migration preserves existing rows and uses the existing automatic backup. No
network access or new dependencies are introduced. User-facing strings are in
Brazilian Portuguese; domain, persistence and export behavior are tested outside
widgets. Generated answer keys follow current question data. Deletions require
confirmation and identify affected records.

## Complexity tracking

No exception is planned.
