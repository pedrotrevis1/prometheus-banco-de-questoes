from prometheus.domain.exam_session import exam_draft, generation_defaults, guard_allows, is_dirty
from prometheus.domain.exam_order import ExamOrder


def test_defaults_are_independent_and_draft_comparison_tracks_changes():
    settings = generation_defaults()
    assert settings == {'multiple': False, 'count': 2, 'shuffle_questions': False,
                        'shuffle_alternatives': False, 'include_answers': True, 'separate_answers': False}
    original = exam_draft((), None, settings)
    settings['count'] = 3
    assert original[2]['count'] == 2
    assert not is_dirty(None, original)
    assert not is_dirty(original, exam_draft((), None, generation_defaults()))
    assert is_dirty(original, exam_draft((1,), None, generation_defaults()))
    assert is_dirty(original, exam_draft((), 1, generation_defaults()))
    assert is_dirty(original, exam_draft((), None, settings))


def test_guard_decision_and_order_synchronization():
    assert guard_allows('discard')
    assert guard_allows('save', saved=True)
    assert not guard_allows('save', saved=False)
    assert not guard_allows('cancel')
    order = ExamOrder()
    order.ids = [2, 1]
    assert exam_draft(order.synchronize({1, 3}), None, generation_defaults())[0] == (1, 3)


def test_fresh_state_clears_shared_selection_and_order_and_resets_search():
    from prometheus.domain.exam_session import fresh_exam
    from prometheus.domain.search import SearchViewState, SearchFilters
    state = SearchViewState()
    shared = state.selected_ids
    shared.update((3, 7))
    state.set_selected_only(True)
    state.page = 3
    order = ExamOrder()
    order.ids = [7, 3]
    draft = fresh_exam(state, order, SearchFilters())
    assert state.selected_ids is shared and not shared
    assert order.ids == [] and state.page == 1 and not state.selected_only
    assert state.applied == SearchFilters()
    assert draft == ((), None, generation_defaults())
