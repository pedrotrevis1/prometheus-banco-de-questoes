# Tasks: Data safety

**Plan**: [plan.md](plan.md). Tests are written before or with each task. `[US#]` links to the spec.

## Phase 1 — Storage layer (no behavior change yet)

- [ ] T001 Create `prometheus/storage/config.py`; move data-dir and config load/save; make save atomic; tests.
- [ ] T002 Create `prometheus/storage/log.py`; initialize logging at startup.
- [ ] T003 Create `prometheus/storage/migrations.py` with migration 0 → 1 reproducing today's table creation and `migrate_db`; tests with a pre-1.1 fixture bank.
- [ ] T004 Create `prometheus/storage/database.py` with `open_bank` and `inspect_bank`; tests for new, Prometheus, foreign, non-SQLite and too-new files.
- [ ] T005 Make `switch_database_connection` use `open_bank(create=True)` everywhere, keeping current behavior; delete `migrate_db` and the inline `CREATE TABLE`s; run the manual regression.

## Phase 2 — Backups [US3]

- [ ] T006 Create `prometheus/storage/backup.py` (`manual`, `automatic`, pruning); tests.
- [ ] T007 Call `backup.automatic` from `migrations.upgrade` before the first step; test that a failing migration leaves the file byte-identical.
- [ ] T008 Add the "Fazer backup" sidebar button and its save dialog.

## Phase 3 — Missing and invalid banks [US1, US2]

- [ ] T009 Pass `create=True` only on first run and in "Criar Novo Banco"; everywhere else `create=False`.
- [ ] T010 Add the "banco não encontrado" dialog (Localizar / Remover da lista / Cancelar) and `config.relink_discipline`; tests for relink.
- [ ] T011 Show specific messages for `NotABankError` and `BankTooNewError`; fall back to the previously open discipline.
- [ ] T012 Handle the startup case where the current discipline's bank is missing and no other discipline exists.

## Phase 4 — Disciplines [US5]

- [ ] T013 Add `add_discipline`, `rename_discipline`, `remove_discipline` with duplicate checks; tests.
- [ ] T014 Use them in "Criar Novo Banco" and "Abrir Banco Existente"; add "Renomear disciplina" and "Remover da lista" to the sidebar.
- [ ] T015 Add `is_cloud_path` with tests; show the advisory warning; reword the save dialog title.

## Phase 5 — Deletion [US4]

- [ ] T016 Confirm the open question on bulk delete with the owner.
- [ ] T017 Add "Excluir" to `QuestionCard` with the identifying confirmation; delete, update the selection counter and the list.
- [ ] T018 Remove `btn_delete_selected_questions` and `delete_selected_questions`.

## Phase 6 — Errors and help [US6]

- [ ] T019 Replace every `except: pass` / bare `except` with logging and, where the user is affected, a message.
- [ ] T020 Update the Help text (backup, missing bank).

## Phase 7 — Verification and docs

- [ ] T021 Manual checklist on Windows:
  - rename a bank file on disk, start the app → dialog, relink works, no new file appears
  - open a `.txt` renamed to `.db` and an unrelated SQLite file → error, file unchanged
  - open a copy of a real v1.1 bank → content identical, one automatic backup created
  - manual backup opens as a bank with the same questions
  - duplicate discipline name rejected in both flows; rename and remove work
  - delete one question from its card; selection counter updates
- [ ] T022 Update `specs/000-baseline/` (BL-012 to BL-016, BL-045, data-model `user_version`, KD table), `docs/architecture.md`, `docs/roadmap.md`, README backup section.
- [ ] T023 Bump the version to 1.2.0, build, tag `v1.2.0`.
