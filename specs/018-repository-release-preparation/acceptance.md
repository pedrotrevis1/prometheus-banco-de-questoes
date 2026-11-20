# Acceptance report: Repository cleanup and release documentation

**Date:** 2026-11-19. **Status:** complete; local preparation only.

## Cleanup performed

- Removed **866.0 MiB** of reproducible build/test intermediates, rejected
  installers, diagnostic outputs, temporary configuration copies and the
  redundant raw `dist/Prometheus` executable.
- Removed **32 accidentally tracked generated files** from the working tree,
  ready to stage as deletions, plus untracked caches. Ten cache directories
  and five Finder metadata files were removed. Source/test/spec/design files,
  `.venv` and `.git` were preserved.
- The only removed database was the spec-authorized
  `build/macos-runtime/acceptance-bank.db`. It contained exactly the two known
  generated questions, the generated category and test exam names, and no
  legacy questions. The prior session was marked restored and the current
  app configuration referenced no database under `build/`.
- The current app configuration was hashed before/after cleanup and is
  unchanged. External teacher databases were not modified or deleted.
- Retained the final app, DMG, checksum and provenance manifest under ignored
  `dist/`. [cleanup.json](cleanup.json) records deletion counts and preserved files.

## Documentation prepared

- Rewrote [README.md](../../README.md) in Brazilian Portuguese for teachers,
  including requirements, installation, checksum verification, workflow,
  bank/backups, upgrade precautions, limitations, privacy and rights.
- Added [public release notes](../../docs/releases/v2.0.0-notes.md) and the
  [maintainer publishing guide](../../docs/releases/publishing.md).
- Corrected stale source-only/build-pending status and statements that
  disposable diagnostic files remained available after cleanup.
- Preserved spec 017's unperformed native acceptance items rather than
  closing them as part of documentation work.

## Release asset integrity

The DMG SHA-256 before and after cleanup is:

```text
4fac0ef532dfc9c0f7e464c996774ae4475c631ec7ec8ece01e51bdcaa6ef028
```

The app and all release-support files were also hashed and remain unchanged.
The runtime and packaging file digests in `dist/macos-build-info.json` remain
the provenance reference for the prepared binary; documentation/cache cleanup
does not require a rebuild.

## Final verification

- **45 targeted tests passed**, with bytecode and pytest cache generation
  disabled for both the parent test run and its subprocess.
- **149 relative Markdown/image links checked**, with no missing targets.
- DMG checksum, runtime/packaging provenance hashes and strict app signature
  all validate. App Info.plist and shell-script syntax checks pass.
- Database/sidecar and release-output ignore patterns work; the checked-in
  macOS PyInstaller spec remains eligible for tracking.
- All previously tracked Python source/test files are present, and the 32
  generated tracked files are ready to be committed as deletions.
- `git diff --check` passes. No commit, push, tag, publication or application
  rebuild was performed. Pending native acceptance remains in spec 017.
