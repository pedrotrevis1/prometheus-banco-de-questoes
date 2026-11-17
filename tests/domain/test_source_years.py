import pytest

from prometheus.domain.source_years import parse_stored_year, validate_year_range, YearRangeError


@pytest.mark.parametrize(('text', 'expected'), [
    ('', None), ('  ', None), ('1', 1), ('9999', 9999), (' 2022 ', 2022),
    ('00002022', 2022), ('0000', None), ('0', None), ('10000', None),
    ('2022/2023', None), ('c. 2022', None), ('s/d', None),
    ('-2022', None), ('+2022', None), ('2022.5', None), ('２０２２', None),
    ('9' * 10000, None), (None, None),
])
def test_stored_year_is_strict_and_bounded(text, expected):
    assert parse_stored_year(text) == expected


def test_optional_and_inclusive_bounds():
    assert validate_year_range('', '') == (None, None)
    assert validate_year_range(' 2022 ', '') == (2022, None)
    assert validate_year_range('', '2022') == (None, 2022)
    assert validate_year_range('0001', '9999') == (1, 9999)
    assert validate_year_range('2022', '2022') == (2022, 2022)


@pytest.mark.parametrize('text', ['202x', '2022.5', '-2022', '0', '10000', '２０２２', '9' * 10000])
def test_invalid_input_reports_field(text):
    with pytest.raises(YearRangeError) as exc:
        validate_year_range(text, '')
    assert exc.value.code == 'invalid' and exc.value.field == 'from'
    with pytest.raises(YearRangeError) as exc:
        validate_year_range('', text)
    assert exc.value.code == 'invalid' and exc.value.field == 'to'


def test_inverted_range_has_distinct_error():
    with pytest.raises(YearRangeError) as exc:
        validate_year_range('2024', '2022')
    assert exc.value.code == 'inverted'
