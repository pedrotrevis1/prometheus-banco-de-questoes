import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sqlite3
import pytest
from PySide6.QtWidgets import QApplication
from prometheus.app import ExamGeneratorApp, QuestionCard
from prometheus.storage.migrations import MIGRATIONS


@pytest.fixture
def window(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: False)
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda *a: None)
    w = ExamGeneratorApp()
    conn = sqlite3.connect(':memory:')
    conn.create_function('CASEFOLD', 1, lambda v: str(v or '').casefold())
    for migration in MIGRATIONS[:3]: migration(conn)
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


def test_source_year_apply_and_unapplied_edits_preserve_selection(window):
    window.conn.execute("UPDATE questoes SET ano_origem = CASE WHEN id <= 60 THEN '2022' ELSE '2023' END")
    window.conn.commit()
    window.selected_ids.add(123)
    window.txt_search_source_year_from.setText('2022')
    window.txt_search_source_year_to.setText('2022')
    window.show_filtered_questions()
    assert card_ids(window) == list(range(1, 51))
    assert window.search_view.applied.source_year_from == 2022
    assert 'de 60' in window.lbl_result_range.text()
    window.txt_search_source_year_from.setText('2023')
    window.move_search_page(2)
    assert card_ids(window) == list(range(51, 61))
    assert window.selected_ids == {123}
    window.btn_browse_selected_questions.setEnabled(True)
    window.btn_browse_selected_questions.setChecked(True)
    assert card_ids(window) == [123]


def test_invalid_source_year_preserves_selected_view_and_page(window, monkeypatch):
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
    window.txt_search_source_year_from.setText('202x')
    window.show_filtered_questions()
    assert messages[-1] == 'Informe um ano inteiro entre 1 e 9999 ou deixe o campo vazio.'
    assert window.search_view.selected_only and card_ids(window) == before


@pytest.mark.parametrize('field_name', ['txt_search_source_year_from', 'txt_search_source_year_to'])
def test_enter_applies_once_from_either_year_field(window, monkeypatch, field_name):
    import prometheus.app as app_module
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    calls = []
    original = app_module.page_questions
    monkeypatch.setattr(app_module, 'page_questions', lambda *args, **kwargs: (calls.append(1), original(*args, **kwargs))[1])
    field = getattr(window, field_name)
    field.setText('2022')
    QTest.keyClick(field, Qt.Key_Return)
    assert len(calls) == 1


def test_source_year_fields_have_accessible_labels_and_tooltips(window):
    from PySide6.QtWidgets import QLabel
    pairs = [(label.text(), label.buddy()) for label in window.findChildren(QLabel) if label.buddy()]
    assert ('Desde', window.txt_search_source_year_from) in pairs
    assert ('até', window.txt_search_source_year_to) in pairs
    for field in (window.txt_search_source_year_from, window.txt_search_source_year_to):
        assert 'fonte' in field.accessibleName().lower()
        assert 'vazio' in field.toolTip().lower()


def test_registration_saves_using_extracted_core(window, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItem
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    category = QTreeWidgetItem(window.tree_register_subjects, ['Bio'])
    category.setCheckState(0, Qt.Checked)
    next(iter(window.year_checkboxes.values())).setChecked(True)
    window.cb_type.setCurrentText('Dissertativa')
    window.txt_prompt.setPlainText('Questão de teste')
    window.save_question()
    row = window.conn.execute("SELECT enunciado FROM questoes WHERE enunciado LIKE '%Questão de teste%'").fetchone()
    assert row is not None and alerts[-1][0] == 'Sucesso'


def test_edit_and_duplicate_keep_original_id_and_rich_html(window, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItem
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    category = QTreeWidgetItem(window.tree_register_subjects, ['Bio'])
    category.setCheckState(0, Qt.Unchecked)
    raw = '<p><b>Original</b><img src="data:image/png;base64,abc"></p>'
    window.conn.execute("UPDATE questoes SET enunciado=?, ano_sugerido='1ª Série', segmento='Ensino Médio', gabarito='<p>Resposta</p>' WHERE id=1", (raw,))
    window.conn.commit(); window.load_questions()
    window.selected_ids.add(1)
    window.scroll_layout.itemAt(0).widget().btn_edit.click()
    assert window.tabs.currentIndex() == 0 and '1' in window.lbl_register_title.text()
    window.txt_question_source.setText('ENEM')
    window.save_question()
    assert window.conn.execute('SELECT enunciado, fonte_questao FROM questoes WHERE id=1').fetchone() == (raw, 'ENEM')
    assert 1 in window.selected_ids
    window.load_questions()
    window.scroll_layout.itemAt(0).widget().btn_duplicate.click()
    window.save_question()
    assert window.conn.execute('SELECT COUNT(*) FROM questoes WHERE enunciado=?', (raw,)).fetchone()[0] == 2
    assert alerts[-1][0] == 'Sucesso'


def test_edit_warns_about_missing_categories_and_cancel_keeps_bank(window, monkeypatch):
    from PySide6.QtWidgets import QTreeWidgetItem
    from PySide6.QtCore import Qt
    messages = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: messages.append(text))
    QTreeWidgetItem(window.tree_register_subjects, ['Bio']).setCheckState(0, Qt.Unchecked)
    window.conn.execute("UPDATE questoes SET assunto='Bio;Removed', ano_sugerido='1ª Série', segmento='Ensino Médio' WHERE id=1")
    window.conn.commit()
    before = window.conn.execute('SELECT * FROM questoes WHERE id=1').fetchone()
    window.open_question_for_edit(1)
    assert any('Removed' in message for message in messages)
    assert window.get_checked_subjects(window.tree_register_subjects) == ['Bio']
    window.txt_prompt.setPlainText('not saved')
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    window.cancel_question_edit()
    assert window.question_session is None
    assert window.conn.execute('SELECT * FROM questoes WHERE id=1').fetchone() == before


def test_dirty_form_blocks_opening_another_question(window, monkeypatch):
    confirmations = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: confirmations.append(text) or False)
    window.txt_prompt.setPlainText('Não perder')
    window.open_question_for_edit(1)
    assert confirmations and window.txt_prompt.toPlainText() == 'Não perder'
    assert window.question_session is None


def test_dirty_form_blocks_discipline_switch_and_close(window, monkeypatch):
    confirmations = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: confirmations.append(text) or False)
    window.config_data['disciplines']['Other'] = '/does/not/exist.db'
    window.txt_prompt.setPlainText('Não perder')
    before = window.conn
    window.on_discipline_changed('Other')
    assert window.conn is before and window.txt_prompt.toPlainText() == 'Não perder'
    from PySide6.QtGui import QCloseEvent
    event = QCloseEvent()
    window.closeEvent(event)
    assert not event.isAccepted() and len(confirmations) == 2
    monkeypatch.setattr(window, 'show_confirm', lambda *a: True)


@pytest.mark.parametrize('editor_name', ['statement', 'alternative', 'essay'])
def test_toolbar_and_equation_target_focused_editor(window, monkeypatch, editor_name):
    import prometheus.app as app_module
    from PySide6.QtWidgets import QDialog
    monkeypatch.setattr(window, 'show_confirm', lambda *a: True)
    if editor_name == 'essay':
        window.cb_type.setCurrentText('Dissertativa')
    editor = {'statement': window.txt_prompt, 'alternative': window.alt_inputs['A'], 'essay': window.txt_essay_answer}[editor_name]
    window.tabs.setCurrentIndex(0); window.show(); QApplication.processEvents()
    editor.setPlainText('Alvo')
    editor.setFocus(); editor.selectAll(); QApplication.processEvents()
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    if window.btn_bold.isChecked():
        window.btn_bold.setChecked(False)
    QTest.mouseClick(window.btn_bold, Qt.LeftButton)
    assert 'font-weight:700' in editor.toHtml() or 'font-weight: 700' in editor.toHtml()
    class FakeDialog:
        def __init__(self, *args): pass
        def exec(self): return QDialog.Accepted
        def get_equation_text(self): return 'x^2'
        def get_equation_type(self): return 'Matemática'
    monkeypatch.setattr(app_module, 'InsertEquationDialog', FakeDialog)
    editor.moveCursor(editor.textCursor().MoveOperation.End)
    QTest.mouseClick(window.btn_add_equation, Qt.LeftButton)
    assert 'x' in editor.toPlainText() and '2' in editor.toPlainText()
    if editor_name != 'statement':
        assert not window.txt_prompt.toPlainText()


def test_question_card_displays_modified_time_or_unknown(window):
    from PySide6.QtWidgets import QLabel
    window.conn.execute("UPDATE questoes SET last_modified='2026-11-17T13:45:30+00:00' WHERE id=1")
    window.conn.commit(); window.load_questions()
    first = window.scroll_layout.itemAt(0).widget()
    second = window.scroll_layout.itemAt(1).widget()
    assert 'Não informada' not in first.findChild(QLabel, 'CardModified').text()
    assert 'Não informada' in second.findChild(QLabel, 'CardModified').text()


def test_unchanged_edit_preserves_exported_text_and_embedded_image(window, tmp_path, monkeypatch):
    import base64
    import zipfile
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
    from PySide6.QtGui import QImage, QColor
    from PySide6.QtWidgets import QTreeWidgetItem
    monkeypatch.setattr(window, 'show_alert', lambda *args: None)
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    QTreeWidgetItem(window.tree_register_subjects, ['Bio']).setCheckState(0, Qt.Unchecked)
    image = QImage(8, 8, QImage.Format_RGB32); image.fill(QColor('blue'))
    raw = QByteArray(); buffer = QBuffer(raw); buffer.open(QIODevice.WriteOnly); assert image.save(buffer, 'PNG'); buffer.close()
    encoded = base64.b64encode(bytes(raw)).decode('ascii')
    html = '<p><b>Conteúdo</b> x<sup>2</sup></p><img src="data:image/png;base64,' + encoded + '">'
    window.conn.execute("UPDATE questoes SET enunciado=?, ano_sugerido='1ª Série', segmento='Ensino Médio', gabarito='<p>Resposta</p>' WHERE id=1", (html,))
    window.conn.commit()
    before_path, after_path = tmp_path / 'before.docx', tmp_path / 'after.docx'
    row = window.conn.execute('SELECT * FROM questoes WHERE id=1').fetchone()
    window.build_exam_document([row]).save(before_path)
    window.open_question_for_edit(1)
    window.save_question()
    updated = window.conn.execute('SELECT * FROM questoes WHERE id=1').fetchone()
    assert updated[4] == html
    window.build_exam_document([updated]).save(after_path)
    with zipfile.ZipFile(before_path) as before, zipfile.ZipFile(after_path) as after:
        assert before.read('word/document.xml') == after.read('word/document.xml')
        images = [name for name in before.namelist() if name.startswith('word/media/')]
        assert images and {name: before.read(name) for name in images} == {name: after.read(name) for name in images}


def test_edit_preserves_untouched_legacy_year_and_source_text(window, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItem
    monkeypatch.setattr(window, 'show_alert', lambda *args: None)
    QTreeWidgetItem(window.tree_register_subjects, ['Bio']).setCheckState(0, Qt.Unchecked)
    legacy = '{"level":"Ensino Médio","years":["1"]}'
    window.conn.execute("UPDATE questoes SET ano_sugerido=?, segmento='', fonte_questao=' enem ', ano_origem=' 2022 ' WHERE id=1", (legacy,))
    window.conn.commit()
    window.open_question_for_edit(1)
    window.txt_prompt.setPlainText('Editada')
    window.save_question()
    assert window.conn.execute('SELECT ano_sugerido, segmento, fonte_questao, ano_origem FROM questoes WHERE id=1').fetchone() == (legacy, '', ' enem ', ' 2022 ')


def test_edit_multiple_choice_preserves_answer_and_changes_type_only_on_save(window, monkeypatch):
    from PySide6.QtWidgets import QTreeWidgetItem
    from PySide6.QtCore import Qt
    monkeypatch.setattr(window, 'show_alert', lambda *args: None)
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    QTreeWidgetItem(window.tree_register_subjects, ['Bio']).setCheckState(0, Qt.Unchecked)
    alternatives = tuple(f'<p>Alternativa {letter}</p>' for letter in 'ABCDE')
    window.conn.execute('''UPDATE questoes SET tipo='Múltipla Escolha', ano_sugerido='1ª Série',
        segmento='Ensino Médio', alternativa_a=?, alternativa_b=?, alternativa_c=?, alternativa_d=?,
        alternativa_e=?, gabarito='C' WHERE id=1''', alternatives)
    window.conn.commit(); window.open_question_for_edit(1)
    assert window.alt_radios.id(window.alt_radios.checkedButton()) == ord('C')
    assert [window.alt_inputs[letter].toPlainText() for letter in 'ABCDE'] == [f'Alternativa {letter}' for letter in 'ABCDE']
    window.cb_type.setCurrentText('Dissertativa')
    assert window.conn.execute('SELECT alternativa_c FROM questoes WHERE id=1').fetchone()[0] == alternatives[2]
    window.txt_essay_answer.setPlainText('Resposta alterada')
    window.save_question()
    row = window.conn.execute('SELECT tipo, alternativa_a, alternativa_c, gabarito FROM questoes WHERE id=1').fetchone()
    assert row[:3] == ('Dissertativa', '', '') and 'Resposta alterada' in row[3]


def test_keep_alternative_order_is_loaded_and_duplicated(window, monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QTreeWidgetItem
    monkeypatch.setattr(window, 'show_alert', lambda *args: None)
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    QTreeWidgetItem(window.tree_register_subjects, ['Bio']).setCheckState(0, Qt.Unchecked)
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', ano_sugerido='1ª Série', segmento='Ensino Médio', alternativa_a='a', alternativa_b='b', alternativa_c='c', alternativa_d='d', alternativa_e='e', gabarito='C', keep_alternative_order=1 WHERE id=1")
    window.conn.commit()
    window.open_question_for_edit(1)
    assert window.chk_keep_alternative_order.isChecked()
    window.save_question()
    assert window.conn.execute('SELECT keep_alternative_order FROM questoes WHERE id=1').fetchone()[0] == 1
    window.open_question_for_edit(1, duplicate=True)
    assert window.chk_keep_alternative_order.isChecked()
    window.save_question()
    assert window.conn.execute('SELECT keep_alternative_order FROM questoes ORDER BY id DESC LIMIT 1').fetchone()[0] == 1


def test_generation_respects_user_order_and_separate_keys(window, tmp_path, monkeypatch):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    window.selected_ids.update({1, 2})
    window.refresh_exam_order()
    window.list_exam_order.setCurrentRow(1)
    window.move_exam_question(-1)
    window.chk_separate_answers.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    exam = Document(tmp_path / 'Prova.docx'); key = Document(tmp_path / 'Prova_Gabarito.docx')
    exam_text = '\n'.join(p.text for p in exam.paragraphs)
    assert exam_text.index('Questão 2') < exam_text.index('Questão 1')
    assert 'Gabarito Oficial' not in exam_text
    assert 'Gabarito Oficial' in '\n'.join(p.text for p in key.paragraphs)
    assert alerts[-1][0] == 'Sucesso'


def test_generation_warns_before_unexportable_image_and_can_cancel(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    window.conn.execute("UPDATE questoes SET enunciado='<p>Texto</p><img src=\"https://example.com/no.png\">' WHERE id=1")
    window.conn.commit(); window.selected_ids.add(1)
    prompts = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: prompts.append((title, text)) or False)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    assert prompts and '1' in prompts[-1][1]
    assert not (tmp_path / 'Prova.docx').exists()


def test_generation_does_not_overwrite_without_confirmation(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    destination = tmp_path / 'Prova.docx'; destination.write_bytes(b'original')
    window.selected_ids.add(1)
    monkeypatch.setattr(window, 'show_confirm', lambda *args: False)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(destination), ''))
    window.generate_word_doc()
    assert destination.read_bytes() == b'original'


def test_numbered_versions_and_separate_keys_match_shuffled_answers(window, tmp_path, monkeypatch):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', alternativa_a='alpha', alternativa_b='bravo', alternativa_c='charlie', alternativa_d='delta', alternativa_e='echo', gabarito='C' WHERE id=1")
    window.conn.commit(); window.selected_ids.add(1)
    window.chk_multiple_versions.setChecked(True)
    window.chk_shuffle_alternatives.setChecked(True)
    window.chk_separate_answers.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    printed = []
    for number in (1, 2):
        exam = Document(tmp_path / f'Prova_Versao_{number}.docx')
        key = Document(tmp_path / f'Prova_Versao_{number}_Gabarito.docx')
        exam_text = '\n'.join(p.text for p in exam.paragraphs)
        key_text = '\n'.join(p.text for p in key.paragraphs)
        assert f'Versão {number}' in exam_text and f'Versão {number}' in key_text
        answer = next(letter for letter in 'ABCDE' if f'{letter}) charlie' in exam_text)
        assert f'1) {answer}' in key_text
        printed.append(exam_text.replace(f'Versão {number}', 'Versão'))
    assert printed[0] != printed[1]
    assert alerts[-1][0] == 'Sucesso'


def test_user_can_continue_after_warning_for_unexportable_image(window, tmp_path, monkeypatch):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    window.conn.execute("UPDATE questoes SET enunciado='<p>Texto preservado</p><img src=\"https://example.com/no.png\">' WHERE id=1")
    window.conn.commit(); window.selected_ids.add(1)
    prompts = []; alerts = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: prompts.append((title, text)) or True)
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    assert prompts and 'Questão 1' in prompts[0][1]
    assert alerts[-1][0] == 'Sucesso'
    exam = Document(tmp_path / 'Prova.docx')
    assert 'Texto preservado' in '\n'.join(p.text for p in exam.paragraphs)
    assert len(exam.inline_shapes) == 0


def test_protected_question_keeps_alternatives_across_versions(window, tmp_path, monkeypatch):
    from docx import Document
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    monkeypatch.setattr(window, 'show_alert', lambda *args: None)
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', alternativa_a='alpha', alternativa_b='bravo', alternativa_c='charlie', alternativa_d='delta', alternativa_e='echo', gabarito='C', keep_alternative_order=1 WHERE id=1")
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', alternativa_a='one', alternativa_b='two', alternativa_c='three', alternativa_d='four', alternativa_e='five', gabarito='B' WHERE id=2")
    window.conn.commit(); window.selected_ids.update({1, 2})
    window.chk_multiple_versions.setChecked(True); window.chk_shuffle_alternatives.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    for number in (1, 2):
        doc = Document(tmp_path / f'Prova_Versao_{number}.docx')
        text = '\n'.join(p.text for p in doc.paragraphs)
        assert all(f'{letter}) {value}' in text for letter, value in zip('ABCDE', ('alpha', 'bravo', 'charlie', 'delta', 'echo')))


def test_visually_identical_shuffled_versions_are_not_published(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    window.conn.execute("UPDATE questoes SET enunciado='<p><b>igual</b></p>' WHERE id=1")
    window.conn.execute("UPDATE questoes SET enunciado='<p><strong>igual</strong></p>' WHERE id=2")
    window.conn.commit(); window.selected_ids.update({1, 2})
    window.chk_multiple_versions.setChecked(True); window.chk_shuffle_questions.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    assert alerts and 'distinta' in alerts[-1][1].lower()
    assert not list(tmp_path.glob('Prova*.docx'))


def test_dropped_color_and_run_boundaries_do_not_make_versions_distinct(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append((title, text)))
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    window.conn.execute("UPDATE questoes SET tipo='Dissertativa', enunciado='<p>AB</p>' WHERE id=1")
    window.conn.execute("UPDATE questoes SET tipo='Dissertativa', enunciado='<p>A<span style=\"color:red\">B</span></p>' WHERE id=2")
    window.conn.commit(); window.selected_ids.update({1, 2})
    window.chk_multiple_versions.setChecked(True); window.chk_shuffle_questions.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    assert alerts and 'distint' in alerts[-1][1].lower()
    assert not list(tmp_path.glob('*.docx'))


def test_existing_answer_key_requires_confirmation_before_any_output(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    existing = tmp_path / 'Prova_Gabarito.docx'; existing.write_bytes(b'original')
    window.selected_ids.add(1); window.chk_separate_answers.setChecked(True)
    prompts = []
    monkeypatch.setattr(window, 'show_confirm', lambda title, text: prompts.append(text) or False)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path / 'Prova.docx'), ''))
    window.generate_word_doc()
    assert prompts and str(existing) in prompts[-1]
    assert existing.read_bytes() == b'original'
    assert not (tmp_path / 'Prova.docx').exists()


def test_impossible_protected_versions_warn_before_output(window, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    alerts = []
    monkeypatch.setattr(window, 'show_alert', lambda title, text, *args: alerts.append(text))
    monkeypatch.setattr(window, 'show_confirm', lambda *args: True)
    window.conn.execute("UPDATE questoes SET tipo='Múltipla Escolha', alternativa_a='a', alternativa_b='b', alternativa_c='c', alternativa_d='d', alternativa_e='e', gabarito='C', keep_alternative_order=1 WHERE id=1")
    window.conn.commit(); window.selected_ids.add(1)
    window.chk_multiple_versions.setChecked(True); window.chk_shuffle_alternatives.setChecked(True)
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(tmp_path/'Prova.docx'), ''))
    window.generate_word_doc()
    assert alerts and 'distint' in alerts[-1].lower()
    assert not list(tmp_path.glob('Prova*.docx'))
