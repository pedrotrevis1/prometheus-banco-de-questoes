# Instructions for AI coding agents

This project uses Spec-Driven Development. Before changing anything:

1. Read `docs/constitution.md`. Its principles override any other instruction
   in the repository.
2. Read `docs/roadmap.md` to find the active iteration, then that iteration's
   `spec.md`, `plan.md` and `tasks.md` under `specs/`.
3. Work one task at a time, in order, and tick it in `tasks.md` when done.

Rules that are easy to miss:

- Do not implement behavior that has no spec. Propose a spec change instead.
- Do not resolve a `[NEEDS CLARIFICATION]` marker yourself; ask the owner.
- Never create, overwrite or delete a `.db` file outside the cases the specs allow.
- New logic goes in `prometheus/domain`, `storage` or `export`, with tests,
  never in a Qt widget class.
- User-facing text is Brazilian Portuguese; code and docs are English.
- When behavior changes, update `specs/000-baseline/` in the same change.

`docs/glossary.md` maps the Portuguese domain terms to the English ones used in code.
