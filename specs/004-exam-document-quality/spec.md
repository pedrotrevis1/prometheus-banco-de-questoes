# Feature specification: Exam document quality

**Folder**: `004-exam-document-quality` | **Status**: In progress | **Created**: 2026-11-14
**Fixes**: KD-08, KD-09, KD-10, KD-11 | **Plan**: [plan.md](plan.md) | **Tasks**: [tasks.md](tasks.md)

## Why

The generated Word file is the product the teacher actually hands to students.
Printed versions cannot be told apart, some images disappear without warning,
and the question order is fixed by database ID. The resulting file is intended
for copying into the school’s own template, not for adding a school header.

## User stories

### US1 — Every printed sheet identifies itself (P1)

**Acceptance scenarios**

1. **Given** multiple versions, **when** the files are generated, **then** each
   document shows its version label on the first page and in the page footer,
   and its answer key carries the same label.
2. **Given** a single version, **when** it is generated, **then** no version
   label is shown.

### US2 — Use the school's own template (P1)

1. **Given** any generated exam, **then** no school header, student identification
   line or school-specific template is added. The teacher can copy the questions
   into the template provided by their school.

### US3 — No image is lost silently (P1)

**Acceptance scenarios**

1. **Given** content pasted from Word or a browser that contains images,
   **when** it is pasted, **then** each image the app can read is embedded in
   the question; for each it cannot, I am told at paste time.
2. **Given** selected questions that contain an image the exporter cannot
   place, **when** I generate, **then** I am shown the affected question IDs
   and can cancel or continue; nothing is omitted without that notice.
3. **Given** an image narrower than the page, **when** exported, **then** it
   keeps its proportions and stored size; wider images are reduced to the text
   width. If only a height is stored, derive the width from the original
   proportions. If both dimensions are stored and conflict with those
   proportions, use the stored width and derive the height.

### US4 — I decide the order of questions (P2)

**Acceptance scenarios**

1. **Given** selected questions, **when** I open the generation tab, **then** I
   see them listed and can move them up and down; the single-version exam
   follows that order.
2. **Given** multiple versions with question shuffling off, **when** generated,
   **then** every version follows my order.

### US5 — The answer key can be kept apart (P2)

**Acceptance scenarios**

1. **Given** the option "Gabarito em arquivo separado", **when** I generate,
   **then** each version produces an exam file without the key and a matching
   key file.

### US6 — Versions are really different (P2)

**Acceptance scenarios**

1. **Given** multiple versions with any shuffling enabled, **when** generated,
   **then** no two versions are identical, or I am told that the requested
   number of distinct versions is not possible.

## Requirements

- **FR-001** Version labels appear in the document body and footer and on the
  answer key.
- **FR-002** Do not add a school header, student identification lines, or
  school-specific template. The user copies the generated questions into their
  school's own template.
- **FR-003** Multiple-version labels use numbers, and filenames use Portuguese
  `_Versao_1.docx` spelling.
- **FR-004** Pasted or inserted images are embedded in the question at input
  time whenever they can be read locally. The app makes no network request to
  fetch images (constitution II).
- **FR-005** Before writing any file, the exporter checks all selected
  questions and reports content it cannot export, by question ID.
- **FR-006** Images are exported at stored size, capped at the text width, in
  JPEG and PNG at least.
- **FR-007** The user can order the selected questions; the order is used
  wherever questions are not shuffled.
- **FR-008** The answer key can be placed at the end of the exam (default) or
  in a separate file.
- **FR-009** When shuffling is enabled, generated versions are pairwise distinct
  or the user is told the requested number is unavailable.
- **FR-010** Page numbers appear in the footer.
- **FR-011** A question can be marked to keep its alternatives in their original
  order, including when alternative shuffling is enabled. This setting persists.

## Success criteria

- A teacher can copy the generated questions into their own school template.
- A printed page from any version can be matched to its answer key.
- KD-08 cannot be reproduced.

## Out of scope

Custom Word templates and logos; PDF output; tables and lists fidelity (KD-17);
real equation objects; saving the exam for later (spec 006).

## Owner decisions

- Use numbered labels ("Versão 1", "Versão 2", …).
- Use Portuguese version filenames (`_Versao_1.docx`).
- Do not add a school header or student identification lines; the user copies
  questions into the school's own template.
- Allow each question to be marked to prevent alternative shuffling.
- When both stored image dimensions conflict with the original aspect ratio,
  use the stored width and preserve the original proportions.
