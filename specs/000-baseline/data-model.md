# Baseline data model (002 in progress)

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

`PRAGMA foreign_keys = ON` is set per connection. `PRAGMA user_version` is 3
after backup-protected forward migration from earlier versions. Newer versions are
rejected. Automatic backups are stored under the app data directory and capped
at three per bank, with confirmation before deleting an identified old copy. The replacement is published before confirmed old copies are removed; a deletion failure can leave more than three copies.

### `questoes`

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

### `assuntos`

| Column | Type | Content |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `nome` | TEXT UNIQUE | |
| `parent_id` | INTEGER → `assuntos(id)` ON DELETE CASCADE | NULL for root categories |

### Observations

- Questions reference categories by name inside a string, so there is no
  referential integrity between `questoes` and `assuntos`.
- Export selects named columns in an explicit order before building the exam;
  unrelated legacy columns do not change the alternative-order setting.
- Questions have an optional last-modified timestamp; generated exams are not recorded.
