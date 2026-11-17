"""Search the existing question schema without a Qt dependency."""
from prometheus.domain.search import SearchFilters, matches_legacy_filters


COLUMNS = '''id, assunto, dificuldade, ano_sugerido, segmento, tipo, enunciado,
             alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito,
             fonte_questao, ano_origem'''


def search_questions(conn, filters, selected_ids=None):
    """Characterize the original unpaged search, including selected-only mode."""
    if selected_ids is not None:
        if not selected_ids:
            return []
        filters = SearchFilters()
    query = f'SELECT {COLUMNS} FROM questoes WHERE 1=1'
    params = []
    if selected_ids is not None:
        query += f" AND id IN ({','.join('?' for _ in selected_ids)})"
        params.extend(sorted(selected_ids))
    for column, values in (('dificuldade', filters.difficulties), ('tipo', filters.question_types)):
        if values:
            query += f" AND {column} IN ({','.join('?' for _ in values)})"
            params.extend(values)
    if filters.text:
        query += ' AND enunciado LIKE ?'
        params.append(f'%{filters.text}%')
    if filters.source:
        query += ' AND INSTR(CASEFOLD(fonte_questao), ?) > 0'
        params.append(filters.source.casefold())
    if filters.source_year:
        query += ' AND ano_origem = ?'
        params.append(filters.source_year)
    rows = conn.execute(query, params).fetchall()
    return [row for row in rows if matches_legacy_filters(row[1], row[3], row[4], filters)]


def register_legacy_matchers(conn):
    """Register connection-local helpers that preserve legacy token semantics."""
    import json
    from prometheus.domain.school_years import parse_question_year_values

    def category_matches(value, encoded):
        wanted = json.loads(encoded)
        tokens = [token.strip() for token in (value or '').split(';')]
        return int(any(category in tokens for category in wanted))

    def year_matches(value, segment, encoded):
        return int(bool(set(json.loads(encoded)).intersection(parse_question_year_values(value, segment))))

    conn.create_function('PROMETHEUS_CATEGORY_MATCH', 2, category_matches, deterministic=True)
    conn.create_function('PROMETHEUS_YEAR_MATCH', 3, year_matches, deterministic=True)


def page_questions(conn, filters, page, selected_ids=None):
    """Count and fetch one bounded page from a single read snapshot."""
    import json
    from prometheus.domain.search import page_bounds

    register_legacy_matchers(conn)
    predicates = []
    params = []
    selected = None if selected_ids is None else frozenset(selected_ids)
    if selected is not None:
        conn.create_function('PROMETHEUS_SELECTED', 1, lambda value: int(value in selected), deterministic=True)
        predicates.append('PROMETHEUS_SELECTED(id)')
    else:
        for column, values in (('dificuldade', filters.difficulties), ('tipo', filters.question_types)):
            if values:
                predicates.append(f"{column} IN ({','.join('?' for _ in values)})")
                params.extend(values)
        if filters.text:
            predicates.append('enunciado LIKE ?')
            params.append(f'%{filters.text}%')
        if filters.source:
            predicates.append('INSTR(CASEFOLD(fonte_questao), ?) > 0')
            params.append(filters.source.casefold())
        if filters.source_year:
            predicates.append('ano_origem = ?')
            params.append(filters.source_year)
        if filters.categories:
            predicates.append('PROMETHEUS_CATEGORY_MATCH(assunto, ?)')
            params.append(json.dumps(filters.categories))
        if filters.school_years:
            predicates.append('PROMETHEUS_YEAR_MATCH(ano_sugerido, segmento, ?)')
            params.append(json.dumps(filters.school_years))
    clause = ' AND '.join(predicates) or '1=1'
    conn.execute('SAVEPOINT prometheus_search')
    try:
        total = conn.execute(f'SELECT COUNT(*) FROM questoes WHERE {clause}', params).fetchone()[0]
        bounds = page_bounds(total, page)
        rows = [] if not total else conn.execute(
            f'SELECT {COLUMNS} FROM questoes WHERE {clause} ORDER BY id ASC LIMIT ? OFFSET ?',
            [*params, 50, bounds.start - 1]).fetchall()
        conn.execute('RELEASE SAVEPOINT prometheus_search')
        return bounds, rows
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT prometheus_search')
        conn.execute('RELEASE SAVEPOINT prometheus_search')
        raise
    finally:
        if selected is not None:
            conn.create_function('PROMETHEUS_SELECTED', 1, None)
