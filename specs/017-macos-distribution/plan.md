# Implementation plan: macOS distribution presentation

## Approach

Use the familiar drag-to-Applications pattern so installation is a normal
Finder copy. Keep the actual app and `/Applications` symlink interactive;
only the heading, instructions and arrow belong to the background.

Keep layout values in a small build-tool module under `packaging/macos/`.
Render a code-native SVG into standard and Retina PNGs using the existing
PySide6 SVG renderer. Compose a clearly labelled preview with the supplied
Prometheus icon and the local system Applications icon; do not redistribute
the system icon as a repository asset.

Use an explicit, checked-in PyInstaller spec for macOS so `BUNDLE` can set
both version fields from the existing source version. Preserve the current
one-file/windowed behavior and bundled icon/Pix paths. Keep the app-build and
DMG-packaging commands separate, with macOS-only execution checks. The DMG
command accepts an already-built bundle and never invokes PyInstaller.

Validate bundle metadata and its executable/icon before packaging, inspect
the executable architecture using `lipo`, and refuse to overwrite output.
Use `dmgbuild` only at the explicitly invoked packaging step.

## Dependency justification

Add macOS-only development dependency `dmgbuild==2.0.0`. It writes Finder
layout metadata directly using its maintained `ds_store`/`mac_alias`
dependencies, avoiding GUI scripting permissions, Finder save timing and
hand-maintained binary `.DS_Store` data. A stdlib-only hdiutil/AppleScript
approach was rejected because deterministic Finder appearance is the core
requirement. No application runtime dependency is added. The dependency's
[settings documentation](https://dmgbuild.readthedocs.io/en/stable/settings/)
defines the layout API; its [overview](https://dmgbuild.readthedocs.io/en/stable/)
explains the Finder-independent approach.

## Constitution check

- I: No banks/configuration are opened, created or changed. Packaging copies
  a supplied app and refuses existing DMG output.
- II: The shipped application remains offline; packaging is a local process.
- IV: Acceptance scenarios precede code, with a baseline update in this change.
- V: No Qt widget class changes. New code is release tooling, with targeted
  tests of configuration, metadata and validation without building.
- VI: The executable remains single-file and requires no installer; the DMG
  is a distribution wrapper with a manual Finder copy.
- VII: Presentation and command errors use Brazilian Portuguese; tooling and
  documentation use English identifiers and prose.

## Verification

Capture PyInstaller spec calls with test doubles, simulate resource extraction
from their declared data paths, and check settings match the design. Use
synthetic plist/executable fixtures and mocked subprocess/builder calls to
exercise invalid input, version mismatches, architecture labels and packaging
without running any disk-image tools. Render and inspect the preview at its
intended size. Keep real Finder/Retina/copy/signing tests unchecked.

## Native packaging correction (2026-11-19)

The first built DMG copied successfully through Finder, but strict signature
verification of the installed app failed: dmgbuild's `hide_extensions`
setting calls SetFile on the already-signed app and adds `com.apple.FinderInfo`.
Remove that setting and rely on normal Finder extension preferences. Add a
regression check before changing the layout, then rebuild the DMG and verify
strict signatures both inside the mounted image and after a Finder copy.

## Frozen Word export correction (2026-11-19)

The owner reported `default-footer.xml` missing when saving an exam from the
first executable. Archive inspection confirms the template is present but
`docx/parts/` is not: python-docx 1.2.0 builds a path containing that directory
before `..`, and the filesystem cannot resolve it when the directory is only
represented by Python modules in the PYZ archive. Explicitly collect docx
data with `include_py_files=True` so the package directory structure exists
after extraction. Reproduce with captured build data and python-docx's real
footer/header factories before fixing, then test the rebuilt executable's
export. Apply the same collection to the Windows command to prevent the
equivalent one-file packaging defect there; no Windows build is performed.

After the usage-limit interruption the owner used the app and changed its
configuration. Preserve the newer configuration and current banks before
resuming disposable-bank tests; do not restore the stale pre-interruption
configuration over those owner changes.

The owner subsequently chose restoration of the original two-bank
configuration. Restore its exact saved bytes after tests, remove the temporary
entry and preserve the database files in their current schema state. The
upgraded bank's legacy questions/categories were compared with its automatic
backup; do not roll that owner-triggered upgrade back.

The owner also accepted a macOS 15.0 minimum after the bundled Qt bindings'
load commands were inspected. Set `LSMinimumSystemVersion` from the shared
layout configuration and validate it before packaging, without changing
runtime dependencies or advertising older-OS compatibility.
