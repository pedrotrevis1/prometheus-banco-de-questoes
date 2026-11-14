# Feature specification: Exam document quality

**Folder**: `004-exam-document-quality` | **Status**: Draft | **Created**: 2026-11-14
**Fixes**: KD-08, KD-09, KD-10, KD-11 | **Plan**: to be written when this iteration starts

## Why

The generated Word file is the product the teacher actually hands to students.
Today it has no header, printed versions cannot be told apart, some images
disappear without warning, and the question order is fixed by database ID.

## User stories

### US1 — Every printed sheet identifies itself (P1)

**Acceptance scenarios**

1. **Given** multiple versions, **when** the files are generated, **then** each
   document shows its version label on the first page and in the page footer,
   and its answer key carries the same label.
2. **Given** a single version, **when** it is generated, **then** no version
   label is shown.

### US2 — The exam has a proper header (P1)

**Acceptance scenarios**

1. **Given** the generation tab, **when** I fill in school, teacher, subject,
   class, date, exam title and instructions, **then** the document starts with
   them, followed by lines for the student's name and number.
2. **Given** I generated an exam before, **when** I return to the tab, **then**
   school, teacher and instructions are pre-filled with my last values.
3. **Given** all header fields empty, **when** I generate, **then** the
   document starts with the student name line only.

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
   width.

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
- **FR-002** Header fields: school, teacher, subject (default: discipline
  name), class, date, title, instructions; all optional. Student name and
  number lines are always present.
- **FR-003** School, teacher and instructions are remembered between sessions.
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
- **FR-009** Generated versions are pairwise distinct.
- **FR-010** Page numbers appear in the footer.

## Success criteria

- A teacher can hand out the generated file without editing it in Word first.
- A printed page from any version can be matched to its answer key.
- KD-08 cannot be reproduced.

## Out of scope

Custom Word templates and logos; PDF output; tables and lists fidelity (KD-17);
real equation objects; saving the exam for later (spec 006).

## Open questions

- [NEEDS CLARIFICATION: Version labels as letters (Versão A, B, …) or numbers?
  With up to 999 versions, numbers are simpler; letters are what teachers
  usually print.]
- [NEEDS CLARIFICATION: Should output file names be Portuguese
  (`_Versao_1.docx`) instead of `_Version_1.docx`?]
- [NEEDS CLARIFICATION: Which header layout does the owner's school use? A
  sample exam would settle FR-002.]
- [NEEDS CLARIFICATION: Should questions with "todas/nenhuma das anteriores"
  be markable as "do not shuffle alternatives"?]
