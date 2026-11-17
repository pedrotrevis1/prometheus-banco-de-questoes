import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sqlite3
import pytest
from PySide6.QtWidgets import QApplication
from prometheus.app import ExamGeneratorApp, QuestionCard
from prometheus.storage.migrations import migrate_0_to_1


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: False)
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *a: None)
    w = ExamGeneratorApp()
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    migrate_0_to_1(conn)
    conn.executemany('INSERT INTO questoes (id, assunto, dificuldade, tipo, enunciado) VALUES (?, ?, ?, ?, ?)',
                     [(i, 'Bio', 'Fácil', 'Dissertativa', f'Questão {i}') for i in range(1, 124)])
    conn.commit(); w.conn = conn
    yield w
    w.close(); conn.close()


def card_ids(window):
    return [window.scroll_layout.itemAt(i).widget().q_id for i in range(window.scroll_layout.count())
            if isinstance(window.scroll_layout.itemAt(i).widget(), QuestionCard)]


def test_first_page_and_failed_query_preserve_content(window, monkeypatch):
    import prometheus.app as app_module
    window.load_questions()
    assert card_ids(window) == list(range(1, 51))
    assert '1–50' in window.lbl_result_range.text()
    assert window.btn_next_page.isEnabled()
    def fail(*args, **kwargs):
        raise RuntimeError('simulated failure')
    monkeypatch.setattr(app_module, 'page_questions', fail)
    window.load_questions()
    assert card_ids(window) == list(range(1, 51))
    assert '1–50' in window.lbl_result_range.text()


def test_navigation_uses_applied_filters_and_preserves_selections(window):
    window.load_questions()
    window.selected_ids.add(1)
    window.txt_search_question_text.setText('not applied')
    window.move_search_page(3)
    assert card_ids(window) == list(range(101, 124))
    window.selected_ids.add(101)
    window.move_search_page(1)
    assert card_ids(window)[0] == 1
    assert window.scroll_layout.itemAt(0).widget().checkbox.isChecked()
    assert window.selected_ids == {1, 101}
    window.show_filtered_questions()
    assert card_ids(window) == []
    assert window.selected_ids == {1, 101}


def test_selected_view_empty_stays_selected_until_user_leaves(window):
    window.load_questions()
    window.selected_ids.add(1)
    window.btn_browse_selected_questions.setEnabled(True)
    window.btn_browse_selected_questions.setChecked(True)
    assert card_ids(window) == [1]
    window.toggle_question_selection(1, 0)
    assert window.btn_browse_selected_questions.isChecked()
    assert card_ids(window) == []
    window.btn_browse_selected_questions.setChecked(False)
    assert card_ids(window) == list(range(1, 51))


def test_selected_view_clamps_last_page_and_restores_normal_search(window):
    window.load_questions()
    window.selected_ids.update(range(1, 102))
    window.btn_browse_selected_questions.setEnabled(True)
    window.btn_browse_selected_questions.setChecked(True)
    window.move_search_page(3)
    assert card_ids(window) == [101]
    window.toggle_question_selection(101, 0)
    assert card_ids(window) == list(range(51, 101))
    assert window.search_view.page == 2
    window.btn_browse_selected_questions.setChecked(False)
    assert card_ids(window) == list(range(1, 51))
    assert len(window.selected_ids) == 100


def test_apply_failure_preserves_current_filters_and_page(window, monkeypatch):
    import prometheus.app as app_module
    window.load_questions()
    window.move_search_page(2)
    window.txt_search_question_text.setText('different')
    monkeypatch.setattr(app_module, 'page_questions', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('failed')))
    window.show_filtered_questions()
    assert window.search_view.applied.text == '' and window.search_view.page == 2
    assert card_ids(window) == list(range(51, 101))


def test_repeated_page_turns_dispose_old_cards(window, qtbot=None):
    from PySide6.QtCore import QCoreApplication, QEvent
    window.load_questions()
    for page in (2, 3, 1, 2, 1):
        window.move_search_page(page)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        QApplication.processEvents()
        assert len(window.scroll_content.findChildren(QuestionCard)) <= 50


def test_exam_includes_selections_from_multiple_pages(window, tmp_path, monkeypatch):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    window.load_questions()
    window.scroll_layout.itemAt(0).widget().checkbox.setChecked(True)
    window.move_search_page(3)
    window.scroll_layout.itemAt(0).widget().checkbox.setChecked(True)
    assert window.selected_ids == {1, 101}
    destination = tmp_path / 'exam.docx'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(destination), ''))
    window.generate_word_doc()
    text = '\n'.join(paragraph.text for paragraph in Document(destination).paragraphs)
    assert 'Questão 1' in text and 'Questão 101' in text
