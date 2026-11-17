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
- **BL-032** The statement editor supports bold, italic, underline,
  superscript, subscript and strikethrough through a toolbar. The toolbar acts
  only on the statement, not on alternatives or the essay answer.
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
- **BL-037** If the source matches an existing source ignoring case, the
  existing spelling is stored.
- **BL-038** After saving, the form is cleared. Type, difficulty, segment and
  school years keep their values.
- **BL-039** A saved question cannot be edited.

## Searching and selecting

- **BL-040** Filters: categories (a question matches if it has any checked
  category), text contained in the statement, source (partial, ignoring
  case), source year (exact), difficulty, school year, type.
  Filters are applied when "Filtrar Questões" is pressed.
- **BL-041** All questions of the bank are listed when a bank is opened.
- **BL-042** Each result is a card showing ID, segment and years, difficulty,
  type, categories, source and source year, and a preview of the statement
  with the alternatives (correct one highlighted) or the expected answer.
  Long previews can be expanded and resized.
- **BL-043** Each card has a "Selecionar" checkbox. A counter shows how many
  questions are selected for the exam. The selection is kept while filtering
  and is lost when the bank is switched or the app is closed.
- **BL-044** "Navegar pelas questões selecionadas" shows only selected
  questions.
- **BL-045** "Excluir questões selecionadas" permanently deletes every selected
  question after a confirmation that shows the bank name and the count.

## Generating an exam

- **BL-050** The exam contains the selected questions ordered by ID, numbered
  `1)`, `2)`…, with alternatives labelled `A)`–`E)`. Text is Arial 12 pt and
  keeps bold, italic, underline, strikethrough, superscript and subscript.
- **BL-051** Embedded images are placed on their own line at a fixed width of
  4.5 inches.
- **BL-052** With "Incluir gabarito" checked (default), a final page "Gabarito
  Oficial" lists the correct letter or expected answer of each question.
- **BL-053** With "Gerar múltiplas versões", 2 to 999 files are written, named
  `<name>_Version_<n>.docx`. Existing files are overwritten only after
  confirmation.
- **BL-054** "Embaralhar questões" gives every version a distinct question
  order; generation is refused if more versions are requested than orders exist.
- **BL-055** "Embaralhar alternativas" reorders the alternatives of
  multiple-choice questions and adjusts the answer key accordingly.
- **BL-056** Files are written completely or not at all; a failure reports
  which versions were saved.
- **BL-057** The document has no title, header, student identification fields
  or version label.

## Non-functional baseline

- **BL-060** Fully offline; no network access.
- **BL-061** Distributed for Windows as a single executable built with
  PyInstaller. The source also runs on macOS.
- **BL-062** UI language is Brazilian Portuguese only.

## Known defects and limitations

| ID | Description | Addressed by |
|---|---|---|
| KD-03 | The delete action applies to the exam selection, including questions hidden by the current filter | Retained by owner decision |
| KD-07 | Questions cannot be edited (BL-039) | 003 |
| KD-08 | Images that are not embedded PNG data (e.g. pasted with HTML from Word or a browser) are omitted from the exam without warning | 004 |
| KD-09 | Exam has no header or version label (BL-057); image width is fixed (BL-051) | 004 |
| KD-10 | Question order in the exam cannot be chosen (BL-050) | 004 |
| KD-11 | With alternatives shuffled but questions not, two versions can come out identical | 004 |
| KD-12 | Filtering by a parent category does not include questions tagged only with its children | 005 |
| KD-13 | Text search runs over stored HTML, so it matches markup, misses text split by formatting, and ignores alternatives | 005 |
| KD-14 | Exactly five alternatives are required | 005 |
| KD-15 | Categories cannot be renamed or moved; names are globally unique | 005 |
| KD-16 | All questions are loaded and rendered at once; large banks will be slow; the owner reports this with approximately 2,500 questions | 007 (planned) |
| KD-17 | Tables and lists in pasted content are flattened in the exam | Backlog |
| KD-18 | Source-year filtering only accepts an exact stored value; no optional inclusive lower/upper year bounds | 008 (planned) |
| KD-19 | Owner reports that dragging the resize corner of a question-card preview in tab 2 makes the interface appear to stretch downward; affected control confirmed, exact reproduction and root cause unverified | 009 (planned) |
| KD-20 | An empty or multi-letter answer can pass validation when shuffling and then fail while remapping the answer key | Backlog |

Planning note (2026-11-16): specs 007–009 describe proposed changes, not released
behavior. BL-040 to BL-044 remain the current contract until implementation;
the corresponding implementation tasks require updating them and recording
which known defects have actually been fixed.
