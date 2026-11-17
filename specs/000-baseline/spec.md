# Baseline specification: Prometheus v1.1 as released

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
  rejected, and a successful open clears the selection and reloads the bank.
- **BL-017** "Fazer backup" copies the open bank to a user-selected new file. Before an upgrade, an automatic backup is made; deleting an older backup requires confirmation and happens only after the replacement is published.
- **BL-016** Disciplines can be renamed or removed from the list; removal keeps the bank file on disk.

## Categories

- **BL-020** Categories form a tree of any depth. A new category is created
  from a dialog that asks for a name and an optional parent.
- **BL-021** A name must be non-empty, must not contain `;`, and must be unique
  across the whole tree.
- **BL-022** Deleting a category (after confirmation) deletes its descendants
  and removes all their names from every question's category list.
- **BL-023** A text box above each tree hides categories that do not match,
  keeping ancestors of matches visible.
- **BL-024** Categories cannot be renamed or moved.

## Registering a question

- **BL-030** Fields: type ("Múltipla Escolha" or "Dissertativa"), difficulty
  ("Fácil", "Médio" default, "Difícil"), segment ("Ensino Fundamental" or
  "Ensino Médio" default), school years (6º–9º Ano, or 1ª–3ª Série), source
  (optional), source year (optional free text), categories, statement.
- **BL-031** A question needs at least one category, a segment, at least one
  school year and a non-empty statement (text or image).
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
- **BL-035** A multiple-choice question requires all five alternatives A–E to
  be non-empty and exactly one marked "Correta".
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
  category), text contained in the statement, source (partial, ignoring
  case), source-year inclusive optional lower/upper bounds, difficulty, school year, type.
  Invalid or non-numeric stored source years remain visible without bounds and
  are excluded when a bound is active; stored text is never rewritten.
  Filters are applied when "Filtrar Questões" is pressed.
- **BL-041** Results are ordered by ID and displayed in pages of at most 50;
  the footer shows the range, total and page controls.
- **BL-042** Each result is a card showing ID, segment and years, difficulty,
  type, categories, source and source year, and a preview of the statement
  with the alternatives (correct one highlighted) or the expected answer.
  Long previews can be expanded and resized. Manual resizing is bounded by
  the result viewport and survives document reflow; toggling resets the fit.
- **BL-043** Each card has a "Selecionar" checkbox. A counter shows how many
  questions are selected for the exam. The selection is kept while filtering or changing pages
  and is lost when the bank is switched or the app is closed.
- **BL-044** "Navegar pelas questões selecionadas" shows only selected
  questions in pages; leaving it restores the last applied search.
- **BL-045** "Excluir questões selecionadas" permanently deletes every selected
  question after a confirmation that shows the bank name and the count.

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

## Non-functional baseline

- **BL-060** Fully offline; no network access.
- **BL-061** Distributed for Windows as a single executable built with
  PyInstaller. The source also runs on macOS.
- **BL-062** UI language is Brazilian Portuguese only.

## Known defects and limitations

| ID | Description | Addressed by |
|---|---|---|
| KD-03 | The delete action applies to the exam selection, including questions hidden by the current filter | Retained by owner decision |
| KD-12 | Filtering by a parent category does not include questions tagged only with its children | 005 |
| KD-13 | Text search runs over stored HTML, so it matches markup, misses text split by formatting, and ignores alternatives | 005 |
| KD-14 | Exactly five alternatives are required | 005 |
| KD-15 | Categories cannot be renamed or moved; names are globally unique | 005 |
| KD-17 | Tables and lists in pasted content are flattened in the exam | Backlog |

Planning note: spec 007 pagination is implemented with platform verification
pending. Spec 008 source-year ranges are implemented with platform verification
pending. Spec 009 preview-resize work is implemented with manual platform checks pending.
