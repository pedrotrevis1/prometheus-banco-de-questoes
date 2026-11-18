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
