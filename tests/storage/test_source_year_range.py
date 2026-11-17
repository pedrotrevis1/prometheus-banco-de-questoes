import sqlite3
import pytest
from prometheus.domain.search import SearchFilters
from prometheus.storage.search import page_questions


@pytest.fixture
def conn():
    c = sqlite3.connect(':memory:')
    c.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    c.execute("""CREATE TABLE questoes (id INTEGER, assunto TEXT, dificuldade TEXT, ano_sugerido TEXT,
        segmento TEXT, tipo TEXT, enunciado TEXT, alternativa_a TEXT, alternativa_b TEXT,
        alternativa_c TEXT, alternativa_d TEXT, alternativa_e TEXT, gabarito TEXT,
        fonte_questao TEXT, ano_origem TEXT)""")
    values = ['2019', '2021', '2022', ' 2022 ', '2023', '2024', '2025',
              '2022/2023', 'c. 2022', 's/d', '', None, '0009', '10', '0', '10000']
    for i, year in enumerate(values, 1):
        c.execute('INSERT INTO questoes (id, assunto, ano_sugerido, segmento, tipo, enunciado, fonte_questao, ano_origem) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (i, 'Física' if i % 2 else 'Bio', '1ª Série', 'Ensino Médio', 'Dissertativa', 'texto', 'ENEM', year))
    c.commit()
    yield c
    c.close()


@pytest.mark.parametrize(('lower', 'upper', 'ids'), [
    (None, None, list(range(1, 17))),
    (2022, None, [3, 4, 5, 6, 7]),
    (None, 2022, [1, 2, 3, 4, 13, 14]),
    (2022, 2024, [3, 4, 5, 6]),
    (2022, 2022, [3, 4]),
    (9, 10, [13, 14]),
])
def test_inclusive_ranges_preserve_legacy_values(conn, lower, upper, ids):
    before = conn.execute('SELECT id, ano_origem FROM questoes ORDER BY id').fetchall()
    schema = conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()
    statements = []
    conn.set_trace_callback(statements.append)
    bounds, rows = page_questions(conn, SearchFilters(source_year_from=lower, source_year_to=upper), 1)
    conn.set_trace_callback(None)
    assert bounds.total == len(ids)
    assert [row[0] for row in rows] == ids
    assert conn.execute('SELECT id, ano_origem FROM questoes ORDER BY id').fetchall() == before
    assert conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall() == schema
    assert all(not sql.lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'ALTER', 'CREATE', 'DROP')) for sql in statements)


def test_combined_and_selected_only_bypass(conn):
    filters = SearchFilters(source_year_from=2022, source_year_to=2024,
                            source='enem', categories=('Física',), school_years=('1ª Série',))
    assert [row[0] for row in page_questions(conn, filters, 1)[1]] == [3, 5]
    bounds, rows = page_questions(conn, filters, 1, {1, 9, 16})
    assert bounds.total == 3 and [row[0] for row in rows] == [1, 9, 16]


def test_count_and_page_agree_over_many_results(conn):
    conn.executemany('INSERT INTO questoes (id, ano_origem) VALUES (?, ?)',
                     [(i, '2022' if i % 2 else '2023') for i in range(100, 225)])
    conn.commit()
    filters = SearchFilters(source_year_from=2022, source_year_to=2022)
    one, rows1 = page_questions(conn, filters, 1)
    two, rows2 = page_questions(conn, filters, 2)
    expected = [3, 4] + [i for i in range(100, 225) if i % 2]
    assert one.total == two.total == len(expected)
    assert [row[0] for row in rows1 + rows2] == expected
    assert len(rows1) == 50 and len(rows2) == len(expected) - 50
