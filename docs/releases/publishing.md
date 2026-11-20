# Publishing Prometheus 2.0.0

This is a preparation guide for the owner. No source commit, push, tag or
GitHub release was created by the cleanup task. The repository is
[pedrotrevis1/prometheus-banco-de-questoes](https://github.com/pedrotrevis1/prometheus-banco-de-questoes).

## Files to attach to the release

The files prepared on their respective platform build hosts are:

| Local file | GitHub release asset name |
|---|---|
| `dist/Prometheus-2.0.0-mac-arm64.dmg` | `Prometheus-2.0.0-mac-arm64.dmg` |
| `dist/SHA256SUMS.txt` | `SHA256SUMS.txt` |
| `dist/macos-build-info.json` | `macos-build-info.json` |
| `dist/Prometheus.exe` | `Prometheus.exe` |
| `dist/SHA256SUMS-windows.txt` | `SHA256SUMS-windows.txt` |
| `dist/windows-build-info.json` | `windows-build-info.json` |

The DMG targets Apple Silicon on macOS 15.0 or newer, with ad-hoc signing and
no Apple notarization. `dist/Prometheus.app` is retained for local use and is
already inside the DMG. The redundant raw executable was removed.

Windows 2.0.0 is locally verified on Windows 11 x64; it needs no installer or
Python installation. See the [Windows acceptance report](../../specs/019-windows-distribution/acceptance.md).
The current Windows checkout contains the Windows assets; collect the macOS
assets from their build host. The Windows style correction changes `app.py`;
the previous macOS provenance identifies an earlier snapshot. Rebuild/revalidate
macOS before claiming its artifact matches this updated release source.

Keep `dist/` ignored by Git. Attach the six files above through GitHub
Releases rather than force-adding binaries to source history. Commit the
reviewed source, packaging configuration, regression tests, specs, documents
and deletion of tracked caches/Finder metadata. Retain design originals.
Personal banks/configuration, local environments and generated test outputs
are not release assets.

## Verify before uploading

From the repository root on macOS:

```sh
(cd dist && shasum -a 256 -c SHA256SUMS.txt)
codesign --verify --deep --strict --verbose=2 dist/Prometheus.app
git diff --check
git status --short
```

For the Windows files, from the repository root in PowerShell:

```powershell
Get-FileHash .\dist\Prometheus.exe -Algorithm SHA256
Get-Content .\dist\SHA256SUMS-windows.txt
git diff --check
```

Compare the hash with the checksum and `artifact.sha256` in
`windows-build-info.json`; check every `source_and_packaging_sha256` entry
against its source file before uploading. The Windows artifact passed 429
source tests (one POSIX-only case skipped), 13 compiled-code Word checks and
native startup/exit with isolated profiles. Clean-machine, downloaded-file and
Microsoft Word visual checks remain unperformed.

Confirm runtime and packaging content still matches the built provenance:

```sh
python - <<'PY'
from pathlib import Path
import hashlib
import json

manifest = json.loads(Path('dist/macos-build-info.json').read_text())
for section in ('source_sha256', 'packaging_sha256'):
    for name, expected in manifest[section].items():
        path = Path(name)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == expected, f'Rebuild required: {name}'
print('Runtime and packaging content match the prepared build.')
PY
```

The manifest records the source commit at build time and the dirty-worktree
flag. Documentation/cache-only cleanup does not change the executable.
If runtime code, packaging, assets or dependencies change, rebuild and
regenerate checksum/provenance before attaching the files.

Review the [macOS checklist](macos-acceptance.md) and
[local acceptance evidence](../../specs/017-macos-distribution/acceptance.md).
Local checks passed, but native save-panel automation, clean-machine/minimum-OS
testing, downloaded quarantine behavior and visual checks in Microsoft Word
remain unperformed. Keep the release as a draft, or use a prerelease if that
matches the owner's intended distribution stage, until required acceptance is
signed off. A valid ad-hoc signature is not a successful Gatekeeper assessment.

## Prepare and publish on GitHub

1. Review and commit the intended source changes, including new untracked
   packaging/tests/spec files and deletion of the tracked generated files.
   Push the reviewed branch and merge it into the intended release branch.
2. In the repository, open **Releases → Draft a new release**.
3. Choose or create tag **`v2.0.0`** at the reviewed release commit. If that
   tag already exists, inspect it before proceeding; do not replace it casually.
4. Set a title such as **Prometheus 2.0.0 — Windows x64 e macOS Apple Silicon**.
5. Paste [v2.0.0-notes.md](v2.0.0-notes.md) into the release description.
6. Attach the six files listed above, using their exact names, after collecting
   and revalidating the assets on their respective build hosts.
7. Review the compatibility, signing and remaining-check statements, choose
   the appropriate draft/prerelease status, then publish when ready.
8. After publication, download the DMG and checksum from the release page,
   verify the checksum and complete the downloaded-artifact/clean-machine
   checks. Record any result before treating distribution acceptance as complete.

GitHub's [official release guide](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
describes draft releases, tags, targets and binary attachments.
