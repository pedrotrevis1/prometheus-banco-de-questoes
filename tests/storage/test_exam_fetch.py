import sqlite3
import pytest
from prometheus.storage.exams import fetch_ordered_questions


def test_fetch_preserves_order_and_respects_sqlite_limit():
    conn = sqlite3.connect(':memory:')
    from prometheus.storage.migrations import MIGRATIONS
    for migration in MIGRATIONS: migration(conn)
    conn.executemany('INSERT INTO questoes (id, enunciado) VALUES (?, ?)', [(i, str(i)) for i in range(1, 11)])
    conn.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 3)
    assert [row[0] for row in fetch_ordered_questions(conn, [9, 1, 8, 2, 7])] == [9, 1, 8, 2, 7]
    with pytest.raises(LookupError, match='99'):
        fetch_ordered_questions(conn, [1, 99])
    conn.close()


def test_summaries_skip_html_head_and_do_not_fetch_full_image_data():
    from prometheus.storage.exams import fetch_question_summaries
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE questoes (id INTEGER, enunciado TEXT)')
    conn.execute('INSERT INTO questoes VALUES (?, ?)', (1, '<html><head><style>css</style></head><body><p>Questão importante</p></body></html>'))
    assert fetch_question_summaries(conn, [1])[1] == 'Questão importante'
    conn.close()


def test_fetch_names_columns_even_when_bank_has_legacy_extra_column():
    from prometheus.storage.migrations import migrate_0_to_1, migrate_1_to_2, migrate_2_to_3
    conn = sqlite3.connect(':memory:')
    migrate_0_to_1(conn); migrate_1_to_2(conn)
    conn.execute('ALTER TABLE questoes ADD COLUMN extra_old_column TEXT')
    migrate_2_to_3(conn)
    conn.execute("INSERT INTO questoes (id, extra_old_column, keep_alternative_order) VALUES (1, 'not-the-flag', 0)")
    row = fetch_ordered_questions(conn, [1])[0]
    assert len(row) == 17 and row[16] == 0
    conn.close()
