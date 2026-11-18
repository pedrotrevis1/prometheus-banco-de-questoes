"""Named data for presenting a question card."""
from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionCardData:
    question_id: int
    categories: str
    difficulty: str
    years: str
    segment: str
    kind: str
    statement: str
    alternatives: tuple[str, ...]
    answer: str
    source: str
    source_year: str
    last_modified: str | None


def legacy_card_data(row):
    """Adapt the historical query shape at the legacy storage boundary."""
    return QuestionCardData(row[0], row[1], row[2], row[3], row[4], row[5],
                            row[6], tuple(row[7:12]), row[12], row[13], row[14], row[15])


def card_metadata(question_id, subject, difficulty, year_label, kind, source, source_year, last_modified):
    """Build the existing card fields without interpreting their text as markup."""
    from prometheus.domain.questions import format_last_modified

    return {
        'id': str(question_id),
        'years': year_label,
        'difficulty': difficulty,
        'kind': kind,
        'subject': (subject or '').replace(';', ', ').strip(', '),
        'source': (source or '').strip() or 'Não informada',
        'source_year': (source_year or '').strip() or 'Não informado',
        'modified': format_last_modified(last_modified) or 'Não informada',
    }


def actions_below_metadata(available_width, metadata_minimum, actions_width, spacing):
    """Choose a stacked header when both columns cannot remain readable."""
    return available_width < metadata_minimum + actions_width + spacing


def wrap_long_tokens(value, limit=24):
    """Permit visual wrapping of long unbroken user text without changing data."""
    import re
    return re.sub(r'\S{' + str(limit) + r'}(?=\S)', lambda match: match.group() + '\u200b', str(value or ''))
