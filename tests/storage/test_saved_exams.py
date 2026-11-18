import sqlite3

import pytest

from prometheus.storage import saved_exams
from prometheus.storage.migrations import MIGRATIONS


@pytest.fixture
def conn():
    db = sqlite3.connect(':memory:')
    db.execute("BEGIN")

    for migration in MIGRATIONS:
        migration(db)
    db.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (1,'essay','easy','A','A','A','a','a',0)")
    db.commit()
    yield db
    db.close()


def test_exam_lifecycle_and_usage(conn):
    class_id = saved_exams.add_class(conn, '2ª B')
    exam_id = saved_exams.save_exam(conn, 'Prova', class_id, {'versions': 1}, [1])
    saved_exams.record_generation(conn, exam_id, [[{'id': 1}]], [1], used_at='2026-01-01')
    assert saved_exams.question_usages(conn, 1) == [('Prova', '2ª B', '2026-01-01')]
    assert saved_exams.versions(conn, exam_id) == [[{'id': 1}]]
    copy = saved_exams.duplicate_exam(conn, exam_id, 'Cópia')
    assert saved_exams.load_exam(conn, copy)['question_ids'] == (1,)
    assert saved_exams.versions(conn, copy) == []
    conn.execute("UPDATE normalized_questions SET updated_at='b' WHERE id=1")
    assert saved_exams.load_exam(conn, exam_id)['changed_ids'] == (1,)
    saved_exams.delete_exam(conn, exam_id)
    assert saved_exams.question_usages(conn, 1) == []
    assert conn.execute('SELECT count(*) FROM normalized_questions').fetchone()[0] == 1


def test_save_rejects_missing_question_and_retains_existing_exam(conn):
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {}, [1])
    with pytest.raises(LookupError):
        saved_exams.save_exam(conn, 'Outra', None, {}, [99], exam_id)
    assert saved_exams.load_exam(conn, exam_id)['name'] == 'Prova'


def test_manage_classes_and_change_detection(conn):
    class_id = saved_exams.add_class(conn, 'Turma A')
    saved_exams.rename_class(conn, class_id, 'Turma B')
    exam_id = saved_exams.save_exam(conn, 'Prova', class_id, {}, [1])
    saved_exams.record_generation(conn, exam_id, [[]], [1])
    conn.execute("UPDATE normalized_questions SET updated_at='b' WHERE id=1")
    conn.commit()
    saved_exams.save_exam(conn, 'Prova', class_id, {}, [1], exam_id)
    assert saved_exams.load_exam(conn, exam_id)['changed_ids'] == (1,)
    saved_exams.delete_class(conn, class_id)
    assert saved_exams.load_exam(conn, exam_id)['class_id'] is None
    assert saved_exams.question_usages(conn, 1)[0][1] == 'Turma B'
    assert saved_exams.containing_exams(conn, [1]) == [(exam_id, 'Prova')]


def test_save_changed_configuration_retains_previous_arrangements_and_usage(conn):
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {'count': 1}, [1])
    saved_exams.record_generation(conn, exam_id, [[]], [1])
    saved_exams.save_exam(conn, 'Prova', None, {'count': 2}, [1], exam_id)
    assert saved_exams.versions(conn, exam_id) == [[]]
    assert saved_exams.matching_versions(conn, exam_id) == []
    saved_exams.save_exam(conn, 'Prova', None, {'count': 1}, [1], exam_id)
    assert saved_exams.matching_versions(conn, exam_id) == [[]]
    assert len(saved_exams.question_usages(conn, 1)) == 1


def test_usage_filters_include_never_and_respect_inclusive_date(conn):
    from prometheus.storage.normalized_search import NormalizedSearchFilters, page_questions
    conn.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (2,'essay','easy','B','B','B','a','a',0)")
    conn.commit()
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {}, [1])
    saved_exams.record_generation(conn, exam_id, [[]], [1], used_at='2026-05-10T10:00:00-03:00')
    assert page_questions(conn, NormalizedSearchFilters(usage='never'))[1] == (2,)
    assert page_questions(conn, NormalizedSearchFilters(usage='since', unused_since='2026-05-10'))[1] == (2,)
    assert page_questions(conn, NormalizedSearchFilters(usage='since', unused_since='2026-05-11'))[1] == (1, 2)


def test_schema_five_upgrade_backs_up_and_preserves_questions(tmp_path):
    from prometheus.storage.database import open_bank
    bank_path = tmp_path / 'bank.db'
    original = sqlite3.connect(bank_path)
    original.execute('BEGIN')
    for migration in MIGRATIONS[:5]:
        migration(original)
    original.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (1,'essay','easy','A','A','A','a','a',0)")
    original.commit()
    original.close()
    conn = open_bank(bank_path, backup_dir=tmp_path, confirm_delete=lambda _: True)
    assert conn.execute('PRAGMA user_version').fetchone() == (6,)
    assert conn.execute('SELECT statement FROM normalized_questions WHERE id=1').fetchone() == ('A',)
    conn.close()
    backups = list((tmp_path / 'backups').rglob('*.db'))
    assert len(backups) == 1
    backup_path = backups[0]
    with sqlite3.connect(f'file:{backup_path}?mode=ro', uri=True) as backup:
        assert backup.execute('PRAGMA user_version').fetchone() == (5,)
        assert backup.execute('SELECT statement FROM normalized_questions WHERE id=1').fetchone() == ('A',)


def test_unknown_legacy_timestamp_is_not_mistaken_for_deleted_question(conn):
    conn.execute('UPDATE normalized_questions SET updated_at=NULL WHERE id=1')
    conn.commit()
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {}, [1])
    assert saved_exams.load_exam(conn, exam_id)['changed_ids'] == ()
    conn.execute('DELETE FROM normalized_questions WHERE id=1')
    conn.commit()
    assert saved_exams.load_exam(conn, exam_id)['changed_ids'] == (1,)


def test_order_and_options_survive_reopening_bank(tmp_path):
    path = tmp_path / 'saved.db'
    db = sqlite3.connect(path)
    db.execute('BEGIN')
    for migration in MIGRATIONS:
        migration(db)
    for question_id in (1, 2):
        db.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (?,'essay','easy','A','A','A','a','a',0)", (question_id,))
    db.commit()
    class_id = saved_exams.add_class(db, '2ª série B')
    exam_id = saved_exams.save_exam(db, 'Avaliação', class_id, {'count': 3}, [2, 1])
    db.close()
    db = sqlite3.connect(f'file:{path}?mode=rw', uri=True)
    exam = saved_exams.load_exam(db, exam_id)
    assert exam['question_ids'] == (2, 1)
    assert exam['class_id'] == class_id
    assert exam['settings'] == {'count': 3}
    db.close()


def test_legacy_arrangements_keep_original_configuration_when_exam_is_saved(conn):
    import json
    settings = {'multiple': True, 'count': 2, 'shuffle_questions': False, 'shuffle_alternatives': True,
                'include_answers': True, 'separate_answers': False}
    exam_id = saved_exams.save_exam(conn, 'Prova', None, settings, [1])
    conn.execute('INSERT INTO exam_versions VALUES (?,?,?)', (exam_id, 1, json.dumps([{'id': 1}])))
    conn.commit()
    presentation = dict(settings, separate_answers=True)
    saved_exams.save_exam(conn, 'Prova', None, presentation, [1], exam_id)
    assert saved_exams.matching_versions(conn, exam_id) == [[{'id': 1}]]
    changed = dict(presentation, count=3)
    saved_exams.save_exam(conn, 'Prova', None, changed, [1], exam_id)
    assert saved_exams.versions(conn, exam_id) == [[{'id': 1}]]
    assert saved_exams.matching_versions(conn, exam_id) == []
    saved_exams.save_exam(conn, 'Prova', None, presentation, [1], exam_id)
    assert saved_exams.matching_versions(conn, exam_id) == [[{'id': 1}]]


def test_failed_usage_transaction_keeps_previously_generated_arrangements(conn):
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {'count': 1}, [1])
    saved_exams.record_generation(conn, exam_id, [[{'id': 1}]], [1])
    conn.execute("CREATE TRIGGER fail_usage BEFORE INSERT ON exam_usages BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        saved_exams.record_generation(conn, exam_id, [[{'id': 2}]], [1])
    assert saved_exams.versions(conn, exam_id) == [[{'id': 1}]]
    assert len(saved_exams.question_usages(conn, 1)) == 1


def test_intentional_question_reordering_does_not_delete_prior_arrangements(conn):
    conn.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,keep_alternative_order) VALUES (2,'essay','easy','B','B','B',0)")
    conn.commit()
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {}, [1, 2])
    original = [[{'id': 1}, {'id': 2}]]
    saved_exams.record_generation(conn, exam_id, original, [1, 2])
    saved_exams.save_exam(conn, 'Prova', None, {}, [2, 1], exam_id)
    assert saved_exams.versions(conn, exam_id) == original
    assert saved_exams.matching_versions(conn, exam_id) == []
    saved_exams.save_exam(conn, 'Prova', None, {}, [1, 2], exam_id)
    assert saved_exams.matching_versions(conn, exam_id) == original


def test_page_usage_counts_match_details_and_count_generations(conn):
    exam_id = saved_exams.save_exam(conn, 'Prova', None, {}, [1])
    assert saved_exams.question_usage_counts(conn, [1, 2]) == {1: 0, 2: 0}
    saved_exams.record_generation(conn, exam_id, [[], [], []], [1], used_at='2026-01-01')
    saved_exams.record_generation(conn, exam_id, [[]], [1], used_at='2026-01-01')
    saved_exams.duplicate_exam(conn, exam_id, 'Cópia')
    counts = saved_exams.question_usage_counts(conn, [1, 2])
    assert counts == {1: 2, 2: 0}
    assert counts[1] == len(saved_exams.question_usages(conn, 1))
    assert saved_exams.question_usage_counts(conn, []) == {}
    assert saved_exams.question_usage_counts(conn, [2]) == {2: 0}
