import sqlite3

import pytest

from prometheus.storage.migrations import MIGRATIONS, SCHEMA_VERSION
from prometheus.storage.normalized_display import question_card_row


def schema4_bank():
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('BEGIN')
    for migration in MIGRATIONS[:3]:
        migration(conn)
    conn.executemany('''INSERT INTO questoes (id, tipo, dificuldade, segmento, ano_sugerido)
        VALUES (?, 'Dissertativa', 'Fácil', ?, ?)''', [
        (1, 'Ensino Médio', ''), (2, '', ''), (3, 'Desconhecido', ''),
        (4, 'Ensino Fundamental', '9º Ano'), (5, '', '{"level":"Ensino Médio","years":[]}'),
        (6, 'Ensino Médio', 'misterioso'),
    ])
    from prometheus.storage.normalization_migration import migrate_v3_to_v4
    migrate_v3_to_v4(conn)
    conn.commit()
    return conn


def test_schema4_forward_migration_recovers_segment_without_inventing_years():
    from prometheus.storage.normalization_migration import migrate_v4_to_v5
    conn = schema4_bank()
    original = conn.execute('SELECT id, segmento, ano_sugerido FROM questoes ORDER BY id').fetchall()
    conn.execute('BEGIN IMMEDIATE')
    migrate_v4_to_v5(conn)
    conn.commit()
    assert conn.execute('PRAGMA user_version').fetchone() == (5,)
    assert conn.execute('SELECT * FROM question_segments ORDER BY question_id').fetchall() == [
        (1, 'medio'), (4, 'fundamental_ii'), (5, 'medio'), (6, 'medio')]
    assert conn.execute('SELECT * FROM question_years').fetchall() == [(4, 'fundamental_ii', 'fundamental_9')]
    assert question_card_row(conn, 1).segment == 'Ensino Médio'
    assert question_card_row(conn, 1).years == ''
    assert question_card_row(conn, 2).segment == ''
    assert (3, 'segmento', 'Desconhecido') in conn.execute('SELECT * FROM normalization_report').fetchall()
    assert (6, 'ano_sugerido', 'misterioso') in conn.execute('SELECT * FROM normalization_report').fetchall()
    assert conn.execute('SELECT id, segmento, ano_sugerido FROM questoes ORDER BY id').fetchall() == original
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []


def test_schema4_upgrade_uses_current_years_instead_of_stale_archive():
    from prometheus.storage.normalization_migration import migrate_v4_to_v5
    conn = schema4_bank()
    conn.execute('DELETE FROM question_years WHERE question_id=4')
    conn.execute("INSERT INTO question_years VALUES (4, 'medio', 'medio_1')")
    conn.commit()
    conn.execute('BEGIN')
    migrate_v4_to_v5(conn)
    assert conn.execute('SELECT segment FROM question_segments WHERE question_id=4').fetchall() == [('medio',)]
    conn.rollback()


def test_unknown_schema4_segment_code_is_preserved_and_reported():
    from prometheus.storage.normalization_migration import migrate_v4_to_v5
    conn = schema4_bank()
    conn.execute("INSERT INTO question_years VALUES (2, 'unknown_code', 'unknown_year')")
    conn.commit()
    conn.execute('BEGIN')
    migrate_v4_to_v5(conn)
    assert conn.execute('SELECT segment FROM question_segments WHERE question_id=2').fetchall() == [('unknown_code',)]
    assert (2, 'segmento', 'unknown_code') in conn.execute('SELECT * FROM normalization_report').fetchall()
    assert (2, 'ano_sugerido', 'unknown_year') in conn.execute('SELECT * FROM normalization_report').fetchall()
    conn.rollback()


def test_schema4_upgrade_rolls_back_completely():
    from prometheus.storage.normalization_migration import migrate_v4_to_v5
    conn = schema4_bank()
    before = conn.execute('SELECT * FROM normalization_report').fetchall()
    conn.execute('BEGIN')
    migrate_v4_to_v5(conn)
    conn.rollback()
    assert conn.execute('PRAGMA user_version').fetchone() == (4,)
    assert conn.execute("SELECT name FROM sqlite_master WHERE name='question_segments'").fetchall() == []
    assert conn.execute('SELECT * FROM normalization_report').fetchall() == before


@pytest.mark.parametrize('version', [3, 4])
def test_open_legacy_bank_backs_up_and_reports_classification(tmp_path, version):
    from prometheus.storage.database import open_bank
    path = tmp_path / 'synthetic.db'
    source = schema4_bank()
    if version == 3:
        source.close()
        source = sqlite3.connect(':memory:')
        source.execute('BEGIN')
        for migration in MIGRATIONS[:3]:
            migration(source)
        source.execute("INSERT INTO questoes (id, tipo, dificuldade, segmento, ano_sugerido) VALUES (1, 'Dissertativa', 'Fácil', 'Ensino Médio', '')")
        source.commit()
    with sqlite3.connect(path) as target:
        source.backup(target)
    source.close()
    reports = []
    conn = open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True,
                     confirm_upgrade=lambda path: True, report_upgrade=reports.append)
    assert conn.execute('PRAGMA user_version').fetchone() == (SCHEMA_VERSION,)
    assert question_card_row(conn, 1).segment == 'Ensino Médio'
    assert conn.execute('SELECT * FROM question_years WHERE question_id = 1').fetchall() == []
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    assert len(reports) == 1
    conn.close()
    backups = list((tmp_path / 'backups').rglob('*.db'))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as saved:
        assert saved.execute('PRAGMA user_version').fetchone() == (version,)
        assert saved.execute('SELECT segmento, ano_sugerido FROM questoes WHERE id=1').fetchone() == ('Ensino Médio', '')


def test_failed_schema4_upgrade_keeps_original_and_backup(tmp_path, monkeypatch):
    from prometheus.storage import database
    from prometheus.storage.normalization_migration import migrate_v4_to_v5
    path = tmp_path / 'synthetic.db'
    source = schema4_bank()
    with sqlite3.connect(path) as target:
        source.backup(target)
    source.close()
    before = path.read_bytes()
    def fail(conn):
        migrate_v4_to_v5(conn)
        raise RuntimeError('simulated interruption')
    monkeypatch.setattr(database, 'MIGRATIONS', (*database.MIGRATIONS[:4], fail))
    with pytest.raises(RuntimeError, match='interruption'):
        database.open_bank(path, backup_dir=tmp_path, confirm_delete=lambda path: True,
                           report_upgrade=lambda rows: None)
    assert path.read_bytes() == before
    assert len(list((tmp_path / 'backups').rglob('*.db'))) == 1


def test_new_and_edited_questions_keep_segments_in_sync_with_selected_years(tmp_path):
    from dataclasses import replace
    from prometheus.domain.normalized_questions import NormalizedQuestion
    from prometheus.storage.categories import create_category
    from prometheus.storage.database import open_bank
    from prometheus.storage.normalized_questions import delete_questions, get_question, save_question
    conn = open_bank(tmp_path / 'synthetic.db', create=True)
    category = create_category(conn, 'Tema')
    question = NormalizedQuestion((category,), 'essay', 'easy', 'Texto',
        (('fundamental_ii', 'fundamental_9'), ('medio', 'medio_1')))
    question_id = save_question(conn, question)
    assert get_question(conn, question_id)['segments'] == ('fundamental_ii', 'medio')
    save_question(conn, replace(question, years=(('medio', 'medio_1'),)), question_id)
    assert get_question(conn, question_id)['segments'] == ('medio',)
    assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
    delete_questions(conn, [question_id])
    assert conn.execute('SELECT * FROM question_segments').fetchall() == []
    conn.close()
