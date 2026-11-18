"""Read named normalized questions for exam generation."""
from prometheus.domain.exam_questions import ExamQuestion
from prometheus.domain.normalization import plain_text
from prometheus.storage.normalized_questions import get_question
import sqlite3


def fetch_ordered_questions(conn, ids):
    questions = []
    for question_id in ids:
        row = get_question(conn, question_id)
        if row is None:
            raise LookupError(f'Questão não encontrada: {question_id}')
        alternatives = row['alternatives']
        if row['kind'] == 'multiple_choice':
            correct = [position for position, _, is_correct in alternatives if is_correct]
            if (not 2 <= len(alternatives) <= 5 or len(correct) != 1 or
                    [position for position, _, _ in alternatives] != list(range(1, len(alternatives) + 1)) or
                    any(not plain_text(content) and '<img' not in content.casefold()
                        for _, content, _ in alternatives)):
                raise ValueError(f'Alternativas ou gabarito inválidos na questão {question_id}.')
            answer = 'ABCDE'[correct[0] - 1]
        elif row['kind'] == 'essay':
            answer = row['expected_answer'] or ''
        else:
            raise ValueError(f'Tipo inválido na questão {question_id}.')
        questions.append(ExamQuestion(question_id, row['kind'], row['statement'] or '',
                        tuple(content for _, content, _ in alternatives), answer,
                        bool(row['keep_alternative_order'])))
    return questions


def fetch_question_summaries(conn, ids):
    ids = list(ids)
    limit = max(1, conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER))
    result = {}
    for start in range(0, len(ids), limit):
        batch = ids[start:start + limit]
        placeholders = ','.join('?' for _ in batch)
        for question_id, statement in conn.execute(
                f'SELECT id, SUBSTR(statement_text, 1, 100) FROM normalized_questions WHERE id IN ({placeholders})', batch):
            result[question_id] = statement
    return result
