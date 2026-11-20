# macOS release acceptance

**Reviewed:** 2026-11-19. **Status:** authorized arm64 app/DMG built for macOS
15.0 or newer; local package/code/signature verification passed. Native
save-panel, clean-machine and Word visual acceptance remain pending. The
owner superseded the original no-build restriction and chose ad-hoc signing.

## Source review evidence

- The host and active Python interpreter run as `arm64` on macOS 27.2.1.
  Python is 3.14.5, PyInstaller 6.20.0 and PySide6 6.11.1. Python and the
  installed Qt Cocoa platform plugin contain both arm64 and x86_64 slices;
  this does not establish compatibility of all dependencies or Intel support.
- `sh -n build_macos.sh` passes and `pip check` reports no broken requirements.
- The macOS spec names the executable `Prometheus` and requests
  `Prometheus.app`, with identifier `com.pedrotrevisan.prometheus`.
  PyInstaller's installed bundle writer derives `CFBundleExecutable` from
  the executable basename and bundle names from the app basename.
- Qt application and display names both use
  `Prometheus - Banco de Questões`. The window title adds the current bank
  filename. These display labels need not be executable filenames. There is
  no evidence identifying the owner's v1.1 failure without its error log.
- Both platform build configurations bundle the Pix JPEG and official runtime PNG. The
  frozen icon resolver previously searched a different directory; that bug
  is fixed under spec 016. Tests load real images through Qt from source and
  simulated extraction layouts derived from the macOS spec and Windows build
  script, while the
  working directory is unrelated to the repository. Both frozen tests failed
  before the fix. The three resource tests and two smoke tests now pass.
- Spec 017 prepares a compact drag-to-Applications DMG layout and separate
  packaging command, without executing the app or image builders. Its
  [acceptance report](../../specs/017-macos-distribution/acceptance.md) records
  source verification and the visual preview.
- The initial source-only checks did not open app data or question banks.
  Subsequent compiled-code checks used the authorized disposable bank. After
  the interruption, the owner chose to restore the original two-bank
  configuration; its bytes were restored exactly. See the 017 report for the
  audit of the owner's intervening real-bank upgrade and preserved rows.
- Current verification passed 45 targeted tests and 13 compiled-code Word
  exports. Strict signatures pass on the built, mounted and installed app.

## Findings to address before release

- **Bundle version — source configuration corrected in 017:** the explicit
  macOS spec now reads `prometheus.__version__` and sets both
  `CFBundleShortVersionString` and `CFBundleVersion` as strings. The current
  value is `2.0.0`. The actual generated plist and Finder Get Info were checked;
  both report the expected release version.
- **Packaging mode:** the constitution requires a single-file executable.
  The current spec retains a one-file windowed executable. PyInstaller advises against
  this combination for app bundles because of extraction overhead and the
  incompatibility with sandboxed Mac App Store distribution. Any switch to
  `--onedir` needs an approved constitution/spec change; do not silently
  change modes. See [PyInstaller's macOS bundle notes](https://pyinstaller.org/en/v6.20.0/usage.html#building-macos-app-bundles).
- **Architecture and macOS floor — owner decisions recorded:** the spec
  explicitly targets `arm64`. The owner accepted macOS 15.0 or newer after
  inspection showed that minimum in the Qt binding binaries, and the bundle
  declares `LSMinimumSystemVersion=15.0`. All 110 collected native Mach-O
  binaries were checked as arm64. Oldest-supported-OS testing remains pending;
  no Intel build is provided. See [architecture support](https://pyinstaller.org/en/v6.20.0/feature-notes.html#macos-multi-arch-support)
  and [OS compatibility](https://pyinstaller.org/en/v6.20.0/usage.html#making-macos-apps-forward-compatible).
- **Distribution — owner-selected ad-hoc signing:** no Developer ID identity,
  notarization or stapling is configured. Strict signatures validate, while
  Gatekeeper rejects this ad-hoc build as expected for the accepted choice.
  Download/quarantine behavior through any eventual distribution channel is
  still unverified. See
  [PyInstaller signing](https://pyinstaller.org/en/v6.20.0/feature-notes.html#macos-binary-code-signing)
  and [Apple's Gatekeeper guidance](https://support.apple.com/en-us/102445).

## Acceptance after build authorization

Record the commit, dependency versions, build host/OS, target architecture,
artifact SHA-256, tester, date, result and any exact error/log for each check.
Source tests do not complete the checks below.

- [x] Build on the actual target Mac architecture with the pinned environment;
  inspect PyInstaller warnings, missing imports and bundled Qt Cocoa/image
  plugins, python-docx templates and native dependency architectures.
- [x] Inspect `Prometheus.app/Contents/Info.plist`: validate its syntax, check
  `CFBundleExecutable` exactly matches an executable file in `Contents/MacOS`,
  bundle/display names, identifier, string version fields and bundle icon.
  Confirm About shows the same release version. Keep the Portuguese window
  title and bank suffix intentional and consistent.
- [ ] Double-click the complete `.app` in Finder with Terminal closed. Test
  first launch, quit/relaunch and launching after moving the app to a path
  containing spaces/non-ASCII characters. Check Dock/menu name and icon.
  Distribute the complete app bundle rather than its inner executable.
- [ ] Repeat on a clean Mac, VM or user account without the repository,
  developer virtual environment, custom Qt variables or existing app config.
  Also test the oldest advertised macOS and each advertised architecture.
- [ ] On first run, decline default-bank creation and confirm no `.db` is
  created. Then explicitly create a disposable test bank, restart and verify
  configuration persistence. Use copies for existing/legacy banks; verify
  the backup-protected upgrade and missing-bank recovery without risking
  original teacher data. Preserve the legacy configuration location
  `~/Library/Application Support/GeradorProvasApp/`.
- [ ] Test light and dark themes, filter popups, all three tabs and native
  file dialogs. Check help resizing/scrolling, About/legal text and the Pix
  QR image after Finder launch. Verify Portuguese accents and Retina display.
- [ ] Open an existing test bank; test search, question preview resizing,
  editing, saved-exam reopening, class selection, usage history, fresh-exam
  reset and compatible regeneration. Verify no unexpected writes on opening.
- [ ] Export exams and answer keys with multiple versions, images, accents,
  equations and representative pasted tables/lists. Inspect the resulting
  files in Microsoft Word for ordering, images and matching answers. Retain
  the known table-formatting limitation unless its behavior is separately
  specified and fixed. Test cancelling a save and an unwritable destination.
- [ ] Repeat core workflows offline; examine the app log and macOS crash
  reports for startup failures, Qt plugin errors and uncaught exceptions.
- [x] Inspect signature validity and Gatekeeper assessment separately; for
  example use `codesign --verify --deep --strict --verbose=2`,
  `codesign -dv --verbose=4`, and `spctl --assess --type execute --verbose=4`
  against the built `.app`. Record the signing identity and exact outcomes.
  For a notarized distribution, validate its ticket as well.
- [ ] Download the actual distributed archive on a clean target and launch
  from Finder with normal quarantine protections intact. Verify extraction
  preserves bundle contents/permissions and test any move to Applications.
  Record first-launch prompts; clearing quarantine is not evidence that the
  distributed app passes Gatekeeper.
- [ ] Mount the actual DMG and confirm the initial compact window, readable
  Portuguese background, arrow alignment, native icon positions and Retina
  appearance. Drag `Prometheus.app` to the `Aplicativos` shortcut, eject the
  volume and launch the copied app from Applications. Check Finder Get Info
  reports the same version as About. Ensure the packaged bundle's signature
  remains valid after distribution and copying.

## Release decision

Keep packaged-app acceptance, publication and the release tag pending until
the required target checks pass and findings are resolved or explicitly
accepted by the owner. Historical source/platform confirmations do not verify
the next packaged artifact.
