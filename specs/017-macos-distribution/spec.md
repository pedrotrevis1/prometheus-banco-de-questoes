# Feature specification: macOS distribution presentation

**Folder**: `017-macos-distribution` | **Status**: Implemented; native acceptance pending | **Created**: 2026-11-19

## Owner request

Prepare a compact, native-looking disk image using the official Prometheus
icon and either an install action or drag-to-Applications guidance. The owner
delegated that design choice and explicitly prohibited building the macOS
app. This iteration prepares source/configuration and a preview only; it does
not build or mount an app or disk image.

## Acceptance scenarios

1. **Given** the disk-image settings, **then** the initial Finder content area
   is 640 × 420 points in icon view, with toolbar, sidebar, path bar and status
   bar hidden; the app and destination icons are 112 points and have fixed
   positions with labels below them.
2. **Given** the disk image is opened after an authorized future build,
   **then** it shows the actual `Prometheus.app` on the left and an
   `Aplicativos` shortcut targeting `/Applications` on the right, connected by
   a subtle blue arrow. Its Portuguese instructions explain dragging the app
   into that folder and opening it there afterward. No installer process or
   automatic copy is introduced.
3. **Given** the background and visual preview are generated, **then** the
   design uses the existing official application icon, restrained typography,
   a light neutral background and both standard/Retina background assets.
   The preview is explicitly a mockup, not native acceptance evidence.
4. **Given** an app build is later authorized, **then** the PyInstaller
   configuration retains a one-file windowed executable named `Prometheus`,
   bundle `Prometheus.app` and identifier `com.pedrotrevisan.prometheus`;
   `CFBundleShortVersionString` and `CFBundleVersion` are strings read from
   `prometheus.__version__`. Finder and About report that same version.
5. **Given** the packaging command is later run against an existing app,
   **then** it validates the app identity, version, executable and icon, derives
   the disk-image architecture label from the actual executable, and packages
   only that bundle plus the destination shortcut and presentation assets.
   Missing/invalid input or an existing output produces a clear error without
   building an app, replacing an artifact or modifying the source app.
6. **Given** this preparation task is verified, **then** automated checks and
   the visual preview run without invoking PyInstaller, dmgbuild's image
   builder, hdiutil, diskutil, Finder automation or any app/database workflow.
7. **Given** a signed app is copied into the disk image and then installed,
   **then** DMG preparation preserves its strict code-signature validity.
   Packaging does not add FinderInfo attributes to the app to hide its
   extension after signing; normal Finder extension preferences apply.
8. **Given** the frozen app exports an exam or answer key, **then** the
   python-docx package includes physical package directories as well as its
   templates, so footer/header/settings/style template lookups containing
   `docx/parts/../templates/` resolve successfully. Exported files retain page
   footers, answer keys and images without relying on the source environment.
9. **Given** this arm64 release is built, **then** `LSMinimumSystemVersion`
   declares `15.0`, matching the minimum declared by the bundled Qt bindings
   and the owner's supported-OS decision. Packaging rejects a bundle whose
   minimum-OS metadata differs from this release configuration.

## Scope

macOS distribution tooling, assets, bundle metadata and documentation only.
The existing Qt display name and bank-specific window title are preserved.
Native Finder installation, signing, quarantine and clean-machine checks
remain release acceptance work after build authorization.

## Build authorization (2026-11-19)

The owner subsequently authorized compiling the macOS app and asked agents
to stop only for decisions that require the owner. This supersedes the
earlier no-build instruction for T006. Preflight checks passed and missing
development dependencies were installed.

- Target architecture: the owner selected Apple Silicon only (`arm64`).
- Signing: the owner selected an ad-hoc-signed build now, accepting that
  downloaded copies can trigger Gatekeeper warnings. Developer ID signing
  and notarization are not part of this build.
- Runtime checks: after automatic approval review rejected the initial
  proposal, the owner explicitly approved creating a disposable two-question
  bank and temporarily replacing the app configuration, with a verified
  backup restored afterward and both original banks checked unchanged.
- Supported OS floor: after inspecting native binary load commands, the
  owner accepted macOS 15.0 or newer. Older macOS support is out of scope.
- Cleanup: the owner chose to restore the original two-bank configuration
  after using the app during the interruption. Its exact saved bytes were
  restored, preserving the upgraded database files and removing the test entry.
- The owner authorized AppleScript for remaining native app checks, but macOS
  denied assistive access. No privacy setting was changed. Live save-panel
  automation remains unverified; compiled bytecode/UI/export checks run offscreen.

Do not infer a minimum supported macOS version from a build on the current
host. Keep older-OS and clean-machine acceptance pending unless tested.
