import json
import os

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
import pytest

from prometheus.app import ExamGeneratorApp
from prometheus.storage import database
from prometheus.storage.normalization_migration import migrate_v3_to_v4


@pytest.fixture
def qt_app():
    return QApplication.instance() or QApplication([])


def test_upgrade_then_create_search_and_edit_four_alternative_question(tmp_path, monkeypatch, qt_app):
    bank = tmp_path / 'bank.db'
    import sqlite3
    from prometheus.storage.migrations import MIGRATIONS
    conn = sqlite3.connect(bank)
    for migration in MIGRATIONS[:3]:
        migration(conn)
    conn.execute("INSERT INTO assuntos (nome) VALUES ('Biologia')")
    conn.commit()
    conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Bio', 'disciplines': {'Bio': str(bank)}}))
    monkeypatch.setattr(database, 'SCHEMA_VERSION', 4)
    monkeypatch.setattr(database, 'MIGRATIONS', (*database.MIGRATIONS[:3], migrate_v3_to_v4))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: True)
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *args: alerts.append((title, text)))
    window = ExamGeneratorApp()
    assert window.conn.execute('PRAGMA user_version').fetchone()[0] == 4
    window.tree_register_subjects.topLevelItem(0).setCheckState(0, Qt.Checked)
    window.year_checkboxes['9º Ano'].setChecked(True)
    window.year_checkboxes['1ª Série'].setChecked(True)
    window.txt_prompt.setPlainText('Revolução Francesa')
    window.alternative_count.setValue(4)
    for letter in 'ABCD':
        window.alt_inputs[letter].setPlainText(letter)
    window.alt_radios.button(ord('C')).setChecked(True)
    window.save_question()
    assert window.conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone() == (1,)
    window.txt_search_question_text.setText('revolucao francesa')
    window.show_filtered_questions()
    assert '1–1 de 1' in window.lbl_result_range.text()
    window.open_question_for_edit(1)
    assert window.alternative_count.value() == 4
    assert window.year_checkboxes['9º Ano'].isChecked()
    assert window.year_checkboxes['1ª Série'].isChecked()
    window.txt_prompt.setPlainText('Texto alterado')
    window.save_question()
    assert 'Texto alterado' in window.conn.execute('SELECT statement_text FROM normalized_questions WHERE id = 1').fetchone()[0]
    window.tree_register_subjects.setCurrentItem(window.tree_register_subjects.topLevelItem(0))
    monkeypatch.setattr(window, 'get_text_prompt', lambda *args: 'Ciências')
    window.rename_selected_category()
    assert window.conn.execute('SELECT name FROM normalized_categories').fetchone() == ('Ciências',)
    assert window.conn.execute('SELECT category_id FROM question_categories WHERE question_id = 1').fetchone() == (1,)
    from prometheus.storage.categories import create_category
    from PySide6.QtWidgets import QInputDialog
    parent = create_category(window.conn, 'Outra categoria')
    window.reload_all_trees()
    for index in range(window.tree_register_subjects.topLevelItemCount()):
        item = window.tree_register_subjects.topLevelItem(index)
        if item.data(0, Qt.UserRole) == 1:
            window.tree_register_subjects.setCurrentItem(item)
    monkeypatch.setattr(QInputDialog, 'getItem', lambda *args: (f'Outra categoria (ID {parent})', True))
    window.move_selected_category()
    assert window.conn.execute('SELECT parent_id FROM normalized_categories WHERE id = 1').fetchone() == (parent,)
    from PySide6.QtWidgets import QFileDialog
    backup = tmp_path / 'manual-backup.db'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args, **kwargs: (str(backup), ''))
    window.action_backup_database()
    window.selected_ids.add(1)
    window.delete_selected_questions()
    assert window.conn.execute('SELECT COUNT(*) FROM normalized_questions').fetchone() == (0,)
    import sqlite3
    with sqlite3.connect(backup) as saved:
        assert saved.execute('SELECT COUNT(*) FROM normalized_questions').fetchone() == (1,)
    assert not [message for title, message in alerts if title == 'Erro']
    window.close()


def test_legacy_question_retains_rich_content_when_edited(tmp_path, monkeypatch, qt_app):
    import sqlite3
    from prometheus.storage.migrations import MIGRATIONS
    bank = tmp_path / 'legacy.db'
    conn = sqlite3.connect(bank)
    for migration in MIGRATIONS[:3]:
        migration(conn)
    conn.execute("INSERT INTO assuntos (id, nome) VALUES (1, 'Citologia')")
    original = '<p>Revolução <b>Francesa</b></p>'
    conn.execute('''INSERT INTO questoes (id, assunto, tipo, dificuldade, enunciado, ano_sugerido,
        segmento, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_e, gabarito)
        VALUES (1, 'Citologia', 'Múltipla Escolha', 'Fácil', ?, '9º Ano', 'Ensino Fundamental',
                'A', 'B', 'C', 'D', 'E', 'C')''', (original,))
    conn.commit()
    conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Bio', 'disciplines': {'Bio': str(bank)}}))
    monkeypatch.setattr(database, 'SCHEMA_VERSION', 4)
    monkeypatch.setattr(database, 'MIGRATIONS', (*database.MIGRATIONS[:3], migrate_v3_to_v4))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: True)
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *args: alerts.append((title, text)))
    window = ExamGeneratorApp()
    window.open_question_for_edit(1)
    window.txt_question_source.setText('ENEM')
    window.save_question()
    assert window.conn.execute('SELECT statement FROM normalized_questions WHERE id = 1').fetchone() == (original,)
    assert window.conn.execute('SELECT source FROM normalized_questions WHERE id = 1').fetchone() == ('ENEM',)
    assert not [message for title, message in alerts if title == 'Erro']
    window.close()
