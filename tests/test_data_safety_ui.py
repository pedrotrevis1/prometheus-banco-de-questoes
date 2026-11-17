import json
import os
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from prometheus.app import ExamGeneratorApp


@pytest.fixture(scope='module')
def qt_app():
    return QApplication.instance() or QApplication([])


def test_declining_first_run_does_not_create_bank(tmp_path, monkeypatch, qt_app):
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: False)
    window = ExamGeneratorApp()
    assert window.conn is None
    assert not (tmp_path / 'biologia.db').exists()
    window.close()


def test_missing_existing_bank_does_not_create_file(tmp_path, monkeypatch, qt_app):
    bank = tmp_path / 'missing.db'
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Bio', 'disciplines': {'Bio': str(bank)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'handle_missing_bank', lambda self, *args: False)
    window = ExamGeneratorApp()
    assert window.conn is None
    assert not bank.exists()
    window.close()


def test_category_read_failure_is_shown(tmp_path, monkeypatch, qt_app):
    from prometheus.storage.database import open_bank
    bank = tmp_path / 'bank.db'
    conn = open_bank(bank, create=True)
    conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Bio', 'disciplines': {'Bio': str(bank)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *args: alerts.append((title, text)))
    window = ExamGeneratorApp()
    window.conn.close()
    window.build_subject_tree(window.tree_register_subjects)
    assert alerts and 'categorias' in alerts[-1][1]
    window.conn = None
    window.close()


def test_manual_backup_and_discipline_management(tmp_path, monkeypatch, qt_app):
    import sqlite3
    from PySide6.QtWidgets import QFileDialog
    from prometheus.storage.database import open_bank
    bank = tmp_path / 'bank.db'
    conn = open_bank(bank, create=True)
    conn.execute("INSERT INTO questoes (enunciado) VALUES ('preserved')")
    conn.commit(); conn.close()
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'Bio', 'disciplines': {'Bio': str(bank)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *args: alerts.append((title, text)))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *args: True)
    window = ExamGeneratorApp()
    destination = tmp_path / 'backup.db'
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **kw: (str(destination), ''))
    window.action_backup_database()
    with sqlite3.connect(destination) as copied:
        assert copied.execute('SELECT enunciado FROM questoes').fetchone() == ('preserved',)
    monkeypatch.setattr(ExamGeneratorApp, 'get_text_prompt', lambda *a: 'Biologia nova')
    window.action_rename_discipline()
    assert window.current_discipline == 'Biologia nova'
    window.action_remove_discipline()
    assert window.conn is None and bank.exists()
    assert json.loads((tmp_path / 'app_config.json').read_text())['disciplines'] == {}
    assert not [message for title, message in alerts if title == 'Erro']
    window.close()


@pytest.mark.parametrize('operation', ['rename', 'switch', 'link', 'create', 'remove', 'remove_last'])
def test_config_save_failure_preserves_active_state(tmp_path, monkeypatch, qt_app, operation):
    from PySide6.QtWidgets import QFileDialog
    from prometheus.storage.database import open_bank
    from prometheus.storage import config as storage_config
    bank = tmp_path / 'a.db'; other = tmp_path / 'b.db'; created = tmp_path / 'new.db'
    for path in (bank, other):
        conn = open_bank(path, create=True); conn.close()
    disciplines = {'A': str(bank)} if operation == 'remove_last' else {'A': str(bank), 'B': str(other)}
    config = {'current_discipline': 'A', 'disciplines': disciplines}
    config_path = tmp_path / 'app_config.json'
    config_path.write_text(json.dumps(config))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *args: alerts.append((title, text)))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: True)
    window = ExamGeneratorApp()
    old_conn = window.conn
    window.selected_ids.add(123)
    monkeypatch.setattr(storage_config.os, 'replace', lambda *a: (_ for _ in ()).throw(OSError('simulated save failure')))
    monkeypatch.setattr(ExamGeneratorApp, 'get_text_prompt', lambda *a: 'Novo')
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **kw: (str(other), ''))
    monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *a, **kw: (str(created), ''))
    if operation == 'rename': window.action_rename_discipline()
    elif operation == 'switch': window.on_discipline_changed('B')
    elif operation == 'link': window.action_link_existing_database()
    elif operation == 'create': window.action_create_new_database()
    else: window.action_remove_discipline()
    assert alerts and any('configura' in text.lower() for _, text in alerts)
    assert window.config_data == config == json.loads(config_path.read_text())
    assert window.conn is old_conn
    assert old_conn.execute('SELECT 1').fetchone() == (1,)
    assert window.current_discipline == 'A' and window.db_path == str(bank)
    assert window.cb_disciplines.currentText() == 'A'
    assert window.txt_db_path.text() == str(bank)
    assert window.selected_ids == {123}
    if operation == 'create':
        assert created.exists() and any(str(created) in text for _, text in alerts)
    window.close()


def test_relink_save_failure_preserves_connection_and_configuration(tmp_path, monkeypatch, qt_app):
    from PySide6.QtWidgets import QFileDialog
    from prometheus.storage.database import open_bank
    from prometheus.storage import config as storage_config
    a, found, missing = (tmp_path / name for name in ('a.db', 'found.db', 'missing.db'))
    for path in (a, found):
        conn = open_bank(path, create=True); conn.close()
    config = {'current_discipline': 'A', 'disciplines': {'A': str(a), 'B': str(missing)}}
    config_path = tmp_path / 'app_config.json'; config_path.write_text(json.dumps(config))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    alerts = []
    monkeypatch.setattr(ExamGeneratorApp, 'show_alert', lambda self, title, text, *a: alerts.append(text))
    window = ExamGeneratorApp(); old_conn = window.conn; window.selected_ids.add(123)
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: next(b for b in self.buttons() if b.text() == 'Localizar arquivo').click())
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **kw: (str(found), ''))
    monkeypatch.setattr(storage_config.os, 'replace', lambda *a: (_ for _ in ()).throw(OSError('failed')))
    window.on_discipline_changed('B')
    assert alerts and 'configura' in alerts[-1].lower()
    assert window.config_data == config == json.loads(config_path.read_text())
    assert window.conn is old_conn and old_conn.execute('SELECT 1').fetchone() == (1,)
    assert (window.current_discipline, window.db_path, window.cb_disciplines.currentText()) == ('A', str(a), 'A')
    assert window.selected_ids == {123}
    window.close()


@pytest.mark.parametrize('choice', ['Remover da lista', 'Cancelar'])
def test_removing_active_with_missing_next_bank_keeps_ui_consistent(tmp_path, monkeypatch, qt_app, choice):
    from prometheus.storage.database import open_bank
    a, missing = tmp_path / 'a.db', tmp_path / 'missing.db'
    conn = open_bank(a, create=True); conn.close()
    config = {'current_discipline': 'A', 'disciplines': {'A': str(a), 'B': str(missing)}}
    config_path = tmp_path / 'app_config.json'; config_path.write_text(json.dumps(config))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: True)
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: next(b for b in self.buttons() if b.text() == choice).click())
    window = ExamGeneratorApp(); old_conn = window.conn; window.selected_ids.add(123)
    window.action_remove_discipline()
    assert window.current_discipline == 'A' and window.db_path == str(a)
    assert window.conn is old_conn and old_conn.execute('SELECT 1').fetchone() == (1,)
    assert window.selected_ids == {123}
    expected = {'A': str(a)} if choice == 'Remover da lista' else config['disciplines']
    assert window.config_data['disciplines'] == expected
    assert json.loads(config_path.read_text()) == window.config_data
    assert [window.cb_disciplines.itemText(i) for i in range(window.cb_disciplines.count())] == list(expected)
    assert window.cb_disciplines.currentText() == 'A'
    window.close()


def test_removing_active_then_relinking_missing_next_bank(tmp_path, monkeypatch, qt_app):
    from PySide6.QtWidgets import QFileDialog
    from prometheus.storage.database import open_bank
    a, b, missing = (tmp_path / name for name in ('a.db', 'b.db', 'missing.db'))
    for path in (a, b):
        conn = open_bank(path, create=True); conn.close()
    config_path = tmp_path / 'app_config.json'
    config_path.write_text(json.dumps({'current_discipline': 'A', 'disciplines': {'A': str(a), 'B': str(missing)}}))
    monkeypatch.setattr(ExamGeneratorApp, 'get_data_dir', lambda self: str(tmp_path))
    monkeypatch.setattr(ExamGeneratorApp, 'show_confirm', lambda *a: True)
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: next(btn for btn in self.buttons() if btn.text() == 'Localizar arquivo').click())
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *a, **kw: (str(b), ''))
    window = ExamGeneratorApp()
    window.action_remove_discipline()
    expected = {'current_discipline': 'B', 'disciplines': {'B': str(b)}}
    assert window.config_data == expected == json.loads(config_path.read_text())
    assert window.current_discipline == 'B' and window.db_path == str(b)
    assert window.cb_disciplines.count() == 1 and window.cb_disciplines.currentText() == 'B'
    assert window.conn.execute('SELECT 1').fetchone() == (1,)
    assert a.exists()
    window.close()
