"""Validation of normalized question data without a UI dependency."""
from dataclasses import dataclass

from prometheus.domain.normalization import DIFFICULTIES, KINDS, YEARS, plain_text


@dataclass(frozen=True)
class NormalizedQuestion:
    category_ids: tuple[int, ...]
    kind: str
    difficulty: str
    statement: str
    years: tuple[tuple[str, str], ...]
    alternatives: tuple[str, ...] = ()
    correct_position: int | None = None
    expected_answer: str = ''
    source: str = ''
    source_year: str = ''
    keep_alternative_order: bool = False


def _has_content(value):
    return bool(plain_text(value) or '<img' in value.casefold())


def validate_normalized_question(question):
    if question.kind not in KINDS.values() or question.difficulty not in DIFFICULTIES.values():
        raise ValueError('Invalid classification')
    if not question.category_ids or len(set(question.category_ids)) != len(question.category_ids):
        raise ValueError('A category is required')
    if not question.years or any(year not in YEARS.values() for year in question.years):
        raise ValueError('Invalid school year')
    if len(set(question.years)) != len(question.years):
        raise ValueError('Duplicate school year')
    if not _has_content(question.statement):
        raise ValueError('Statement is required')
    if question.kind == 'multiple_choice':
        if not 2 <= len(question.alternatives) <= 5 or not all(map(_has_content, question.alternatives)):
            raise ValueError('Two to five alternatives are required')
        if question.correct_position not in range(1, len(question.alternatives) + 1):
            raise ValueError('Invalid correct alternative')
    elif question.alternatives or question.correct_position is not None:
        raise ValueError('Essay questions cannot have alternatives')
    return question


def from_form(draft):
    kind = KINDS.get(draft.kind, '')
    alternatives = tuple(content.html for content in draft.alternatives) if kind == 'multiple_choice' else ()
    position = 'ABCDE'.find(draft.answer) + 1 if len(draft.answer) == 1 else None
    question = NormalizedQuestion(
        category_ids=draft.categories, kind=kind, difficulty=DIFFICULTIES.get(draft.difficulty, ''),
        statement=draft.statement.html, years=tuple(YEARS[year] for year in draft.years if year in YEARS),
        alternatives=alternatives, correct_position=position if alternatives else None,
        expected_answer=draft.essay_answer.html if kind == 'essay' and draft.essay_answer.has_content else '',
        source=draft.source, source_year=draft.source_year, keep_alternative_order=draft.keep_alternative_order)
    return validate_normalized_question(question)
