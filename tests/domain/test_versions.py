import random
import unittest

from prometheus.domain.versions import make_version_questions


class VersionTests(unittest.TestCase):
    def question(self, options=None, answer='C', kind='Múltipla Escolha'):
        return [42, None, None, kind, None, *(options or ['a', 'b', 'c', 'd', 'e']), answer]

    def test_answer_follows_content(self):
        random.seed(42)
        original = self.question()
        result = make_version_questions([original], True, True)[0]
        self.assertEqual(result[5 + 'ABCDE'.index(result[10])], 'c')
        self.assertCountEqual(result[5:10], original[5:10])
        self.assertNotEqual(result[5:10], original[5:10])
        self.assertEqual(original[10], 'C')

    def test_essay_untouched(self):
        question = self.question(kind='Dissertativa')
        self.assertEqual(make_version_questions([question], False, True), [question])

    def test_invalid_answer(self):
        with self.assertRaises(ValueError):
            make_version_questions([self.question(answer='Z')], False, True)

    def test_identical_alternatives(self):
        result = make_version_questions([self.question(['a'] * 5)], False, True)[0]
        self.assertEqual(result[5:10], ['a'] * 5)
        self.assertIn(result[10], 'ABCDE')
