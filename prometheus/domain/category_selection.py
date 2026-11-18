"""Reconcile category selections after a hierarchy changes."""
from dataclasses import replace


def surviving_category_ids(selected_ids, available_ids):
    available = set(available_ids)
    return tuple(value for value in selected_ids if value in available)


def reconcile_applied_categories(filters, available_ids):
    if not hasattr(filters, 'category_ids'):
        return filters
    return replace(filters, category_ids=surviving_category_ids(filters.category_ids, available_ids))
