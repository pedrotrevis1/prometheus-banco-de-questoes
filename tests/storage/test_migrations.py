import sqlite3
from prometheus.storage.migrations import migrate_0_to_1


def test_migration_preserves_legacy_rows_and_adds_missing_columns():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE questoes (id INTEGER PRIMARY KEY, enunciado TEXT)')
    conn.execute("INSERT INTO questoes VALUES (1, 'Original')")
    conn.execute('CREATE TABLE assuntos (id INTEGER PRIMARY KEY, nome TEXT, parent_id INTEGER)')
    conn.commit()
    conn.execute('BEGIN IMMEDIATE')
    migrate_0_to_1(conn)
    conn.commit()
    assert conn.execute('SELECT id, enunciado FROM questoes').fetchall() == [(1, 'Original')]
    assert {'ano_sugerido', 'segmento', 'fonte_questao', 'ano_origem'} <= {row[1] for row in conn.execute('PRAGMA table_info(questoes)')}
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 1
    conn.close()


def test_migration_can_roll_back_all_schema_changes():
    conn = sqlite3.connect(':memory:')
    conn.execute('BEGIN IMMEDIATE')
    migrate_0_to_1(conn)
    conn.rollback()
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 0
    assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    conn.close()
