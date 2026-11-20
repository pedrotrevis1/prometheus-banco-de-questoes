# Implementation plan: Official application icon

Use the supplied 1024px Apple export as the single source of truth. Set it on
QApplication for source and frozen execution, pass platform-specific packaging
options to the Windows and macOS build commands, bundle the runtime PNG, and
use a stable macOS bundle identifier. Pillow is added to development
requirements because PyInstaller uses it to convert a non-native PNG icon when
building the macOS bundle.

## Constitution check

- No database, user data, or runtime behavior is changed.
- The new build script is explicit about macOS-only execution.
- The icon source remains in the user-provided `icon/` folder.

## Pre-build review follow-up (2026-11-19)

Both build scripts put the runtime PNG in
`icon/prometheus-icon-apple Exports/`, but frozen lookup searched `icon/`.
Preserve the same relative path in source and frozen execution. Regression
tests copy the assets declared by each actual build script to a temporary
extraction directory and load the icon and Pix image through Qt, from an
unrelated working directory. This verifies the declared layout without
invoking PyInstaller or launching the application.

Record remaining packaging and native acceptance work in
`docs/releases/macos-acceptance.md`. The owner explicitly prohibited a macOS
build during this review; no packaged-app check is completed by simulation.
