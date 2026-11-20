# Roadmap

Last updated: 2026-11-19

Follow the dependencies and the ordered tasks within each iteration. Iteration
006 is implemented with automated checks; platform and release checks remain.
Spec 005 passed owner-led manual checks and an
exhaustive automated comparison of the supplied biology bank; see its
[acceptance report](../specs/005-schema-normalization/acceptance.md).
New planning documents do not mean that prerequisites have been implemented.
The owner reported a remaining preview-resize defect on 2026-11-18, supported
by a screen recording. Spec 010 fixes the reported defect; the owner confirmed all scenarios checked
and accepted the implementation.

The owner requested plans for compact question cards and a fresh-exam action
on 2026-11-18. Spec 011 is done; the owner accepted closure with the unperformed native checks documented.
Spec 012 is done; the owner confirmed the visual test and authorized T009 closure. The owner confirmed that "Nova prova" resets selection, class, generation
options and filters, then returns to search. See the
[implementation handoff](card-and-new-exam-workflow.md).

| # | Spec | Goal | Depends on | Status |
|---|---|---|---|---|
| 000 | [baseline](../specs/000-baseline/spec.md) | Document the released v1.1 behavior | — | Done |
| 001 | [project-foundation](../specs/001-project-foundation/spec.md) | Make the project buildable, testable and versioned, with no behavior change | — | Done (historical standalone move commit waived by owner) |
| 002 | [data-safety](../specs/002-data-safety/spec.md) | Reduce ways to lose or misplace a question bank | 001 foundation | Done |
| 003 | [question-editing](../specs/003-question-editing/spec.md) | Edit and duplicate existing questions | 002 | Done |
| 004 | [exam-document-quality](../specs/004-exam-document-quality/spec.md) | Version labels, faithful images, chosen order and answer keys | 001 | Done |
| 005 | [schema-normalization](../specs/005-schema-normalization/spec.md) | Relational categories and alternatives, real text search | 002, 003 | Done; biology-bank and Word acceptance verified |
| 006 | [saved-exams-and-history](../specs/006-saved-exams-and-history/spec.md) | Save exams, see where each question was used | 005 | Implemented; platform checks pending |
| 007 | [search-pagination](../specs/007-search-pagination/spec.md) | Browse 50 question cards per page with bounded content reads and persistent selection | 001, 002 | Done |
| 008 | [source-year-range](../specs/008-source-year-range/spec.md) | Optional inclusive "Desde" / "até" source-year filtering without rewriting legacy values | 007 | Done |
| 009 | [preview-resize](../specs/009-preview-resize/spec.md) | Reproduce and fix question-preview resizing without stretching the outer UI | 008 (execution sequence) | Done; visible-resize follow-up completed in 010 |
| 010 | [preview-visible-resize](../specs/010-preview-visible-resize/spec.md) | Make preview growth visibly enlarge its card and reflow later cards without clipping | 009 implementation | Done; owner confirmed all scenarios checked |
| 011 | [compact-question-cards](../specs/011-compact-question-cards/spec.md) | Readable metadata, stacked compact actions, usage count and on-demand history | 006, 007, 009/010 | Done; owner accepted remaining unperformed native checks |
| 012 | [new-exam-workflow](../specs/012-new-exam-workflow/spec.md) | Start a fresh exam safely, resetting selection/options/filters without restarting | 006, 007/008; execute after 011 | Done; visual acceptance confirmed by owner |
| 013 | [dark-theme-consistency](../specs/013-dark-theme-consistency/spec.md) | Keep generate surfaces and filter popups consistent in dark mode | 012 | Implemented |
| 014 | [help-dialog-layout](../specs/014-help-dialog-layout/spec.md) | Make the Ajuda guide wide, resizable and scrollable | 013 | Implemented |
| 015 | [help-and-legal-copy](../specs/015-help-and-legal-copy/spec.md) | Refresh help guidance and add legal fine print to Sobre | 014 | Implemented |
| 016 | [official-app-icon](../specs/016-official-app-icon/spec.md) | Use the supplied official icon in runtime and packaged artifacts | 015 | Implemented |
| 017 | [macos-distribution](../specs/017-macos-distribution/spec.md) | Prepare a compact drag-to-Applications disk image and consistent Finder version metadata | 016 | arm64 app/DMG built for macOS 15+; local checks passed, remaining native acceptance documented |
| 018 | [repository-release-preparation](../specs/018-repository-release-preparation/spec.md) | Remove disposable repository artifacts and prepare public documentation/release assets | 017 local build | Done; 866 MiB cleaned, release docs/assets prepared, no publication performed |
| 019 | [windows-distribution](../specs/019-windows-distribution/spec.md) | Build and verify the Windows executable and update release documentation | 018 | Windows x64 built; 429 tests passed (one POSIX skip), 13 compiled Word checks and native startup/exit passed; publication pending |

## Owner-requested search fixes (2026-11-16)

The owner requested plans for these three issues and confirmed 50 results per
page and that the resize symptom concerns a question-card preview. Specs
007–009 were implemented with platform checks marked complete. The owner later
reported preview clipping/no visible card reflow; 010 resolved that
follow-up. See
[the agent handoff](search-tab-fixes.md).

Proposed next priority after 001/002: **007 → 008 → 009**, before the broader
feature work in 003–006. Their higher numbers identify new specs, not a need
to wait for 006. This sequence and 005 verification are complete; 006 is implemented. The owner chose to retain the existing bulk deletion behavior, including
selected questions hidden by a filter.

007/008 do not require 005's schema normalization: paging uses the existing
schema and year ranges interpret stored text without a migration. When 005 is
implemented, preserve these public contracts and adapt their query tests.

## Why this order

- **001 before 002.** The safety fixes must ship with tests (constitution V),
  and today nothing can be tested without launching the GUI. 001 is small and
  changes no behavior.
- **002 before everything else that writes data.** It introduces schema
  versioning and automatic backups, which every later migration relies on.
- **003 before 005.** Editing is the most-missed feature and is cheap on the
  current schema; 005 then migrates one well-understood write path.
- **004 is independent** of 002/003 and can be done in parallel or earlier if
  exam output matters more to the owner.

## Planned release

Spec 012 is complete. No release version, build or
publication is assigned by this planning change; existing v2.0.0 source
preparation and remaining release checks retain their recorded scope.

| Release | Contents |
|---|---|
| v2.0.0 | Implemented work in 001–017, including schema 6 and the arm64 macOS package; 018 prepares repository/docs for publication |

The owner skipped the previously suggested v1.2.0 and v1.3.0 releases. The
005/006 implementation and review fixes are included in source preparation for
v2.0.0, and the application version is now 2.0.0. The later 010 resize follow-up is complete and accepted by the owner. On 2026-11-18, the owner
authorized committing, pushing and merging this work while explicitly
excluding app builds. The owner later authorized the arm64 macOS 15+ app and
DMG in 017; those local artifacts are now prepared. Remaining native acceptance,
publication and the release tag are still pending. The Windows build was
subsequently authorized and verified in spec 019. Spec 018
cleans disposable files and prepares the public README/release guidance.
See the [release notes](releases/v2.0.0.md).

On 2026-11-19 the owner authorized the Windows build, verification and README
updates. Spec 019 produced `dist/Prometheus.exe` (2.0.0, x64), checksum and
provenance. The clean Windows 11 environment passed 429 tests with one POSIX
permission case skipped; compiled code produced 13 valid Word files, and the
actual EXE started/exited with isolated empty and synthetic-bank profiles.
A reproduced Windows style-lifetime crash was corrected before building.
See the [Windows acceptance report](../specs/019-windows-distribution/acceptance.md)
for remaining checks and macOS source-snapshot implications. No publication,
commit or tag was performed by this task.

On 2026-11-17, the owner confirmed that the implemented functionality works on
Windows and macOS and requested that all platform checks be marked complete.
The owner also verified the exported files in Word, noting unusual formatting
when exporting tables; its cause remains unconfirmed. Release work remains open.

## Backlog (no spec yet)

- Import/export of question packs to share between colleagues.
- Real equation support (fractions, roots) exported as Word equations.
- More question types (true/false, matching, numeric).
- Persist the chosen theme between sessions.
- Preserve tables and lists from pasted content in the exported exam.
