# Implementation plan: Repository cleanup and release documentation

## Approach

Audit ignored and tracked outputs before deleting. Retain the final app,
DMG, SHA256SUMS.txt and macos-build-info.json under ignored `dist/`; remove
the redundant raw executable. Remove `build/` only after the database-specific
safety gates in this spec pass. Its earlier rejected images, temporary
configuration backups, logs and generated Word/screenshot fixtures are
disposable now that results are recorded and the original app configuration
was restored. Do not touch the current configuration or external banks.

Remove `.DS_Store`, Python bytecode/cache directories and `.pytest_cache`
outside `.git`/`.venv`, including accidentally tracked copies. Preserve test
source and the checked-in macOS PyInstaller spec. Extend ignore patterns for
SQLite sidecars so local bank data cannot be added accidentally.

Rewrite the teacher-facing README in Brazilian Portuguese, deriving repository
links from the configured GitHub remote. Keep internal publishing instructions
in English and provide a separate Portuguese release body. Update stale
source-only status and artifact-retention statements in the release reports.
Use GitHub's release UI guidance and Apple's official app-opening guidance.

## Constitution check

- I: The only permitted database deletion is the validated generated fixture
  named in acceptance scenario 3. Real banks/configuration are not modified.
- IV: This spec precedes cleanup; baseline behavior is unchanged.
- V: Regression tests are retained and rerun after bytecode removal.
- VI: Use existing Python/standard-library tooling; add no dependency.
- VII: Public installation/release text is Portuguese; internal specs and
  maintainer instructions are English.

## Verification

Record final artifact checksums before and after cleanup. Validate runtime and
packaging hashes against macos-build-info.json, the app's strict signature,
the known fixture contents, absence of current references to `build/`, and
successful prior restoration. Run the existing targeted packaging/export
suite with bytecode and pytest cache generation disabled. Check Markdown
relative links, `git diff --check`, source/test retention and final output sizes.

No additional application build or new test implementation is needed for
this documentation/cache cleanup.
