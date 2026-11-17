from dataclasses import replace
import pytest
from prometheus.domain.questions import RichContent, QuestionDraft, QuestionValidationError, question_values


@pytest.fixture
def draft():
    content = RichContent('<p>text</p>', True)
    return QuestionDraft(('Bio',), 'Fácil', 'Múltipla Escolha', content, ('1ª Série',),
                         'Ensino Médio', (content,) * 5, 'C', RichContent('', False), 'ENEM', '2024')


@pytest.mark.parametrize(('change', 'code'), [
    ({'categories': ()}, 'categories'), ({'years': ()}, 'years'),
    ({'statement': RichContent('', False)}, 'statement'), ({'answer': ''}, 'answer'),
    ({'alternatives': (RichContent('', False),) * 5}, 'alternative'),
])
def test_validation(draft, change, code):
    with pytest.raises(QuestionValidationError) as error:
        question_values(replace(draft, **change))
    assert error.value.code == code


def test_rich_content_and_essay_serialization(draft):
    image = RichContent('<p><img src="data:image/png;base64,abc"></p>', False)
    values = question_values(replace(draft, statement=image, kind='Dissertativa', essay_answer=image))
    assert values[3] == image.html and values[6:11] == ('',) * 5 and values[11] == image.html


def test_session_detects_edits_and_preserves_unchanged_stored_html(draft):
    from prometheus.domain.questions import QuestionSession
    rendered = replace(draft, statement=RichContent('<p>Qt normalized</p>', True))
    session = QuestionSession('edit', 7, rendered, draft)
    assert not session.is_dirty(rendered)
    assert session.prepare(rendered).statement == draft.statement
    changed = replace(rendered, source='Other')
    assert session.is_dirty(changed)
    assert session.prepare(changed).statement == draft.statement
    new_statement = RichContent('<p>New</p>', True)
    assert session.prepare(replace(rendered, statement=new_statement)).statement == new_statement


def test_missing_categories_are_identified():
    from prometheus.domain.questions import split_available_categories
    assert split_available_categories(' Bio ; Removed ; Física ', {'Bio', 'Física'}) == (('Bio', 'Física'), ('Removed',))


def test_last_modified_format_and_unknown_values():
    from datetime import timezone
    from prometheus.domain.questions import format_last_modified
    assert format_last_modified('2026-11-17T13:45:30+00:00', timezone.utc) == '17/11/2026 13:45'
    assert format_last_modified(None) is None
    assert format_last_modified('invalid') is None
    assert format_last_modified('2026-11-17T13:45:30') is None


def test_unmodified_duplicate_is_unsaved_work(draft):
    from prometheus.domain.questions import QuestionSession
    session = QuestionSession('duplicate', 1, draft, draft)
    assert session.is_dirty(draft)
