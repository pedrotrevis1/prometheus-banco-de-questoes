"""Capture and reconstruct generated versions using alternative positions."""
from dataclasses import replace


def arrangement_configuration(question_ids, settings):
    """Identify only the choices that intentionally change version orders."""
    return {'question_ids': list(question_ids),
            'settings': {key: settings.get(key) for key in
                         ('multiple', 'count', 'shuffle_questions', 'shuffle_alternatives')}}


def capture_arrangements(source, versions):
    originals = {question.id: question for question in source}
    result = []
    for version in versions:
        arrangement = []
        for question in version:
            original = originals[question.id]
            unused = list(range(len(original.alternatives)))
            positions = []
            for alternative in question.alternatives:
                index = next((i for i in unused if original.alternatives[i] == alternative), None)
                if index is None:
                    raise ValueError('Generated alternative does not match its source')
                positions.append(index)
                unused.remove(index)
            # Identical alternatives can occupy different positions; ensure the
            # correct original position maps to the generated correct position.
            if original.kind == 'multiple_choice':
                correct = 'ABCDE'.index(original.answer)
                target = 'ABCDE'.index(question.answer)
                current = positions.index(correct)
                if current != target:
                    if question.alternatives[current] != question.alternatives[target]:
                        raise ValueError('Generated answer does not match its source')
                    positions[current], positions[target] = positions[target], positions[current]
            arrangement.append({'id': question.id, 'kind': question.kind, 'alternatives': positions})
        result.append(arrangement)
    return result


def restore_arrangements(source, arrangements):
    originals = {question.id: question for question in source}
    result = []
    for arrangement in arrangements:
        if len(arrangement) != len(source) or {item['id'] for item in arrangement} != set(originals):
            raise ValueError('A ordem salva não corresponde às questões atuais.')
        version = []
        for item in arrangement:
            question = originals[item['id']]
            positions = item['alternatives']
            if item['kind'] != question.kind or sorted(positions) != list(range(len(question.alternatives))):
                raise ValueError(f'A ordem salva não corresponde às alternativas atuais da questão {question.id}.')
            answer = question.answer
            if question.kind == 'multiple_choice':
                answer = 'ABCDE'[positions.index('ABCDE'.index(question.answer))]
            version.append(replace(question, alternatives=tuple(question.alternatives[i] for i in positions), answer=answer))
        result.append(version)
    return result
