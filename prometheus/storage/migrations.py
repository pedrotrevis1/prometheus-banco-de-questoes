"""Forward-only schema migrations; callers manage transactions and backups."""
SCHEMA_VERSION = 6


def migrate_0_to_1(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, assunto TEXT, dificuldade TEXT,
        tipo TEXT, enunciado TEXT, alternativa_a TEXT, alternativa_b TEXT,
        alternativa_c TEXT, alternativa_d TEXT, alternativa_e TEXT, gabarito TEXT,
        ano_sugerido TEXT NOT NULL DEFAULT '', segmento TEXT NOT NULL DEFAULT '',
        fonte_questao TEXT NOT NULL DEFAULT '', ano_origem TEXT NOT NULL DEFAULT ''
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS assuntos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE,
        parent_id INTEGER REFERENCES assuntos(id) ON DELETE CASCADE
    )''')
    columns = {row[1] for row in conn.execute('PRAGMA table_info(questoes)')}
    for name in ('assunto', 'dificuldade', 'tipo', 'enunciado', 'alternativa_a',
                 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e', 'gabarito'):
        if name not in columns:
            conn.execute(f'ALTER TABLE questoes ADD COLUMN {name} TEXT')
    for name in ('ano_sugerido', 'segmento', 'fonte_questao', 'ano_origem'):
        if name not in columns:
            conn.execute(f"ALTER TABLE questoes ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
    category_columns = {row[1] for row in conn.execute('PRAGMA table_info(assuntos)')}
    if 'parent_id' not in category_columns:
        conn.execute('ALTER TABLE assuntos ADD COLUMN parent_id INTEGER REFERENCES assuntos(id) ON DELETE CASCADE')
    conn.execute('PRAGMA user_version = 1')


def migrate_1_to_2(conn):
    conn.execute('ALTER TABLE questoes ADD COLUMN last_modified TEXT')
    conn.execute('PRAGMA user_version = 2')


def migrate_2_to_3(conn):
    conn.execute('ALTER TABLE questoes ADD COLUMN keep_alternative_order INTEGER NOT NULL DEFAULT 0')
    conn.execute('PRAGMA user_version = 3')


from prometheus.storage.normalization_migration import migrate_v3_to_v4, migrate_v4_to_v5

def migrate_5_to_6(conn):
    conn.execute('CREATE TABLE exam_classes (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE)')
    conn.execute('''CREATE TABLE saved_exams (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, class_id INTEGER REFERENCES exam_classes(id),
        settings TEXT NOT NULL DEFAULT '{}')''')
    conn.execute('''CREATE TABLE saved_exam_questions (
        exam_id INTEGER NOT NULL REFERENCES saved_exams(id) ON DELETE CASCADE,
        position INTEGER NOT NULL, question_id INTEGER NOT NULL,
        question_updated_at TEXT, PRIMARY KEY (exam_id, position), UNIQUE (exam_id, question_id))''')
    conn.execute('''CREATE TABLE exam_versions (
        exam_id INTEGER NOT NULL REFERENCES saved_exams(id) ON DELETE CASCADE,
        version INTEGER NOT NULL, arrangement TEXT NOT NULL, PRIMARY KEY (exam_id, version))''')
    conn.execute('''CREATE TABLE exam_usages (
        id INTEGER PRIMARY KEY, exam_id INTEGER NOT NULL REFERENCES saved_exams(id) ON DELETE CASCADE,
        class_name TEXT NOT NULL, used_at TEXT NOT NULL, version_count INTEGER NOT NULL)''')
    conn.execute('''CREATE TABLE exam_usage_questions (
        usage_id INTEGER NOT NULL REFERENCES exam_usages(id) ON DELETE CASCADE,
        question_id INTEGER NOT NULL, PRIMARY KEY (usage_id, question_id))''')
    conn.execute('CREATE INDEX exam_usage_question_lookup ON exam_usage_questions(question_id)')
    conn.execute('PRAGMA user_version = 6')


MIGRATIONS = (migrate_0_to_1, migrate_1_to_2, migrate_2_to_3, migrate_v3_to_v4, migrate_v4_to_v5, migrate_5_to_6)
