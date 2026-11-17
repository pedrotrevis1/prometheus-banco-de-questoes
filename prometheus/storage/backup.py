"""Consistent SQLite backups and explicitly confirmed retention."""
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid


class BackupCancelled(Exception):
    """The user declined to remove an older backup."""


def _write_copy(conn, destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(str(destination))
    fd, temp_name = tempfile.mkstemp(prefix='.prometheus-backup-', suffix='.tmp', dir=destination.parent)
    os.close(fd)
    try:
        target = sqlite3.connect(temp_name)
        try:
            conn.backup(target)
        finally:
            target.close()
        # Linking fails if another file appears at the destination: never overwrite it.
        os.link(temp_name, destination)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return destination


def manual(conn, destination):
    return _write_copy(conn, destination)


def backup_directory(bank_path, data_dir):
    path = Path(bank_path).resolve()
    identity = hashlib.sha256(os.fsencode(path)).hexdigest()[:16]
    return Path(data_dir) / 'backups' / f'{path.stem}-{identity}'


def automatic(conn, bank_path, data_dir, confirm_delete):
    directory = backup_directory(bank_path, data_dir)
    directory.mkdir(parents=True, exist_ok=True)
    existing = sorted(directory.glob('*.db'), key=lambda p: (p.stat().st_mtime_ns, p.name))
    remove = existing[:max(0, len(existing) - 2)]
    # Ask about all candidates before deleting anything.
    for old in remove:
        if not confirm_delete(old):
            raise BackupCancelled(str(old))
    name = datetime.now().strftime('%Y-%m-%d_%H%M%S_%f') + '-' + uuid.uuid4().hex[:8] + '.db'

    result = _write_copy(conn, directory / name)
    for old in remove:
        old.unlink()
    return result


def is_cloud_path(path):
    parts = str(path).replace('\\', '/').casefold().split('/')
    exact = {'iclouddrive', 'mobile documents', 'dropbox', 'google drive', 'my drive'}
    return any(part in exact or part.startswith('onedrive') for part in parts)
