# Question cards and new-exam workflow: implementation handoff

**Prepared**: 2026-11-18 | **Status**: 011 done, with owner-accepted unperformed checks; 012 planning only

## Requests and confirmed decision

The owner supplied two screenshots and requested a detailed plan for a future
agent, with no application implementation in this change:

1. Decongest question-card metadata, use bold/regular hierarchy, reduce action
   space and consider stacking buttons. Replace inline usage histories with a
   count and show when the question was used on hover.
2. Add a way to start another exam with a different question selection from the
   third tab, without restarting the application.

In a follow-up choice, the owner explicitly selected **reset everything related
to exam preparation**: empty selection, "Sem turma", default generation settings
and search filters, returning to search. Unsaved changes use Save/Discard/Cancel;
saved exams are preserved. This is recorded in 012's reset table.

The specs propose precise layouts, interaction details and failure handling to
make those requests implementable. Spec 012 remains Draft; do not describe all design
details as separately owner-approved. No unresolved clarification marker was
found in the inspected prerequisite specs. If a new ambiguity appears, ask the
owner and record the answer; never resolve an existing marker yourself.

## Sequence and documents

| Order | Work | Documents |
|---|---|---|
| 1 | Compact card metadata/actions; count and bounded on-demand history | [011 spec](../specs/011-compact-question-cards/spec.md), [plan](../specs/011-compact-question-cards/plan.md), [tasks](../specs/011-compact-question-cards/tasks.md) |
| 2 | Guarded fresh exam; reset selection/options/filters and return to search | [012 spec](../specs/012-new-exam-workflow/spec.md), [plan](../specs/012-new-exam-workflow/plan.md), [tasks](../specs/012-new-exam-workflow/tasks.md) |

Execute sequentially because both touch `prometheus/app.py` and saved-exam/search
tests. 012 does not depend on 011's product behavior; this sequence avoids shared
file conflicts. Existing 006 release/platform work is separate and is not closed
by these plans. Neither change requires a schema migration or new dependency.

## Key implementation decisions

- Card metadata gets labeled rows, bold labels/regular values, a prominent ID,
  and a narrow action column: selection, then expand/edit/duplicate. Keep school
  year distinct from source year and preserve all classifications.
- The resting card shows `Usos: N`, including zero. One use is one completed
  generation containing the question; multiple versions do not multiply it.
  Multiple generations of the same exam do count separately.
- History is a screen-bounded scrollable popup with date, exam and class, newest
  first. Hover reveals it; click/keyboard activation allows extended reading.
  All entries remain reachable. Count queries are page-scoped; details are lazy.
- `Nova prova` gets its own draft-action row, instead of adding another wide
  button to the current six-button row.
- Guard dirty work before reset; cancelled/failed Save leaves the draft/view
  intact. Once authorized, clear global selection in place, explicit order and
  open-exam identity; apply the full reset table and clean snapshot.
- Reset changes no saved rows or output files. Only an explicit Save uses the
  existing persistence path. Newly generated B must not inherit A's saved
  arrangements, name, class or usage links.
- Extract changed formatting/default/dirty/reset rules into the Qt-free domain
  first. Widgets adapt controls/layout/events; queries belong in storage.
  Preserve 009/010's visible preview/card reflow.

## Scope of this documentation change

The original documentation change created the specs and handoff. Spec 011 has since been implemented and tested; its [acceptance report](../specs/011-compact-question-cards/acceptance.md) records the owner-accepted unperformed native checks. Spec 012 has not been implemented.

## Original implementation prompt (historical)

> Implement the owner-requested card and new-exam improvements documented in
> `docs/card-and-new-exam-workflow.md`. Read AGENTS.md, docs/constitution.md,
> docs/roadmap.md, docs/glossary.md and the applicable spec/plan/tasks first.
> Begin with spec 011's next unchecked task, then implement 012 sequentially.
> Revalidate checkout/prerequisites. Work one task at a time in order; tick it
> only after its tests/checks pass. Honor 012's owner-confirmed full reset.
> Ask about newly discovered ambiguity; never guess clarification-marker answers.
> Keep new logic in domain/storage/export with tests and thin Qt adapters;
> preserve 009/010 preview behavior. Use isolated synthetic/in-memory fixtures,
> never the owner's personal bank or normal configuration. Update baseline with
> each behavior implementation; record automated/native acceptance and leave
> unavailable platform checks pending. Report completed task IDs, tests,
> remaining work and blockers. No builds, publishing, merging or tags requested.

For one iteration only, use "Implement spec 011" or, after its completion,
"Implement spec 012", retaining the same constraints.
