# Tasks: Optional source-year range

**Plan**: [plan.md](plan.md) | **Status**: In progress

Do tasks in order, one at a time; mark only after validation. The owner requested the next iteration while platform checks remain pending.

- [x] T001 Read the handoff and spec/plan; verify 007 implementation and module layout. The owner checked macOS and requested the next iteration; detailed platform checks remain pending.
- [x] T002 Add failing domain tests for the spec's complete optional-bound/legacy-year table, inclusive endpoints, malformed input, inverted bounds and integer limits.
- [x] T003 Implement pure year parsing/range validation and extend the applied-filter model; pass T002 with no Qt or I/O in domain code.
- [x] T004 Add failing in-memory query tests for lower-only/upper-only/equal bounds, unknown legacy years, numeric rather than lexical ordering, combined filters, selected-only bypass and count/page agreement across more than 50 matches.
- [x] T005 Add the shared conversion function and parameterized range predicates to storage; pass T004 and verify that all stored values/schema stay unchanged and search issues no writes.
- [x] T006 Replace the exact-year input with labeled optional "Desde" / "até" text fields and tooltips. Connect Enter from either to the shared Apply action; validation must precede filter/page/mode changes. Add offscreen checks for both success and failure paths.
- [ ] T007 Automated domain/storage/UI regressions cover hidden selections, unapplied edits, equal-year searches and combined filters. The owner reports the macOS version works correctly. Detailed sidebar/theme checks and Windows checks remain pending.
- [x] T008 Update Help, BL-040, KD-18 and roadmap to the delivered range behavior. Keep the spec 005 numeric-storage mapping question open; record checks actually performed and remaining platform coverage.
