import sqlite3

import pytest

from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage.normalization_migration import convert_v3, migrate_v3_to_v4


def legacy_bank():
    conn = sqlite3.connect(':memory:')
    for migration in MIGRATIONS[:3]:
        migration(conn)
    conn.execute("INSERT INTO assuntos (id, nome) VALUES (1, 'Citologia')")
    conn.execute('''INSERT INTO questoes
        (id, assunto, dificuldade, tipo, enunciado, alternativa_a, alternativa_b,
         alternativa_c, alternativa_d, alternativa_e, gabarito, ano_sugerido,
         segmento, fonte_questao, ano_origem)
        VALUES (10, 'Citologia; Excluída', 'Fácil', 'Múltipla Escolha',
                '<p>Revolução <b>Francesa</b></p>', 'a', 'b', 'c', 'd', 'e',
                'C', '6º Ano', 'Ensino Fundamental', 'Livro', 'c. 2020')''')
    conn.commit()
    return conn


def test_conversion_preserves_data_and_reports_unmapped_values():
    conn = legacy_bank()
    conn.execute('INSERT INTO assuntos (id, nome, parent_id) VALUES (2, ?, 1)', ('Mitose',))
    conn.commit()
    conn.execute('PRAGMA foreign_keys = ON')
    before = conn.execute('SELECT * FROM questoes').fetchall()
    conn.execute('BEGIN IMMEDIATE')
    convert_v3(conn)
    conn.commit()
    assert conn.execute('SELECT * FROM questoes').fetchall() == before
    assert conn.execute('SELECT id, kind, difficulty, statement_text, source_year, source_year_raw FROM normalized_questions').fetchone() == (
        10, 'multiple_choice', 'easy', 'Revolução Francesa', None, 'c. 2020')
    assert conn.execute('SELECT search_text FROM normalized_questions').fetchone() == ('Revolução Francesa a b c d e',)
    assert conn.execute('SELECT * FROM question_categories').fetchall() == [(10, 1)]
    assert conn.execute('SELECT id, name, parent_id FROM normalized_categories ORDER BY id').fetchall() == [
        (1, 'Citologia', None), (2, 'Mitose', 1)]
    assert conn.execute('SELECT * FROM question_years').fetchall() == [(10, 'fundamental_ii', 'fundamental_6')]
    assert conn.execute('SELECT position, content, is_correct FROM question_alternatives ORDER BY position').fetchall() == [
        (1, 'a', 0), (2, 'b', 0), (3, 'c', 1), (4, 'd', 0), (5, 'e', 0)]
    assert set(conn.execute('SELECT field, value FROM normalization_report')) == {
        ('assunto', 'Excluída'), ('ano_origem', 'c. 2020')}


def test_conversion_rolls_back_without_touching_legacy_records():
    conn = legacy_bank()
    conn.execute('BEGIN IMMEDIATE')
    convert_v3(conn)
    conn.rollback()
    assert conn.execute('SELECT id, assunto FROM questoes').fetchall() == [(10, 'Citologia; Excluída')]
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'normalized_questions'").fetchall() == []


def test_conversion_requires_caller_transaction():
    conn = legacy_bank()
    with pytest.raises(RuntimeError, match='transaction'):
        convert_v3(conn)


def test_unknown_classification_is_reported():
    conn = legacy_bank()
    conn.execute("UPDATE questoes SET tipo = 'Outra', dificuldade = 'Especial', ano_sugerido = '42º Ano', segmento = 'Ensino Fundamental' WHERE id = 10")
    conn.commit()
    conn.execute('BEGIN IMMEDIATE')
    convert_v3(conn)
    assert set(conn.execute('SELECT field, value FROM normalization_report')) >= {
        ('tipo', 'Outra'), ('dificuldade', 'Especial'), ('ano_sugerido', '42º Ano')}
    assert conn.execute('SELECT tipo, dificuldade, ano_sugerido FROM questoes').fetchone() == (
        'Outra', 'Especial', '42º Ano')
    conn.rollback()


def test_missing_classification_and_alternative_are_reported():
    conn = legacy_bank()
    conn.execute("UPDATE questoes SET dificuldade = NULL, alternativa_c = '', gabarito = 'X' WHERE id = 10")
    conn.commit()
    conn.execute('BEGIN IMMEDIATE')
    convert_v3(conn)
    assert set(conn.execute('SELECT field, value FROM normalization_report')) >= {
        ('dificuldade', ''), ('alternativa_c', ''), ('gabarito', 'X')}
    conn.rollback()


def test_legacy_answer_is_normalized_without_changing_original():
    conn = legacy_bank()
    conn.execute("UPDATE questoes SET gabarito = ' c ' WHERE id = 10")
    conn.commit()
    conn.execute('BEGIN IMMEDIATE')
    convert_v3(conn)
    assert conn.execute('SELECT position FROM question_alternatives WHERE is_correct = 1').fetchone() == (3,)
    assert conn.execute('SELECT gabarito FROM questoes').fetchone() == (' c ',)
    assert conn.execute("SELECT value FROM normalization_report WHERE field = 'gabarito'").fetchall() == []


def test_failure_during_conversion_rolls_back_schema_and_original_data():
    conn = legacy_bank()
    before = conn.execute('SELECT * FROM questoes').fetchall()
    conn.execute('BEGIN IMMEDIATE')
    conn.execute('CREATE TABLE question_years (conflicting_column TEXT)')
    with pytest.raises(sqlite3.OperationalError):
        convert_v3(conn)
    conn.rollback()
    assert conn.execute('SELECT * FROM questoes').fetchall() == before
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'normalized_questions'").fetchall() == []


def test_schema_version_advances_and_rolls_back_with_conversion():
    conn = legacy_bank()
    conn.execute('BEGIN IMMEDIATE')
    migrate_v3_to_v4(conn)
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 4
    conn.rollback()
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 3
    assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'normalized_questions'").fetchall() == []


def test_migration_rejects_unexpected_schema_version():
    conn = legacy_bank()
    conn.execute('PRAGMA user_version = 2')
    conn.execute('BEGIN IMMEDIATE')
    with pytest.raises(ValueError, match='version 3'):
        migrate_v3_to_v4(conn)
    conn.rollback()


@pytest.mark.parametrize('parent, error', [(10, 'missing parent'), (1, 'cyclic hierarchy')])
def test_invalid_category_hierarchy_is_rejected_without_modification(parent, error):
    conn = legacy_bank()
    conn.execute('UPDATE assuntos SET parent_id = ? WHERE id = 1', (parent,))
    conn.commit()
    conn.execute('BEGIN IMMEDIATE')
    with pytest.raises(ValueError, match=error):
        migrate_v3_to_v4(conn)
    conn.rollback()
    assert conn.execute('SELECT parent_id FROM assuntos WHERE id = 1').fetchone() == (parent,)
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 3


def disk_bank(path):
    conn = legacy_bank()
    with sqlite3.connect(path) as target:
        conn.backup(target)
    conn.close()


def enable_test_upgrade(monkeypatch):
    from prometheus.storage import database
    monkeypatch.setattr(database, 'SCHEMA_VERSION', 4)
    monkeypatch.setattr(database, 'MIGRATIONS', (*database.MIGRATIONS[:3], migrate_v3_to_v4))
    return database


def test_upgrade_confirmation_backup_and_report(tmp_path, monkeypatch):
    path = tmp_path / 'bank.db'
    disk_bank(path)
    database = enable_test_upgrade(monkeypatch)
    events = []
    conn = database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True,
                              confirm_upgrade=lambda path: events.append('confirm') or True,
                              report_upgrade=lambda report: events.append(report))
    assert events[0] == 'confirm'
    assert (10, 'assunto', 'Excluída') in events[1]
    assert conn.execute('PRAGMA user_version').fetchone()[0] == 4
    conn.close()
    backups = list((tmp_path / 'backups').rglob('*.db'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as saved:
        assert saved.execute('PRAGMA user_version').fetchone()[0] == 3
        assert saved.execute('SELECT assunto FROM questoes').fetchone() == ('Citologia; Excluída',)


def test_declining_upgrade_leaves_bank_untouched_and_creates_no_backup(tmp_path, monkeypatch):
    path = tmp_path / 'bank.db'
    disk_bank(path)
    before = path.read_bytes()
    database = enable_test_upgrade(monkeypatch)
    with pytest.raises(database.UpgradeCancelled):
        database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True,
                           confirm_upgrade=lambda path: False, report_upgrade=lambda report: None)
    assert path.read_bytes() == before
    assert not (tmp_path / 'backups').exists()


def test_upgrade_refuses_missing_confirmation_callbacks(tmp_path, monkeypatch):
    path = tmp_path / 'bank.db'
    disk_bank(path)
    database = enable_test_upgrade(monkeypatch)
    with pytest.raises(database.BankError, match='callbacks'):
        database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True)


def test_failed_upgrade_leaves_original_bank_unchanged_after_backup(tmp_path, monkeypatch):
    path = tmp_path / 'bank.db'
    disk_bank(path)
    with sqlite3.connect(path) as conn:
        conn.execute('UPDATE assuntos SET parent_id = id WHERE id = 1')
    before = path.read_bytes()
    database = enable_test_upgrade(monkeypatch)
    with pytest.raises(ValueError, match='cyclic hierarchy'):
        database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True,
                           confirm_upgrade=lambda path: True, report_upgrade=lambda report: None)
    assert path.read_bytes() == before
    assert len(list((tmp_path / 'backups').rglob('*.db'))) == 1
