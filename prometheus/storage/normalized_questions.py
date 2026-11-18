"""Persistence of normalized questions and their dependent records."""
from datetime import datetime, timezone

from prometheus.domain.normalization import map_source_year, plain_text
from prometheus.domain.normalized_questions import validate_normalized_question


def save_question(conn, question, question_id=None):
    validate_normalized_question(question)
    category_ids = set(question.category_ids)
    found = {row[0] for row in conn.execute('SELECT id FROM normalized_categories')}
    if not category_ids <= found:
        raise ValueError('Category does not exist')
    timestamp = datetime.now(timezone.utc).isoformat(timespec='microseconds')
    source_year, raw_year = map_source_year(question.source_year)
    source = question.source.strip()
    if question_id is not None:
        existing = conn.execute('SELECT source FROM normalized_questions WHERE id = ?', (question_id,)).fetchone()
        if existing is None:
            raise LookupError(f'Question {question_id} does not exist')
        if source == (existing[0] or '').strip():
            source = existing[0] or ''
    if source and (question_id is None or source != (existing[0] or '')):
        match = next((value for (value,) in conn.execute(
            'SELECT source FROM normalized_questions ORDER BY id') if (value or '').strip().casefold() == source.casefold()), None)
        if match:
            source = match.strip()
    searchable = [question.statement, *question.alternatives, question.expected_answer]
    searchable = ' '.join(filter(None, (plain_text(value) for value in searchable)))
    values = (question.kind, question.difficulty, question.statement, plain_text(question.statement),
              searchable, question.expected_answer, source, source_year, raw_year,
              timestamp, int(question.keep_alternative_order))
    with conn:
        has_segments = conn.execute('PRAGMA user_version').fetchone()[0] >= 5
        if question_id is None:
            cursor = conn.execute('''INSERT INTO normalized_questions
                (kind, difficulty, statement, statement_text, search_text, expected_answer,
                 source, source_year, source_year_raw, created_at, updated_at, keep_alternative_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (*values[:-2], timestamp, *values[-2:]))
            question_id = cursor.lastrowid
        else:
            cursor = conn.execute('''UPDATE normalized_questions SET kind=?, difficulty=?, statement=?,
                statement_text=?, search_text=?, expected_answer=?, source=?, source_year=?,
                source_year_raw=?, updated_at=?, keep_alternative_order=? WHERE id=?''', (*values, question_id))
            if cursor.rowcount != 1:
                raise LookupError(f'Question {question_id} does not exist')
            for table in ('question_categories', 'question_years', 'question_alternatives'):
                conn.execute(f'DELETE FROM {table} WHERE question_id = ?', (question_id,))
            if has_segments:
                conn.execute('DELETE FROM question_segments WHERE question_id = ?', (question_id,))
        conn.executemany('INSERT INTO question_categories VALUES (?, ?)',
                         ((question_id, category_id) for category_id in question.category_ids))
        conn.executemany('INSERT INTO question_years VALUES (?, ?, ?)',
                         ((question_id, segment, year) for segment, year in question.years))
        if has_segments:
            conn.executemany('INSERT INTO question_segments VALUES (?, ?)',
                             ((question_id, segment) for segment in sorted({segment for segment, _ in question.years})))
        conn.executemany('INSERT INTO question_alternatives VALUES (?, ?, ?, ?)',
                         ((question_id, position, content, int(position == question.correct_position))
                          for position, content in enumerate(question.alternatives, 1)))
    return question_id


def get_question(conn, question_id):
    cursor = conn.execute('''SELECT id, kind, difficulty, statement, expected_answer, source,
        source_year, source_year_raw, created_at, updated_at, keep_alternative_order
        FROM normalized_questions WHERE id = ?''', (question_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    result = dict(zip((column[0] for column in cursor.description), row))
    result['category_ids'] = tuple(row[0] for row in conn.execute(
        'SELECT category_id FROM question_categories WHERE question_id = ? ORDER BY category_id', (question_id,)))
    result['years'] = tuple(conn.execute('SELECT segment, year FROM question_years WHERE question_id = ? ORDER BY segment, year', (question_id,)))
    if conn.execute('PRAGMA user_version').fetchone()[0] >= 5:
        result['segments'] = tuple(row[0] for row in conn.execute(
            'SELECT segment FROM question_segments WHERE question_id = ? ORDER BY segment', (question_id,)))
    else:
        result['segments'] = tuple(sorted({segment for segment, _ in result['years']}))
    result['alternatives'] = tuple(conn.execute('SELECT position, content, is_correct FROM question_alternatives WHERE question_id = ? ORDER BY position', (question_id,)))
    return result


def delete_questions(conn, question_ids):
    ids = tuple(set(question_ids))
    if not ids:
        return 0
    with conn:
        count = 0
        has_segments = conn.execute('PRAGMA user_version').fetchone()[0] >= 5
        for question_id in ids:
            for table in ('question_categories', 'question_years', 'question_alternatives', 'normalization_report'):
                conn.execute(f'DELETE FROM {table} WHERE question_id = ?', (question_id,))
            if has_segments:
                conn.execute('DELETE FROM question_segments WHERE question_id = ?', (question_id,))
            count += conn.execute('DELETE FROM normalized_questions WHERE id = ?', (question_id,)).rowcount
            conn.execute('DELETE FROM questoes WHERE id = ?', (question_id,))
    return count
