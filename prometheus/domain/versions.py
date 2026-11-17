"""Create exam versions without changing stored question data."""
import itertools
import math
from collections import Counter
import random


class DistinctVersionsUnavailable(ValueError):
    """The requested number of visibly distinct versions cannot be produced."""


def make_version_questions(source_questions, shuffle_questions, shuffle_alternatives, *, rng=None, force_change=True):
    rng = rng or random
    questions = [list(question) for question in source_questions]
    if shuffle_questions:
        rng.shuffle(questions)
    if shuffle_alternatives:
        for question in questions:
            if question[3] != 'Múltipla Escolha' or (len(question) > 16 and question[16]):
                continue
            options = [(letter, question[5 + index]) for index, letter in enumerate('ABCDE')]
            correct = str(question[10] or '').strip().upper()
            if correct not in tuple('ABCDE'):
                raise ValueError(f'Gabarito inválido na questão {question[0]}.')
            original = [option for _, option in options]
            rng.shuffle(options)
            if force_change and len(set(original)) > 1 and [option for _, option in options] == original:
                for offset in range(1, len(options)):
                    candidate = options[offset:] + options[:offset]
                    if [option for _, option in candidate] != original:
                        options = candidate
                        break
            question[5:10] = [option for _, option in options]
            question[10] = 'ABCDE'[next(i for i, (letter, _) in enumerate(options) if letter == correct)]
    return questions


def _visible_signature(questions):
    return tuple((question[3], question[4], tuple(question[5:10]) if question[3] == 'Múltipla Escolha' else ())
                 for question in questions)


def _deterministic_variants(question, shuffle_alternatives):
    if not shuffle_alternatives or question[3] != 'Múltipla Escolha' or (len(question) > 16 and question[16]):
        return [list(question)]
    options = list(zip('ABCDE', question[5:10]))
    seen = set()
    result = []
    for permutation in itertools.permutations(options):
        visible = tuple(value for _, value in permutation)
        if visible in seen:
            continue
        seen.add(visible)
        candidate = list(question)
        candidate[5:10] = visible
        candidate[10] = 'ABCDE'[next(index for index, (letter, _) in enumerate(permutation) if letter == question[10])]
        result.append(candidate)
    return result


def generate_versions(source_questions, count, shuffle_questions, shuffle_alternatives, *, rng=None):
    if count < 1:
        raise ValueError('count must be positive')
    rng = rng or random
    prepared = [list(question) for question in source_questions]
    for question in prepared:
        if question[3] == 'Múltipla Escolha':
            correct = str(question[10] or '').strip().upper()
            if correct not in tuple('ABCDE'):
                raise ValueError(f'Gabarito inválido na questão {question[0]}.')
            question[10] = correct
    source_questions = prepared
    if not shuffle_questions and not shuffle_alternatives:
        return [[list(question) for question in source_questions] for _ in range(count)]
    capacity = 1
    if shuffle_questions:
        groups = Counter((_visible_signature([question])[0],
                          bool(len(question) > 16 and question[16]) if shuffle_alternatives else False)
                         for question in source_questions)
        total = 0
        for size in groups.values():
            capacity *= math.comb(total + size, size)
            total += size
            if capacity >= count:
                break
    if shuffle_alternatives:
        for question in source_questions:
            if question[3] == 'Múltipla Escolha' and not (len(question) > 16 and question[16]):
                capacity *= len(set(itertools.permutations(question[5:10])))
                if capacity >= count:
                    break
    if capacity < count:
        raise DistinctVersionsUnavailable('Não há versões distintas suficientes para as opções escolhidas.')
    versions = []
    seen = set()
    for _ in range(max(2000, min(5000, count * 40))):
        candidate = make_version_questions(source_questions, shuffle_questions, shuffle_alternatives, rng=rng, force_change=False)
        signature = _visible_signature(candidate)
        if signature not in seen:
            seen.add(signature)
            versions.append(candidate)
            if len(versions) == count:
                return versions
    # If random sampling missed possible combinations, enumerate bounded
    # alternatives and orderings before reporting failure.
    pools = []
    combination_count = 1
    for question in source_questions:
        if combination_count < count:
            variants = _deterministic_variants(question, shuffle_alternatives)
            combination_count *= len(variants)
        else:
            variants = [make_version_questions([question], False, shuffle_alternatives, rng=rng, force_change=False)[0]]
        pools.append(variants)
    orders = itertools.permutations(range(len(pools))) if shuffle_questions else [tuple(range(len(pools)))]
    attempts = 0
    for order in orders:
        for combination in itertools.product(*(pools[index] for index in order)):
            attempts += 1
            signature = _visible_signature(combination)
            if signature not in seen:
                seen.add(signature)
                versions.append([list(question) for question in combination])
                if len(versions) == count:
                    return versions
            if attempts >= max(20000, count * 40):
                raise DistinctVersionsUnavailable('Não foi possível gerar versões distintas suficientes para as opções escolhidas.')
    raise DistinctVersionsUnavailable('Não há versões distintas suficientes para as opções escolhidas.')
