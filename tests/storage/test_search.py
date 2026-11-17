import sqlite3

import pytest
from prometheus.domain.search import SearchFilters
from prometheus.storage.search import search_questions


@pytest.fixture
def conn():
    c = sqlite3.connect(':memory:')
    c.create_function('CASEFOLD', 1, lambda value: str(value or '').casefold())
    c.execute('''CREATE TABLE questoes (id INTEGER, assunto TEXT, dificuldade TEXT, ano_sugerido TEXT,
        segmento TEXT, tipo TEXT, enunciado TEXT, alternativa_a TEXT, alternativa_b TEXT,
        alternativa_c TEXT, alternativa_d TEXT, alternativa_e TEXT, gabarito TEXT,
        fonte_questao TEXT, ano_origem TEXT)''')
    rows = [
        (1, 'Bio; Física', 'Fácil', '1ª Série', 'Ensino Médio', 'Múltipla Escolha', '<p>célula</p>', '', '', '', '', '', 'A', 'ENEM', '2022'),
        (2, 'Biologia', 'Difícil', '{"level":"Ensino Fundamental","years":["6"]}', '', 'Dissertativa', '<b>texto</b>', '', '', '', '', '', '', 'Fuvest', '2023'),
        (3, 'Física', 'Fácil', '2ª Série;3ª Série', 'Ensino Médio', 'Dissertativa', 'outro', '', '', '', '', '', '', 'enem', '2023'),
    ]
    c.executemany('INSERT INTO questoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    yield c
    c.close()


@pytest.mark.parametrize(('filters', 'ids'), [
    (SearchFilters(), [1, 2, 3]),
    (SearchFilters(difficulties=('Fácil',)), [1, 3]),
    (SearchFilters(question_types=('Dissertativa',)), [2, 3]),
    (SearchFilters(text='texto'), [2]),
    (SearchFilters(source='EnEm'), [1, 3]),
    (SearchFilters(source_year_from=2023, source_year_to=2023), [2, 3]),
    (SearchFilters(categories=('Bio',)), [1]),
    (SearchFilters(categories=('Física',), school_years=('2ª Série',)), [3]),
    (SearchFilters(school_years=('6º Ano',)), [2]),
])
def test_legacy_filters(conn, filters, ids):
    assert [row[0] for row in search_questions(conn, filters)] == ids


def test_selected_only_ignores_filters_and_empty_stays_empty(conn):
    filters = SearchFilters(text='not found', categories=('missing',))
    assert [row[0] for row in search_questions(conn, filters, {1, 3})] == [1, 3]
    assert search_questions(conn, filters, set()) == []


def test_connection_matchers_preserve_token_and_legacy_year_semantics(conn):
    import json
    from prometheus.storage.search import register_legacy_matchers
    register_legacy_matchers(conn)
    rows = conn.execute('''SELECT id FROM questoes WHERE
        PROMETHEUS_CATEGORY_MATCH(assunto, ?) AND PROMETHEUS_YEAR_MATCH(ano_sugerido, segmento, ?)''',
        (json.dumps(['Biologia']), json.dumps(['6º Ano']))).fetchall()
    assert rows == [(2,)]


def test_paged_results_count_and_content_match_all_predicates(conn):
    from prometheus.storage.search import page_questions
    rows = [(i, 'Física' if i % 3 == 0 else 'Bio', 'Fácil',
             '2ª Série' if i % 2 == 0 else '1ª Série', 'Ensino Médio', 'Dissertativa',
             'grande ' * 100, '', '', '', '', '', '', 'ENEM', '2022') for i in range(10, 410)]
    conn.executemany('INSERT INTO questoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', reversed(rows))
    filters = SearchFilters(categories=('Física',), school_years=('2ª Série',), source='enem')
    expected = [3] + [i for i in range(10, 410) if i % 6 == 0]
    pages = []
    for page in range(1, 3):
        bounds, result = page_questions(conn, filters, page)
        assert bounds.total == len(expected)
        assert len(result) <= 50
        pages.extend(row[0] for row in result)
    assert pages == expected


def test_selected_page_respects_small_bind_limit_and_bypasses_filters(conn):
    from prometheus.storage.search import page_questions
    rows = [(i, '', '', '', '', '', 'x', '', '', '', '', '', '', '', '') for i in range(10, 210)]
    conn.executemany('INSERT INTO questoes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    conn.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, 16)
    selected = set(range(10, 210))
    bounds, result = page_questions(conn, SearchFilters(text='missing'), 3, selected)
    assert bounds.total == 200
    assert [r[0] for r in result] == list(range(110, 160))
    bounds, result = page_questions(conn, SearchFilters(), 99, set())
    assert bounds.total == 0 and result == []
