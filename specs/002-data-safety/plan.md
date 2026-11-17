# Implementation plan: Data safety

**Spec**: [spec.md](spec.md) | **Status**: Draft | **Created**: 2026-11-14
**Prerequisite**: 001 foundation implemented; Windows verification remains pending by owner decision.

## Approach

Introduce the `prometheus/storage/` layer and move the connection, schema and
configuration code into it (constitution V: extract, then change). The UI keeps
its `self.conn` usage for queries; only opening, migrating, backing up and
configuration go through the new modules in this iteration.

## New modules

### `storage/config.py`

- `data_dir()`, `load_config()`, `save_config()` moved from the main window.
- `add_discipline(config, name, path)`, `rename_discipline`, `remove_discipline`,
  `relink_discipline`; names compared with `strip().casefold()`; raise
  `DuplicateDisciplineError`.
- `save_config` writes to a temp file then `os.replace`, as the exam export does. Discipline changes use a separate configuration candidate, which is persisted before changing the active connection or UI state. If a newly created bank cannot be linked because saving fails, report its path and leave the file intact.

### `storage/database.py`

- `open_bank(path, *, create=False) -> sqlite3.Connection`
  - `create=False` and file missing → `BankNotFoundError` (no directory or
    file is created).
  - Opens, runs `inspect_bank`, sets `foreign_keys`, registers `CASEFOLD`,
    then calls `migrations.upgrade`.
- `inspect_bank(conn) -> BankState`: `NEW` (no tables), `PROMETHEUS`
  (`questoes` and `assuntos` present), `FOREIGN` (anything else), plus
  `user_version`. A non-SQLite file surfaces as `sqlite3.DatabaseError` and is
  mapped to `NotABankError`.
- `create=True` is passed only after first-run confirmation and by "Criar Novo Banco".

### `storage/migrations.py`

- `SCHEMA_VERSION = 1`.
- Ordered list of migration functions; index = version they upgrade *from*.
- Migration 0 → 1: create both tables if absent, add the four v1.1 columns if
  missing (the logic of today's `migrate_db`), set `user_version = 1`.
- `upgrade(conn, path)`: if `user_version > SCHEMA_VERSION` raise
  `BankTooNewError`; if lower and the bank is not `NEW`, call
  `backup.automatic(path)` first; run each step inside `BEGIN IMMEDIATE … COMMIT`
  with rollback on error.
- A v1.1 bank has `user_version = 0` and all columns, so 0 → 1 is a no-op
  apart from stamping the version. v1.1 ignores `user_version`, so the old
  app still opens upgraded banks.

### `storage/backup.py`

- `manual(conn, destination)`: `sqlite3.Connection.backup()` into a new file,
  written to a temporary file then published without overwriting an existing destination.
- `automatic(path)`: same into `<data_dir>/backups/<bank-stem>/<timestamp>.db`,
  retain at most 3, requesting explicit confirmation naming each old backup before deletion; cancel the upgrade if declined. Publish the replacement successfully before deleting confirmed old backups; a failed deletion leaves the replacement and any undeleted copies in place.
- `is_cloud_path(path) -> bool`: matches path components `OneDrive*`,
  `iCloudDrive`, `Mobile Documents`, `Dropbox`, `Google Drive`, `My Drive`.

### `storage/log.py`

- Standard `logging` to `<data_dir>/prometheus.log` with rotation (stdlib).

## UI changes (in `app.py`)

| Area | Change |
|---|---|
| `switch_database_connection` | Calls `open_bank`; handles `BankNotFoundError` with the Locate / Remove / Cancel dialog; handles `NotABankError`, `BankTooNewError` with messages; on failure, falls back to the previous discipline |
| Sidebar | Add "Fazer backup", "Renomear disciplina", "Remover da lista"; change the save dialog title; cloud warning after choosing a path |
| `action_link_existing_database`, `action_create_new_database` | Use `config.add_discipline`; show duplicate-name error |
| Search tab | Retain the existing bulk deletion workflow by owner decision |
| `build_subject_tree`, `populate_parents`, connection close | Replace `except: pass` with logging plus a user message |
| `show_help` | Add the backup and missing-bank paragraphs |

## Test strategy

All storage tests use `tmp_path`; none need Qt.

- `open_bank`: missing file without `create` raises and creates nothing;
  text file → `NotABankError`; foreign SQLite file is not modified (compare
  bytes before and after); future `user_version` raises.
- Migrations: a fixture builds a pre-1.1 bank (no `segmento`, `fonte_questao`,
  …) with rows; after upgrade rows are intact, columns exist, version is 1,
  one automatic backup exists. A migration forced to fail leaves the file
  byte-identical and the version unchanged.
- Backup: copy opens and has the same row counts; retention keeps 3 with explicit confirmation; refusal cancels the upgrade.
- Config: duplicate names (case, spaces), rename, remove, relink; atomic save.
- UI flows (US1, US5): manual checklist in `tasks.md`.

## Constitution check

| Principle | Result |
|---|---|
| I Data safety | The purpose of this iteration |
| III No silent failure | `except: pass` removed; log added |
| IV Spec before code | Baseline BL-012–016, BL-045 and KD table updated on completion |
| V Testable core | All new logic in `storage/`, tested without Qt |
| VI Simplicity | Standard library only |
| VII Languages | New UI strings in Portuguese |

## Risks

- **Backup size and time** for banks with many images: the automatic backup
  runs only when an upgrade is needed, not on every open.
- **Cloud detection is heuristic.** It is advisory only and never blocks.
- **Bulk deletion** retains its existing risk of including hidden selected questions, by owner decision.
