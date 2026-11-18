"""Rules for the current exam draft, independent of the interface."""


def generation_defaults():
    return {'multiple': False, 'count': 2, 'shuffle_questions': False,
            'shuffle_alternatives': False, 'include_answers': True,
            'separate_answers': False}


def exam_draft(order, class_id, settings):
    return (tuple(order), class_id, dict(settings))


def is_dirty(snapshot, draft):
    return snapshot is not None and draft != snapshot


def guard_allows(choice, saved=False):
    return choice == 'discard' or (choice == 'save' and saved)


def fresh_exam(search_state, order, filters):
    search_state.reset(filters)
    order.ids.clear()
    return exam_draft((), None, generation_defaults())
