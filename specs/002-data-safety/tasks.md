# Tasks: Data safety

**Plan**: [plan.md](plan.md). Tests are written before or with each task. `[US#]` links to the spec.

## Phase 1 — Storage layer (no behavior change yet)

- [x] T001 Create `prometheus/storage/config.py`; move data-dir and config load/save; make save atomic; tests.
- [x] T002 Create `prometheus/storage/log.py`; initialize logging at startup.
- [x] T003 Create `prometheus/storage/migrations.py` with migration 0 → 1 reproducing today's table creation and `migrate_db`; tests with a pre-1.1 fixture bank.
- [x] T004 Create bank inspection and safe opening for current-version banks; reject older banks until backup-backed upgrades are available; tests.
- [x] T005 Create `prometheus/storage/backup.py` (manual and automatic backup, retention with confirmation); tests.
- [x] T006 Add backup-backed atomic migration and bank opening; test failures and explicit creation.
- [x] T007 Integrate safe opening without implicit creation of missing databases; delete inline schema code; run the offscreen copied-bank regression.

## Phase 2 — Backups [US3]
- [x] T008 Add the "Fazer backup" sidebar button and its save dialog.

## Phase 3 — Missing and invalid banks [US1, US2]

- [x] T009 Pass `create=True` only after first-run confirmation and in "Criar Novo Banco"; everywhere else `create=False`.
- [x] T010 Add the "banco não encontrado" dialog (Localizar / Remover da lista / Cancelar) and `config.relink_discipline`; tests for relink.
- [x] T011 Show specific messages for `NotABankError` and `BankTooNewError`; fall back to the previously open discipline.
- [x] T012 Handle the startup case where the current discipline's bank is missing and no other discipline exists.

## Phase 4 — Disciplines [US5]

- [x] T013 Add `add_discipline`, `rename_discipline`, `remove_discipline` with duplicate checks; tests.
- [x] T014 Use them in "Criar Novo Banco" and "Abrir Banco Existente"; add "Renomear disciplina" and "Remover da lista" to the sidebar.
- [x] T015 Add `is_cloud_path` with tests; show the advisory warning; reword the save dialog title.

## Phase 5 — Deletion [US4]

- [x] T016 Owner chose to retain bulk deletion as it works today.
- [x] T017 No per-card deletion: owner chose to retain the existing workflow.
- [x] T018 Retain `btn_delete_selected_questions` and `delete_selected_questions`.

## Phase 6 — Errors and help [US6]

- [x] T019 Replace every `except: pass` / bare `except` with logging and, where the user is affected, a message.
- [x] T020 Update the Help text (backup, missing bank).

## Phase 7 — Verification and docs

- [x] T021 Manual checklist on Windows: owner confirmed platform checks complete on 2026-11-17.
  - rename a bank file on disk, start the app → dialog, relink works, no new file appears
  - open a `.txt` renamed to `.db` and an unrelated SQLite file → error, file unchanged
  - open a copy of a real v1.1 bank → content identical, one automatic backup created
  - manual backup opens as a bank with the same questions
  - duplicate discipline name rejected in both flows; rename and remove work
  - confirm bulk deletion still uses the current selection, including hidden questions
- [x] T022 Update `specs/000-baseline/` (BL-012 to BL-016, BL-045, data-model `user_version`, KD table), `docs/architecture.md`, `docs/roadmap.md`, README backup section.
- [x] T023 Skipped by owner decision: no 1.2.0 version bump, build or tag; the next planned release is 2.0.0 after 005 and 006.

## Ordered review follow-up

- [x] R001 Preserve existing automatic backups when publication fails; add a regression test.
- [x] R002 Make configuration changes transactional across persistence and UI state; test failures for discipline operations.
- [x] R003 Fix nested missing-bank removal recovery and preserve state on cancellation; add regression tests.
- [x] R004 Fix repository-wide plain `pytest` imports and verify both pytest entry points.
