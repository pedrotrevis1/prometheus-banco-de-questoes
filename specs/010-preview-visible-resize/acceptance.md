# Acceptance: visible preview resizing

**Status: Done; owner confirmed all scenarios checked**

The current source reproduced the reported clipping with isolated synthetic
cards; the pre-fix compact and expanded regression failed, and both pass after
the layout fix. The cause, before/after geometry, environment and limitation
of the simulated pointer are recorded in [reproduction.md](reproduction.md).
The preview sizing policy and stored content were not changed.

On macOS arm64, Python 3.14.5 and Qt 6.11.1 with the offscreen plugin,
`PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` passed: 356 tests.
These include preview bounds, toggling, release and lost-grab cleanup, scroll
positions, image preview/page disposal, shared handles, search and paging.
The geometry regression covers compact and expanded multiple-choice cards,
positive growth, containment, reflow, inverse shrink and unchanged HTML.
Additional offscreen measurements cover essay and wrapped header/usage rows.

On 2026-11-18 the owner confirmed that all scenarios were checked and asked
for the spec to be marked fully complete. This confirmation covers the
remaining scenario and platform checks in T006 and T007, including the
macOS/Windows, theme and scaling scenarios. The owner did not provide separate
per-combination measurements or captures; the synthetic before/after geometry
is recorded in [reproduction.md](reproduction.md). This acceptance records
the owner's report separately from the automated offscreen evidence above.
