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


def test_protected_alternatives_are_not_shuffled():
    from prometheus.domain.versions import make_version_questions
    row = [1, None, None, 'Múltipla Escolha', 'prompt', 'a', 'b', 'c', 'd', 'e', 'C', '', '', '', '', None, 1]
    result = make_version_questions([row], False, True)[0]
    assert result[5:11] == row[5:11]


def test_empty_or_multiletter_answer_is_rejected():
    import pytest
    from prometheus.domain.versions import make_version_questions
    for answer in ('', 'AB'):
        row = [1, None, None, 'Múltipla Escolha', 'prompt', 'a', 'b', 'c', 'd', 'e', answer]
        with pytest.raises(ValueError):
            make_version_questions([row], False, True)


def test_versions_are_distinct_and_preserve_chosen_order_when_not_shuffled():
    import random
    from prometheus.domain.versions import generate_versions
    rows = [[1, None, None, 'Múltipla Escolha', 'first', 'a', 'b', 'c', 'd', 'e', 'C'],
            [2, None, None, 'Dissertativa', 'second', '', '', '', '', '', 'answer']]
    versions = generate_versions(rows, 5, False, True, rng=random.Random(42))
    assert all([q[0] for q in version] == [1, 2] for version in versions)
    assert len({tuple(v[0][5:11]) for v in versions}) == 5
    assert all(v[0][5 + 'ABCDE'.index(v[0][10])] == 'c' for v in versions)


def test_impossible_distinct_versions_are_reported():
    import random
    import pytest
    from prometheus.domain.versions import generate_versions, DistinctVersionsUnavailable
    row = [1, None, None, 'Múltipla Escolha', 'prompt', 'a', 'b', 'c', 'd', 'e', 'C', '', '', '', '', None, 1]
    with pytest.raises(DistinctVersionsUnavailable):
        generate_versions([row], 2, False, True, rng=random.Random(42))


def test_invalid_answer_is_rejected_even_without_shuffling():
    import pytest
    from prometheus.domain.versions import generate_versions
    row = [1, None, None, 'Múltipla Escolha', 'prompt', 'a', 'b', 'c', 'd', 'e', '']
    with pytest.raises(ValueError, match='questão 1'):
        generate_versions([row], 1, False, False)


def test_identical_visible_questions_cannot_form_distinct_ordered_versions():
    import pytest
    from prometheus.domain.versions import generate_versions, DistinctVersionsUnavailable
    first = [1, None, None, 'Dissertativa', 'igual', '', '', '', '', '', '']
    second = [2, None, None, 'Dissertativa', 'igual', '', '', '', '', '', '']
    class NoShuffle:
        def shuffle(self, values):
            raise AssertionError('An impossible case should be detected before random attempts')
    with pytest.raises(DistinctVersionsUnavailable):
        generate_versions([first, second], 2, True, False, rng=NoShuffle())


def test_distinct_generation_does_not_depend_on_random_luck():
    from prometheus.domain.versions import generate_versions
    class NoShuffle:
        def shuffle(self, values): pass
    row = [1, None, None, 'Múltipla Escolha', 'questão', 'a', 'b', 'c', 'd', 'e', 'C']
    versions = generate_versions([row], 5, False, True, rng=NoShuffle())
    assert len({tuple(version[0][5:10]) for version in versions}) == 5
    assert all(version[0][5 + 'ABCDE'.index(version[0][10])] == 'c' for version in versions)
