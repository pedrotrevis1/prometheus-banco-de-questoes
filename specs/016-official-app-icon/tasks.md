# Tasks: Official application icon

- [x] Add source/frozen runtime icon resolution and QApplication icon setup.
- [x] Add Windows and macOS PyInstaller icon/bundle configuration.
- [x] Add the required build dependency and document the icon source.
- [x] Verify icon resolution and the smoke test.

## Pre-build macOS review (2026-11-19)

- [x] T005 Reproduce and fix the frozen runtime icon path mismatch against both build scripts; verify source and simulated frozen assets without building. Both simulated frozen cases failed before the fix; all five asset/smoke checks passed afterward.
- [x] T006 Record the macOS release acceptance checklist and unresolved packaging findings. Keep actual builds and packaged-app checks pending until authorized. See [macOS acceptance](../../docs/releases/macos-acceptance.md).
