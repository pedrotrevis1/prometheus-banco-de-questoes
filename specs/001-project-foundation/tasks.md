# Tasks: Project foundation

**Plan**: [plan.md](plan.md). Do tasks in order; commit after each.

## Phase 1 — Repository setup

- [ ] T001 Add `.gitignore` (venvs, `__pycache__`, `build/`, `dist/`, `*.spec`, `*.db`, `.pytest_cache`).
- [ ] T002 Add `requirements.txt` and `requirements-dev.txt` with the pinned versions from the README.
- [ ] T003 Resolve the license question with the owner and add `LICENSE`.

## Phase 2 — Package without behavior change

- [ ] T004 `git mv Prometheus1.1.py prometheus/app.py`; commit the move alone.
- [ ] T005 Add `prometheus/__init__.py` with `__version__`; replace `APP_VERSION` usages.
- [ ] T006 Add `prometheus/__main__.py` holding the former `if __name__ == "__main__"` block; confirm `python -m prometheus` starts the app.
- [ ] T007 Decode the embedded QR image to `prometheus/assets/pix_qr.jpg`, add `prometheus/resources.py`, load the image from the file, delete the base64 block and the `base64` import.
- [ ] T008 Remove imports left unused by the move.

## Phase 3 — Extract and test pure logic

- [ ] T009 Move `make_version_questions` to `prometheus/domain/versions.py`; keep a delegating method.
- [ ] T010 Write `tests/domain/test_versions.py`: answer letter follows content; essay questions untouched; invalid answer letter raises; identical alternatives do not loop.
- [ ] T011 Move `parse_question_year_values` and `format_question_year_info` to `prometheus/domain/school_years.py`; keep delegating methods.
- [ ] T012 Write `tests/domain/test_school_years.py`: `;`-joined values, legacy JSON for both segments, empty input, formatting with and without segment.
- [ ] T013 Move `html_fragment` and `format_equation_html` to `prometheus/domain/richtext.py`; keep delegating methods.
- [ ] T014 Write `tests/domain/test_richtext.py`: body extraction, style stripping, plain text escaping, `^`/`_` conversion, chemistry subscripts, arrow replacement.
- [ ] T015 Add `tests/test_smoke.py` importing `prometheus.app` under `QT_QPA_PLATFORM=offscreen`.
- [ ] T016 Record any suspicious behavior found in T010–T014 as new `KD-nn` rows in the baseline spec.

## Phase 4 — Build and docs

- [ ] T017 Resolve the build-command question with the owner; add `build_windows.ps1` including the asset.
- [ ] T018 Build on Windows; verify the app starts and "Sobre" → Pix shows the QR code.
- [ ] T019 Update the README developer section (install, run, test, build) and the file references.
- [ ] T020 Manual regression: open a copy of a v1.1 bank, register a question, filter, generate a two-version exam.
- [ ] T021 Update `docs/architecture.md` "Current state" and `docs/roadmap.md` status.
