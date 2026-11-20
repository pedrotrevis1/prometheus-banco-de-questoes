# Feature specification: Repository cleanup and release documentation

**Folder**: `018-repository-release-preparation` | **Status**: Complete | **Created**: 2026-11-19

## Owner request

Clean repository files that can safely be deleted, including generated test
outputs, and rewrite README.md so the owner can push version 2.0.0 and attach
the macOS DMG to a GitHub release. This authorizes local preparation only;
no commit, push, tag or public release is performed by this iteration.

## Acceptance scenarios

1. **Given** the repository contains generated build/test intermediates,
   caches and Finder metadata, **then** cleanup removes them, including tracked
   `.pyc`/`.DS_Store` files, without removing source, regression tests, specs,
   design originals, the development environment or Git history.
2. **Given** the final app/DMG/checksum/manifest in `dist/`, **then** they remain
   intact, the DMG checksum and app signature still validate, and only the
   redundant standalone `dist/Prometheus` executable is removed there.
3. **Given** `build/macos-runtime/acceptance-bank.db` is considered for deletion,
   **then** it may be deleted only when the previous acceptance session is
   recorded as restored, the current app configuration references no bank
   under `build/`, and inspection confirms exactly the generated two-question
   fixture and generated exam names. No other database may be deleted. If a
   check fails, preserve the database and ask the owner before dependent cleanup.
4. **Given** a teacher reads README.md, **then** it accurately describes
   features, the arm64/macOS 15+ installer, ad-hoc signing, installing and
   opening banks, backup/upgrade precautions, known limitations, privacy and
   rights. Public-facing guidance remains Brazilian Portuguese.
5. **Given** the owner prepares a GitHub release, **then** documentation lists
   the DMG, checksum and provenance manifest to attach as release assets,
   distinguishes them from source commits, and includes paste-ready release
   notes without claiming that publication or pending native checks happened.
6. **Given** cleanup finishes, **then** targeted tests and Markdown link checks
   pass, no generated caches remain outside the retained environment, and the
   app/runtime packaging file hashes still match the built release manifest.

## Scope

Repository hygiene and documentation only. No app behavior, schema, data
location, runtime dependency, release version or executable payload changes.
The pending manual checks in spec 017 remain documented; they are not closed
by cleanup. The baseline behavior specification needs no further change.
