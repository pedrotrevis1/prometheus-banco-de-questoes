"""Read selected questions in the teacher's chosen order."""
import sqlite3


EXPORT_COLUMNS = ('id', 'assunto', 'dificuldade', 'tipo', 'enunciado',
                  'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e',
                  'gabarito', 'ano_sugerido', 'segmento', 'fonte_questao', 'ano_origem',
                  'last_modified', 'keep_alternative_order')


def fetch_ordered_questions(conn, ids):
    ids = list(ids)
    limit = max(1, conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER))
    found = {}
    for start in range(0, len(ids), limit):
        batch = ids[start:start + limit]
        placeholders = ','.join('?' for _ in batch)
        for row in conn.execute(f"SELECT {', '.join(EXPORT_COLUMNS)} FROM questoes WHERE id IN ({placeholders})", batch):
            found[row[0]] = row
    missing = [question_id for question_id in ids if question_id not in found]
    if missing:
        raise LookupError('Questões não encontradas: ' + ', '.join(map(str, missing)))
    return [found[question_id] for question_id in ids]


def fetch_question_summaries(conn, ids):
    """Read a bounded statement prefix for each selected question."""
    from html.parser import HTMLParser

    class SummaryParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.hidden = 0
            self.parts = []

        def handle_starttag(self, tag, attrs):
            if tag.lower() in ('head', 'style', 'script'):
                self.hidden += 1

        def handle_endtag(self, tag):
            if tag.lower() in ('head', 'style', 'script') and self.hidden:
                self.hidden -= 1

        def handle_data(self, data):
            if not self.hidden:
                self.parts.append(data)

    ids = list(ids)
    limit = max(1, conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER))
    result = {}
    for start in range(0, len(ids), limit):
        batch = ids[start:start + limit]
        placeholders = ','.join('?' for _ in batch)
        for question_id, text in conn.execute(
                f'SELECT id, SUBSTR(enunciado, 1, 4096) FROM questoes WHERE id IN ({placeholders})', batch):
            parser = SummaryParser(); parser.feed(text or ''); parser.close()
            result[question_id] = ' '.join(' '.join(parser.parts).split())[:100]
    return result
