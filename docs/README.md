# Project documentation

Prometheus follows Spec-Driven Development: behavior is specified before it is
coded, and the documents here are the source of truth for what the app should do.

Windows 2.0.0 is built and locally verified on Windows 11 x64: 429 source tests
passed (one POSIX-only test skipped), 13 compiled-code Word outputs passed, and
the standalone executable started and exited successfully with isolated empty
and synthetic-bank profiles. The local artifact is `dist/Prometheus.exe`;
GitHub upload/publication remains separate. See the
[Windows acceptance report](../specs/019-windows-distribution/acceptance.md) and
[release publishing guide](releases/publishing.md).

## Map

| Document | Purpose |
|---|---|
| [constitution.md](constitution.md) | Non-negotiable principles and workflow |
| [roadmap.md](roadmap.md) | Ordered list of iterations and their status |
| [architecture.md](architecture.md) | Current structure, target structure, key decisions |
| [glossary.md](glossary.md) | Domain terms, Portuguese ↔ English |
| [search-tab-fixes.md](search-tab-fixes.md) | Owner-requested tab-2 fixes, decisions, source evidence and instructions for future implementation chats |
| [card-and-new-exam-workflow.md](card-and-new-exam-workflow.md) | Specs 011–012 handoff: compact cards, count/hover history and the owner-confirmed fresh-exam reset |
| [../specs/000-baseline/](../specs/000-baseline/spec.md) | What the released app does today, including known defects |
| `../specs/NNN-name/` | One folder per feature: `spec.md`, then `plan.md` and `tasks.md` |

## The three documents of a feature

- **spec.md** — *what* and *why*: user stories, acceptance scenarios,
  requirements, success criteria. No implementation detail.
- **plan.md** — *how*: design, files touched, data changes, test strategy,
  constitution check. Written when the feature is about to be built.
- **tasks.md** — ordered, checkable steps derived from the plan.

Specs 001–010 have implementation plans and tasks; consult the roadmap for
their current delivery/verification status. The owner accepted 010's preview
fix. Spec 011 is done with owner-accepted unperformed checks; spec 012 is done with owner-confirmed visual acceptance.
Their addition records current limitations and proposes changes, without
implementing application behavior. Revalidate paths/prerequisites before starting.

## Conventions

- Requirement IDs: `BL-nnn` (baseline), `FR-nnn` (feature), `KD-nn` (known defect).
- `[NEEDS CLARIFICATION: …]` marks a decision the project owner must make.
  A spec with open markers is not ready for planning.
- Spec status: `Draft` → `Approved` → `In progress` → `Done`.
- The layout matches GitHub Spec Kit, so the folders can be adopted by that
  tool later without rewriting.
