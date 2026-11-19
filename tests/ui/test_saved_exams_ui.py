import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sqlite3
import pytest
from PySide6.QtWidgets import QApplication
from prometheus.app import ExamGeneratorApp
from prometheus.storage.migrations import MIGRATIONS
from prometheus.storage import saved_exams

confirm_save_exam = ExamGeneratorApp.confirm_save_exam


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *args: None)
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: False)
    monkeypatch.setattr(ExamGeneratorApp, 'confirm_save_exam', lambda self: True)
    w = ExamGeneratorApp()
    conn = sqlite3.connect(':memory:')
    conn.execute('BEGIN')
    for migration in MIGRATIONS:
        migration(conn)
    conn.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (1,'essay','easy','A','A','A','a','a',0)")
    conn.commit()
    w.conn = conn
    w.refresh_saved_exam_controls()
    yield w
    w.conn = None
    w.close()
    conn.close()


def test_save_and_open_restores_selection_class_and_options(window, monkeypatch):
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    class_id = saved_exams.add_class(window.conn, '2ª B')
    window.refresh_saved_exam_controls()
    window.cb_exam_class.setCurrentIndex(window.cb_exam_class.findData(class_id))
    window.selected_ids.add(1)
    window.chk_include_answers.setChecked(False)
    assert window.save_current_exam()
    exam_id = window.open_exam_id
    window.selected_ids.clear()
    window.chk_include_answers.setChecked(True)
    window.open_saved_exam()
    assert window.open_exam_id == exam_id
    assert window.selected_ids == {1}
    assert window.cb_exam_class.currentData() == class_id
    assert not window.chk_include_answers.isChecked()
    assert window.exam_snapshot == window.exam_draft()


def test_generation_records_each_usage_and_reuses_arrangement(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'exam.docx'), ''))
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, message, *args: alerts.append((title, message)))
    window.selected_ids.add(1)
    window.generate_word_doc()
    assert (tmp_path / 'exam.docx').is_file()
    exam_id = window.open_exam_id
    arrangements = saved_exams.versions(window.conn, exam_id)
    assert len(arrangements) == 1
    window.generate_word_doc()
    assert saved_exams.versions(window.conn, exam_id) == arrangements
    assert len(saved_exams.question_usages(window.conn, 1)) == 2
    assert not [item for item in alerts if item[0].startswith('Erro')]


def test_usage_filter_card_and_delete_warning(window, monkeypatch):
    exam_id = saved_exams.save_exam(window.conn, 'História', None, {}, [1])
    saved_exams.record_generation(window.conn, exam_id, [[]], [1], used_at='2026-05-10')
    window.show_filtered_questions()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.usage_control.text() == 'Usos: 1'
    card.usage_popup.activate()
    from PySide6.QtWidgets import QLabel
    assert card.usage_popup.findChild(QLabel, 'UsageEntry').text() == 'História — Sem turma — 10/05/2026'
    card.usage_popup.close_history()
    window.cb_usage_filter.setCurrentIndex(window.cb_usage_filter.findData('never'))
    window.show_filtered_questions()
    assert 'Nenhuma' in window.lbl_result_range.text()
    window.selected_ids.add(1)
    confirmations = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: confirmations.append(text) or False)
    window.delete_selected_questions()
    assert 'História' in confirmations[0]
    assert window.conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone() == (1,)


def test_incompatible_question_edit_blocks_regeneration(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'exam.docx'), ''))
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    window.selected_ids.add(1)
    window.generate_word_doc()
    window.conn.execute("UPDATE normalized_questions SET kind='multiple_choice', updated_at='b' WHERE id=1")
    window.conn.executemany('INSERT INTO question_alternatives VALUES (?,?,?,?)', [(1, 1, 'A', 1), (1, 2, 'B', 0)])
    window.conn.commit()
    window.generate_word_doc()
    assert len(saved_exams.question_usages(window.conn, 1)) == 1
    assert any('ordem salva' in text for _, text in alerts)


def test_unsaved_exam_prompt_allows_save_discard_or_cancel(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window.exam_snapshot = window.exam_draft()
    window.selected_ids.add(1)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Cancel)
    assert not confirm_save_exam(window)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Discard)
    assert confirm_save_exam(window)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Save)
    monkeypatch.setattr(window, 'save_current_exam', lambda: False)
    assert not confirm_save_exam(window)
    monkeypatch.setattr(window, 'save_current_exam', lambda: True)
    assert confirm_save_exam(window)


@pytest.mark.parametrize('action', ['rename', 'duplicate', 'delete'])
@pytest.mark.parametrize('has_class', [True, False])
def test_exam_management_keeps_open_draft_class_and_usage(window, monkeypatch, tmp_path, action, has_class):
    from PySide6.QtWidgets import QFileDialog
    first = saved_exams.add_class(window.conn, 'Turma A')
    saved_exams.add_class(window.conn, 'Turma Z')
    window.refresh_saved_exam_controls()
    selected_class = first if has_class else None
    window.cb_exam_class.setCurrentIndex(window.cb_exam_class.findData(selected_class))
    window.selected_ids.add(1)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova aberta')
    assert window.save_current_exam()
    open_id = window.open_exam_id
    other = saved_exams.save_exam(window.conn, 'Outra prova', None, window.exam_draft()[2], [1])
    window.refresh_saved_exam_controls(other)
    window.chk_include_answers.setChecked(False)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova alterada')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'out.docx'), ''))
    getattr(window, {'rename': 'rename_saved_exam', 'duplicate': 'duplicate_saved_exam', 'delete': 'delete_saved_exam'}[action])()
    assert window.open_exam_id == open_id
    assert window.cb_exam_class.currentData() == selected_class
    assert not window.chk_include_answers.isChecked()
    window.generate_word_doc()
    assert saved_exams.load_exam(window.conn, open_id)['class_id'] == selected_class
    assert saved_exams.question_usages(window.conn, 1)[0][1] == ('Turma A' if has_class else '')


def test_deleting_selected_class_keeps_history_and_selects_no_class(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    first = saved_exams.add_class(window.conn, 'Turma A')
    saved_exams.add_class(window.conn, 'Turma Z')
    window.refresh_saved_exam_controls()
    window.cb_exam_class.setCurrentIndex(window.cb_exam_class.findData(first))
    window.selected_ids.add(1)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'out.docx'), ''))
    window.generate_word_doc()
    window.delete_exam_class()
    assert window.cb_exam_class.currentData() is None
    assert saved_exams.load_exam(window.conn, window.open_exam_id)['class_id'] is None
    window.generate_word_doc()
    assert saved_exams.load_exam(window.conn, window.open_exam_id)['class_id'] is None
    assert {row[1] for row in saved_exams.question_usages(window.conn, 1)} == {'Turma A', ''}


def prepare_shuffled_exam(window, monkeypatch, tmp_path):
    import random
    import prometheus.app as app_module
    from PySide6.QtWidgets import QFileDialog
    from prometheus.domain.normalized_versions import generate_versions
    window.conn.execute("UPDATE normalized_questions SET kind='multiple_choice' WHERE id=1")
    window.conn.executemany('INSERT INTO question_alternatives VALUES (?,?,?,?)',
                            [(1, i, f'Alternativa {i}', int(i == 2)) for i in range(1, 6)])
    window.conn.commit()
    window.selected_ids.add(1)
    window.chk_multiple_versions.setChecked(True)
    window.spin_version_count.setValue(2)
    window.chk_shuffle_alternatives.setChecked(True)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'exam.docx'), ''))
    monkeypatch.setattr(app_module, 'generate_normalized_versions',
                        lambda *args: generate_versions(*args, rng=random.Random(1)))
    window.generate_word_doc()
    exam_id = window.open_exam_id
    arrangements = saved_exams.versions(window.conn, exam_id)
    assert len(arrangements) == 2
    assert len(saved_exams.question_usages(window.conn, 1)) == 1
    return exam_id, arrangements


@pytest.mark.parametrize('presentation', ['separate', 'none'])
def test_presentation_changes_preserve_orders_and_use_current_answers(window, monkeypatch, tmp_path, presentation):
    import prometheus.app as app_module
    exam_id, old = prepare_shuffled_exam(window, monkeypatch, tmp_path)
    window.conn.execute("UPDATE normalized_questions SET statement='Novo enunciado', updated_at='changed' WHERE id=1")
    window.conn.execute("UPDATE question_alternatives SET content='Conteúdo atualizado', is_correct=(position=4) WHERE question_id=1 AND position=4")
    window.conn.execute('UPDATE question_alternatives SET is_correct=0 WHERE question_id=1 AND position=2')
    window.conn.commit()
    if presentation == 'separate':
        window.chk_separate_answers.setChecked(True)
    else:
        window.chk_include_answers.setChecked(False)
    monkeypatch.setattr(app_module, 'generate_normalized_versions', lambda *args: pytest.fail('Unexpected reshuffle'))
    from prometheus.export.documents import build_exam_documents
    rendered = []
    def capture(questions, **kwargs):
        rendered.append((questions, kwargs['answer_placement']))
        return build_exam_documents(questions, **kwargs)
    monkeypatch.setattr(app_module, 'build_exam_documents', capture)
    window.generate_word_doc()
    assert saved_exams.versions(window.conn, exam_id) == old
    assert len(saved_exams.question_usages(window.conn, 1)) == 2
    assert len(rendered) == 2
    for index, (questions, placement) in enumerate(rendered):
        question = questions[0]
        assert question.statement == 'Novo enunciado'
        assert question.alternatives.index('Conteúdo atualizado') == old[index][0]['alternatives'].index(3)
        assert question.answer == 'ABCDE'[question.alternatives.index('Conteúdo atualizado')]
        assert placement == ('separate' if presentation == 'separate' else 'none')


@pytest.mark.parametrize('edit', ['count', 'type'])
@pytest.mark.parametrize('presentation', ['separate', 'none'])
def test_presentation_change_does_not_bypass_incompatible_question(window, monkeypatch, tmp_path, edit, presentation):
    exam_id, old = prepare_shuffled_exam(window, monkeypatch, tmp_path)
    if edit == 'count':
        window.conn.execute('DELETE FROM question_alternatives WHERE question_id=1 AND position=5')
    else:
        window.conn.execute("UPDATE normalized_questions SET kind='essay' WHERE id=1")
        window.conn.execute('DELETE FROM question_alternatives WHERE question_id=1')
    window.conn.commit()
    if presentation == 'separate':
        window.chk_separate_answers.setChecked(True)
    else:
        window.chk_include_answers.setChecked(False)
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    window.generate_word_doc()
    assert any('ordem salva' in text for _, text in alerts)
    assert saved_exams.versions(window.conn, exam_id) == old
    assert len(saved_exams.question_usages(window.conn, 1)) == 1


@pytest.mark.parametrize('change', ['presentation', 'configuration'])
@pytest.mark.parametrize('failure', ['cancel', 'fail'])
def test_unsuccessful_export_retains_previous_arrangements(window, monkeypatch, tmp_path, change, failure):
    import prometheus.app as app_module
    from PySide6.QtWidgets import QFileDialog
    exam_id, old = prepare_shuffled_exam(window, monkeypatch, tmp_path)
    if change == 'presentation':
        window.chk_separate_answers.setChecked(True)
    else:
        window.chk_shuffle_questions.setChecked(True)
    if failure == 'cancel':
        monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: ('', ''))
    else:
        def fail(*args, **kwargs):
            raise OSError('synthetic failure')
        monkeypatch.setattr(app_module, 'publish_documents', fail)
    window.generate_word_doc()
    assert saved_exams.versions(window.conn, exam_id) == old
    assert len(saved_exams.question_usages(window.conn, 1)) == 1
    if change == 'configuration':
        assert saved_exams.matching_versions(window.conn, exam_id) == []
        window.chk_shuffle_questions.setChecked(False)
        assert window.save_current_exam()
    assert saved_exams.matching_versions(window.conn, exam_id) == old


def test_successful_intentional_version_change_replaces_arrangements(window, monkeypatch, tmp_path):
    exam_id, old = prepare_shuffled_exam(window, monkeypatch, tmp_path)
    window.spin_version_count.setValue(3)
    window.generate_word_doc()
    new = saved_exams.versions(window.conn, exam_id)
    assert len(new) == 3
    assert new != old
    assert saved_exams.matching_versions(window.conn, exam_id) == new
    assert len(saved_exams.question_usages(window.conn, 1)) == 2


def test_page_usage_counts_are_bulk_and_details_deferred(window, monkeypatch):
    exam_id = saved_exams.save_exam(window.conn, 'Prova', None, {}, [1])
    saved_exams.record_generation(window.conn, exam_id, [[]], [1], used_at='2026-01-01')
    calls = []
    original_counts = saved_exams.question_usage_counts
    original_details = saved_exams.question_usages
    monkeypatch.setattr(saved_exams, 'question_usage_counts', lambda conn, ids: (calls.append(('counts', tuple(ids))), original_counts(conn, ids))[1])
    monkeypatch.setattr(saved_exams, 'question_usages', lambda conn, qid: (calls.append(('details', qid)), original_details(conn, qid))[1])
    window.show_filtered_questions()
    assert calls == [('counts', (1,))]
    card = window.scroll_layout.itemAt(0).widget()
    assert card.usage_count == 1
    assert card.history_request() == [('Prova', '', '2026-01-01')]
    assert calls[-1] == ('details', 1)


def test_compact_card_has_labeled_metadata_and_stacked_actions(window):
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
    window.show_filtered_questions()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.findChild(QLabel, 'CardIdentifier').text() == 'Questão #1'
    assert card.checkbox.parentWidget() is card.btn_edit.parentWidget()
    assert card.action_layout.indexOf(card.checkbox) < card.action_layout.indexOf(card.btn_edit) < card.action_layout.indexOf(card.btn_duplicate)
    assert card.findChild(QLabel, 'CardSubject').textFormat() == Qt.RichText  # rich labels, escaped data


def test_usage_popup_loads_on_request_retries_and_is_bounded(window, monkeypatch):
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    exam_id = saved_exams.save_exam(window.conn, 'Prova <especial>', None, {}, [1])
    saved_exams.record_generation(window.conn, exam_id, [[]], [1], used_at='2026-05-10')
    attempts = []
    original = saved_exams.question_usages
    def read(conn, qid):
        attempts.append(qid)
        if len(attempts) == 1:
            raise RuntimeError('synthetic failure')
        return original(conn, qid)
    monkeypatch.setattr(saved_exams, 'question_usages', read)
    window.show_filtered_questions()
    window.show()
    QApplication.processEvents()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.usage_control.text() == 'Usos: 1'
    assert attempts == []
    card.usage_popup.activate()
    assert 'Não foi possível carregar' in card.usage_popup.findChild(QLabel, 'UsageEntry').text()
    card.usage_popup.close_history()
    card.usage_popup.activate()
    assert card.usage_popup.findChild(QLabel, 'UsageEntry').text() == 'Prova <especial> — Sem turma — 10/05/2026'
    screen = QApplication.screenAt(card.usage_popup.geometry().center()) or QApplication.primaryScreen()
    assert screen.availableGeometry().contains(card.usage_popup.geometry())
    QTest.keyClick(card.usage_popup, Qt.Key_Escape)
    assert not card.usage_popup.isVisible()
    QTest.keyClick(card.usage_control, Qt.Key_Return)
    assert card.usage_popup.isVisible() and card.usage_popup.activated
    card.usage_popup.close_history()
    assert attempts == [1, 1, 1]


def test_zero_and_unavailable_popup_do_not_read(window, monkeypatch):
    from PySide6.QtWidgets import QLabel
    from prometheus.app import QuestionCard
    window.show_filtered_questions()
    card = window.scroll_layout.itemAt(0).widget()
    card.history_request = lambda: (_ for _ in ()).throw(AssertionError('unexpected read'))
    card.usage_popup.request = card.history_request
    card.usage_popup.activate()
    assert card.usage_popup.findChild(QLabel, 'UsageEntry').text() == 'Nenhum uso registrado.'
    card.usage_popup.close_history()
    legacy = QuestionCard(2, '', '', '', '', '', False, lambda *args: None)
    legacy.usage_popup.activate()
    assert legacy.usage_control.text() == 'Usos: não disponível'
    assert 'não disponível' in legacy.usage_popup.findChild(QLabel, 'UsageEntry').text()
    legacy.usage_popup.close_history()
    legacy.deleteLater()


def test_long_usage_popup_scroll_keyboard_and_disposal(window):
    from PySide6.QtCore import QCoreApplication, QEvent, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QLabel
    exam_id = saved_exams.save_exam(window.conn, 'Prova extensa ' + 'x' * 150, None, {}, [1])
    for i in range(100):
        saved_exams.record_generation(window.conn, exam_id, [[]], [1], used_at=f'2026-01-{i % 28 + 1:02d}')
    window.show_filtered_questions()
    window.show()
    for _ in range(4): QApplication.processEvents()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.usage_control.text() == 'Usos: 100'
    card.usage_control.setFocus()
    QTest.keyClick(card.usage_control, Qt.Key_Space)
    for _ in range(4): QApplication.processEvents()
    popup = card.usage_popup
    assert popup.isVisible() and popup.activated
    assert len(popup.findChildren(QLabel, 'UsageEntry')) == 100
    bar = popup.scroll.verticalScrollBar()
    assert bar.maximum() > 0
    QTest.keyClick(popup, Qt.Key_End)
    assert bar.value() == bar.maximum()
    QTest.keyClick(popup, Qt.Key_Home)
    assert bar.value() == 0
    window.show_filtered_questions()
    assert not popup.isVisible()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    QApplication.processEvents()


def test_usage_hover_and_outside_click(window):
    from PySide6.QtCore import QEvent
    window.show_filtered_questions()
    window.show()
    QApplication.processEvents()
    card = window.scroll_layout.itemAt(0).widget()
    QApplication.sendEvent(card.usage_control, QEvent(QEvent.Enter))
    assert card.usage_popup.isVisible() and not card.usage_popup.activated
    card.usage_popup.activate()
    assert card.usage_popup.activated
    from PySide6.QtTest import QTest
    from PySide6.QtCore import Qt
    QTest.mouseClick(window.lbl_result_range, Qt.LeftButton)
    assert not card.usage_popup.isVisible()


def test_aggregate_error_keeps_previous_cards(window, monkeypatch):
    window.show_filtered_questions()
    old = window.scroll_layout.itemAt(0).widget()
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda *args: alerts.append(args))
    def fail(*args):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr(saved_exams, 'question_usage_counts', fail)
    assert not window.load_questions()
    assert window.scroll_layout.itemAt(0).widget() is old
    assert alerts and 'synthetic failure' in alerts[-1][1]


def test_switching_bank_disposes_open_popup(window):
    exam = saved_exams.save_exam(window.conn, 'Primeiro banco', None, {}, [1])
    saved_exams.record_generation(window.conn, exam, [[]], [1])
    window.show_filtered_questions()
    card = window.scroll_layout.itemAt(0).widget()
    card.usage_popup.activate()
    assert card.usage_popup.isVisible()
    previous = window.conn
    other = sqlite3.connect(':memory:')
    other.execute('BEGIN')
    for migration in MIGRATIONS:
        migration(other)
    window.conn = other
    try:
        assert window.load_questions()
        assert not card.usage_popup.isVisible()
        assert window.scroll_layout.count() == 0
    finally:
        window.conn = previous
        other.close()


def test_usage_count_refreshes_after_generation_and_deletion(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'exam.docx'), ''))
    window.selected_ids.add(1)
    window.show_filtered_questions()
    assert window.scroll_layout.itemAt(0).widget().usage_control.text() == 'Usos: 0'
    window.generate_word_doc()
    assert window.scroll_layout.itemAt(0).widget().usage_control.text() == 'Usos: 1'
    window.delete_saved_exam()
    assert window.scroll_layout.itemAt(0).widget().usage_control.text() == 'Usos: 0'


def test_card_layout_header_count_and_literal_values(qt_app=None):
    from PySide6.QtWidgets import QApplication, QLabel, QBoxLayout
    from PySide6.QtGui import QTextDocument
    from prometheus.app import QuestionCard
    app = QApplication.instance() or QApplication([])
    heights = []
    for count in (2, 1000):
        card = QuestionCard(1, 'A < B & "C"', 'Médio', 'Médio', 'Dissertativa', '<p>Curto</p>', False,
                            lambda *args: None, question_source='X < Y & Z', usage_count=count)
        card.resize(640, 300)
        card.show()
        for _ in range(5): app.processEvents()
        heights.append(card.header_layout.geometry().height())
        for name, value in [('CardSubject', 'A < B & "C"'), ('CardSource', 'X < Y & Z')]:
            document = QTextDocument()
            document.setHtml(card.findChild(QLabel, name).text())
            assert value in document.toPlainText()
        card.resize(300, 500)
        for _ in range(5): app.processEvents()
        assert card.header_layout.direction() == QBoxLayout.TopToBottom
        card.close()
    assert heights[0] == heights[1]


def test_unbroken_metadata_and_history_stay_within_available_width():
    from prometheus.app import QuestionCard
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    card = QuestionCard(1, 'A' * 300, 'Médio', 'Médio', 'Dissertativa', '<p>Curto</p>', False,
                        lambda *args: None, question_source='B' * 300, usage_count=1,
                        history_request=lambda: [('C' * 500, 'D' * 500, '2026-01-01')])
    card.resize(640, 300)
    card.show()
    for _ in range(5): app.processEvents()
    assert card.width() == 640
    card.usage_popup.activate()
    for _ in range(5): app.processEvents()
    assert card.usage_popup.scroll.horizontalScrollBar().maximum() == 0
    assert card.usage_popup.scroll.verticalScrollBar().maximum() > 0
    card.usage_popup.close_history()
    card.close()


def test_card_usage_and_popup_follow_theme_and_metadata_stays_green(window):
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QLabel
    window.show_filtered_questions()
    window.show()
    QApplication.processEvents()
    card = window.scroll_layout.itemAt(0).widget()
    window.is_dark_mode = True
    window.apply_theme()
    card.usage_popup.activate()
    QApplication.processEvents()
    assert card.usage_control.palette().color(QPalette.Button) == QColor('#313244')
    assert card.usage_popup.content.palette().color(QPalette.Window) == QColor('#252538')
    assert card.metadata_widget.palette().color(QPalette.Window) == QColor('#294338')
    assert card.findChild(QLabel, 'CardIdentifier').palette().color(QPalette.WindowText) == QColor('#E2E8F0')
    card.usage_popup.close_history()
    window.show_filtered_questions()
    card = window.scroll_layout.itemAt(0).widget()
    assert card.metadata_widget.palette().color(QPalette.Window) == QColor('#294338')
    window.is_dark_mode = False
    window.apply_theme()
    QApplication.processEvents()
    assert card.usage_control.palette().color(QPalette.Button) == QColor('#FFFFFF')
    assert card.metadata_widget.palette().color(QPalette.Window) == QColor('#DCFCE7')
    assert card.findChild(QLabel, 'CardIdentifier').palette().color(QPalette.WindowText) == QColor('#183D2B')


def test_new_exam_resets_draft_filters_and_groups_controls(window, monkeypatch):
    from PySide6.QtWidgets import QFrame
    from PySide6.QtCore import Qt
    window.show_filtered_questions()
    window.selected_ids.add(1)
    window.exam_order.ids = [1]
    window.chk_multiple_versions.setChecked(True)
    window.spin_version_count.setValue(5)
    window.chk_include_answers.setChecked(False)
    window.txt_search_question_text.setText('texto')
    window.txt_search_source_year_from.setText('inválido')
    window.tabs.setCurrentIndex(2)
    monkeypatch.setattr('prometheus.app.QMessageBox.question', lambda *args: __import__('PySide6.QtWidgets', fromlist=['QMessageBox']).QMessageBox.Discard)
    shared = window.selected_ids
    window.btn_new_exam.click()
    assert window.selected_ids is shared and not shared
    assert window.exam_order.ids == [] and window.open_exam_id is None
    assert window.tabs.currentIndex() == 1
    assert window.txt_search_question_text.text() == '' and window.txt_search_source_year_from.text() == ''
    assert not window.chk_multiple_versions.isChecked() and window.spin_version_count.value() == 2
    assert window.chk_include_answers.isChecked() and not window.chk_separate_answers.isChecked()
    assert window.cb_saved_exams.currentIndex() == -1
    assert window.exam_snapshot == window.exam_draft()
    assert window.lbl_open_exam.text() == 'Prova aberta: nova prova (não salva)'
    panel = window.findChild(QFrame, 'ExamManagementPanel')
    assert panel and panel.isAncestorOf(window.btn_new_exam) and panel.isAncestorOf(window.cb_saved_exams)


def test_new_exam_cancel_keeps_current_draft(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window.selected_ids.add(1)
    window.tabs.setCurrentIndex(2)
    window.txt_search_question_text.setText('preservar')
    before = window.exam_draft()
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Cancel)
    window.btn_new_exam.click()
    assert window.exam_draft() == before and window.tabs.currentIndex() == 2
    assert window.txt_search_question_text.text() == 'preservar'


def test_new_exam_refresh_failure_clears_stale_cards_and_retries(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    from prometheus.storage import saved_exams as storage
    window.show_filtered_questions()
    window.selected_ids.add(1)
    old = window.scroll_layout.itemAt(0).widget()
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Discard)
    original = storage.question_usage_counts
    monkeypatch.setattr(storage, 'question_usage_counts', lambda *args: (_ for _ in ()).throw(RuntimeError('erro sintético')))
    window.btn_new_exam.click()
    assert not window.selected_ids and window.scroll_layout.count() == 0
    assert not old.usage_popup.isVisible()
    assert 'Não foi possível' in window.lbl_result_range.text()
    assert not window.btn_retry_search.isHidden()
    monkeypatch.setattr(storage, 'question_usage_counts', original)
    window.btn_retry_search.click()
    assert window.scroll_layout.count() == 1 and window.btn_retry_search.isHidden()


def test_new_exam_is_disabled_without_bank(window):
    old = window.conn
    window.conn = None
    window.refresh_saved_exam_controls()
    assert not window.btn_new_exam.isEnabled()
    window.conn = old
    window.refresh_saved_exam_controls()
    assert window.btn_new_exam.isEnabled()


def test_new_exam_resets_pending_filters_and_preserves_editor(window, monkeypatch):
    from PySide6.QtCore import QDate, Qt
    from PySide6.QtWidgets import QMessageBox, QTreeWidgetItem
    window.txt_prompt.setPlainText('edição preservada')
    window.txt_filter_search_subjects.setText('não encontrado')
    item = QTreeWidgetItem(window.tree_search_subjects, ['Categoria sintética'])
    item.setCheckState(0, Qt.Checked)
    window.txt_search_question_source.setText('fonte')
    window.txt_search_source_year_from.setText('inválido')
    window.txt_search_source_year_to.setText('2020')
    window.search_diff_checkboxes['Fácil'].setChecked(True)
    window.search_year_checkboxes['2ª Série'].setChecked(True)
    window.search_type_checkboxes['Dissertativa'].setChecked(True)
    window.cb_usage_filter.setCurrentIndex(window.cb_usage_filter.findData('since'))
    window.date_usage_filter.setDate(QDate(2020, 1, 2))
    window.selected_ids.add(1)
    window.search_view.set_selected_only(True)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Discard)
    window.btn_new_exam.click()
    assert window.txt_prompt.toPlainText() == 'edição preservada'
    assert item.checkState(0) == Qt.Unchecked and not item.isHidden()
    assert not window.txt_filter_search_subjects.text() and not window.txt_search_question_source.text()
    assert not window.txt_search_source_year_from.text() and not window.txt_search_source_year_to.text()
    assert window.search_diff_checkboxes['Todas as Dificuldades'].isChecked()
    assert window.search_year_checkboxes['Todos os Anos'].isChecked()
    assert window.search_type_checkboxes['Todos os Tipos'].isChecked()
    assert window.cb_usage_filter.currentData() == 'all' and window.date_usage_filter.date() == QDate.currentDate()
    assert not window.date_usage_filter.isEnabled() and not window.search_view.selected_only
    assert window.search_view.page == 1 and window.search_view.applied.text == ''
    assert not window.btn_browse_selected_questions.isChecked() and not window.btn_browse_selected_questions.isEnabled()
    window.btn_new_exam.click()
    assert window.exam_snapshot == window.exam_draft()


def test_new_exam_with_empty_bank(window):
    window.conn.execute('DELETE FROM normalized_questions')
    window.conn.commit()
    window.show_filtered_questions()
    window.btn_new_exam.click()
    assert window.scroll_layout.count() == 0
    assert 'Nenhuma' in window.lbl_result_range.text()
    assert window.exam_snapshot == window.exam_draft()


@pytest.mark.parametrize('mode', ['save', 'name_cancel', 'save_error', 'discard', 'cancel'])
def test_new_exam_guard_preserves_or_saves_draft(window, monkeypatch, mode):
    from PySide6.QtWidgets import QMessageBox
    window.selected_ids.add(1)
    window.txt_search_question_text.setText('filtro pendente')
    window.tabs.setCurrentIndex(2)
    window.chk_shuffle_questions.setChecked(True)
    old_draft = window.exam_draft()
    answer = {'save': QMessageBox.Save, 'name_cancel': QMessageBox.Save,
              'save_error': QMessageBox.Save, 'discard': QMessageBox.Discard,
              'cancel': QMessageBox.Cancel}[mode]
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: answer)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: None if mode == 'name_cancel' else 'Primeira prova')
    if mode == 'save_error':
        monkeypatch.setattr(saved_exams, 'save_exam', lambda *args: (_ for _ in ()).throw(RuntimeError('erro sintético')))
    window.btn_new_exam.click()
    if mode in ('name_cancel', 'save_error', 'cancel'):
        assert window.exam_draft() == old_draft and window.tabs.currentIndex() == 2
        assert window.txt_search_question_text.text() == 'filtro pendente'
        assert window.open_exam_id is None
    else:
        assert window.exam_draft() == window.exam_snapshot and not window.selected_ids
        assert window.open_exam_id is None and window.tabs.currentIndex() == 1
    rows = saved_exams.list_exams(window.conn)
    assert len(rows) == (1 if mode == 'save' else 0)
    if mode == 'save':
        assert saved_exams.load_exam(window.conn, rows[0][0])['question_ids'] == (1,)


def test_new_exam_after_generation_keeps_saved_exam_and_separates_new_one(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    window.conn.execute("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (2,'essay','easy','B','B','B','a','a',0)")
    window.conn.commit()
    names = iter(['Prova A', 'Prova B'])
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: next(names))
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    files = iter([str(tmp_path / 'a.docx'), str(tmp_path / 'b.docx')])
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (next(files), ''))
    window.selected_ids.add(1)
    window.generate_word_doc()
    first = window.open_exam_id
    first_exam = saved_exams.load_exam(window.conn, first)
    first_versions = saved_exams.versions(window.conn, first)
    first_usages = saved_exams.question_usages(window.conn, 1)
    window.btn_new_exam.click()
    assert window.open_exam_id is None and not window.selected_ids
    assert saved_exams.load_exam(window.conn, first) == first_exam
    assert saved_exams.versions(window.conn, first) == first_versions
    assert saved_exams.question_usages(window.conn, 1) == first_usages
    window.selected_ids.add(2)
    assert saved_exams.question_usages(window.conn, 2) == []
    window.generate_word_doc()
    second = window.open_exam_id
    assert second != first and saved_exams.load_exam(window.conn, second)['question_ids'] == (2,)
    assert len(saved_exams.question_usages(window.conn, 2)) == 1
    window.btn_new_exam.click()
    for exam_id, expected in ((first, {1}), (second, {2})):
        window.cb_saved_exams.setCurrentIndex(window.cb_saved_exams.findData(exam_id))
        window.open_saved_exam()
        assert window.selected_ids == expected
        window.btn_new_exam.click()
    assert len(saved_exams.list_exams(window.conn)) == 2


def test_new_exam_discard_preserves_saved_tables_and_hidden_selection_clears(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    exam_id = saved_exams.save_exam(window.conn, 'Original', None, {}, [1])
    saved_exams.record_generation(window.conn, exam_id, [[]], [1], used_at='2026-01-01')
    tables = ('saved_exams', 'saved_exam_questions', 'exam_usages', 'exam_usage_questions', 'exam_versions', 'normalized_questions')
    before = {name: window.conn.execute('SELECT * FROM ' + name).fetchall() for name in tables}
    window.open_exam_id = exam_id
    window.exam_snapshot = window.exam_draft()
    window.selected_ids.update((1, 99))
    window.search_view.set_selected_only(True)
    window.exam_order.ids = [99, 1]
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Discard)
    window.btn_new_exam.click()
    assert not window.selected_ids and not window.exam_order.ids and not window.search_view.selected_only
    assert {name: window.conn.execute('SELECT * FROM ' + name).fetchall() for name in tables} == before


def test_new_exam_cancel_does_not_synchronize_order(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window.exam_order.ids = [99]
    window.selected_ids.add(1)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Cancel)
    window.btn_new_exam.click()
    assert window.exam_order.ids == [99] and window.selected_ids == {1}


@pytest.mark.parametrize('choice', ['save', 'discard', 'cancel'])
def test_new_exam_guard_on_open_saved_draft(window, monkeypatch, choice):
    from PySide6.QtWidgets import QMessageBox
    window.selected_ids.add(1)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Existente')
    assert window.save_current_exam()
    exam_id = window.open_exam_id
    previous = saved_exams.load_exam(window.conn, exam_id)
    window.chk_include_answers.setChecked(False)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: {'save': QMessageBox.Save,
                        'discard': QMessageBox.Discard, 'cancel': QMessageBox.Cancel}[choice])
    window.btn_new_exam.click()
    saved = saved_exams.load_exam(window.conn, exam_id)
    if choice == 'cancel':
        assert window.open_exam_id == exam_id and not window.chk_include_answers.isChecked()
        assert saved == previous
    else:
        assert window.open_exam_id is None and not window.selected_ids
        assert saved['settings']['include_answers'] == (choice != 'save')


def test_new_exam_does_not_reuse_shuffled_arrangements(window, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QFileDialog
    window.conn.executemany("INSERT INTO normalized_questions (id,kind,difficulty,statement,statement_text,search_text,created_at,updated_at,keep_alternative_order) VALUES (?, 'essay','easy',?,?,?,'a','a',0)", [(2,'B','B','B'), (3,'C','C','C')])
    window.conn.commit()
    names = iter(['Prova A', 'Prova B'])
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: next(names))
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    files = iter([str(tmp_path / 'a.docx'), str(tmp_path / 'b.docx')])
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (next(files), ''))
    window.selected_ids.update((1, 2))
    window.chk_multiple_versions.setChecked(True)
    window.chk_shuffle_questions.setChecked(True)
    window.generate_word_doc()
    first = window.open_exam_id
    first_versions = saved_exams.versions(window.conn, first)
    assert len(first_versions) == 2
    window.btn_new_exam.click()
    assert not window.chk_multiple_versions.isChecked() and not window.chk_shuffle_questions.isChecked()
    window.selected_ids.add(3)
    window.generate_word_doc()
    second = window.open_exam_id
    assert second != first and len(saved_exams.versions(window.conn, second)) == 1
    assert saved_exams.versions(window.conn, first) == first_versions
    assert len(saved_exams.question_usages(window.conn, 1)) == 1
    assert len(saved_exams.question_usages(window.conn, 3)) == 1


def test_management_panel_fits_and_tracks_theme(window):
    from PySide6.QtWidgets import QFrame, QPushButton, QScrollArea
    from PySide6.QtGui import QColor, QPalette
    window.resize(1250, 850)
    window.tabs.setCurrentIndex(2)
    window.show()
    for _ in range(4): QApplication.processEvents()
    panel = window.findChild(QFrame, 'ExamManagementPanel')
    buttons = panel.findChildren(QPushButton)
    assert [button.text() for button in buttons] == ['Nova prova', 'Abrir', 'Salvar', 'Salvar como', 'Renomear', 'Duplicar', 'Excluir']
    assert all(panel.rect().contains(button.mapTo(panel, button.rect().bottomRight())) for button in buttons)
    assert panel.palette().color(QPalette.Window) == QColor('#FFFFFF')
    window.is_dark_mode = True
    window.apply_theme()
    QApplication.processEvents()
    assert panel.palette().color(QPalette.Window) == QColor('#252538')
    generation_content = next(
        area.widget() for area in window.findChildren(QScrollArea)
        if area.widget() and area.widget().objectName() == 'GenerationScrollContent'
    )
    assert generation_content.objectName() == 'GenerationScrollContent'
    assert generation_content.palette().color(QPalette.Window) == QColor('#1E1E2E')


def test_usage_filter_popup_follows_dark_theme(window):
    from PySide6.QtGui import QColor, QPalette
    window.is_dark_mode = True
    window.apply_theme()
    popup = window.cb_usage_filter.view().parentWidget()
    assert popup.objectName() == 'ComboPopupContainer'
    assert popup.palette().color(QPalette.Window) == QColor('#313244')
    assert window.date_usage_filter.palette().color(QPalette.Base) == QColor('#313244')


def test_help_dialog_is_wide_resizable_and_scrollable(window, monkeypatch):
    from PySide6.QtWidgets import QDialog, QTextBrowser
    captured = {}

    original_exec = QDialog.exec
    def capture_exec(dialog):
        if dialog.objectName() == 'HelpDialog':
            captured['dialog'] = dialog
            return QDialog.Rejected
        return original_exec(dialog)

    monkeypatch.setattr(QDialog, 'exec', capture_exec)
    window.show_help()
    dialog = captured['dialog']
    browser = dialog.findChild(QTextBrowser, 'HelpContent')
    assert dialog.minimumWidth() >= 720
    assert dialog.isSizeGripEnabled()
    assert browser is not None and browser.isReadOnly()
    dialog.show()
    QApplication.processEvents()
    assert browser.verticalScrollBar().maximum() > 0
    dialog.close()


def test_about_dialog_contains_readable_legal_notice(window, monkeypatch):
    from PySide6.QtWidgets import QDialog, QLabel
    captured = {}
    original_exec = QDialog.exec

    def capture_exec(dialog):
        if dialog.windowTitle() == 'Sobre o Prometheus':
            captured['dialog'] = dialog
            return QDialog.Rejected
        return original_exec(dialog)

    monkeypatch.setattr(QDialog, 'exec', capture_exec)
    window.show_about()
    notice = captured['dialog'].findChild(QLabel, 'LegalNotice')
    assert notice is not None and notice.wordWrap()
    assert 'responsabiliza' in notice.text()
    assert 'conteúdo que cadastra' in notice.text()


def test_new_exam_save_failure_reading_existing_exam_preserves_draft(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window.selected_ids.add(1)
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Existente')
    assert window.save_current_exam()
    exam_id = window.open_exam_id
    window.chk_include_answers.setChecked(False)
    before = window.exam_draft()
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda *args: alerts.append(args))
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Save)
    monkeypatch.setattr(saved_exams, 'load_exam', lambda *args: (_ for _ in ()).throw(RuntimeError('erro sintético')))
    window.btn_new_exam.click()
    assert window.open_exam_id == exam_id and window.exam_draft() == before
    assert alerts and 'erro sintético' in alerts[-1][1]


def test_generate_suggests_saved_exam_name_in_file_dialog(window, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    suggestions = []
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova de Biologia')
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (suggestions.append(args[2]) or '', ''))
    window.selected_ids.add(1)
    window.generate_word_doc()
    assert suggestions == ['Prova de Biologia.docx']
    assert saved_exams.load_exam(window.conn, window.open_exam_id)['name'] == 'Prova de Biologia'


def test_generate_suggests_open_exam_name_not_picker_selection(window, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Prova original')
    window.selected_ids.add(1)
    assert window.save_current_exam()
    saved_exams.save_exam(window.conn, 'Outra prova', None, window.exam_draft()[2], [1])
    window.refresh_saved_exam_controls(window.open_exam_id)
    window.cb_saved_exams.setCurrentIndex(window.cb_saved_exams.findText('Outra prova'))
    suggestions = []
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (suggestions.append(args[2]) or '', ''))
    window.generate_word_doc()
    assert suggestions == ['Prova original.docx']
