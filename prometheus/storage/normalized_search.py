"""Bounded search against the normalized question schema."""
from dataclasses import dataclass

from prometheus.domain.normalization import search_text
from prometheus.domain.search import page_bounds


@dataclass(frozen=True)
class NormalizedSearchFilters:
    kinds: tuple[str, ...] = ()
    difficulties: tuple[str, ...] = ()
    text: str = ''
    source: str = ''
    source_year_from: int | None = None
    source_year_to: int | None = None
    years: tuple[str, ...] = ()
    category_ids: tuple[int, ...] = ()
    uncategorized: bool = False
    usage: str = 'all'
    unused_since: str | None = None


def page_questions(conn, filters, page=1, selected_ids=None):
    conn.create_function('PROMETHEUS_NORMALIZE', 1, search_text, deterministic=True)
    conn.create_function('PROMETHEUS_CASEFOLD', 1, lambda value: str(value or '').casefold(), deterministic=True)
    predicates, params = [], []
    if selected_ids is not None:
        selected = frozenset(selected_ids)
        conn.create_function('PROMETHEUS_SELECTED_NORMALIZED', 1, lambda value: int(value in selected), deterministic=True)
        predicates.append('PROMETHEUS_SELECTED_NORMALIZED(q.id)')
    else:
        if filters.usage == 'never':
            predicates.append('NOT EXISTS (SELECT 1 FROM exam_usage_questions uq WHERE uq.question_id=q.id)')
        elif filters.usage == 'since':
            if not filters.unused_since:
                raise ValueError('A usage date is required')
            predicates.append('''NOT EXISTS (SELECT 1 FROM exam_usage_questions uq
                JOIN exam_usages u ON u.id=uq.usage_id
                WHERE uq.question_id=q.id AND substr(u.used_at, 1, 10)>=?)''')
            params.append(filters.unused_since)
        elif filters.usage != 'all':
            raise ValueError('Invalid usage filter')
        for column, values in (('kind', filters.kinds), ('difficulty', filters.difficulties)):
            if values:
                predicates.append(f"q.{column} IN ({','.join('?' for _ in values)})")
                params.extend(values)
        if filters.text:
            predicates.append('INSTR(PROMETHEUS_NORMALIZE(q.search_text), ?) > 0')
            params.append(search_text(filters.text))
        if filters.source:
            predicates.append('INSTR(PROMETHEUS_CASEFOLD(q.source), ?) > 0')
            params.append(filters.source.casefold())
        if filters.source_year_from is not None:
            predicates.append('q.source_year >= ?')
            params.append(filters.source_year_from)
        if filters.source_year_to is not None:
            predicates.append('q.source_year <= ?')
            params.append(filters.source_year_to)
        if filters.years:
            predicates.append(f"EXISTS (SELECT 1 FROM question_years y WHERE y.question_id = q.id AND y.year IN ({','.join('?' for _ in filters.years)}))")
            params.extend(filters.years)
        category_predicates = []
        if filters.category_ids:
            category_predicates.append('''EXISTS (WITH RECURSIVE tree(id) AS (
                SELECT id FROM normalized_categories WHERE id IN (''' + ','.join('?' for _ in filters.category_ids) + ''')
                UNION SELECT c.id FROM normalized_categories c JOIN tree ON c.parent_id = tree.id
            ) SELECT 1 FROM question_categories qc JOIN tree ON tree.id = qc.category_id WHERE qc.question_id = q.id)''')
            params.extend(filters.category_ids)
        if filters.uncategorized:
            category_predicates.append('NOT EXISTS (SELECT 1 FROM question_categories qc WHERE qc.question_id = q.id)')
        if category_predicates:
            predicates.append('(' + ' OR '.join(category_predicates) + ')')
    clause = ' AND '.join(predicates) or '1=1'
    conn.execute('SAVEPOINT normalized_search')
    try:
        total = conn.execute(f'SELECT COUNT(*) FROM normalized_questions q WHERE {clause}', params).fetchone()[0]
        bounds = page_bounds(total, page)
        ids = () if not total else tuple(row[0] for row in conn.execute(
            f'SELECT q.id FROM normalized_questions q WHERE {clause} ORDER BY q.id LIMIT ? OFFSET ?',
            (*params, 50, bounds.start - 1)))
        conn.execute('RELEASE SAVEPOINT normalized_search')
        return bounds, ids
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT normalized_search')
        conn.execute('RELEASE SAVEPOINT normalized_search')
        raise
    finally:
        if selected_ids is not None:
            conn.create_function('PROMETHEUS_SELECTED_NORMALIZED', 1, None)
