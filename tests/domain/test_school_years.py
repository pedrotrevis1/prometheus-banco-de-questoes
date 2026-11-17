import unittest
from prometheus.domain.school_years import parse_question_year_values, format_question_year_info


class SchoolYearTests(unittest.TestCase):
    def test_semicolon_and_empty(self):
        self.assertEqual(parse_question_year_values(' 1º Ano ; 2º Ano; '), ['1º Ano', '2º Ano'])
        self.assertEqual(parse_question_year_values(''), [])

    def test_legacy(self):
        self.assertEqual(parse_question_year_values('{"level":"Ensino Médio","years":["1", "2"]}'), ['1ª Série', '2ª Série'])
        self.assertEqual(parse_question_year_values('{"level":"Ensino Fundamental","years":["3"]}'), ['3º Ano'])

    def test_format(self):
        self.assertEqual(format_question_year_info('1º Ano; 2º Ano', 'Fundamental'), 'Fundamental — 1º Ano, 2º Ano')
        self.assertEqual(format_question_year_info('1º Ano', ''), '1º Ano')
        self.assertEqual(format_question_year_info('', 'Médio'), 'Médio')
