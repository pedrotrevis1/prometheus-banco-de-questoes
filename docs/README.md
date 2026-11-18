# Project documentation

Prometheus follows Spec-Driven Development: behavior is specified before it is
coded, and the documents here are the source of truth for what the app should do.

## Map

| Document | Purpose |
|---|---|
| [constitution.md](constitution.md) | Non-negotiable principles and workflow |
| [roadmap.md](roadmap.md) | Ordered list of iterations and their status |
| [architecture.md](architecture.md) | Current structure, target structure, key decisions |
| [glossary.md](glossary.md) | Domain terms, Portuguese ↔ English |
| [search-tab-fixes.md](search-tab-fixes.md) | Owner-requested tab-2 fixes, decisions, source evidence and instructions for future implementation chats |
| [../specs/000-baseline/](../specs/000-baseline/spec.md) | What the released app does today, including known defects |
| `../specs/NNN-name/` | One folder per feature: `spec.md`, then `plan.md` and `tasks.md` |

## The three documents of a feature

- **spec.md** — *what* and *why*: user stories, acceptance scenarios,
  requirements, success criteria. No implementation detail.
- **plan.md** — *how*: design, files touched, data changes, test strategy,
  constitution check. Written when the feature is about to be built.
- **tasks.md** — ordered, checkable steps derived from the plan.

Specs 001–009 have implementation plans and tasks; consult the roadmap for
their current delivery and verification status. Spec 010 has a Draft spec,
plan, ordered tasks and recorded visual evidence at the owner's request for
another agent to fix a remaining preview-resize defect. Its addition documents
the existing failure and does not implement a behavior change. Revalidate paths
and prerequisites before beginning implementation.

## Conventions

- Requirement IDs: `BL-nnn` (baseline), `FR-nnn` (feature), `KD-nn` (known defect).
- `[NEEDS CLARIFICATION: …]` marks a decision the project owner must make.
  A spec with open markers is not ready for planning.
- Spec status: `Draft` → `Approved` → `In progress` → `Done`.
- The layout matches GitHub Spec Kit, so the folders can be adopted by that
  tool later without rewriting.
