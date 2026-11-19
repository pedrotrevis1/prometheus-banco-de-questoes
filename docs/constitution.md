# Prometheus Constitution

**Version**: 1.1.0 | **Ratified**: 2026-11-14 | **Status**: Proposed (awaiting project owner approval)

This document holds the non-negotiable rules of the project. Every spec, plan,
task and code change must comply with it. When a spec and the constitution
disagree, the constitution wins, or it is amended first (see Governance).

## Product statement

Prometheus is a desktop tool that lets teachers build, maintain and reuse a
personal bank of questions and turn selections of them into printable exams.
It is used by one teacher at a time, on their own computer, with no IT support.

## Core principles

### I. The teacher's data is never lost or silently changed

A question bank represents years of a teacher's work.

- No code path may create, overwrite, truncate or delete a database file
  without the user having explicitly asked for exactly that.
- Every destructive action names what will be destroyed and requires
  confirmation.
- Every schema change ships as a forward migration that preserves all existing
  rows, and an automatic backup is taken before it runs.
- Any database created by a released version must open in every later version.

### II. Local-first, offline, private

- The app works fully without a network connection, an account or a server.
- It makes no network requests and collects no telemetry.
- Data lives in files the user owns and can copy, back up and share.

### III. The exam is a legal-grade artifact: no silent degradation

A printed exam with a missing image or a wrong answer key harms students.

- If content cannot be exported faithfully, the user is told which question is
  affected before the file is produced. Content is never dropped silently.
- The answer key always matches the document it was generated with.
- Errors are shown to the user or logged; they are never swallowed
  (`except: pass` is forbidden).

### IV. Spec before code

- Every behavior change starts from a spec in `specs/` with acceptance
  scenarios. No spec, no merge.
- When a change alters current behavior, `specs/000-baseline/` is updated in
  the same change, so the baseline always describes the released app.
- Unknowns are written as `[NEEDS CLARIFICATION]` and resolved by the project
  owner, not guessed during implementation.

### V. A testable core, a thin UI

- Domain rules, persistence and document export live outside Qt widget classes
  and are covered by automated tests that run without opening a window.
- New logic is never added to a widget class. When existing logic inside a
  widget class must change, it is extracted first, then changed.
- A bug fix comes with a test that fails without the fix.

### VI. Simplicity for a solo maintainer

- Prefer the standard library, then the existing dependencies (PySide6,
  python-docx). A new dependency needs a written justification in the plan.
- No speculative abstractions, plugin systems, servers or multi-user features.
- The app ships as a single executable that needs no installer.

### VII. Portuguese for users, English for code, codes for data

- All user-facing text is Brazilian Portuguese.
- Code identifiers, comments, commit messages and these documents are English.
- Stored values are stable codes, never display labels. (Existing databases
  violate this; spec 005 corrects it.)

## Technical constraints

| Area | Constraint |
|---|---|
| Language | Python 3.14 |
| UI | PySide6 (Qt 6) |
| Storage | SQLite, one file per question bank, schema versioned with `PRAGMA user_version` |
| Export | python-docx, `.docx` output |
| Packaging | PyInstaller single-file executable |
| Platforms | Windows is the primary target; macOS must keep working |
| Tests | pytest; targeted tests covering the changed behavior and its regressions must pass before finalizing or merging to `main` |
| Versioning | Semantic versioning, git tags (`v1.2.0`); the version is defined in one place in code |

## Development workflow

1. Pick the next item from `docs/roadmap.md`.
2. Review its `spec.md`; resolve every `[NEEDS CLARIFICATION]` with the owner.
3. Write `plan.md` (how) and `tasks.md` (ordered steps) in the same folder.
   The plan includes a constitution check.
4. Implement on a branch named after the spec folder (e.g. `002-data-safety`),
   one task at a time, tests alongside.
5. Verify every acceptance scenario with targeted automated tests for the
   changed behavior and its regressions, update the baseline spec and roadmap,
   then merge and tag. A full-suite run is optional and may be used when its
   additional confidence justifies the time.

## Governance

- The project owner approves amendments. An amendment changes this file, bumps
  its version and states the reason in the commit message. Version 1.1.0
  changes verification from a mandatory full-suite run to targeted tests so
  feature delivery remains practical while preserving regression coverage.
- Reviews (human or AI) check constitution compliance before anything else.
- A justified exception is recorded in the plan under "Complexity tracking",
  with the simpler alternative that was rejected and why.
