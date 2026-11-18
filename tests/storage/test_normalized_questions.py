import sqlite3
from dataclasses import replace

import pytest

from prometheus.domain.normalized_questions import NormalizedQuestion
from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage.normalization_migration import migrate_v3_to_v4
from prometheus.storage.normalized_questions import get_question, save_question


@pytest.fixture
def conn():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('BEGIN')
    for migration in MIGRATIONS[:3]:
        migration(db)
    db.execute("INSERT INTO assuntos (id, nome) VALUES (1, 'Biologia')")
    migrate_v3_to_v4(db)
    db.commit()
    yield db
    db.close()


def draft():
    return NormalizedQuestion((1,), 'multiple_choice', 'easy', '<p>Pergunta</p>',
                              (('fundamental_ii', 'fundamental_9'), ('medio', 'medio_1')),
                              ('A', 'B', 'C', 'D'), 3, source_year=' 2024 ')


def test_save_and_update_question_with_multiple_segments_and_four_alternatives(conn):
    question_id = save_question(conn, draft())
    result = get_question(conn, question_id)
    assert result['source_year'] == 2024 and result['source_year_raw'] == ' 2024 '
    assert len(result['years']) == 2
    assert result['alternatives'] == ((1, 'A', 0), (2, 'B', 0), (3, 'C', 1), (4, 'D', 0))
    assert result['created_at'] and result['updated_at']
    save_question(conn, replace(draft(), statement='<p>Nova pergunta</p>', correct_position=4), question_id)
    updated = get_question(conn, question_id)
    assert updated['created_at'] == result['created_at']
    assert updated['statement'] == '<p>Nova pergunta</p>'
    assert updated['alternatives'][-1] == (4, 'D', 1)


@pytest.mark.parametrize('alternatives, answer', [(('A',), 1), (('A', 'B'), 3), (('A', ''), 1)])
def test_invalid_alternatives_are_rejected_without_writes(conn, alternatives, answer):
    with pytest.raises(ValueError):
        save_question(conn, replace(draft(), alternatives=alternatives, correct_position=answer))
    assert conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone() == (0,)


def test_missing_category_and_missing_question_are_rejected(conn):
    with pytest.raises(ValueError, match='Category'):
        save_question(conn, replace(draft(), category_ids=(999,)))
    with pytest.raises(LookupError):
        save_question(conn, draft(), 999)


def test_four_alternatives_export_with_matching_shuffled_answer(conn):
    import random
    from prometheus.domain.normalized_versions import generate_versions
    from prometheus.export.documents import build_exam_documents
    from prometheus.storage.normalized_exams import fetch_ordered_questions
    question_id = save_question(conn, draft())
    questions = fetch_ordered_questions(conn, [question_id])
    variants = generate_versions(questions, 4, False, True, rng=random.Random(4))
    for version in variants:
        question = version[0]
        assert question.alternatives['ABCDE'.index(question.answer)] == 'C'
        exam, key = build_exam_documents(version, answer_placement='separate')
        paragraphs = [paragraph.text for paragraph in exam.paragraphs]
        assert any(text.startswith('D)') for text in paragraphs)
        assert not any(text.startswith('E)') for text in paragraphs)
        assert question.answer in '\n'.join(paragraph.text for paragraph in key.paragraphs)


def test_card_data_preserves_variable_alternative_count(conn):
    from prometheus.storage.normalized_display import question_card_row
    question_id = save_question(conn, draft())
    row = question_card_row(conn, question_id)
    assert row.question_id == question_id
    assert row.categories == 'Biologia'
    assert row.segment == 'Ensino Fundamental; Ensino Médio'
    assert row.alternatives == ('A', 'B', 'C', 'D')
    assert row.answer == 'C'


def test_source_spelling_is_reused_ignoring_case(conn):
    first = save_question(conn, replace(draft(), source='ENEM'))
    second = save_question(conn, replace(draft(), source='enem'))
    assert get_question(conn, first)['source'] == 'ENEM'
    assert get_question(conn, second)['source'] == 'ENEM'


def test_delete_question_removes_normalized_and_legacy_records(conn):
    from prometheus.storage.normalized_questions import delete_questions
    question_id = save_question(conn, draft())
    conn.execute('INSERT INTO questoes (id, enunciado) VALUES (?, ?)', (question_id, 'original'))
    conn.commit()
    assert delete_questions(conn, [question_id]) == 1
    assert get_question(conn, question_id) is None
    assert conn.execute('SELECT id FROM questoes').fetchall() == []
    assert conn.execute('SELECT question_id FROM question_alternatives').fetchall() == []
