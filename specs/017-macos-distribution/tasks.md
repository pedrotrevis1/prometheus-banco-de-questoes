# Tasks: macOS distribution presentation

- [x] T001 Record owner scope, design choice, acceptance scenarios and plan.
- [x] T002 Prepare compact Finder layout, SVG background and a preview-only renderer. Inspected the 640 × 420 design using the official icon and a temporary system-folder icon; no app or disk image was built.
- [x] T003 Prepare the explicit macOS PyInstaller spec with source-derived versions and verify packaging/resource contracts without building. Seven configuration/resource/smoke checks pass; Finder version fields read `prometheus.__version__`.
- [x] T004 Add guarded DMG packaging for an existing app, dependency declaration and targeted validation tests without building. 22 targeted packaging/resource/smoke checks pass using test doubles for native tools and the image builder.
- [x] T005 Render and inspect the preview; update the baseline, roadmap and release/build guidance; record test results. See [acceptance report](acceptance.md); 22 tests passed and no app/DMG build ran.
- [ ] T006 Complete native/release acceptance. Authorized arm64 app and DMG built; names/version/minimum-OS metadata, checksum, Retina representations, mounted/installed strict signatures and compiled-code export/dialog checks passed. 45 targeted tests and 13 Word exports passed. Live save-panel, clean-machine/oldest-OS and Microsoft Word checks remain unperformed; AppleScript assistive access was denied. See [acceptance report](acceptance.md).
