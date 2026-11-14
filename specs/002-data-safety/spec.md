# Feature specification: Data safety

**Folder**: `002-data-safety` | **Status**: Draft | **Created**: 2026-11-14
**Fixes**: KD-01, KD-02, KD-03, KD-04, KD-05, KD-06

## Why

A question bank is years of a teacher's work, and today it can appear to
vanish, be unlinked, be deleted by accident, or be damaged with no copy to fall
back on. This iteration closes every known path to data loss (constitution I).

## User stories

### US1 — A missing bank is reported, never replaced (P1)

As a teacher whose bank file was moved, or whose external or cloud drive is
not available, I am told the file was not found and asked what to do, instead
of seeing an empty bank.

**Acceptance scenarios**

1. **Given** a discipline whose file no longer exists, **when** I open the app
   or switch to that discipline, **then** I see a message naming the discipline
   and the expected path, with the options "Localizar arquivo", "Remover da
   lista" and "Cancelar", and no file is created.
2. **Given** that message, **when** I locate the moved file, **then** the
   discipline points to the new path and my questions appear.
3. **Given** a first run with no configuration, **when** the app starts,
   **then** the default bank is created as today.

### US2 — Only Prometheus banks are opened and modified (P1)

**Acceptance scenarios**

1. **Given** a file that is not a SQLite database, or a SQLite database with
   no Prometheus tables and other content, **when** I choose it in "Abrir Banco
   Existente", **then** I get an explanatory error and the file is not modified.
2. **Given** a bank created by a newer version of Prometheus than the one
   running, **when** I open it, **then** I am told to update the app and the
   file is not modified.

### US3 — I can back up a bank, and the app backs it up before risky operations (P1)

**Acceptance scenarios**

1. **Given** an open bank, **when** I choose "Fazer backup" and a destination,
   **then** a complete copy is written there and I am told where.
2. **Given** a bank that needs a schema upgrade, **when** I open it, **then** a
   copy is saved automatically before any change, and the upgrade either
   completes or leaves the bank exactly as it was.
3. **Given** more than the retention limit of automatic backups for a bank,
   **when** a new one is made, **then** the oldest are removed.

### US4 — Deleting questions is deliberate and visible (P1)

As a teacher, I cannot delete questions merely because they are ticked for an
exam, and I always see what I am about to delete.

**Acceptance scenarios**

1. **Given** a question card, **when** I choose "Excluir" on it and confirm a
   dialog that shows its ID and the beginning of its statement, **then** that
   question alone is deleted and removed from the exam selection.
2. **Given** several questions selected for an exam, **when** I look at the
   search tab, **then** there is no action that deletes all of them at once.

### US5 — Disciplines can be managed without losing a link (P2)

**Acceptance scenarios**

1. **Given** an existing discipline "Física", **when** I link another file and
   name it "Física", **then** the name is rejected and nothing changes.
2. **Given** a discipline, **when** I rename it, **then** it keeps pointing to
   the same file.
3. **Given** a discipline, **when** I remove it from the list, **then** I am
   told the file is kept on disk, and the file is untouched.

### US6 — Problems are shown, not hidden (P2)

**Acceptance scenarios**

1. **Given** a bank whose categories cannot be read, **when** the tree is
   loaded, **then** an error message is shown instead of an empty tree.

## Requirements

- **FR-001** The app never creates a database file except on first run
  (default bank) or when the user completes "Criar Novo Banco".
- **FR-002** Before using a file as a bank, the app verifies it is a SQLite
  database that is either empty/new or contains the Prometheus tables.
- **FR-003** Banks carry a schema version. The app upgrades older banks,
  refuses newer ones, and records the version after each upgrade.
- **FR-004** Each upgrade runs atomically, after an automatic backup.
- **FR-005** The user can create a backup of the current bank at any time to a
  location of their choice. Default file name: `<bank>_backup_<YYYY-MM-DD_HHMM>.db`.
- **FR-006** Automatic backups are stored in a `backups` folder inside the app
  data directory and limited to the 5 most recent per bank.
- **FR-007** Questions are deleted one at a time from their card, with a
  confirmation identifying the question. The bulk "Excluir questões
  selecionadas" action is removed.
- **FR-008** Discipline names are unique ignoring case and surrounding spaces,
  in both "Criar Novo Banco" and "Abrir Banco Existente".
- **FR-009** A discipline can be renamed and can be removed from the list.
  Removing never deletes or modifies the file.
- **FR-010** When the chosen location for a bank is inside a known
  cloud-synced folder (OneDrive, iCloud Drive, Dropbox, Google Drive), the app
  warns that syncing an open bank can damage it and recommends backups; the
  user may proceed. The save dialog no longer suggests cloud folders.
- **FR-011** No database or file error is ignored: it is shown to the user or
  written to a log file in the app data directory.
- **FR-012** The Help text explains backup and what to do when a bank is not found.

## Success criteria

- None of KD-01 to KD-06 can be reproduced.
- A bank from v1.1 opens, is backed up once, is upgraded, and shows identical
  content.
- Interrupting an upgrade (simulated failure) leaves the original bank intact.

## Out of scope

- An in-app "restore" flow (a backup is restored by opening it as a bank).
- Trash / undo for deleted questions.
- Scheduled backups; detection of concurrent use from two computers.

## Open questions

- [NEEDS CLARIFICATION: Is removing bulk delete acceptable (FR-007)? The
  alternative is to keep it but with its own separate selection and a list of
  the affected questions in the confirmation.]
- [NEEDS CLARIFICATION: Is 5 the right number of automatic backups to keep?
  Banks with many images can be large.]
- [NEEDS CLARIFICATION: Should the last removed/renamed discipline be undoable,
  or is "the file is kept on disk" enough?]
