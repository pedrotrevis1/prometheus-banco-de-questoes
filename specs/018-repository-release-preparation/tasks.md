# Tasks: Repository cleanup and release documentation

- [x] T001 Audit repository/generated outputs, validate release artifacts and define database safety gates.
- [x] T002 Remove verified disposable build/test outputs, tracked/untracked caches and redundant raw executable; update ignore rules. Removed 866.0 MiB, including 32 tracked generated files and the validated unlinked synthetic bank. Release artifacts and current configuration are unchanged; see [cleanup.json](cleanup.json).
- [x] T003 Rewrite public README/release notes and maintainer publishing guidance; update stale release-status and retention statements. Public instructions are Portuguese; publishing guidance lists the three preserved release assets and remaining acceptance limits.
- [x] T004 Verify targeted tests, links, source/runtime hashes, artifact signatures/checksums and cleanup results; record acceptance and roadmap status. 45 tests and 149 relative links passed; final artifacts/provenance are unchanged and signatures validate. See [acceptance.md](acceptance.md).
