# Acceptance report: macOS distribution presentation

**Date:** 2026-11-19. **Result:** authorized arm64 app/DMG built for macOS 15+;
local packaged-code and signature checks passed. Remaining native acceptance
is listed below. Earlier no-build restrictions were superseded by the owner's
explicit build authorization.

## Prepared behavior

- 640 × 420 Finder layout, light neutral background, restrained typography,
  official icon, blue arrow and Portuguese drag-to-Applications instructions.
- A real `Prometheus.app` and `Aplicativos` symlink to `/Applications`, with
  fixed icon positions and hidden Finder toolbar/sidebar/status elements.
- Standard and Retina presentation backgrounds generated from one SVG.
- Explicit PyInstaller bundle configuration with both Finder version fields
  read from `prometheus.__version__` (currently `2.0.0`). Executable name,
  bundle name and identifier retain their existing values.
- Separate DMG packaging of an existing app, with identity/content checks,
  actual executable architecture labels, protection against existing-output
  replacement and cleanup of staged artifacts on failure.

## Automated verification

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q tests/test_resources.py tests/test_smoke.py tests/test_macos_packaging.py
sh -n build_macos.sh build_macos_dmg.sh
git diff --check
```

The initial preparation passed 22 tests. After the FinderInfo and Word-template
corrections and the agreed minimum-OS metadata, verification passed **45 tests**:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q tests/test_resources.py tests/test_smoke.py tests/test_macos_packaging.py tests/export/test_exam_document.py
```

Shell syntax and whitespace checks passed.

The tests capture spec calls with test doubles and simulate bundled asset
extraction. Synthetic plist/executable fixtures exercise validation, all
supported architecture labels, non-Mac/missing-input errors, preservation of
existing output/source app, and failed-builder cleanup. Background rendering
checks actual PNG dimensions. No real PyInstaller analysis/build, DMG builder,
lipo, hdiutil, diskutil or Finder automation is invoked by the tests. No
question-bank or configuration workflow runs.

## Visual review

Rendered and inspected the [preview](../../docs/releases/assets/macos-dmg-preview.png)
at 2× resolution. The heading, instructions, icon labels and footer are
readable; both icons and the arrow fit the compact layout without overlap.
The preview was regenerated using the owner's restored project icon folder.
Its title bar and native folder representation are a mockup; the folder icon
can vary by macOS version. The system icon is loaded locally for the preview
and is not included as a standalone distribution asset.

## Pending native verification

T006 remains unchecked for the unperformed native checks described below.

## Authorized build and packaging verification

- Python 3.14.5, PyInstaller 6.20.0, PySide6 6.11.1, python-docx 1.2.0,
  Pillow 11.3.0 and dmgbuild 2.0.0; build host macOS 27.2.1, native arm64.
- Executable `Prometheus`, bundle `Prometheus.app`, identifier
  `com.pedrotrevisan.prometheus`; both version fields are `2.0.0`.
  Finder Get Info displayed `Versão: 2.0.0` and Apple silicon application type.
- The owner accepted the Qt bindings' declared macOS 15.0 minimum;
  `LSMinimumSystemVersion` now states `15.0`. Older macOS is out of scope.
- The DMG checksum verifies. Its real Finder presentation was opened and
  inspected: compact bounds, official icon, Portuguese instructions/arrow
  and an actual `Aplicativos` symlink to `/Applications`. The stored Retina
  TIFF contains 640 × 420 at 72 dpi and 1280 × 840 at 144 dpi.
- The app was copied through Finder into Applications during initial
  acceptance. Final corrected copies were also installed from the mounted
  image with metadata-preserving copy and checked against the final executable.
- Strict code-signature verification passed on the final app, its copy inside
  the read-only mounted DMG and its installed copy. Gatekeeper rejects the
  ad-hoc-signed app, as expected for the distribution choice accepted by the
  owner; no notarization or quarantine removal was performed.
- Build outputs are in `dist/`. `SHA256SUMS.txt` and `macos-build-info.json`
  identify the final image and source/dependency provenance. The source
  working tree contains uncommitted changes; this is not a published release.

## Packaging defects reproduced and corrected

1. `hide_extensions` caused dmgbuild to add `com.apple.FinderInfo` to the
   signed app. Strict verification failed after copying. Removing that setting
   fixed the image/copy signatures; the regression test failed before the fix.
2. The owner reported `default-footer.xml` missing during export. The XML
   was present in the archive, but `docx/parts` was absent. python-docx uses
   `docx/parts/../templates/default-footer.xml`, which cannot resolve without
   the intermediate directory. A regression test reproduced that exact
   `FileNotFoundError`. Explicit collection of docx Python files alongside
   templates fixes the directory structure. The Windows command has equivalent
   collection configured, but Windows was not built during this task.

Earlier defective images/executables were retained for diagnosis and then
removed during the owner-authorized repository cleanup in spec 018. The final
`dist/` deliverables were preserved and their checksums rechecked.

## Compiled-code export and UI verification

A temporary diagnostic harness loaded the actual final app's `prometheus`
and `docx` bytecode from its PYZ archive, extracted its bundled template and
image data, and assigned the corresponding frozen file paths. It used the
same installed native dependency versions in an offscreen Qt process. This
checks compiled code/resource behavior; it is not live save-panel automation.

- Twelve Word files covered three versions with answers at the end, separate
  answer keys or no answers. ZIP validity, page/version footers, embedded images
  and matching answer letters were checked.
- A thirteenth file was generated through the compiled
  `ExamGeneratorApp.generate_word_doc()` handler against a disposable bank,
  with only prompt/file-dialog responses substituted. It contained its footer
  and image and completed without an error alert.
- The compiled window opened the schema-6 fixture. Help, About/legal/version
  and Pix dialogs were rendered in light/dark modes and visually inspected.
  Screenshots and detailed diagnostic results were inspected before the
  owner-authorized cleanup removed the generated test outputs. This report
  retains the verification summary.

The installed app started outside Terminal, but the normal desktop tool could
not attach to PyInstaller's GUI child. The owner authorized AppleScript as a
fallback; macOS denied assistive access. No privacy setting was changed. Native
save-panel interaction, clean-machine/oldest-supported-OS testing, downloaded
quarantine behavior and visual inspection in Microsoft Word remain unperformed
(Microsoft Word is not installed). See the
[macOS release checklist](../../docs/releases/macos-acceptance.md).

## User-data preservation after interruption

The usage limit interrupted testing with the disposable configuration active.
The owner then relinked/used a real bank, which upgraded from schema 3 to 6 with
an automatic backup. SQLite integrity passes; all 2,597 legacy question rows
and 149 category rows match that backup, and there are 2,597 normalized questions.
The newer configuration was preserved separately before resuming.

After testing, the owner chose to restore the original two-bank configuration.
Its saved bytes were restored exactly and the temporary entry removed. Real
banks were not changed during resumed checks; the second original bank also
retains its pre-interruption checksum. The first bank's schema upgrade was
preserved rather than rolled back.
