# Feature specification: Windows release build and verification

**Folder**: `019-windows-distribution` | **Status**: Done (local checks passed; distribution limits recorded) | **Created**: 2026-11-19

## Owner request

Build the Windows version, check that it works, and update the READMEs when
verification succeeds. This authorizes local build and documentation changes;
GitHub publication, commits and tags are outside this request.

## Acceptance scenarios

1. Given Windows and the pinned development dependencies, the existing build
   command produces a single windowed `dist/Prometheus.exe` for version 2.0.0,
   containing the official executable/runtime icons and Pix image.
2. The source regression suite runs on Windows, with platform-specific limits
   and any failures recorded honestly.
3. The actual executable starts from an unrelated working directory with an
   isolated user profile, displays the first-run prompt and application window,
   and exits without a crash. No real user bank or configuration is modified.
4. Packaged application modules can create a synthetic bank, register/search
   questions, save/reload exams and export valid Word documents with footers,
   matching answer keys and images. Test banks/backups may be created only in
   dedicated temporary test directories; existing user databases are untouched.
5. Successful checks are recorded with artifact SHA-256, dependency/platform
   details and remaining manual limits. READMEs and release guidance describe
   the validated local Windows artifact without claiming GitHub publication,
   clean-machine compatibility or unperformed Microsoft Word visual checks.

## Scope

Build and verification of existing behavior specified in 001 and 016. No app
behavior, schema, release version or minimum Windows compatibility changes.
Packaging fixes, if necessary, require a reproduced failure and regression test.

## Verification-discovered correction

The initial Windows suite crashes with an access violation while replacing the
application-wide selection style during successive window construction. Given
an existing application selection style, constructing another window must reuse
it so widgets retaining that style remain valid. Cover this with a subprocess
regression and update the baseline; no question-bank behavior changes.
