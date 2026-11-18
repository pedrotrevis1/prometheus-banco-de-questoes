import json
import os

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QInputDialog

from prometheus.app import ExamGeneratorApp
from prometheus.domain.normalized_questions import NormalizedQuestion
from prometheus.storage.categories import create_category
from prometheus.storage.database import open_bank
from prometheus.storage.normalized_questions import save_question

os.environ['QT_QPA_PLATFORM'] = 'offscreen'


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / 'bank.db'
    conn = open_bank(path, create=True)
    first = create_category(conn, 'A')
    second = create_category(conn, 'B')
    parent = create_category(conn, 'Parent')
    question = save_question(conn, NormalizedQuestion((first, second), 'essay', 'easy',
        '<p>Original</p>', (('medio', 'medio_1'),)))
    conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Teste', 'disciplines': {'Teste': str(path)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *args: None)
    widget = ExamGeneratorApp()
    widget.open_question_for_edit(question)
    widget.txt_prompt.setPlainText('Unsaved content')
    yield widget, first, second, parent, question
    widget.close()


def item_by_id(tree, target):
    def find(item):
        if item.data(0, Qt.UserRole) == target:
            return item
        for index in range(item.childCount()):
            result = find(item.child(index))
            if result is not None:
                return result
    for index in range(tree.topLevelItemCount()):
        result = find(tree.topLevelItem(index))
        if result is not None:
            return result


@pytest.mark.parametrize('operation', ['rename', 'move', 'create'])
@pytest.mark.parametrize('duplicate', [False, True])
def test_category_reorganization_keeps_form_and_search_selection(window, monkeypatch, operation, duplicate):
    widget, first, second, parent, question = window
    if duplicate:
        widget.open_question_for_edit(question, duplicate=True)
        widget.txt_prompt.setPlainText('Unsaved content')
    item_by_id(widget.tree_search_subjects, second).setCheckState(0, Qt.Checked)
    widget.show_filtered_questions()
    widget.tree_register_subjects.setCurrentItem(item_by_id(widget.tree_register_subjects, first))
    if operation == 'rename':
        monkeypatch.setattr(widget, 'get_text_prompt', lambda *args: 'Renamed')
        widget.rename_selected_category()
    elif operation == 'move':
        monkeypatch.setattr(QInputDialog, 'getItem', lambda *args: (f'Parent (ID {parent})', True))
        widget.move_selected_category()
    else:
        class Dialog:
            def __init__(self, parent, conn): self.conn = conn
            def setStyleSheet(self, value): pass
            def exec(self):
                create_category(self.conn, 'New')
                return QDialog.Accepted
        monkeypatch.setattr('prometheus.app.AddSubjectDialog', Dialog)
        widget.open_add_subject_dialog()
    assert set(widget.get_checked_subject_ids(widget.tree_register_subjects)) == {first, second}
    assert second in widget.get_checked_subject_ids(widget.tree_search_subjects)
    assert widget.search_view.applied.category_ids == (second,)
    assert widget.question_session.mode == ('duplicate' if duplicate else 'edit')
    assert widget.txt_prompt.toPlainText() == 'Unsaved content'
    widget.save_question()
    saved_id = widget.conn.execute('SELECT MAX(id) FROM normalized_questions').fetchone()[0] if duplicate else question
    assert set(row[0] for row in widget.conn.execute('SELECT category_id FROM question_categories WHERE question_id=?', (saved_id,))) == {first, second}
    assert 'Unsaved content' in widget.conn.execute('SELECT statement_text FROM normalized_questions WHERE id=?', (saved_id,)).fetchone()[0]


def test_deleting_category_preserves_only_surviving_checks(window):
    widget, first, second, _, _ = window
    item_by_id(widget.tree_search_subjects, first).setCheckState(0, Qt.Checked)
    item_by_id(widget.tree_search_subjects, second).setCheckState(0, Qt.Checked)
    widget.show_filtered_questions()
    widget.tree_register_subjects.setCurrentItem(item_by_id(widget.tree_register_subjects, first))
    widget.delete_selected_subject(widget.tree_register_subjects)
    assert widget.get_checked_subject_ids(widget.tree_register_subjects) == [second]
    assert widget.get_checked_subject_ids(widget.tree_search_subjects) == [second]
    assert widget.search_view.applied.category_ids == (second,)
    assert widget.txt_prompt.toPlainText() == 'Unsaved content'
