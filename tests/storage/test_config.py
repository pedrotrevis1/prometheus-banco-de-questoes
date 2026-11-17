import json
import os
from unittest.mock import patch

import pytest
from prometheus.storage.config import load_config, save_config


def test_defaults_and_invalid_config(tmp_path):
    expected = {'current_discipline': 'Biologia', 'disciplines': {'Biologia': str(tmp_path / 'biologia.db')}}
    assert load_config(str(tmp_path)) == expected
    (tmp_path / 'app_config.json').write_text('{broken')
    assert load_config(str(tmp_path)) == expected


def test_load_normalizes_and_falls_back_to_existing_discipline(tmp_path):
    (tmp_path / 'app_config.json').write_text(json.dumps({'current_discipline': 'absent', 'disciplines': {' Bio ': ' /bank.db ', '': ''}}))
    assert load_config(str(tmp_path)) == {'current_discipline': 'Bio', 'disciplines': {'Bio': '/bank.db'}}


def test_save_roundtrip_and_failed_replace_preserves_original(tmp_path):
    original = {'current_discipline': 'Bio', 'disciplines': {'Bio': '/bank.db'}}
    save_config(original, str(tmp_path))
    assert load_config(str(tmp_path)) == original
    with patch('prometheus.storage.config.os.replace', side_effect=OSError('failed')):
        with pytest.raises(OSError):
            save_config({'other': True}, str(tmp_path))
    assert load_config(str(tmp_path)) == original
    assert sorted(os.listdir(tmp_path)) == ['app_config.json']


def test_relink_and_remove_last_discipline_roundtrip(tmp_path):
    from prometheus.storage.config import relink_discipline, remove_discipline
    config = {'current_discipline': 'Bio', 'disciplines': {'Bio': '/old.db'}}
    relink_discipline(config, 'Bio', '/new.db')
    assert config['disciplines']['Bio'] == '/new.db'
    remove_discipline(config, 'Bio')
    save_config(config, str(tmp_path))
    assert load_config(str(tmp_path)) == {'current_discipline': '', 'disciplines': {}}


def test_unique_names_rename_and_remove_keep_paths():
    from prometheus.storage.config import add_discipline, rename_discipline, remove_discipline, DuplicateDisciplineError
    config = {'current_discipline': 'Biologia', 'disciplines': {'Biologia': '/bio.db'}}
    with pytest.raises(DuplicateDisciplineError):
        add_discipline(config, ' biOLOGIA ', '/other.db')
    add_discipline(config, ' Física ', '/physics.db')
    with pytest.raises(DuplicateDisciplineError):
        rename_discipline(config, 'Física', ' biologia ')
    rename_discipline(config, 'Biologia', 'BIOLOGIA')
    assert config['current_discipline'] == 'BIOLOGIA'
    assert config['disciplines']['BIOLOGIA'] == '/bio.db'
    remove_discipline(config, 'BIOLOGIA')
    assert config == {'current_discipline': 'Física', 'disciplines': {'Física': '/physics.db'}}
