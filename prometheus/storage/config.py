"""Read and safely write application configuration."""
import json
import logging
import os
import platform
import tempfile


def data_dir():
    if platform.system() == "Darwin":
        path = os.path.expanduser("~/Library/Application Support/GeradorProvasApp")
    else:
        path = os.path.expanduser("~/.gerador_provas_app")
    os.makedirs(path, exist_ok=True)
    return path


def load_config(directory=None):
    directory = directory or data_dir()
    config_file = os.path.join(directory, 'app_config.json')
    default = {'current_discipline': 'Biologia',
               'disciplines': {'Biologia': os.path.join(directory, 'biologia.db')}}
    if os.path.exists(config_file):
        try:
            with open(config_file, encoding='utf-8') as f:
                config = json.load(f)
            if not isinstance(config, dict):
                return default
            disciplines = config.get('disciplines')
            if not isinstance(disciplines, dict):
                return default
            if not disciplines:
                return {'current_discipline': '', 'disciplines': {}}
            valid = {name.strip(): path.strip() for name, path in disciplines.items()
                     if isinstance(name, str) and name.strip()
                     and isinstance(path, str) and path.strip()}
            if not valid:
                return default
            current = config.get('current_discipline')
            if not isinstance(current, str) or current not in valid:
                current = next(iter(valid))
            return {'current_discipline': current, 'disciplines': valid}
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            logging.getLogger('prometheus.config').exception('Failed to read configuration %s', config_file)
            return default
    return default


def save_config(config, directory=None):
    directory = directory or data_dir()
    fd, temporary_path = tempfile.mkstemp(prefix='.app_config_', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        os.replace(temporary_path, os.path.join(directory, 'app_config.json'))
    finally:
        if os.path.exists(temporary_path):
            os.unlink(temporary_path)


def relink_discipline(config, name, path):
    if name not in config['disciplines']:
        raise KeyError(name)
    config['disciplines'][name] = str(path)


def remove_discipline(config, name):
    del config['disciplines'][name]
    if config['current_discipline'] == name:
        config['current_discipline'] = next(iter(config['disciplines']), '')


class DuplicateDisciplineError(ValueError):
    pass


def _validated_name(config, name, excluding=None):
    name = name.strip()
    if not name:
        raise ValueError('empty name')
    if any(existing != excluding and existing.strip().casefold() == name.casefold()
           for existing in config['disciplines']):
        raise DuplicateDisciplineError(name)
    return name


def add_discipline(config, name, path):
    name = _validated_name(config, name)
    config['disciplines'][name] = str(path)
    return name


def rename_discipline(config, old_name, new_name):
    if old_name not in config['disciplines']:
        raise KeyError(old_name)
    new_name = _validated_name(config, new_name, excluding=old_name)
    config['disciplines'] = {new_name if name == old_name else name: path
                             for name, path in config['disciplines'].items()}
    if config['current_discipline'] == old_name:
        config['current_discipline'] = new_name
    return new_name


def copy_config(config):
    """Make an independent candidate for an atomic configuration update."""
    return {'current_discipline': config['current_discipline'],
            'disciplines': config['disciplines'].copy()}
