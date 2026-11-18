"""Validate and safely open SQLite question banks."""
from enum import Enum
import os
from pathlib import Path
import sqlite3
import tempfile

from prometheus.storage import backup
from prometheus.storage.migrations import MIGRATIONS, SCHEMA_VERSION


class BankError(Exception):
    """A bank cannot be opened safely."""


class BankNotFoundError(BankError):
    pass


class NotABankError(BankError):
    pass


class BankTooNewError(BankError):
    pass


class UpgradeCancelled(BankError):
    pass


class BankState(Enum):
    NEW = 'new'
    PROMETHEUS = 'prometheus'
    FOREIGN = 'foreign'


def inspect_bank(conn):
    objects = conn.execute("SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
    tables = {name for name, kind in objects if kind == 'table'}
    version = conn.execute('PRAGMA user_version').fetchone()[0]
    if not objects:
        return BankState.NEW, version
    if {'questoes', 'assuntos'} <= tables:
        return BankState.PROMETHEUS, version
    return BankState.FOREIGN, version


def _initialize_new(path):
    fd, temporary = tempfile.mkstemp(prefix='.prometheus-new-', suffix='.tmp', dir=path.parent)
    os.close(fd)
    try:
        conn = sqlite3.connect(temporary)
        try:
            conn.execute('BEGIN IMMEDIATE')
            for migration in MIGRATIONS:
                migration(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        os.link(temporary, path)  # Fails if the requested destination exists.
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def open_bank(path, *, create=False, backup_dir=None, confirm_delete=None,
              confirm_upgrade=None, report_upgrade=None):
    path = Path(path).resolve()
    if not path.is_file():
        if not create:
            raise BankNotFoundError(str(path))
        _initialize_new(path)
    elif create:
        raise FileExistsError(str(path))
    conn = None
    try:
        conn = sqlite3.connect(path.as_uri() + '?mode=rw', uri=True)
        try:
            state, version = inspect_bank(conn)
        except sqlite3.DatabaseError as exc:
            raise NotABankError(str(path)) from exc
        if state == BankState.FOREIGN:
            raise NotABankError(str(path))
        if version > SCHEMA_VERSION:
            raise BankTooNewError(str(path))
        if version < SCHEMA_VERSION:
            if backup_dir is None or confirm_delete is None:
                raise BankError('Backup destination and confirmation callback are required for migration')
            normalization_upgrade = version < 4 <= SCHEMA_VERSION
            segment_upgrade = version < 5 <= SCHEMA_VERSION
            if segment_upgrade and report_upgrade is None:
                raise BankError('Upgrade report callback is required')
            if normalization_upgrade:
                if confirm_upgrade is None or report_upgrade is None:
                    raise BankError('Upgrade confirmation and report callbacks are required')
                if not confirm_upgrade(path):
                    raise UpgradeCancelled(str(path))
            backup.automatic(conn, path, backup_dir, confirm_delete)
            conn.execute('BEGIN IMMEDIATE')
            try:
                for migration in MIGRATIONS[version:]:
                    migration(conn)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            if normalization_upgrade or segment_upgrade:
                report_upgrade(conn.execute(
                    'SELECT question_id, field, value FROM normalization_report ORDER BY question_id, field, value'
                ).fetchall())
        conn.create_function('CASEFOLD', 1, lambda value: str(value or '').casefold(), deterministic=True)
        conn.execute('PRAGMA foreign_keys = ON')
        return conn
    except BaseException:
        if conn is not None:
            conn.close()
        raise


def seed_biology_categories(conn, discipline):
    """Preserve the legacy default categories for empty biology banks."""
    normalized = conn.execute('PRAGMA user_version').fetchone()[0] >= 4
    table = 'normalized_categories' if normalized else 'assuntos'
    name_column = 'name' if normalized else 'nome'
    if 'biologia' not in discipline.lower() or conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]:
        return
    names = ('Citologia', 'Ecologia', 'Embriologia', 'Evolução', 'Fisiologia',
             'Genética', 'Histologia', 'Origem da Vida', 'Parasitologia',
             'Reino Animal', 'Protistas', 'Reino Vegetal', 'Fungos', 'Bactérias')
    conn.executemany(f'INSERT OR IGNORE INTO {table} ({name_column}, parent_id) VALUES (?, NULL)', ((name,) for name in names))
    conn.commit()
