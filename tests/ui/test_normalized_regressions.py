import json
import os
from dataclasses import replace

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import pytest
from PySide6.QtWidgets import QApplication

from prometheus.app import ExamGeneratorApp, QuestionCard
from prometheus.domain.normalized_questions import NormalizedQuestion
from prometheus.storage.categories import create_category
from prometheus.storage.database import open_bank
from prometheus.storage.normalized_questions import save_question


@pytest.fixture(params=[4, 5], ids=['schema4', 'schema5'])
def window(tmp_path, monkeypatch, request):
    app = QApplication.instance() or QApplication([])
    from prometheus.storage import database
    monkeypatch.setattr(database, 'SCHEMA_VERSION', request.param)
    monkeypatch.setattr(database, 'MIGRATIONS', database.MIGRATIONS[:request.param])
    path = tmp_path / 'bank.db'
    conn = open_bank(path, create=True)
    category = create_category(conn, 'Bio')
    draft = NormalizedQuestion((category,), 'essay', 'easy', 'Question', (('medio', 'medio_1'),))
    for index in range(1, 124):
        save_question(conn, replace(draft, statement=f'Question {index}', source_year='2022' if index <= 60 else '2023'))
    conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Test', 'disciplines': {'Test': str(path)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *args: None)
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: False)
    widget = ExamGeneratorApp()
    assert widget.conn.execute('PRAGMA user_version').fetchone()[0] == request.param
    yield widget
    widget.close()


def card_ids(widget):
    return [widget.scroll_layout.itemAt(index).widget().q_id for index in range(widget.scroll_layout.count())
            if isinstance(widget.scroll_layout.itemAt(index).widget(), QuestionCard)]


def test_schema4_pagination_year_range_global_selection_and_selected_only(window):
    assert card_ids(window) == list(range(1, 51))
    window.selected_ids.update({1, 123})
    window.txt_search_source_year_from.setText('2022')
    window.txt_search_source_year_to.setText('2022')
    window.show_filtered_questions()
    assert 'de 60' in window.lbl_result_range.text()
    window.move_search_page(2)
    assert card_ids(window) == list(range(51, 61))
    assert window.selected_ids == {1, 123}
    window.btn_browse_selected_questions.setEnabled(True)
    window.btn_browse_selected_questions.setChecked(True)
    assert card_ids(window) == [1, 123]
    window.btn_browse_selected_questions.setChecked(False)
    assert card_ids(window) == list(range(1, 51))


def test_schema4_query_failure_preserves_page_and_applied_filters(window, monkeypatch):
    import prometheus.app as app
    window.move_search_page(2)
    before = card_ids(window)
    monkeypatch.setattr(app, 'page_normalized_questions', lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('failed')))
    window.txt_search_question_text.setText('new filter')
    window.show_filtered_questions()
    assert card_ids(window) == before
    assert window.search_view.page == 2 and not window.search_view.applied.text


def test_invalid_source_year_preserves_selected_view(window, monkeypatch):
    messages = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: messages.append(text))
    window.selected_ids.update(range(1, 102))
    window.btn_browse_selected_questions.setEnabled(True)
    window.btn_browse_selected_questions.setChecked(True)
    window.move_search_page(2)
    before = card_ids(window)
    window.txt_search_source_year_from.setText('2024')
    window.txt_search_source_year_to.setText('2022')
    window.show_filtered_questions()
    assert messages[-1] == "O ano em 'Desde' deve ser menor ou igual ao ano em 'até'."
    assert window.search_view.selected_only and window.search_view.page == 2
    assert card_ids(window) == before and len(window.selected_ids) == 101


def test_schema4_delete_includes_selected_questions_hidden_by_filter(window, monkeypatch):
    window.selected_ids.update({1, 123})
    window.txt_search_source_year_from.setText('2022')
    window.txt_search_source_year_to.setText('2022')
    window.show_filtered_questions()
    assert 123 not in card_ids(window)
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    window.delete_selected_questions()
    assert window.conn.execute('SELECT id FROM normalized_questions WHERE id IN (1, 123)').fetchall() == []
    assert window.conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone()[0] == 121


def test_schema4_edit_duplicate_and_cancel_bank_switch_preserve_form(window):
    original = window.conn
    window.open_question_for_edit(1)
    window.txt_prompt.setPlainText('Unsaved')
    window.config_data['disciplines']['Other'] = '/does/not/exist.db'
    window.on_discipline_changed('Other')
    assert window.conn is original and window.question_session.mode == 'edit'
    assert window.current_discipline == 'Test'
    assert window.txt_prompt.toPlainText() == 'Unsaved'
    window.question_session = None
    window.form_snapshot = window.question_draft_from_form()
    window.open_question_for_edit(1, duplicate=True)
    assert window.question_session.mode == 'duplicate'
    window.save_question()
    assert window.conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone()[0] == 124


@pytest.mark.parametrize('count', [2, 3, 4, 5])
def test_schema4_exam_export_preserves_correct_answer(window, tmp_path, monkeypatch, count):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    draft = NormalizedQuestion((1,), 'multiple_choice', 'easy', 'Unique question',
        (('medio', 'medio_1'),), tuple(f'Option {letter}' for letter in 'ABCDE'[:count]), count)
    question_id = save_question(window.conn, draft)
    window.selected_ids.add(question_id)
    destination = tmp_path / f'exam-{count}.docx'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(destination), ''))
    window.generate_word_doc()
    text = '\n'.join(paragraph.text for paragraph in Document(destination).paragraphs)
    for letter in 'ABCDE'[:count]:
        assert f'{letter}) Option {letter}' in text
    if count < 5:
        assert f"{'ABCDE'[count]})" not in text
    assert f'1) {"ABCDE"[count - 1]}' in text


@pytest.mark.parametrize('count', [2, 3, 4, 5])
def test_shuffled_exam_versions_keep_answer_with_content(window, count):
    import random
    from prometheus.domain.normalized_versions import generate_versions
    from prometheus.export.documents import build_exam_documents
    from prometheus.storage.normalized_exams import fetch_ordered_questions
    options = tuple(f'Option {letter}' for letter in 'ABCDE'[:count])
    question = save_question(window.conn, NormalizedQuestion((1,), 'multiple_choice', 'easy',
        'Prompt', (('medio', 'medio_1'),), options, count))
    versions = generate_versions(fetch_ordered_questions(window.conn, [question]), 2, False, True,
                                 rng=random.Random(42))
    for version in versions:
        record = version[0]
        assert record.alternatives['ABCDE'.index(record.answer)] == options[-1]
        exam, key = build_exam_documents(version, answer_placement='separate')
        exam_text = '\n'.join(p.text for p in exam.paragraphs)
        key_text = '\n'.join(p.text for p in key.paragraphs)
        assert f'{record.answer}) {options[-1]}' in exam_text
        assert f'1) {record.answer}' in key_text
