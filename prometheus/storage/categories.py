"""Category operations on the normalized schema."""
import sqlite3


class CategoryError(ValueError):
    pass


def list_categories(conn):
    return conn.execute('SELECT id, name, parent_id FROM normalized_categories ORDER BY name COLLATE NOCASE').fetchall()


def category_paths(conn):
    rows = list_categories(conn)
    by_id = {category_id: (name, parent) for category_id, name, parent in rows}
    paths = []
    for category_id, _, _ in rows:
        current, names = category_id, []
        while current is not None:
            name, current = by_id[current]
            names.append(name)
        paths.append((category_id, ' / '.join(reversed(names))))
    return paths


def _require_category(conn, category_id):
    if conn.execute('SELECT 1 FROM normalized_categories WHERE id = ?', (category_id,)).fetchone() is None:
        raise CategoryError('Category does not exist')


def _name(name):
    name = name.strip()
    if not name or ';' in name:
        raise CategoryError('Invalid category name')
    return name


def create_category(conn, name, parent_id=None):
    name = _name(name)
    if parent_id is not None:
        _require_category(conn, parent_id)
    try:
        with conn:
            return conn.execute('INSERT INTO normalized_categories (name, parent_id) VALUES (?, ?)',
                                (name, parent_id)).lastrowid
    except sqlite3.IntegrityError as exc:
        raise CategoryError('Category already exists among siblings') from exc


def rename_category(conn, category_id, name):
    _require_category(conn, category_id)
    try:
        with conn:
            conn.execute('UPDATE normalized_categories SET name = ? WHERE id = ?', (_name(name), category_id))
    except sqlite3.IntegrityError as exc:
        raise CategoryError('Category already exists among siblings') from exc


def descendants(conn, category_id):
    _require_category(conn, category_id)
    return tuple(row[0] for row in conn.execute('''WITH RECURSIVE tree(id) AS (
        SELECT id FROM normalized_categories WHERE id = ?
        UNION SELECT c.id FROM normalized_categories c JOIN tree ON c.parent_id = tree.id
    ) SELECT id FROM tree ORDER BY id''', (category_id,)))


def move_category(conn, category_id, parent_id):
    children = descendants(conn, category_id)
    if parent_id is not None:
        _require_category(conn, parent_id)
        if parent_id in children:
            raise CategoryError('Category cannot be moved under itself or a descendant')
    try:
        with conn:
            conn.execute('UPDATE normalized_categories SET parent_id = ? WHERE id = ?', (parent_id, category_id))
    except sqlite3.IntegrityError as exc:
        raise CategoryError('Category already exists among siblings') from exc


def delete_category(conn, category_id):
    ids = descendants(conn, category_id)
    # Explicitly remove links and descendants so question preservation does not
    # depend on a caller having enabled SQLite's connection-local foreign keys.
    placeholders = ','.join('?' for _ in ids)
    with conn:
        conn.execute(f'DELETE FROM question_categories WHERE category_id IN ({placeholders})', ids)
        conn.execute(f'DELETE FROM normalized_categories WHERE id IN ({placeholders})', ids)


def uncategorized_question_ids(conn):
    return tuple(row[0] for row in conn.execute('''SELECT q.id FROM normalized_questions q
        WHERE NOT EXISTS (SELECT 1 FROM question_categories qc WHERE qc.question_id = q.id)
        ORDER BY q.id'''))


def question_ids_for_category(conn, category_id):
    _require_category(conn, category_id)
    return tuple(row[0] for row in conn.execute('''WITH RECURSIVE tree(id) AS (
        SELECT id FROM normalized_categories WHERE id = ?
        UNION SELECT c.id FROM normalized_categories c JOIN tree ON c.parent_id = tree.id
    ) SELECT DISTINCT qc.question_id FROM question_categories qc
      JOIN tree ON tree.id = qc.category_id ORDER BY qc.question_id''', (category_id,)))
