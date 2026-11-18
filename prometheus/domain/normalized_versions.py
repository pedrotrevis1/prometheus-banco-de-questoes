"""Generate exam versions from named question records."""
from dataclasses import replace
from itertools import permutations, product
import random

from prometheus.domain.versions import DistinctVersionsUnavailable


def generate_versions(questions, count, shuffle_questions, shuffle_alternatives, *, rng=None):
    if count < 1:
        raise ValueError('count must be positive')
    rng = rng or random
    for question in questions:
        if (question.kind == 'multiple_choice' and
                (len(question.answer) != 1 or question.answer not in 'ABCDE'[:len(question.alternatives)])):
            raise ValueError(f'Gabarito inválido na questão {question.id}.')
    if not shuffle_questions and not shuffle_alternatives:
        return [list(questions) for _ in range(count)]

    def variants(question):
        if question.kind != 'multiple_choice' or question.keep_alternative_order or not shuffle_alternatives:
            return [question]
        options = list(enumerate(question.alternatives))
        result, seen = [], set()
        for order in permutations(options):
            content = tuple(value for _, value in order)
            if content in seen:
                continue
            seen.add(content)
            original = 'ABCDE'.index(question.answer)
            answer = 'ABCDE'[next(index for index, (position, _) in enumerate(order) if position == original)]
            result.append(replace(question, alternatives=content, answer=answer))
        return result

    pools = [variants(question) for question in questions]
    versions, seen = [], set()
    for _ in range(max(2000, min(5000, count * 40))):
        candidate = [rng.choice(pool) for pool in pools]
        if shuffle_questions:
            rng.shuffle(candidate)
        signature = tuple((q.kind, q.statement, q.alternatives) for q in candidate)
        if signature not in seen:
            seen.add(signature)
            versions.append(candidate)
            if len(versions) == count:
                return versions
    orders = permutations(range(len(pools))) if shuffle_questions else [tuple(range(len(pools)))]
    attempts = 0
    for order in orders:
        for candidate in product(*(pools[index] for index in order)):
            attempts += 1
            signature = tuple((q.kind, q.statement, q.alternatives) for q in candidate)
            if signature not in seen:
                seen.add(signature)
                versions.append(list(candidate))
                if len(versions) == count:
                    return versions
            if attempts >= max(20000, count * 40):
                raise DistinctVersionsUnavailable('Não foi possível gerar versões distintas suficientes.')
    raise DistinctVersionsUnavailable('Não há versões distintas suficientes para as opções escolhidas.')
