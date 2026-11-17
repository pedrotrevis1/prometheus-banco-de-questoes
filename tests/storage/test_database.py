import sqlite3
import pytest
from prometheus.storage.database import (BankNotFoundError, BankState, BankTooNewError,
    BankError, NotABankError, inspect_bank, open_bank)


def test_missing_is_never_created(tmp_path):
    path = tmp_path / 'missing.db'
    with pytest.raises(BankNotFoundError):
        open_bank(path)
    assert not path.exists()


def test_inspection():
    conn = sqlite3.connect(':memory:')
    assert inspect_bank(conn) == (BankState.NEW, 0)
    conn.execute('CREATE TABLE other (value)')
    assert inspect_bank(conn)[0] is BankState.FOREIGN
    conn.execute('CREATE TABLE questoes (id)')
    conn.execute('CREATE TABLE assuntos (id)')
    assert inspect_bank(conn)[0] is BankState.PROMETHEUS
    conn.close()


def test_foreign_and_non_sqlite_are_unchanged(tmp_path):
    path = tmp_path / 'foreign.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE other (value)')
    before = path.read_bytes()
    with pytest.raises(NotABankError): open_bank(path)
    assert path.read_bytes() == before
    text = tmp_path / 'text.db'; text.write_text('not sqlite')
    with pytest.raises(NotABankError): open_bank(text)
    assert text.read_text() == 'not sqlite'


def test_future_and_old_bank_are_not_changed(tmp_path):
    path = tmp_path / 'bank.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE questoes (id)')
        conn.execute('CREATE TABLE assuntos (id)')
        conn.execute('PRAGMA user_version=2')
    before = path.read_bytes()
    with pytest.raises(BankTooNewError): open_bank(path)
    assert path.read_bytes() == before
    with sqlite3.connect(path) as conn: conn.execute('PRAGMA user_version=0')
    before = path.read_bytes()
    with pytest.raises(BankError): open_bank(path)
    assert path.read_bytes() == before


def test_current_bank_opens(tmp_path):
    path = tmp_path / 'bank.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE questoes (id)')
        conn.execute('CREATE TABLE assuntos (id)')
        conn.execute('PRAGMA user_version=1')
    conn = open_bank(path)
    assert conn.execute("SELECT CASEFOLD('Á')").fetchone()[0] == 'á'
    assert conn.execute('PRAGMA foreign_keys').fetchone()[0] == 1
    conn.close()


def test_create_requires_explicit_request_and_never_replaces(tmp_path):
    path = tmp_path / 'new.db'
    conn = open_bank(path, create=True)
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 1
    conn.close()
    original = path.read_bytes()
    with pytest.raises(FileExistsError): open_bank(path, create=True)
    assert path.read_bytes() == original


def test_upgrade_makes_backup_and_preserves_rows(tmp_path):
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE questoes (id INTEGER PRIMARY KEY, enunciado TEXT)')
        conn.execute('CREATE TABLE assuntos (id INTEGER PRIMARY KEY, nome TEXT)')
        conn.execute("INSERT INTO questoes VALUES (1, 'keep')")
    conn = open_bank(path, backup_dir=tmp_path, confirm_delete=lambda p: True)
    assert conn.execute('SELECT enunciado FROM questoes').fetchone() == ('keep',)
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 1
    conn.close()
    backups = list((tmp_path / 'backups').rglob('*.db'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as copied:
        assert copied.execute('PRAGMA user_version').fetchone()[0] == 0
        assert copied.execute('SELECT enunciado FROM questoes').fetchone() == ('keep',)


def test_failed_migration_rolls_back(tmp_path, monkeypatch):
    from prometheus.storage import database
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE questoes (id)')
        conn.execute('CREATE TABLE assuntos (id)')
    before = path.read_bytes()
    def fail(conn):
        conn.execute('ALTER TABLE questoes ADD COLUMN extra TEXT')
        raise RuntimeError('simulated failure')
    monkeypatch.setattr(database, 'MIGRATIONS', (fail,))
    with pytest.raises(RuntimeError):
        open_bank(path, backup_dir=tmp_path, confirm_delete=lambda p: True)
    assert path.read_bytes() == before
    assert len(list((tmp_path / 'backups').rglob('*.db'))) == 1


def test_declining_backup_retention_cancels_upgrade(tmp_path):
    from prometheus.storage.backup import BackupCancelled, automatic
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE questoes (id)')
        conn.execute('CREATE TABLE assuntos (id)')
    with sqlite3.connect(path) as conn:
        for _ in range(3):
            automatic(conn, path, tmp_path, lambda p: True)
    original = path.read_bytes()
    with pytest.raises(BackupCancelled):
        open_bank(path, backup_dir=tmp_path, confirm_delete=lambda p: False)
    assert path.read_bytes() == original
    assert len(list((tmp_path / 'backups').rglob('*.db'))) == 3
