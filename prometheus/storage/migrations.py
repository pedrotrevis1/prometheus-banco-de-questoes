"""Forward-only schema migrations; callers manage transactions and backups."""
SCHEMA_VERSION = 1


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
    for name in ('ano_sugerido', 'segmento', 'fonte_questao', 'ano_origem'):
        if name not in columns:
            conn.execute(f"ALTER TABLE questoes ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
    conn.execute('PRAGMA user_version = 1')


MIGRATIONS = (migrate_0_to_1,)
