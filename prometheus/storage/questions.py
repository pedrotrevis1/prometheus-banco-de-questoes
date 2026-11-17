"""Question persistence on an existing bank connection."""
from datetime import datetime, timezone
from prometheus.domain.questions import question_values


COLUMNS = ('assunto', 'dificuldade', 'tipo', 'enunciado', 'ano_sugerido', 'segmento',
           'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e',
           'gabarito', 'fonte_questao', 'ano_origem', 'keep_alternative_order')


def _values_with_source(conn, draft, existing_source=None):
    values = list(question_values(draft))
    source_index = COLUMNS.index('fonte_questao')
    if existing_source is not None and values[source_index] == existing_source.strip():
        values[source_index] = existing_source
    elif values[source_index]:
        row = conn.execute('SELECT fonte_questao FROM questoes WHERE CASEFOLD(TRIM(fonte_questao)) = ? ORDER BY id LIMIT 1',
                           (values[source_index].casefold(),)).fetchone()
        if row:
            values[source_index] = row[0].strip()
    return values


def _timestamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _apply_unchanged(values, unchanged):
    for column, value in (unchanged or {}).items():
        values[COLUMNS.index(column)] = value
    return values


def insert_question(conn, draft, unchanged=None):
    values = _apply_unchanged(_values_with_source(conn, draft), unchanged)
    try:
        cursor = conn.execute(f"INSERT INTO questoes ({', '.join(COLUMNS)}, last_modified) VALUES ({', '.join('?' for _ in COLUMNS)}, ?)", [*values, _timestamp()])
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    return cursor.lastrowid


def get_question(conn, question_id):
    cursor = conn.execute(f"SELECT id, {', '.join(COLUMNS)}, last_modified FROM questoes WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    return dict(zip(('id', *COLUMNS, 'last_modified'), row)) if row else None


def update_question(conn, question_id, draft, unchanged=None):
    current = conn.execute('SELECT fonte_questao FROM questoes WHERE id = ?', (question_id,)).fetchone()
    if current is None:
        raise LookupError(f'Question {question_id} no longer exists')
    values = _apply_unchanged(_values_with_source(conn, draft, existing_source=current[0] or ''), unchanged)
    assignments = ', '.join(f'{column} = ?' for column in COLUMNS)
    try:
        cursor = conn.execute(f'UPDATE questoes SET {assignments}, last_modified = ? WHERE id = ?',
                              [*values, _timestamp(), question_id])
        if cursor.rowcount != 1:
            raise LookupError(f'Question {question_id} no longer exists')
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
