# Implementation plan: Project foundation

**Spec**: [spec.md](spec.md) | **Status**: Draft | **Created**: 2026-11-14

## Approach

Move, do not rewrite. The UI code is relocated byte-for-byte except for
imports; only four functions that are already pure are extracted.

## Target layout after this iteration

```
prometheus/
  __init__.py          # __version__ = "1.2.0.dev0"
  __main__.py          # creates QApplication, shows the window
  app.py               # former Prometheus1.1.py minus what is extracted below
  resources.py         # asset_path(name): handles sys._MEIPASS when frozen
  domain/
    versions.py        # make_version_questions
    school_years.py    # parse_question_year_values, format_question_year_info
    richtext.py        # html_fragment, format_equation_html
  assets/pix_qr.jpg
tests/
  domain/test_versions.py, test_school_years.py, test_richtext.py
  test_smoke.py        # imports prometheus.app with QT_QPA_PLATFORM=offscreen
requirements.txt       # PySide6==6.11.1, python-docx==1.2.0
requirements-dev.txt   # -r requirements.txt, pytest, pyinstaller==6.20.0
build_windows.ps1      # the PyInstaller command, with --add-data for assets
.gitignore
```

## Design notes

- **Extraction.** The four functions are static or do not use `self`. They
  move to `domain/` unchanged; `ExamGeneratorApp` keeps thin methods that
  delegate, so call sites do not change.
- **Characterization tests.** Tests assert what the functions do today, not
  what they should do. Suspected bugs found while writing them are recorded as
  known defects in the baseline, not fixed here.
- **Randomness.** `make_version_questions` uses the global `random` module.
  Tests seed it; they assert invariants (same set of alternatives, answer
  letter follows its content, order differs from the original when contents
  differ) rather than exact orders.
- **QR asset.** The base64 block is decoded once to `assets/pix_qr.jpg`;
  `show_pix_qr` loads it via `resources.asset_path`.
- **Version.** `APP_VERSION` is replaced by `prometheus.__version__`.
- **Git history.** Use `git mv Prometheus1.1.py prometheus/app.py` in its own
  commit before editing, so history follows the file.

## Test strategy

- Unit tests for `domain/` run with plain pytest, no Qt import.
- One smoke test imports the UI module and constructs nothing, to catch import
  errors. Full GUI tests are out of scope.
- Manual check of US4: open a copy of a real v1.1 bank and walk the three tabs.

## Constitution check

| Principle | Result |
|---|---|
| I Data safety | No storage code changes |
| IV Spec before code | This plan; baseline unchanged because behavior is unchanged |
| V Testable core | First step toward it; extracted code is covered |
| VI Simplicity | Only pytest added (dev-only) |
| VII Languages | No UI text changes |

## Risks

- A subtle behavior change during the move. Mitigation: extract by cut and
  paste only, review the diff with whitespace ignored, run the manual check.
- The frozen executable not finding the asset. Mitigation: US3 scenario is
  verified on a real Windows build before tagging.
