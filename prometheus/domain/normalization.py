"""Lossless legacy value mapping and text normalization for schema upgrades."""
from html.parser import HTMLParser
import re
import unicodedata

from prometheus.domain.source_years import parse_stored_year


KINDS = {'Múltipla Escolha': 'multiple_choice', 'Dissertativa': 'essay'}
DIFFICULTIES = {'Fácil': 'easy', 'Médio': 'medium', 'Difícil': 'hard'}
SEGMENTS = {'Ensino Fundamental': 'fundamental_ii', 'Ensino Médio': 'medio'}
YEARS = {
    **{f'{year}º Ano': ('fundamental_ii', f'fundamental_{year}') for year in range(6, 10)},
    **{f'{year}ª Série': ('medio', f'medio_{year}') for year in range(1, 4)},
}


def map_legacy(value, mapping):
    """Return a known code and always retain the original value for recovery."""
    return mapping.get(value), value


def map_source_year(value):
    """Apply the existing range-filter interpretation without losing raw text."""
    return parse_stored_year(value), value


class _TextParser(HTMLParser):
    BLOCKS = frozenset(('p', 'div', 'br', 'li', 'tr', 'td', 'th', 'hr',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6'))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('head', 'style', 'script'):
            self.hidden += 1
        elif not self.hidden and tag in self.BLOCKS:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('head', 'style', 'script') and self.hidden:
            self.hidden -= 1
        elif not self.hidden and tag in self.BLOCKS:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    parser = _TextParser()
    parser.feed(value or '')
    parser.close()
    return re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()


def search_text(value):
    decomposed = unicodedata.normalize('NFD', value or '').casefold()
    return ''.join(char for char in decomposed if unicodedata.category(char) != 'Mn')


def format_upgrade_report(rows):
    if not rows:
        return 'Atualização concluída. Nenhum valor não reconhecido foi encontrado.'
    labels = {'assunto': 'Categoria', 'tipo': 'Tipo', 'dificuldade': 'Dificuldade',
              'segmento': 'Segmento', 'ano_sugerido': 'Ano escolar',
              'ano_origem': 'Ano da fonte', 'gabarito': 'Gabarito'}
    def label(field):
        if field.startswith('alternativa_'):
            return 'Alternativa ' + field.removeprefix('alternativa_').upper()
        return labels.get(field, field)
    return ('Atualização concluída. Os seguintes valores precisam de revisão:\n\n' +
            '\n'.join(f'Questão {question_id} — {label(field)}: {value}'
                      for question_id, field, value in rows))
