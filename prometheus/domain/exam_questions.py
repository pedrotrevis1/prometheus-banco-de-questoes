"""Named question data passed to exam generation and export."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ExamQuestion:
    id: int
    kind: str
    statement: str
    alternatives: tuple[str, ...] = ()
    answer: str = ''
    keep_alternative_order: bool = False


def as_exam_question(question):
    if isinstance(question, ExamQuestion):
        return question
    # Compatibility with the old storage boundary until the application is switched.
    return ExamQuestion(question[0], 'multiple_choice' if question[3] == 'Múltipla Escolha' else 'essay',
                        question[4], tuple(question[5:10]) if question[3] == 'Múltipla Escolha' else (),
                        question[10] or '', bool(len(question) > 16 and question[16]))
