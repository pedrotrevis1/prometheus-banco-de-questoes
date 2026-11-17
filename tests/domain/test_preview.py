from prometheus.domain.preview import legacy_drag_height


def test_existing_drag_calculation_and_minimum():
    assert legacy_drag_height(150, 100, 60) == 250
    assert legacy_drag_height(150, -500, 60) == 60


def test_drag_uses_press_origin_and_viewport_cap():
    from prometheus.domain.preview import PreviewSizing
    state = PreviewSizing()
    state.begin_drag(150, 1000)
    assert state.drag_to(1100, 500, 100) == 250
    assert state.drag_to(1200, 500, 100) == 350
    assert state.drag_to(2000, 500, 100) == 400
    assert state.drag_to(0, 500, 100) == 60
    assert state.drag_to(2000, 100, 100) == 60


def test_manual_precedence_toggle_and_viewport_shrink():
    from prometheus.domain.preview import PreviewSizing
    state = PreviewSizing()
    assert state.fit(1000, 800, 100) == 150
    state.toggle(True)
    assert state.fit(1000, 800, 100) == 300
    state.begin_drag(300, 0)
    assert state.drag_to(250, 800, 100) == 550
    assert state.fit(2000, 800, 100) == 550
    assert state.fit(2000, 400, 100) == 300
    assert state.fit(2000, 800, 100) == 300
    state.toggle(False)
    assert state.fit(70, 800, 100) == 70
    assert state.fit(70, 800, 100) == 70
