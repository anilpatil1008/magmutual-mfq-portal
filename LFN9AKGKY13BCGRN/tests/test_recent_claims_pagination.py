from __future__ import annotations

from components.tables import _recent_claims_pagination_items


def _labels(current_page: int, total_pages: int) -> list[str]:
    return [str(item) for item in _recent_claims_pagination_items(current_page, total_pages)]


def test_recent_claims_pager_starts_with_first_five_pages_and_icons():
    assert _labels(1, 12) == ["first", "prev", "1", "2", "3", "4", "5", "....", "next", "last"]


def test_recent_claims_pager_centers_five_quick_pages_for_page_four():
    assert _labels(4, 12) == ["first", "prev", ".", "2", "3", "4", "5", "6", "....", "next", "last"]


def test_recent_claims_pager_centers_five_quick_pages_for_page_six():
    assert _labels(6, 12) == ["first", "prev", "..", "4", "5", "6", "7", "8", "....", "next", "last"]


def test_recent_claims_pager_centers_five_quick_pages_for_page_eight():
    assert _labels(8, 12) == ["first", "prev", "..", "6", "7", "8", "9", "10", "....", "next", "last"]


def test_recent_claims_pager_limits_to_available_pages():
    assert _labels(1, 3) == ["first", "prev", "1", "2", "3", "next", "last"]
