"""Prepare normalized records for the existing question-card presentation."""
from prometheus.domain.normalization import DIFFICULTIES, KINDS, YEARS
from prometheus.domain.card_data import QuestionCardData
from prometheus.storage.normalized_questions import get_question


def question_card_row(conn, question_id):
    question = get_question(conn, question_id)
    if question is None:
        raise LookupError(f'Question {question_id} no longer exists')
    kinds = {code: label for label, code in KINDS.items()}
    difficulties = {code: label for label, code in DIFFICULTIES.items()}
    years = {code: label for label, code in YEARS.items()}
    names = [row[0] for row in conn.execute('''SELECT c.name FROM normalized_categories c
        JOIN question_categories qc ON qc.category_id = c.id
        WHERE qc.question_id = ? ORDER BY c.name''', (question_id,))]
    alternatives = question['alternatives']
    option_text = [content for _, content, _ in alternatives]
    answer = next(('ABCDE'[position - 1] for position, _, correct in alternatives if correct), '')
    if question['kind'] == 'essay':
        answer = question['expected_answer'] or ''
    labels = [years.get(year, year[1]) for year in question['years']]
    segment_names = {'fundamental_ii': 'Ensino Fundamental', 'medio': 'Ensino Médio'}
    segments = '; '.join(segment_names.get(code, code) for code in question['segments'])
    return QuestionCardData(question_id, '; '.join(names), difficulties.get(question['difficulty'], ''),
        '; '.join(labels), segments, kinds.get(question['kind'], ''), question['statement'],
        tuple(option_text), answer, question['source'], question['source_year_raw'], question['updated_at'])
