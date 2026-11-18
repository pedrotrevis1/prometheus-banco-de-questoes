import sqlite3

import pytest

from prometheus.domain.normalized_questions import NormalizedQuestion
from prometheus.storage.categories import create_category, delete_category
from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage.normalization_migration import migrate_v3_to_v4
from prometheus.storage.normalized_questions import save_question
from prometheus.storage.normalized_search import NormalizedSearchFilters, page_questions


@pytest.fixture
def conn():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('BEGIN')
    for migration in MIGRATIONS[:3]:
        migration(db)
    migrate_v3_to_v4(db)
    db.commit()
    yield db
    db.close()


def test_search_visible_text_alternatives_and_expected_answer(conn):
    category = create_category(conn, 'História')
    first = save_question(conn, NormalizedQuestion((category,), 'multiple_choice', 'easy',
        '<p>Revolução <b>Francesa</b></p>', (('medio', 'medio_1'),), ('Nobreza', 'Povo'), 2))
    second = save_question(conn, NormalizedQuestion((category,), 'essay', 'easy',
        '<p>Outra questão</p>', (('medio', 'medio_1'),), expected_answer='<p>Declaração</p>'))
    for text, expected in [('revolucao francesa', (first,)), ('nobreza', (first,)),
                           ('declaracao', (second,)), ('span', ()), ('font', ())]:
        assert page_questions(conn, NormalizedSearchFilters(text=text))[1] == expected


def test_descendants_uncategorized_and_year_range(conn):
    parent = create_category(conn, 'Citologia')
    child = create_category(conn, 'Mitose', parent)
    question_id = save_question(conn, NormalizedQuestion((child,), 'essay', 'easy', 'Texto',
        (('medio', 'medio_1'),), source_year='2021'))
    assert page_questions(conn, NormalizedSearchFilters(category_ids=(parent,), source_year_from=2020))[1] == (question_id,)
    assert page_questions(conn, NormalizedSearchFilters(source_year_to=2020))[1] == ()
    delete_category(conn, child)
    assert page_questions(conn, NormalizedSearchFilters(uncategorized=True))[1] == (question_id,)


def test_pagination_and_selected_only(conn):
    category = create_category(conn, 'Tema')
    for _ in range(55):
        save_question(conn, NormalizedQuestion((category,), 'essay', 'easy', 'Texto', (('medio', 'medio_1'),)))
    bounds, ids = page_questions(conn, NormalizedSearchFilters(), 2)
    assert (bounds.total, bounds.pages, len(ids)) == (55, 2, 5)
    assert page_questions(conn, NormalizedSearchFilters(text='inexistente'), selected_ids={1, 55})[1] == (1, 55)


def test_search_two_thousand_questions(conn):
    category = create_category(conn, 'Tema')
    question = NormalizedQuestion((category,), 'essay', 'easy', 'Revolução <b>Francesa</b>', (('medio', 'medio_1'),))
    for _ in range(2000):
        save_question(conn, question)
    bounds, ids = page_questions(conn, NormalizedSearchFilters(text='revolucao francesa'))
    assert bounds.total == 2000 and len(ids) == 50
