# Baseline data model (006 implementation)

## Application data directory

| Platform | Path |
|---|---|
| Windows, Linux | `~/.gerador_provas_app/` |
| macOS | `~/Library/Application Support/GeradorProvasApp/` |

### `app_config.json`

```json
{
    "current_discipline": "Biologia",
    "disciplines": { "Biologia": "<absolute path to .db>" }
}
```

An unreadable or invalid file is logged and replaced in memory by the default above.
An empty discipline list is supported. Configuration saves use atomic replacement.
The theme is not stored.

## Question bank (SQLite, one file per discipline)

`PRAGMA foreign_keys = ON` is set per connection. `PRAGMA user_version` is 6
after backup-protected forward migration from earlier versions. Newer versions are
rejected. Automatic backups are stored under the app data directory and capped
at three per bank, with confirmation before deleting an identified old copy. The replacement is published before confirmed old copies are removed; a deletion failure can leave more than three copies.

### Normalized tables

- `normalized_questions`: question ID, stable kind and difficulty codes, rich
  statement, plain-text statement and search content, expected answer, source,
  numeric source year and original text, timestamps, and alternative-order flag.
- `normalized_categories`: ID, name and parent ID; unique indexes enforce names
  among siblings and among roots.
- `question_categories`: question and category IDs with foreign keys.
- `question_segments`: question ID and stable segment code, independent of
  school-year records. Upgrades from schema 4 recover segment-only legacy
  classifications from retained original rows when there are no current years.
- `question_years`: question ID and stable segment and school-year codes.
- `question_alternatives`: question ID, ordered position, rich content and
  correct-answer flag.
- `normalization_report`: question ID, field and unmapped original value.
- `exam_classes`: managed class names.
- `saved_exams` and `saved_exam_questions`: exam names, class references,
  generation settings, ordered question IDs and modification timestamps.
- `exam_versions`: generated question and alternative positions and the
  arrangement-affecting exam configuration, without frozen question content.
  Existing position-only records remain readable. The last successful
  arrangements are retained until a replacement generation succeeds.
- `exam_usages` and `exam_usage_questions`: generation date, class name,
  version count and question IDs for each completed generation.

The following legacy tables are retained as a migration archive. New changes
use the normalized tables; explicit question deletion also removes the archived
legacy row. The app warns before migration that older executables may not work.

### Legacy `questoes`

| Column | Type | Content |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `assunto` | TEXT | Category **names** joined by `;` |
| `dificuldade` | TEXT | Display label: `Fácil`, `Médio`, `Difícil` |
| `tipo` | TEXT | Display label: `Múltipla Escolha`, `Dissertativa` |
| `enunciado` | TEXT | Full Qt HTML document; images inline as `data:image/png;base64,…` |
| `alternativa_a` … `alternativa_e` | TEXT | Qt HTML; empty string for essay questions |
| `gabarito` | TEXT | Letter `A`–`E`, or Qt HTML of the expected answer, or empty |
| `ano_sugerido` | TEXT NOT NULL DEFAULT '' | School-year labels joined by `;` (e.g. `1ª Série;2ª Série`) |
| `segmento` | TEXT NOT NULL DEFAULT '' | `Ensino Fundamental` or `Ensino Médio` |
| `fonte_questao` | TEXT NOT NULL DEFAULT '' | Free text |
| `ano_origem` | TEXT NOT NULL DEFAULT '' | Free text |
| `last_modified` | TEXT, nullable | UTC timestamp; unknown for legacy questions |
| `keep_alternative_order` | INTEGER NOT NULL DEFAULT 0 | 1 preserves alternative order during shuffling |

Legacy rows may hold JSON in `ano_sugerido` (`{"level": …, "years": […]}`);
the app still reads that format.

### Legacy `assuntos`

| Column | Type | Content |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `nome` | TEXT UNIQUE | |
| `parent_id` | INTEGER → `assuntos(id)` ON DELETE CASCADE | NULL for root categories |

### Observations

- The legacy tables preserve original migration inputs and are not the active
  question and category store.
- Historical question creation times are unknown; new questions have creation
  and modification times. Deleting an exam also deletes its usage records after
  confirmation; deleting a class retains the class name in existing usages.
