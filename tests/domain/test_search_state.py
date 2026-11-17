from prometheus.domain.search import SearchViewState


def test_selected_view_requires_selection_and_keeps_ids():
    state = SearchViewState()
    assert not state.set_selected_only(True)
    state.selected_ids.update((1, 2))
    assert state.set_selected_only(True)
    assert state.selected_only
    assert state.set_selected_only(False)
    assert state.selected_ids == {1, 2}


def test_page_boundaries():
    from prometheus.domain.search import page_bounds
    expected = [(0, 0, 0, 0), (1, 1, 1, 1), (49, 1, 1, 49),
                (50, 1, 1, 50), (51, 2, 51, 51), (123, 3, 101, 123)]
    for total, pages, start, end in expected:
        result = page_bounds(total, 999)
        assert (result.pages, result.page, result.start, result.end) == (pages, pages, start, end)


def test_page_clamps_negative_and_first_page():
    from prometheus.domain.search import page_bounds
    assert page_bounds(123, -1).page == 1
    assert page_bounds(123, 1).end == 50


def test_applied_filters_mode_and_selection_survive_page_changes():
    from prometheus.domain.search import SearchFilters, SearchViewState
    state = SearchViewState()
    applied = SearchFilters(text='first')
    edited = SearchFilters(text='edited')
    state.apply(applied)
    state.page = 3
    assert state.applied == applied and state.applied != edited
    state.selected_ids.update((2, 101))
    assert state.set_selected_only(True)
    assert state.page == 1 and state.selected_ids == {2, 101}
    assert state.set_selected_only(False)
    assert state.page == 1 and state.applied == applied
