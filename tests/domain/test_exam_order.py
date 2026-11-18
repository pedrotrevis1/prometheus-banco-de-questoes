from prometheus.domain.exam_order import ExamOrder


def test_order_tracks_selection_without_losing_user_order():
    order = ExamOrder()
    assert order.synchronize({3, 1, 2}) == (1, 2, 3)
    assert order.move(2, -1) == 1
    assert order.synchronize({2, 3, 5}) == (3, 2, 5)
    assert order.move(0, -1) == 0


def test_preview_does_not_mutate_order_before_guard():
    order = ExamOrder()
    order.ids = [2, 1]
    assert order.preview({1, 3}) == (1, 3)
    assert order.ids == [2, 1]
