# Acceptance report: Windows distribution

**Date:** 2026-11-19. **Result:** Windows 2.0.0 built and locally verified on
Windows 11 x64. GitHub upload, publication and release tagging were not performed.

## Artifact

- `dist/Prometheus.exe`: **56,258,222 bytes** (53.65 MiB), single-file,
  windowed PE executable, AMD64 (`0x8664`), Windows GUI subsystem (`2`).
- SHA-256: `53de8d4f24072f3df6836cf9897149b9ff4ab03a88d5eaae3c61e8c9daa91517`.
- `dist/SHA256SUMS-windows.txt` and `dist/windows-build-info.json` accompany
  the executable; generated release files remain ignored by Git.
- Both PE icon/group-icon resources and the official runtime PNG are present.
  The Pix JPEG and physical `docx/parts` directory/header/footer templates load.
- No Authenticode signature is provided. No compatibility claim beyond the
  tested Windows 11 x64 host is established by these checks.

## Environment and build

Windows 11, build 22631, AMD64; Python 3.14.5, PySide6/shiboken6 6.11.1,
python-docx 1.2.0, lxml 6.1.3, PyInstaller 6.20.0, hooks 2026.10,
pytest 9.0.2 and Pillow 11.3.0.

The pre-existing `.venv` contained unrelated Qt 6.12 PDF/WebEngine packages
whose requirements conflicted with the pinned Qt 6.11 bindings. It was not
used for the final build. Installed the pinned development requirements in the
previously empty `.venv-1`; `pip check` reports no broken requirements.

With `.venv-1/Scripts` first on PATH:

```powershell
python -B -u -m pytest -q -p no:cacheprovider --junitxml=build/windows-source-tests-final.xml
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_windows.ps1
```

The child-process execution-policy option was necessary because this host blocks
PowerShell scripts by default; no permanent policy was changed. The build script
itself is unchanged. The manifest records the source commit, dirty worktree,
dependency versions and SHA-256 values for runtime code, assets and packaging
inputs. No personal configuration or question bank is bundled.

## Source verification and corrections

**429 passed, 1 skipped** in 107.56 seconds in the clean environment.

The initial broad run reproduced a native access violation in successive
`ExamGeneratorApp` construction: replacing the application-wide Qt proxy style
invalidated styles retained by existing widgets. A new subprocess regression
failed before the correction. Style initialization now uses a module-level UI
adapter and reuses the existing application-owned style. The regression plus
data-safety tests passed all 31 checks; the final full suite also passed.
The baseline records the lifetime guarantee.

Four additional failures were test portability issues, not product defects:
macOS fixture paths used literal POSIX separators, a POSIX execute-bit test
cannot run on Windows, and two theme assertions assumed macOS colors despite
the existing Windows-specific palette. Path/color expectations now account for
the host; the date filter additionally checks its enabled surface. Only the
POSIX permission case is skipped on Windows. macOS runtime/packaging behavior
was not modified by those test changes.

## Compiled modules and Word output

A disposable harness read the final EXE's CArchive/PYZ, loaded **135 compiled
`prometheus` and `docx` modules**, extracted bundled images/templates/Python
package data, and assigned their frozen file paths. Native dependencies came
from the matching clean environment. This checks actual packaged bytecode and
resources, independently of importing application Python source.

- Twelve Word files cover versions 1–3 with answers at the end, separate keys,
  or omitted answers. Checks cover ZIP integrity, reopened documents, header
  and footer templates, page fields, version labels, embedded image counts
  and the expected correct answer `C`.
- A thirteenth document was produced through the compiled
  `ExamGeneratorApp.generate_word_doc()` handler using a synthetic schema-6
  bank. It contains its image and page footer, reports success, and records
  one completed usage. Only prompts/file-dialog responses were substituted.
- Synthetic question registration, accent-insensitive search (`celula` finds
  `célula`), exam save/reopen and restored question selection passed.
- About includes `2.0.0`; the Pix dialog loads its image in both themes.
  Offscreen checks verify content/resources. Offscreen font rendering is not
  visual acceptance; the actual native executable was inspected separately.

Diagnostic harnesses/logs, 13 documents, screenshots and JSON results are under
ignored `build/`; final checks use `build/windows-acceptance-final/`.
An earlier disposable harness paused on an unstubbed save/discard prompt;
it was stopped and rerun with the intended prompt responses. No real bank or
configuration was involved.

## Actual executable startup

Launched the actual final `dist/Prometheus.exe` twice from an unrelated working
directory with isolated `USERPROFILE`/AppData directories. Its PATH contained
only Windows/System32; Python/Qt environment overrides were removed.

1. Fresh profile: the native Portuguese default-bank confirmation appears.
   Closing it declines creation, the empty application opens, and no `.db`
   file is created. Closing the main window exits with code **0**.
2. Synthetic-bank profile: the packaged app opens the schema-6 fixture and
   displays its Biologia category. Closing exits with code **0**.

Both error logs are empty. Native window captures were inspected: Portuguese
text, accented characters, layout and controls render correctly. Direct screen
capture returned a black desktop in this execution session; window capture via
PrintWindow succeeded. Qt appends its display name to dialog captions, which
the harness accounts for. Earlier harness-only caption/capture attempts are
not treated as product failures. Final results are recorded in
`build/windows-acceptance-final/native-results.json` and the release manifest.

Existing user banks/configuration were never opened or changed. All created
banks belong to explicitly authorized temporary synthetic test fixtures.

## Remaining scope limits

- No clean-machine, other-Windows-version, ARM64 or 32-bit validation.
- No GitHub downloaded-artifact/SmartScreen or antivirus-distribution check.
- No visual inspection in Microsoft Word or live native save-panel automation;
  compiled handler/document checks substitute only the dialog responses.
- No macOS rebuild or native revalidation here. The earlier macOS package and
  manifest describe their original source snapshot; `prometheus/app.py` changed
  for the Windows style correction, so that earlier manifest no longer matches
  this file in the current checkout. Rebuild/revalidate on macOS before claiming
  that its artifact matches the updated release source.

These limits remain documented; local readiness does not claim publication or
unperformed compatibility checks.

## Final documentation and integrity checks

All three READMEs, release notes, publishing guidance and roadmap now reflect
the validated local Windows artifact. All **157 relative links in 84 Markdown
files** resolve. All **49 runtime/packaging source hashes**, the executable's
manifest hash and its checksum-file hash match. The PE certificate table is
empty, confirming the unsigned status. `git diff --check` passes.
