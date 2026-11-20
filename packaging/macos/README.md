# macOS release tooling

The owner authorized an Apple Silicon (`arm64`) build for macOS 15.0 or newer,
using ad-hoc signing. The app and DMG were built and locally checked under
spec 017. See the [acceptance report](../../specs/017-macos-distribution/acceptance.md)
for evidence and remaining native/clean-machine checks. No Developer ID
signature or notarization is provided by this configuration.

Windows 2.0.0 has also been built and locally verified on Windows 11 x64 under
[spec 019](../../specs/019-windows-distribution/acceptance.md). Its standalone
`dist/Prometheus.exe` is a separate release asset; this directory contains only
macOS tooling. GitHub publication remains an owner step.

## Visual preview only

From the repository root, using the prepared development environment:

```sh
python packaging/macos/render.py --preview /tmp/prometheus-dmg-preview.png
```

This renders an approximation of Finder with the official app icon and the
local system Applications icon; it does not compile, create/mount a disk
image, automate Finder or open any question bank. Only the SVG background
is part of the DMG presentation assets; the app and folder in the DMG are
real Finder items. The native folder icon can vary between macOS versions.

## App build, when authorized

```sh
./build_macos.sh
```

The checked-in `Prometheus.spec` preserves one-file/windowed packaging,
official icon and Pix assets. It sets the executable name `Prometheus`, bundle
name `Prometheus.app`, and stable identifier. Both Finder version fields are
read from `prometheus/__init__.py`; no release version is duplicated here.
The Qt display name and bank-specific window title remain unchanged.
`LSMinimumSystemVersion` declares the agreed macOS 15.0 floor, matching the
bundled Qt binding binaries. The physical python-docx package tree is included
alongside its templates so paths containing `docx/parts/../templates/` resolve
after extraction when creating document footers and headers.

Build on the actual target architecture and inspect the artifact before
packaging. Signing/notarization configuration and compatibility claims still
require the decisions in the [release checklist](../../docs/releases/macos-acceptance.md).

## DMG packaging, when authorized

Install `requirements-dev.txt` first; the macOS-only `dmgbuild` dependency is
release tooling and is not bundled into the application.

```sh
./build_macos_dmg.sh
# Or use an existing bundle/output at explicit locations:
./build_macos_dmg.sh --app "/path/to/Prometheus.app" --output "/path/to/release.dmg"
```

The command never invokes PyInstaller. It validates bundle names, identifier,
version, executable permissions and icon, then reads actual executable slices
with `lipo`. Default output is
`dist/Prometheus-<version>-mac-<architecture>.dmg`, where architecture is
`arm64`, `x86_64` or `universal2` as observed in the supplied executable.
This label does not replace native compatibility tests.

The source bundle is copied without changing its plist or re-signing it.
The image also contains the `Aplicativos` symlink to `/Applications` and its
presentation metadata/background. Finder starts in icon view with a
640 × 420 window bounds, fixed 112-point icons, and no toolbar/sidebar/status
bar. Installation is a normal drag/copy; no installer executable is supplied.
`render.py` creates normal and `@2x` PNGs for dmgbuild's Retina handling.
The signed app is not passed to SetFile to hide its extension: adding
FinderInfo after signing makes strict signature verification fail. Normal
Finder extension preferences apply.

Image creation uses a temporary directory alongside the output, then publishes
the completed artifact atomically without replacing an existing file. Failures
remove temporary presentation/partial-image files and report the error.

The real DMG must still pass the mounted-Finder, drag-copy, version, signature,
quarantine and clean-machine checks in the release checklist. The preview and
mocked packaging tests are not native acceptance evidence.
