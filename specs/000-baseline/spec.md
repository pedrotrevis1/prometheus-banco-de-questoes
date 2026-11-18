# Baseline specification: current development behavior

**Status**: Done (describes existing behavior) | **Created**: 2026-11-14
**Source**: reverse-engineered from `Prometheus1.1.py` by static reading; not yet confirmed by running the app.

This is the "as-is" contract. It records what the app does, including behavior
that is wrong. Feature specs describe changes against it, and it is updated
whenever a release changes behavior (constitution IV).

Data structures are in [data-model.md](data-model.md).

## Actors

- **Teacher** — the only user. Registers questions, searches, builds exams.

## Application shell

- **BL-001** The main window has three tabs: "Cadastrar Questão", "Buscar e
  Selecionar Questões", "Configurar e Gerar Prova".
- **BL-002** A sidebar, hidden at start and toggled by the "Menu" button, holds
  discipline management, the theme toggle, "Ajuda" and "Sobre".
- **BL-003** The window title shows the app name and the bank file name.
- **BL-004** Light theme is the default; a button toggles dark mode. The choice
  is not remembered between sessions.
- **BL-005** "Sobre" shows authorship text and a button that displays a Pix
  donation QR code.

## Disciplines and question banks

- **BL-009** Configuration saves replace the existing configuration atomically; if saving fails, the previous configuration, connection, discipline and selection remain active and the user is notified. A newly created bank is retained and its path is reported.
- **BL-010** On first run the app asks before creating the default "Biologia" bank
  at `biologia.db` in the app data directory. Declining creates no bank.
- **BL-011** When the current discipline's name contains "biologia" and its
  category table is empty, 14 default biology categories are inserted.
- **BL-012** "Criar Novo Banco (Disciplina)" asks for a name (rejected if it
  already exists ignoring case and surrounding spaces), then a new file location, and switches to the new bank.
- **BL-013** "Abrir Banco Existente (.db)" asks for a file, then a name, and
  switches to it. Names must be unique ignoring case and surrounding spaces.
- **BL-014** A dropdown switches between registered disciplines; the choice is
  saved as the current discipline.
- **BL-015** Opening an existing bank validates it and backs it up before a schema
  upgrade. Missing files are not created: the app offers to locate the file, remove the
  discipline from the list, or cancel. Unrelated or newer databases are
  rejected, and a successful open clears the selection and reloads the bank. Before
  normalization, the user is warned about incompatibility with older versions and
  can cancel. Unmapped values are identified in an upgrade report.
- **BL-017** "Fazer backup" copies the open bank to a user-selected new file. Before an upgrade, an automatic backup is made; deleting an older backup requires confirmation and happens only after the replacement is published.
- **BL-016** Disciplines can be renamed or removed from the list; removal keeps the bank file on disk.

## Categories

- **BL-020** Categories form a tree of any depth. A new category is created
  from a dialog that asks for a name and an optional parent.
- **BL-021** A name must be non-empty, must not contain `;`, and must be unique
  among siblings.
- **BL-022** Deleting a category (after confirmation) deletes its descendants
  and removes all their names from every question's category list.
- **BL-023** A text box above each tree hides categories that do not match,
  keeping ancestors of matches visible.
- **BL-024** Categories can be renamed and moved, except under themselves or a
  descendant. Their question links follow the category ID. Questions without a
  category remain available through the "Sem categoria" filter.
- **BL-025** Rebuilding category trees after adding, renaming, moving or deleting
  categories preserves checked surviving category IDs in the question form and
  search tree. Deleted IDs are removed from the applied category filter without
  selecting a replacement. The current edit or duplication and unsaved content
  remain in place.

## Registering a question

- **BL-030** Fields: type ("Múltipla Escolha" or "Dissertativa"), difficulty
  ("Fácil", "Médio" default, "Difícil"), school years (6º–9º Ano and/or
  1ª–3ª Série, including years from both segments), source
  (optional), source year (optional free text), categories, statement.
- **BL-031** A question needs at least one category, a segment, at least one
  school year and a non-empty statement (text or image) when saved. A legacy
  segment without a school year remains visible after upgrade without inventing
  a year; unmappable classification values are reported.
- **BL-032** The statement, alternative and expected-answer editors support bold, italic, underline,
  superscript, subscript and strikethrough through a toolbar. The toolbar acts
  on the last focused supported editor.
- **BL-033** "Inserir equação" converts typed text to formatted text: `^` and
  `_` become superscript and subscript, arrows are replaced by symbols, and in
  "Química" mode digits after a letter become subscripts. It is not a
  mathematical equation editor.
- **BL-034** Images can be inserted from a file (png, jpg, jpeg, bmp) or pasted
  from the clipboard. They are scaled down to 500 px wide if larger and stored
  inside the question as PNG.
- **BL-035** A multiple-choice question requires two to five non-empty alternatives
  in order, with exactly one marked "Correta".
- **BL-036** An essay question may have an expected answer; it is optional.
- **BL-036a** A question can be marked to keep its alternative order when
  generating shuffled versions; the setting is preserved when editing or duplicating.
- **BL-037** If the source matches an existing source ignoring case, the
  existing spelling is stored.
- **BL-038** After saving, the form is cleared. Type, difficulty, segment and
  school years keep their values.
- **BL-039** Saved questions can be edited or duplicated from their cards.
  Edits retain the question ID and exam selection; duplicates get a new ID.
  Unsaved changes require confirmation before they are discarded. A successful
  bank change resets edit mode; a cancelled or failed change preserves it.
  Failed question saves roll back and keep the form available for retry. Cards
  show the last-modified time when known.

## Searching and selecting

- **BL-040** Filters: categories (a question matches if it has any checked
  category or its descendants, or no category), visible text contained in the
  statement, alternatives or expected answer (ignoring case and accents), source (partial, ignoring
  case), source-year inclusive optional lower/upper bounds, difficulty, school year, type.
  Invalid or non-numeric stored source years remain visible without bounds and
  are excluded when a bound is active; original source-year text is retained.
  Filters are applied when "Filtrar Questões" is pressed.
- **BL-041** Results are ordered by ID and displayed in pages of at most 50;
  the footer shows the range, total and page controls.
- **BL-042** Each result is a card showing ID, segment and years, difficulty,
  type, categories, source and source year, and a preview of the statement
  with the alternatives (correct one highlighted) or the expected answer.
  Long previews can be expanded and resized. Manual resizing is bounded by
  the result viewport and survives document reflow; toggling resets the fit.
  Cards also list the exam, class and date of each recorded use. Search can
  restrict results to never-used questions or questions not used on or after
  a chosen date.
- **BL-043** Each card has a "Selecionar" checkbox. A counter shows how many
  questions are selected for the exam. The selection is kept while filtering or changing pages
  and can be saved as part of an exam. Unsaved changes prompt for save, discard
  or cancel before closing or switching banks.
- **BL-044** "Navegar pelas questões selecionadas" shows only selected
  questions in pages; leaving it restores the last applied search.
- **BL-045** "Excluir questões selecionadas" permanently deletes every selected
  question after a confirmation that shows the bank name, the count, and names
  of saved exams containing the selected questions.

## Generating an exam

- **BL-050** Selected questions can be reordered before generation; that order
  is used when question shuffling is off. Questions are numbered `1)`, `2)`…,
  with alternatives labelled `A)`–`E)`; supported text formatting is retained.
- **BL-051** Readable pasted local PNG/JPEG images are embedded at paste time.
  Images retain their proportions and stored width, or derive their width from a
  stored height if no width is present; width takes precedence when both are
  specified. Width is capped at the document text width. Before any output,
  unsupported images are reported by question ID; continuation is explicit.
- **BL-052** The answer key is included at the end by default, can be placed in
  a separate matching file, or omitted.
- **BL-053** Multiple versions are numbered and use filenames
  `<name>_Versao_<n>.docx`; the version appears in the document and footer.
  Single-version documents do not show a version label.
- **BL-054** When shuffling is enabled, generated versions must have distinct
  visible question content or generation reports that it could not produce them.
  Version labels, answer keys and incidental text-run boundaries do not make
  student content distinct; text, supported formatting, image data and sizes,
  and question order do.
- **BL-055** Alternative shuffling updates the answer key; questions marked to
  keep their alternative order are not shuffled.
- **BL-056** All outputs are prepared before publication; existing destinations
  require confirmation and a failure reports any files already saved.
- **BL-057** Documents have page numbers and no school header or student
  identification fields; teachers use their school’s own template.
- **BL-058** Named exams retain ordered questions, a managed class and generation
  options. They can be opened, renamed, duplicated or deleted. Deleting an exam
  also removes its usage history after confirmation; questions are retained.
  Refreshing exam and class controls retains the selected class, or selects
  "Sem turma" if it was deleted. Existing usage records keep their class name.
- **BL-059** Completed generation records the date, class, version count and
  included questions. Regeneration retains compatible saved arrangements but
  uses current question content and correct answers. A changed or missing
  question is reported on opening; incompatible arrangements block generation.
  Answer-key inclusion and placement do not change arrangements. Intentional
  question selection, order or version/shuffle changes establish new arrangements
  only after a successful export; cancellation and failure retain the last
  successful arrangements and do not record a completed usage.

## Non-functional baseline

- **BL-060** Fully offline; no network access.
- **BL-061** Distributed for Windows as a single executable built with
  PyInstaller. The source also runs on macOS.
- **BL-062** UI language is Brazilian Portuguese only.

## Known defects and limitations

| ID | Description | Addressed by |
|---|---|---|
| KD-03 | The delete action applies to the exam selection, including questions hidden by the current filter | Retained by owner decision |
| KD-17 | Tables and lists in pasted content are flattened in the exam | Backlog |

Planning note: spec 005 remains subject to owner verification using real banks
and exported documents before release.
