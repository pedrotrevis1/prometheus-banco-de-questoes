import sqlite3

import pytest

from prometheus.storage import categories
from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage.normalization_migration import migrate_v3_to_v4


@pytest.fixture
def conn():
    db = sqlite3.connect(':memory:')
    db.execute('PRAGMA foreign_keys = ON')
    db.execute('BEGIN')
    for migration in MIGRATIONS[:3]:
        migration(db)
    db.execute("INSERT INTO questoes (id, tipo, dificuldade, assunto) VALUES (1, 'Dissertativa', 'Fácil', 'Mitose')")
    db.execute("INSERT INTO assuntos (id, nome) VALUES (1, 'Mitose')")
    migrate_v3_to_v4(db)
    db.commit()
    yield db
    db.close()


def test_sibling_uniqueness_and_duplicate_names_under_different_parents(conn):
    first = categories.create_category(conn, 'Primeira')
    second = categories.create_category(conn, 'Segunda')
    categories.create_category(conn, 'Introdução', first)
    categories.create_category(conn, 'Introdução', second)
    with pytest.raises(categories.CategoryError):
        categories.create_category(conn, 'Introdução', first)


def test_move_rename_and_cycle_rejection_preserve_question_links(conn):
    parent = categories.create_category(conn, 'Citologia')
    categories.move_category(conn, 1, parent)
    categories.rename_category(conn, 1, 'Divisão celular')
    assert categories.descendants(conn, parent) == (1, parent)
    assert categories.question_ids_for_category(conn, parent) == (1,)
    assert conn.execute('SELECT * FROM question_categories').fetchall() == [(1, 1)]
    with pytest.raises(categories.CategoryError, match='descendant'):
        categories.move_category(conn, parent, 1)
    assert conn.execute('SELECT parent_id FROM normalized_categories WHERE id = ?', (parent,)).fetchone() == (None,)


def test_delete_subtree_keeps_question_and_makes_it_uncategorized(conn):
    parent = categories.create_category(conn, 'Citologia')
    categories.move_category(conn, 1, parent)
    categories.delete_category(conn, parent)
    assert conn.execute('SELECT id FROM normalized_questions').fetchall() == [(1,)]
    assert categories.uncategorized_question_ids(conn) == (1,)
    assert conn.execute('SELECT * FROM normalized_categories').fetchall() == []
