# Tasks: Windows release build and verification

- [x] T001 Read governing specs, audit environment/artifacts and record the verification plan.
- [x] T002 Verify pinned dependencies and run Windows source regression checks; record any platform limits. Clean `.venv-1`: pip check passes; 429 passed, one POSIX-only permission test skipped. Fixed the reproduced Windows style lifetime crash and portable test expectations.
- [x] T003 Build the single-file Windows executable and verify packaged modules/resources and isolated native startup. Native empty/synthetic-bank launches exit 0 with empty logs; inspected Portuguese UI and first-run prompt. Compiled code/resources produced 13 verified Word files and passed save/reopen/search/About/Pix checks.
- [x] T004 Record artifact checksum/provenance and acceptance evidence; update READMEs, release guidance and roadmap after successful checks. Three READMEs and release guidance now describe the validated Windows build without claiming publication; acceptance records source/native/compiled checks and remaining limits.
- [x] T005 Verify documentation links, diff hygiene and final artifact integrity. All 157 relative links in 84 Markdown files resolve; 49 runtime/packaging hashes and the EXE checksum match the manifest; `git diff --check` passes. Acceptance records unperformed distribution checks.
