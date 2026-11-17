import random


def make_version_questions(source_questions, shuffle_questions, shuffle_alternatives):
    questions = [list(question) for question in source_questions]

    if shuffle_questions:
        random.shuffle(questions)

    if shuffle_alternatives:
        for question in questions:
            if question[3] != "Múltipla Escolha":
                continue
            options = [(letter, question[5 + index]) for index, letter in enumerate("ABCDE")]
            correct_letter = str(question[10] or "").strip().upper()
            if correct_letter not in "ABCDE":
                raise ValueError(f"Gabarito inválido na questão {question[0]}.")
            original_content_order = [option for _, option in options]
            random.shuffle(options)
            if len(set(original_content_order)) > 1 and [option for _, option in options] == original_content_order:
                for offset in range(1, len(options)):
                    candidate = options[offset:] + options[:offset]
                    if [option for _, option in candidate] != original_content_order:
                        options = candidate
                        break
            question[5:10] = [option for _, option in options]
            question[10] = "ABCDE"[next(
                index for index, (original_letter, _) in enumerate(options)
                if original_letter == correct_letter
            )]

    return questions
