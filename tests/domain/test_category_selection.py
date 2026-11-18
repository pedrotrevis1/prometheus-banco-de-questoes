from prometheus.domain.category_selection import reconcile_applied_categories, surviving_category_ids
from prometheus.storage.normalized_search import NormalizedSearchFilters


def test_removed_categories_are_dropped_without_replacement():
    filters = NormalizedSearchFilters(category_ids=(3, 1, 2), uncategorized=True, text='cell')
    updated = reconcile_applied_categories(filters, {1, 2, 4})
    assert updated.category_ids == (1, 2)
    assert updated.uncategorized and updated.text == 'cell'
    assert surviving_category_ids((3,), {1, 2}) == ()
