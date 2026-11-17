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


def test_version_one_upgrade_backs_up_and_preserves_legacy_rows(tmp_path):
    from prometheus.storage.database import open_bank
    path = tmp_path / 'legacy.db'
    conn = sqlite3.connect(path)
    migrate_0_to_1(conn)
    conn.execute("INSERT INTO questoes (id, enunciado) VALUES (1, '<p>Original</p>')")
    conn.commit(); conn.close()
    conn = open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True)
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 2
    assert conn.execute('SELECT id, enunciado, last_modified FROM questoes').fetchall() == [(1, '<p>Original</p>', None)]
    assert conn.execute('PRAGMA table_info(questoes)').fetchall()[-1][1] == 'last_modified'
    conn.close()
    backups = list((tmp_path / 'backups').rglob('*.db'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute('PRAGMA user_version').fetchone()[0] == 1
        assert backup.execute('SELECT id, enunciado FROM questoes').fetchall() == [(1, '<p>Original</p>')]


def test_version_one_upgrade_failure_rolls_back(tmp_path, monkeypatch):
    from prometheus.storage import database
    path = tmp_path / 'legacy.db'
    conn = sqlite3.connect(path); migrate_0_to_1(conn); conn.commit(); conn.close()
    before = path.read_bytes()
    def fail(conn):
        conn.execute('ALTER TABLE questoes ADD COLUMN last_modified TEXT')
        raise RuntimeError('migration failed')
    monkeypatch.setattr(database, 'MIGRATIONS', (database.MIGRATIONS[0], fail))
    monkeypatch.setattr(database, 'SCHEMA_VERSION', 2)
    import pytest
    with pytest.raises(RuntimeError, match='migration failed'):
        database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True)
    assert path.read_bytes() == before
    assert len(list((tmp_path / 'backups').rglob('*.db'))) == 1
