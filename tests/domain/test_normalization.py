from prometheus.domain.normalization import (
    DIFFICULTIES, KINDS, SEGMENTS, YEARS, map_legacy, map_source_year,
    plain_text, search_text,
)


def test_upgrade_report_uses_portuguese_labels():
    from prometheus.domain.normalization import format_upgrade_report
    assert 'Nenhum valor' in format_upgrade_report([])
    report = format_upgrade_report([(5, 'assunto', 'Perdida'), (5, 'alternativa_b', '')])
    assert 'Questão 5 — Categoria: Perdida' in report
    assert 'Questão 5 — Alternativa B:' in report


def test_known_labels_and_unknown_values_are_preserved():
    assert map_legacy('Múltipla Escolha', KINDS) == ('multiple_choice', 'Múltipla Escolha')
    assert map_legacy('Fácil', DIFFICULTIES) == ('easy', 'Fácil')
    assert map_legacy('Ensino Médio', SEGMENTS) == ('medio', 'Ensino Médio')
    assert map_legacy('6º Ano', YEARS) == (('fundamental_ii', 'fundamental_6'), '6º Ano')
    assert map_legacy('Outro', YEARS) == (None, 'Outro')


def test_source_year_mapping_preserves_legacy_text():
    assert map_source_year(' 02024 ') == (2024, ' 02024 ')
    assert map_source_year('cerca de 2020') == (None, 'cerca de 2020')
    assert map_source_year(None) == (None, None)


def test_plain_text_ignores_markup_and_preserves_words_across_formatting():
    rich = '<html><head><style>font { color: red }</style></head><body><p>Revolução <b>Francesa</b></p><p>A &amp; B</p></body></html>'
    assert plain_text(rich) == 'Revolução Francesa A & B'
    assert search_text(plain_text(rich)) == 'revolucao francesa a & b'
    assert 'font' not in search_text(plain_text(rich))


def test_inline_markup_does_not_split_words():
    assert plain_text('<p>revo<b>lução</b></p>') == 'revolução'
