import pytest
from dataclasses import replace
from prometheus.domain.exam_questions import ExamQuestion
from prometheus.domain.exam_arrangements import capture_arrangements, restore_arrangements


def test_restores_order_using_current_content_and_answer():
    original = ExamQuestion(1, 'multiple_choice', 'old', ('A', 'B', 'C'), 'A')
    generated = replace(original, alternatives=('C', 'A', 'B'), answer='B')
    arrangements = capture_arrangements([original], [[generated]])
    edited = replace(original, statement='new', alternatives=('X', 'Y', 'Z'), answer='C')
    restored = restore_arrangements([edited], arrangements)[0][0]
    assert restored.statement == 'new'
    assert restored.alternatives == ('Z', 'X', 'Y')
    assert restored.answer == 'A'


def test_rejects_changed_alternative_count():
    question = ExamQuestion(1, 'multiple_choice', 'old', ('A', 'B'), 'A')
    arrangements = capture_arrangements([question], [[question]])
    with pytest.raises(ValueError, match='questão 1'):
        restore_arrangements([replace(question, alternatives=('A', 'B', 'C'))], arrangements)


def test_duplicate_alternatives_preserve_correct_position():
    question = ExamQuestion(1, 'multiple_choice', '', ('A', 'A', 'B'), 'B')
    generated = replace(question, alternatives=('A', 'B', 'A'), answer='C')
    assert restore_arrangements([question], capture_arrangements([question], [[generated]])) == [[generated]]
