import sqlite3
import pytest
from prometheus.storage.backup import BackupCancelled, automatic, manual


def test_manual_backup_copies_and_never_overwrites(tmp_path):
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE questions (text)')
    conn.execute("INSERT INTO questions VALUES ('original')")
    conn.commit()
    path = tmp_path / 'copy.db'
    manual(conn, path)
    with sqlite3.connect(path) as copied:
        assert copied.execute('SELECT text FROM questions').fetchall() == [('original',)]
    original = path.read_bytes()
    with pytest.raises(FileExistsError): manual(conn, path)
    assert path.read_bytes() == original
    conn.close()


def test_automatic_retention_requires_confirmation(tmp_path):
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE questions (id)')
    paths = [automatic(conn, tmp_path/'bank.db', tmp_path, lambda p: False) for _ in range(3)]
    with pytest.raises(BackupCancelled):
        automatic(conn, tmp_path/'bank.db', tmp_path, lambda p: False)
    assert all(p.exists() for p in paths)
    asked = []
    new = automatic(conn, tmp_path/'bank.db', tmp_path, lambda p: asked.append(p) or True)
    assert asked == [paths[0]]
    assert not paths[0].exists() and new.exists()
    assert len(list(new.parent.glob('*.db'))) == 3
    conn.close()


def test_automatic_banks_with_same_name_are_separate(tmp_path):
    conn = sqlite3.connect(':memory:')
    a = automatic(conn, tmp_path/'one'/'bank.db', tmp_path, lambda p: True)
    b = automatic(conn, tmp_path/'two'/'bank.db', tmp_path, lambda p: True)
    assert a.parent != b.parent
    conn.close()


def test_cloud_detection_matches_components():
    from prometheus.storage.backup import is_cloud_path
    assert is_cloud_path(r'C:\Users\Teacher\OneDrive - School\bank.db')
    assert is_cloud_path('/Users/t/Library/Mobile Documents/com~apple~CloudDocs/bank.db')
    assert is_cloud_path('/Users/t/Dropbox/bank.db')
    assert not is_cloud_path('/Users/t/Dropbox-notes/bank.db')
    assert not is_cloud_path('/Users/t/Documents/bank.db')


def test_publication_failure_preserves_existing_backups_and_bank(tmp_path, monkeypatch):
    from prometheus.storage import backup
    bank = tmp_path / 'bank.db'
    with sqlite3.connect(bank) as conn:
        conn.execute('CREATE TABLE questions (id)')
        conn.execute('INSERT INTO questions VALUES (42)')
        conn.commit()
        paths = [automatic(conn, bank, tmp_path, lambda p: True) for _ in range(3)]
        original_bank = bank.read_bytes()
        originals = {path: path.read_bytes() for path in paths}
        def fail_link(*args):
            raise OSError('simulated publication failure')
        monkeypatch.setattr(backup.os, 'link', fail_link)
        with pytest.raises(OSError, match='publication failure'):
            automatic(conn, bank, tmp_path, lambda p: True)
        assert bank.read_bytes() == original_bank
        assert all(path.exists() and path.read_bytes() == data for path, data in originals.items())
        assert set(paths[0].parent.glob('*.db')) == set(paths)
