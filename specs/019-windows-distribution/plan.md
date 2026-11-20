# Implementation plan: Windows release build and verification

Use the existing Windows Python 3.14 development environment and pinned
dependencies. Run source tests, then invoke `build_windows.ps1` with that
environment's Python first on PATH. Inspect the resulting PyInstaller archive,
PE architecture/icon, resource paths and dependencies. Exercise compiled modules
using a test-only archive loader and isolated synthetic fixtures, then launch
the actual executable with an isolated profile and working directory.

Record checks and limitations in `acceptance.md`; prepare a Windows-specific
checksum/provenance file under ignored `dist/`. Update the public README in
Brazilian Portuguese and internal documentation in English only after passing
local checks. Preserve unrelated macOS documentation and outstanding checks.

## Constitution check

- I: Existing banks/configuration are never opened or modified. Only explicit
  synthetic temporary fixtures are created for regression/packaged checks.
- IV: This spec precedes work. Existing behavior is unchanged; no baseline
  requirement change is needed unless a behavior defect is fixed.
- V: Existing regression tests cover behavior; any packaging fix gets a
  meaningful failing regression before implementation.
- VI: Retain single-file PyInstaller packaging; add no runtime dependency.
- VII: Public instructions stay Brazilian Portuguese; internal reports English.

## Verification

Run pytest without bytecode/cache output; record platform-specific failures
before choosing targeted follow-ups. Verify the final executable independently
of the source startup path and record source/artifact hashes. Check relative
Markdown links and `git diff --check` after documentation updates. Local checks
do not establish clean-machine, minimum-OS, SmartScreen or Word visual acceptance.

## Source-check findings

The Windows style crash is covered by an isolated subprocess test; extract the
style setup into a UI adapter helper and reuse the existing application-owned
style instead of destroying it during every window construction. Existing macOS
packaging tests also need portable path expectations and a Windows skip for the
POSIX execute-bit-only case. These test corrections do not change packaging.
Two theme checks assumed the macOS palette; assert the existing Windows
surface/disabled colors on Windows and additionally check the enabled date
filter. Preserve the established platform-specific themes.
