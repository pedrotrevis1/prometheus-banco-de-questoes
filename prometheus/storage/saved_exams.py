"""Persistence for saved exams, managed classes and question usage."""
import json
from datetime import datetime

from prometheus.domain.exam_arrangements import arrangement_configuration


def _name(value):
    value = value.strip()
    if not value:
        raise ValueError('Name must not be empty')
    return value


def add_class(conn, name):
    with conn:
        return conn.execute('INSERT INTO exam_classes(name) VALUES (?)', (_name(name),)).lastrowid


def list_classes(conn):
    return conn.execute('SELECT id, name FROM exam_classes ORDER BY name COLLATE NOCASE, id').fetchall()


def rename_class(conn, class_id, name):
    with conn:
        if not conn.execute('UPDATE exam_classes SET name=? WHERE id=?', (_name(name), class_id)).rowcount:
            raise LookupError('Class not found')


def delete_class(conn, class_id):
    with conn:
        conn.execute('UPDATE saved_exams SET class_id=NULL WHERE class_id=?', (class_id,))
        conn.execute('DELETE FROM exam_classes WHERE id=?', (class_id,))


def list_exams(conn):
    return conn.execute('''SELECT e.id, e.name, c.name FROM saved_exams e
        LEFT JOIN exam_classes c ON c.id=e.class_id ORDER BY e.name COLLATE NOCASE, e.id''').fetchall()


def save_exam(conn, name, class_id, settings, question_ids, exam_id=None):
    name = _name(name)
    ids = tuple(question_ids)
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate question')
    rows = []
    for question_id in ids:
        row = conn.execute('SELECT updated_at FROM normalized_questions WHERE id=?', (question_id,)).fetchone()
        if row is None:
            raise LookupError(f'Question {question_id} not found')
        rows.append((question_id, row[0]))
    if class_id is not None and not conn.execute('SELECT 1 FROM exam_classes WHERE id=?', (class_id,)).fetchone():
        raise LookupError('Class not found')
    with conn:
        if exam_id is None:
            exam_id = conn.execute('INSERT INTO saved_exams(name,class_id,settings) VALUES (?,?,?)',
                                   (name, class_id, json.dumps(settings))).lastrowid
        else:
            previous = load_exam(conn, exam_id)
            snapshots = dict(conn.execute('SELECT question_id, question_updated_at FROM saved_exam_questions WHERE exam_id=?', (exam_id,)))
            # Older version records contain only the arrangement. Attach the
            # configuration before overwriting it, so a later cancelled export
            # cannot make those records appear to belong to the new draft.
            configuration = arrangement_configuration(previous['question_ids'], previous['settings'])
            for version, encoded in conn.execute('SELECT version, arrangement FROM exam_versions WHERE exam_id=?', (exam_id,)).fetchall():
                value = json.loads(encoded)
                if isinstance(value, list):
                    conn.execute('UPDATE exam_versions SET arrangement=? WHERE exam_id=? AND version=?',
                                 (json.dumps({'configuration': configuration, 'arrangement': value}), exam_id, version))
            conn.execute('UPDATE saved_exams SET name=?,class_id=?,settings=? WHERE id=?',
                         (name, class_id, json.dumps(settings), exam_id))
            rows = [(question_id, snapshots.get(question_id, updated)) for question_id, updated in rows]
            conn.execute('DELETE FROM saved_exam_questions WHERE exam_id=?', (exam_id,))
        conn.executemany('INSERT INTO saved_exam_questions VALUES (?,?,?,?)',
                         ((exam_id, pos, question_id, updated) for pos, (question_id, updated) in enumerate(rows)))
    return exam_id


def load_exam(conn, exam_id):
    row = conn.execute('SELECT name,class_id,settings FROM saved_exams WHERE id=?', (exam_id,)).fetchone()
    if row is None:
        raise LookupError('Exam not found')
    questions = conn.execute('''SELECT s.question_id, s.question_updated_at, q.updated_at, q.id
        FROM saved_exam_questions s LEFT JOIN normalized_questions q ON q.id=s.question_id
        WHERE s.exam_id=? ORDER BY s.position''', (exam_id,)).fetchall()
    return {'id': exam_id, 'name': row[0], 'class_id': row[1], 'settings': json.loads(row[2]),
            'question_ids': tuple(q[0] for q in questions),
            'changed_ids': tuple(q[0] for q in questions if q[1] != q[2] or q[3] is None)}


def rename_exam(conn, exam_id, name):
    with conn:
        if not conn.execute('UPDATE saved_exams SET name=? WHERE id=?', (_name(name), exam_id)).rowcount:
            raise LookupError('Exam not found')


def duplicate_exam(conn, exam_id, name):
    exam = load_exam(conn, exam_id)
    return save_exam(conn, name, exam['class_id'], exam['settings'], exam['question_ids'])


def delete_exam(conn, exam_id):
    with conn:
        usages = [r[0] for r in conn.execute('SELECT id FROM exam_usages WHERE exam_id=?', (exam_id,))]
        conn.executemany('DELETE FROM exam_usage_questions WHERE usage_id=?', ((i,) for i in usages))
        for table in ('exam_usages', 'exam_versions', 'saved_exam_questions'):
            conn.execute(f'DELETE FROM {table} WHERE exam_id=?', (exam_id,))
        conn.execute('DELETE FROM saved_exams WHERE id=?', (exam_id,))


def record_generation(conn, exam_id, arrangements, question_ids, *, used_at=None):
    exam = load_exam(conn, exam_id)
    class_name = ''
    if exam['class_id'] is not None:
        row = conn.execute('SELECT name FROM exam_classes WHERE id=?', (exam['class_id'],)).fetchone()
        class_name = row[0] if row else ''
    with conn:
        conn.execute('DELETE FROM exam_versions WHERE exam_id=?', (exam_id,))
        configuration = arrangement_configuration(exam['question_ids'], exam['settings'])
        conn.executemany('INSERT INTO exam_versions VALUES (?,?,?)',
                         ((exam_id, i, json.dumps({'configuration': configuration, 'arrangement': value}))
                          for i, value in enumerate(arrangements, 1)))
        usage_id = conn.execute('INSERT INTO exam_usages(exam_id,class_name,used_at,version_count) VALUES (?,?,?,?)',
            (exam_id, class_name, used_at or datetime.now().astimezone().isoformat(), len(arrangements))).lastrowid
        conn.executemany('INSERT INTO exam_usage_questions VALUES (?,?)', ((usage_id, i) for i in set(question_ids)))
        conn.execute('''UPDATE saved_exam_questions SET question_updated_at =
            (SELECT updated_at FROM normalized_questions WHERE id = saved_exam_questions.question_id)
            WHERE exam_id=?''', (exam_id,))


def versions(conn, exam_id):
    return [value['arrangement'] if isinstance(value, dict) else value for value in _version_records(conn, exam_id)]


def _version_records(conn, exam_id):
    return [json.loads(row[0]) for row in conn.execute(
        'SELECT arrangement FROM exam_versions WHERE exam_id=? ORDER BY version', (exam_id,))]


def matching_versions(conn, exam_id):
    exam = load_exam(conn, exam_id)
    configuration = arrangement_configuration(exam['question_ids'], exam['settings'])
    records = _version_records(conn, exam_id)
    if any(isinstance(value, dict) and value['configuration'] != configuration for value in records):
        return []
    return [value['arrangement'] if isinstance(value, dict) else value for value in records]


def question_usages(conn, question_id):
    return conn.execute('''SELECT e.name,u.class_name,u.used_at FROM exam_usage_questions q
        JOIN exam_usages u ON u.id=q.usage_id JOIN saved_exams e ON e.id=u.exam_id
        WHERE q.question_id=? ORDER BY u.used_at DESC,u.id DESC''', (question_id,)).fetchall()


def containing_exams(conn, question_ids):
    ids = set(question_ids)
    return [(exam_id, name) for exam_id, name, question_id in conn.execute('''SELECT e.id,e.name,q.question_id
        FROM saved_exams e JOIN saved_exam_questions q ON q.exam_id=e.id ORDER BY e.name''') if question_id in ids]
