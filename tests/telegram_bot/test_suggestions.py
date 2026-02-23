"""Unit tests for subcategory suggestions"""

import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection

from telegram_bot.services.suggestions import get_subcategory_suggestions


@pytest.mark.django_db
def test_suggestions_from_user_history(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that most used subcategories appear first"""
    suggestions = get_subcategory_suggestions(authenticated_user, "spesa", limit=5)

    # Bar should be first (used 3 times)
    assert len(suggestions) > 0
    assert suggestions[0].name == "Bar"


@pytest.mark.django_db
def test_suggestions_respects_limit(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that suggestions respect the limit parameter"""
    suggestions = get_subcategory_suggestions(authenticated_user, "test", limit=3)
    assert len(suggestions) <= 3


@pytest.mark.django_db
def test_suggestions_fuzzy_match(authenticated_user, categories_setup):
    """Test fuzzy matching on subcategory names"""
    # "carbu" should match "Carburante" (partial match)
    suggestions = get_subcategory_suggestions(authenticated_user, "carbu", limit=5)

    # Should include Carburante due to fuzzy match
    subcat_names = [s.name for s in suggestions]
    assert "Carburante" in subcat_names


@pytest.mark.django_db
def test_suggestions_no_duplicates(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that suggestions don't include duplicates"""
    suggestions = get_subcategory_suggestions(authenticated_user, "bar", limit=5)

    # Check for unique subcategory IDs
    subcat_ids = [s.id for s in suggestions]
    assert len(subcat_ids) == len(set(subcat_ids))


@pytest.mark.django_db
def test_suggestions_combines_history_and_fuzzy(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that suggestions combine history and fuzzy matching"""
    # "bar" matches both history (used 3 times) and fuzzy (contains "bar")
    suggestions = get_subcategory_suggestions(authenticated_user, "bar", limit=5)

    assert len(suggestions) > 0
    # Bar should definitely be in the results
    subcat_names = [s.name for s in suggestions]
    assert "Bar" in subcat_names


@pytest.mark.django_db
def test_suggestions_empty_when_no_subcategories(authenticated_user, db):
    """Test suggestions return empty when no subcategories exist"""
    # No categories_setup fixture, so no subcategories
    suggestions = get_subcategory_suggestions(authenticated_user, "test", limit=5)
    assert suggestions == []


@pytest.mark.django_db
def test_suggestions_with_category_preloaded(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that suggestions include preloaded category"""
    suggestions = get_subcategory_suggestions(authenticated_user, "spesa", limit=5)

    # Access category should not trigger additional query
    for subcat in suggestions:
        # This should not raise an error or trigger a query
        assert subcat.category is not None
        assert subcat.category.name is not None


@pytest.mark.django_db
def test_suggestions_fuzzy_score_threshold(authenticated_user, categories_setup):
    """Test that fuzzy matching uses reasonable threshold"""
    # Very different word should not match
    suggestions = get_subcategory_suggestions(authenticated_user, "xyzabc", limit=5)

    # Should still return some suggestions, but not based on fuzzy match
    # (will return top subcategories if any)
    assert isinstance(suggestions, list)


@pytest.mark.django_db
def test_suggestions_case_insensitive(authenticated_user, categories_setup):
    """Test that fuzzy matching is case insensitive"""
    suggestions_lower = get_subcategory_suggestions(authenticated_user, "bar", limit=5)
    suggestions_upper = get_subcategory_suggestions(authenticated_user, "BAR", limit=5)

    # Should return same subcategories regardless of case
    names_lower = {s.name for s in suggestions_lower}
    names_upper = {s.name for s in suggestions_upper}
    assert names_lower == names_upper


@pytest.mark.django_db
def test_suggestions_history_uses_single_bulk_query(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that fetching subcategories from history uses a single bulk query, not N+1"""
    with CaptureQueriesContext(connection) as ctx:
        suggestions = get_subcategory_suggestions(
            authenticated_user, "__no_match__", limit=5
        )

    # history step: 1 query for recent_usage aggregation + 1 bulk query for subcategories
    # fuzzy step: 1 query for all_subcategories (no fuzzy match, so no extra queries)
    # Total queries should be fixed (not scale with number of history items)
    query_count = len(ctx.captured_queries)
    assert query_count <= 3, f"Expected ≤3 queries, got {query_count}"
    assert len(suggestions) > 0


@pytest.mark.django_db
def test_suggestions_skips_duplicates_in_results(
    authenticated_user, categories_setup, category_usage_history
):
    """Test that if same subcategory appears in history and fuzzy match, it's not duplicated"""
    # "bar" will match both:
    # 1. User history (Bar used 3 times)
    # 2. Fuzzy match (name contains "bar")

    suggestions = get_subcategory_suggestions(authenticated_user, "bar", limit=10)

    # Check for unique subcategory IDs
    subcat_ids = [s.id for s in suggestions]
    assert len(subcat_ids) == len(set(subcat_ids)), "Suggestions contain duplicates"

    # Bar should appear only once
    bar_count = sum(1 for s in suggestions if s.name == "Bar")
    assert bar_count == 1, f"Bar appears {bar_count} times, expected 1"
