from prometheus.domain.card_data import card_metadata
from prometheus.domain.school_years import format_question_year_info


def test_card_metadata_preserves_values_and_fallbacks():
    years = format_question_year_info('1º Ano; 2º Ano', 'Fundamental')
    fields = card_metadata(7, 'A < B; C & "D"', 'Médio', years, 'Dissertativa', ' ', '', None)
    assert fields == {'id': '7', 'years': 'Fundamental — 1º Ano, 2º Ano',
                      'difficulty': 'Médio', 'kind': 'Dissertativa',
                      'subject': 'A < B,  C & "D"', 'source': 'Não informada',
                      'source_year': 'Não informado', 'modified': 'Não informada'}


def test_segment_only_and_multiple_segments_are_preserved():
    for years, segments in [('', 'Médio'), ('1ª Série; 2ª Série', 'Fundamental; Médio')]:
        label = format_question_year_info(years, segments)
        assert card_metadata(1, '', '', label, '', '', '', None)['years'] == label


def test_card_actions_move_below_when_width_is_insufficient():
    from prometheus.domain.card_data import actions_below_metadata
    assert actions_below_metadata(399, 260, 130, 10)
    assert not actions_below_metadata(400, 260, 130, 10)


def test_long_tokens_can_wrap_without_changing_their_visible_content():
    from prometheus.domain.card_data import wrap_long_tokens
    source = 'A' * 80 + ' & <fim>'
    result = wrap_long_tokens(source)
    assert '\u200b' in result
    assert result.replace('\u200b', '') == source
