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
    assert 'História — Sem turma — 10/05/2026' in card.findChild(type(window.lbl_selected_count)).text()
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
