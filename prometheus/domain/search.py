"""Legacy search criteria independent of the user interface."""
from dataclasses import dataclass

from prometheus.domain.school_years import parse_question_year_values


@dataclass(frozen=True)
class SearchFilters:
    difficulties: tuple[str, ...] = ()
    question_types: tuple[str, ...] = ()
    text: str = ''
    source: str = ''
    source_year_from: int | None = None
    source_year_to: int | None = None
    school_years: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()


def matches_legacy_filters(category, school_year, segment, filters):
    if filters.school_years and not set(filters.school_years).intersection(
        parse_question_year_values(school_year, segment)
    ):
        return False
    if filters.categories:
        tokens = [token.strip() for token in (category or '').split(';')]
        if not any(category in tokens for category in filters.categories):
            return False
    return True


class SearchViewState:
    """Selection and selected-only mode independent of Qt controls."""

    def __init__(self):
        self.selected_ids = set()
        self.selected_only = False
        self.applied = SearchFilters()
        self.page = 1

    def apply(self, filters):
        self.applied = filters
        self.selected_only = False
        self.page = 1

    def reset(self, filters):
        self.selected_ids.clear()
        self.apply(filters)

    def set_selected_only(self, checked):
        if checked and not self.selected_ids:
            return False
        self.selected_only = bool(checked)
        self.page = 1
        return True


@dataclass(frozen=True)
class PageBounds:
    page: int
    pages: int
    start: int
    end: int
    total: int


def page_bounds(total, page):
    if total < 0:
        raise ValueError('total must be nonnegative')
    pages = (total + 49) // 50
    if not pages:
        return PageBounds(0, 0, 0, 0, total)
    page = min(max(1, page), pages)
    start = (page - 1) * 50 + 1
    return PageBounds(page, pages, start, min(page * 50, total), total)
