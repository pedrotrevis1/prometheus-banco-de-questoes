"""Question data and validation independent of the UI."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RichContent:
    html: str
    has_text: bool

    @property
    def has_content(self):
        return self.has_text or '<img' in self.html


@dataclass(frozen=True)
class QuestionDraft:
    categories: tuple[str, ...]
    difficulty: str
    kind: str
    statement: RichContent
    years: tuple[str, ...]
    segment: str
    alternatives: tuple[RichContent, ...]
    answer: str
    essay_answer: RichContent
    source: str
    source_year: str


class QuestionValidationError(ValueError):
    def __init__(self, code, letter=None):
        self.code = code
        self.letter = letter
        super().__init__(code)


def validate_question(draft):
    if not draft.categories:
        raise QuestionValidationError('categories')
    if not draft.segment or not draft.years:
        raise QuestionValidationError('years')
    if not draft.statement.has_content:
        raise QuestionValidationError('statement')
    if draft.kind == 'Múltipla Escolha':
        if draft.answer not in ('A', 'B', 'C', 'D', 'E'):
            raise QuestionValidationError('answer')
        if len(draft.alternatives) != 5:
            raise QuestionValidationError('alternatives')
        for letter, value in zip('ABCDE', draft.alternatives):
            if not value.has_content:
                raise QuestionValidationError('alternative', letter)
    return draft


def question_values(draft):
    validate_question(draft)
    if draft.kind == 'Múltipla Escolha':
        alternatives = tuple(value.html.strip() for value in draft.alternatives)
        answer = draft.answer
    else:
        alternatives = ('',) * 5
        answer = draft.essay_answer.html.strip() if draft.essay_answer.has_content else ''
    return (';'.join(draft.categories), draft.difficulty, draft.kind, draft.statement.html,
            ';'.join(draft.years), draft.segment, *alternatives, answer,
            draft.source.strip(), draft.source_year.strip())


class QuestionSession:
    """Track a form snapshot and preserve unchanged stored rich content."""
    def __init__(self, mode, question_id, initial_form, original, original_record=None, missing_categories=()):
        self.mode = mode
        self.question_id = question_id
        self.initial_form = initial_form
        self.original = original
        self.original_record = original_record
        self.missing_categories = missing_categories

    def is_dirty(self, current):
        return self.mode == 'duplicate' or current != self.initial_form

    def prepare(self, current):
        from dataclasses import replace
        def preserve(value, shown, stored):
            return stored if value == shown else value
        return replace(current,
            statement=preserve(current.statement, self.initial_form.statement, self.original.statement),
            alternatives=tuple(preserve(value, shown, stored) for value, shown, stored in
                               zip(current.alternatives, self.initial_form.alternatives, self.original.alternatives)),
            essay_answer=preserve(current.essay_answer, self.initial_form.essay_answer, self.original.essay_answer))

    def unchanged_values(self, current):
        if self.original_record is None:
            return {}
        row = self.original_record
        fields = {}
        for attribute, column in (('years', 'ano_sugerido'), ('segment', 'segmento'),
                                  ('source', 'fonte_questao'), ('source_year', 'ano_origem')):
            if getattr(current, attribute) == getattr(self.initial_form, attribute):
                fields[column] = row[column]
        if current.categories == self.initial_form.categories and not self.missing_categories:
            fields['assunto'] = row['assunto']
        if (current.kind == self.initial_form.kind == 'Múltipla Escolha'
                and current.answer == self.initial_form.answer):
            fields['gabarito'] = row['gabarito']
        return fields


def split_available_categories(stored_names, available_names):
    available = set(available_names)
    names = [part.strip() for part in (stored_names or '').split(';') if part.strip()]
    return tuple(name for name in names if name in available), tuple(name for name in names if name not in available)


def stored_school_years(year_value, segment):
    import json
    from prometheus.domain.school_years import parse_question_year_values
    resolved = (segment or '').strip()
    if not resolved and (year_value or '').strip().startswith('{'):
        try:
            legacy = json.loads(year_value)
            if isinstance(legacy, dict):
                resolved = str(legacy.get('level', '')).strip()
        except (ValueError, TypeError):
            return resolved, tuple(parse_question_year_values(year_value, resolved))
    return resolved, tuple(parse_question_year_values(year_value, resolved))


def format_last_modified(value, display_timezone=None):
    from datetime import datetime
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(display_timezone).strftime('%d/%m/%Y %H:%M')
    except (TypeError, ValueError, OverflowError):
        return None
