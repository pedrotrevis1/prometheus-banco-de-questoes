# Implementation plan: Exam document quality

**Spec**: [spec.md](spec.md) | **Status**: In progress

## Approach

The generated content is copied into the school's own template: do not add a
school header or student fields. Multiple versions use numbered labels and
Portuguese filenames. Preserve existing single-version output except for the
specified page numbering and image-safety improvements.

Add a backup-protected schema 2 → 3 migration for the per-question stable
alternative-order flag. Expose it in question registration/editing and retain
it during duplication; migrations must preserve rows and older column indexes.

Move version generation, output planning, image inspection and document
construction into tested domain/export modules. Qt widgets collect choices,
display warnings and handle files only. Preflight every selected question's
statement, alternatives and included answers before writing any output. Detect
unsupported/unreadable images by question ID; never fetch a network URL. Offer
explicit cancellation/continuation only after warning, as specified. Embed
readable pasted local images; warn when pasted images cannot be read.

Preserve image aspect ratio and stored display size where known, capped to the
printable text width; derive width from a height-only value, and give width
precedence when both stored dimensions conflict. Render exact question order and matching answer keys.
Support separate answer-key files and page/numbered-version footers. Generate
pairwise distinct versions whenever any shuffling is enabled. Check the rendered
exam content before publication; if distinct versions cannot be produced or
verified within bounded attempts, report the failure without publishing duplicates.

All output files are prepared before publication, with explicit confirmation
for every existing target and clear reporting of any partial failure. Preserve
the teacher's banks and use only in-memory or temporary synthetic fixtures.

## Verification

- Test migration backups, rollback and legacy row preservation without Qt.
- Test stable alternatives, answer mapping, ordering and distinct versions.
- Test image preflight, allowed/refused sources, dimensions and malformed data,
  including successful output only after explicit acknowledgement of omissions.
- Test generated DOCX text, footer fields, image and answer-key matching.
- Test UI validation, warnings, per-question setting, ordering and save paths
  using offscreen Qt and temporary files; never open a personal bank.
- Update baseline, help and roadmap; record platform checks that remain pending.

## Constitution check

Schema changes use the existing forward migration and pre-migration backup;
no network requests or new dependencies. Errors and unexportable content are
reported before output. Domain/export logic is outside widgets and tested.
All new user-facing text is Brazilian Portuguese.
