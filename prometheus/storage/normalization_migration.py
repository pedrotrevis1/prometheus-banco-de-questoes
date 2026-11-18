"""Conversion of version-3 banks; callers own the transaction and backup.

The caller must provide an explicit transaction and a backup before running it.
"""
from prometheus.domain.normalization import (
    DIFFICULTIES, KINDS, SEGMENTS, YEARS, map_source_year, plain_text,
)
from prometheus.domain.questions import stored_school_years


class CategoryMigrationError(ValueError):
    def __init__(self, category_id, reason):
        self.category_id = category_id
        self.reason = reason
        super().__init__(f'Category {category_id}: {reason}')


def _validate_categories(rows):
    """Reject malformed trees before constructing the normalized hierarchy."""
    parents = {category_id: parent for category_id, _, parent in rows}
    for category_id, name, _ in rows:
        if not isinstance(name, str) or not name:
            raise CategoryMigrationError(category_id, 'missing name')
        visited = set()
        current = category_id
        while current is not None:
            if current in visited:
                raise CategoryMigrationError(category_id, 'cyclic hierarchy')
            if current not in parents:
                raise CategoryMigrationError(category_id, f'missing parent {current}')
            visited.add(current)
            current = parents[current]


def convert_v3(conn):
    """Create normalized data alongside its untouched legacy source.

    A caller must wrap this operation in a transaction. Raw legacy records are
    retained to allow recovery of values which cannot be interpreted safely.
    """
    if not conn.in_transaction:
        raise RuntimeError('Normalization requires an active transaction')
    category_rows = conn.execute('SELECT id, nome, parent_id FROM assuntos').fetchall()
    _validate_categories(category_rows)
    for statement in (
        '''CREATE TABLE normalized_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT, difficulty TEXT, statement TEXT, statement_text TEXT NOT NULL,
            search_text TEXT NOT NULL,
            expected_answer TEXT, source TEXT, source_year INTEGER, source_year_raw TEXT,
            created_at TEXT, updated_at TEXT, keep_alternative_order INTEGER NOT NULL)''',
        '''CREATE TABLE normalized_categories (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL,
            parent_id INTEGER REFERENCES normalized_categories(id) ON DELETE CASCADE)''',
        '''CREATE UNIQUE INDEX normalized_category_root_name
            ON normalized_categories(name) WHERE parent_id IS NULL''',
        '''CREATE UNIQUE INDEX normalized_category_sibling_name
            ON normalized_categories(parent_id, name) WHERE parent_id IS NOT NULL''',
        '''CREATE TABLE question_categories (
            question_id INTEGER NOT NULL REFERENCES normalized_questions(id) ON DELETE CASCADE,
            category_id INTEGER NOT NULL REFERENCES normalized_categories(id) ON DELETE CASCADE,
            PRIMARY KEY (question_id, category_id))''',
        '''CREATE TABLE question_years (
            question_id INTEGER NOT NULL REFERENCES normalized_questions(id) ON DELETE CASCADE,
            segment TEXT NOT NULL, year TEXT NOT NULL,
            PRIMARY KEY (question_id, segment, year))''',
        '''CREATE TABLE question_alternatives (
            question_id INTEGER NOT NULL REFERENCES normalized_questions(id) ON DELETE CASCADE,
            position INTEGER NOT NULL, content TEXT NOT NULL, is_correct INTEGER NOT NULL,
            PRIMARY KEY (question_id, position))''',
        '''CREATE TABLE normalization_report (
            question_id INTEGER NOT NULL REFERENCES normalized_questions(id) ON DELETE CASCADE,
            field TEXT NOT NULL, value TEXT NOT NULL)''',
    ):
        conn.execute(statement)

    categories = {name: category_id for category_id, name, _ in category_rows}
    for category_id, name, _ in category_rows:
        conn.execute('INSERT INTO normalized_categories (id, name) VALUES (?, ?)',
                     (category_id, name))
    for category_id, _, parent_id in category_rows:
        if parent_id is not None:
            conn.execute('UPDATE normalized_categories SET parent_id = ? WHERE id = ?',
                         (parent_id, category_id))
    cursor = conn.execute('SELECT * FROM questoes ORDER BY id')
    names = tuple(column[0] for column in cursor.description)
    for values in cursor:
        row = dict(zip(names, values))
        question_id = row['id']
        kind = KINDS.get(row['tipo'])
        difficulty = DIFFICULTIES.get(row['dificuldade'])
        source_year, source_year_raw = map_source_year(row['ano_origem'])
        expected = row['gabarito'] if kind == 'essay' else None
        searchable = [row['enunciado']]
        searchable.extend(row[f'alternativa_{letter}'] for letter in 'abcde')
        if kind == 'essay':
            searchable.append(expected)
        search_text = ' '.join(filter(None, (plain_text(value) for value in searchable)))
        conn.execute('''INSERT INTO normalized_questions VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)''',
            (question_id, kind, difficulty, row['enunciado'], plain_text(row['enunciado']),
             search_text, expected, row['fonte_questao'], source_year, source_year_raw,
             row['last_modified'], row['keep_alternative_order']))

        def report(field, value):
            conn.execute('INSERT INTO normalization_report VALUES (?, ?, ?)',
                         (question_id, field, str(value)))

        for field, value, code in (('tipo', row['tipo'], kind),
                                   ('dificuldade', row['dificuldade'], difficulty)):
            if code is None:
                report(field, '' if value is None else value)
        if source_year is None and source_year_raw and source_year_raw.strip():
            report('ano_origem', source_year_raw)
        for category in (part.strip() for part in (row['assunto'] or '').split(';')):
            if not category:
                continue
            if category not in categories:
                report('assunto', category)
            else:
                conn.execute('INSERT OR IGNORE INTO question_categories VALUES (?, ?)',
                             (question_id, categories[category]))
        segment, years = stored_school_years(row['ano_sugerido'], row['segmento'])
        if segment and segment not in SEGMENTS:
            report('segmento', segment)
        for year in years:
            mapped = YEARS.get(year)
            if mapped is None or (segment and SEGMENTS.get(segment) != mapped[0]):
                report('ano_sugerido', year)
            else:
                conn.execute('INSERT OR IGNORE INTO question_years VALUES (?, ?, ?)',
                             (question_id, *mapped))
        if kind == 'multiple_choice':
            answer = str(row['gabarito'] or '').strip().upper()
            if answer not in 'ABCDE' or len(answer) != 1:
                report('gabarito', row['gabarito'] or '')
            for position, letter in enumerate('ABCDE', 1):
                content = row[f'alternativa_{letter.lower()}'] or ''
                if not content.strip():
                    report(f'alternativa_{letter.lower()}', content)
                conn.execute('INSERT INTO question_alternatives VALUES (?, ?, ?, ?)',
                             (question_id, position, content, int(answer == letter)))


def migrate_v3_to_v4(conn):
    """Convert and advance the schema version as part of the caller's transaction."""
    if conn.execute('PRAGMA user_version').fetchone()[0] != 3:
        raise ValueError('Expected schema version 3')
    convert_v3(conn)
    conn.execute('PRAGMA user_version = 4')


def migrate_v4_to_v5(conn):
    """Preserve independent segments, recovering lossless schema-4 upgrades."""
    if not conn.in_transaction:
        raise RuntimeError('Normalization requires an active transaction')
    if conn.execute('PRAGMA user_version').fetchone()[0] != 4:
        raise ValueError('Expected schema version 4')
    conn.execute('''CREATE TABLE question_segments (
        question_id INTEGER NOT NULL REFERENCES normalized_questions(id) ON DELETE CASCADE,
        segment TEXT NOT NULL,
        PRIMARY KEY (question_id, segment))''')
    conn.execute('''INSERT INTO question_segments (question_id, segment)
        SELECT DISTINCT question_id, segment FROM question_years''')
    for question_id, segment in conn.execute('SELECT question_id, segment FROM question_segments'):
        if segment not in SEGMENTS.values():
            conn.execute('''INSERT INTO normalization_report (question_id, field, value)
                SELECT ?, 'segmento', ? WHERE NOT EXISTS
                (SELECT 1 FROM normalization_report WHERE question_id = ? AND field = 'segmento' AND value = ?)''',
                (question_id, segment, question_id, segment))
    for question_id, segment, year in conn.execute('SELECT question_id, segment, year FROM question_years'):
        if (segment, year) not in YEARS.values():
            conn.execute('''INSERT INTO normalization_report (question_id, field, value)
                SELECT ?, 'ano_sugerido', ? WHERE NOT EXISTS
                (SELECT 1 FROM normalization_report WHERE question_id = ? AND field = 'ano_sugerido' AND value = ?)''',
                (question_id, year, question_id, year))
    rows = conn.execute('''SELECT q.id, legacy.segmento, legacy.ano_sugerido
        FROM normalized_questions q JOIN questoes legacy ON legacy.id = q.id
        WHERE NOT EXISTS (SELECT 1 FROM question_years y WHERE y.question_id = q.id)''')
    for question_id, raw_segment, raw_years in rows:
        segment, _ = stored_school_years(raw_years, raw_segment)
        if segment in SEGMENTS:
            conn.execute('INSERT INTO question_segments VALUES (?, ?)', (question_id, SEGMENTS[segment]))
        elif segment:
            conn.execute('''INSERT INTO normalization_report (question_id, field, value)
                SELECT ?, 'segmento', ? WHERE NOT EXISTS
                (SELECT 1 FROM normalization_report WHERE question_id = ? AND field = 'segmento' AND value = ?)''',
                (question_id, segment, question_id, segment))
    conn.execute('PRAGMA user_version = 5')
