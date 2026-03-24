"""Tests for appinsight.filters - rating, keyword, date, version filters + sorting."""

from datetime import datetime, timezone, timedelta

import pytest

from appinsight.scrapers.appstore import Review
from appinsight.output.filters import (
    by_rating,
    by_keywords,
    by_days,
    by_version,
    sort_reviews,
    apply_filters,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_review(**overrides) -> Review:
    """Helper to create a Review with sensible defaults."""
    defaults = {
        "id": "1",
        "title": "Great app",
        "content": "Works well",
        "rating": 3,
        "author": "user1",
        "date": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "vote_sum": 0,
        "vote_count": 0,
    }
    defaults.update(overrides)
    return Review(**defaults)


@pytest.fixture
def sample_reviews():
    now = datetime.now(timezone.utc)
    return [
        _make_review(id="1", rating=1, title="Terrible", content="Crashes constantly",
                     date=(now - timedelta(days=5)).isoformat(), version="2.0",
                     vote_sum=10, vote_count=12),
        _make_review(id="2", rating=2, title="Bad", content="Very slow and buggy",
                     date=(now - timedelta(days=15)).isoformat(), version="2.0",
                     vote_sum=5, vote_count=6),
        _make_review(id="3", rating=3, title="OK", content="Missing some features",
                     date=(now - timedelta(days=30)).isoformat(), version="1.9",
                     vote_sum=2, vote_count=3),
        _make_review(id="4", rating=4, title="Good", content="Nice but could improve",
                     date=(now - timedelta(days=60)).isoformat(), version="1.8",
                     vote_sum=0, vote_count=1),
        _make_review(id="5", rating=5, title="Perfect", content="Love this app!",
                     date=(now - timedelta(days=90)).isoformat(), version="1.8",
                     vote_sum=20, vote_count=25),
    ]


# ---------------------------------------------------------------------------
# by_rating
# ---------------------------------------------------------------------------

class TestByRating:
    def test_max_rating_only(self, sample_reviews):
        result = by_rating(sample_reviews, max_rating=2)
        assert [r.id for r in result] == ["1", "2"]

    def test_min_and_max_rating(self, sample_reviews):
        result = by_rating(sample_reviews, max_rating=4, min_rating=3)
        assert [r.id for r in result] == ["3", "4"]

    def test_exact_rating(self, sample_reviews):
        result = by_rating(sample_reviews, max_rating=3, min_rating=3)
        assert [r.id for r in result] == ["3"]

    def test_all_ratings(self, sample_reviews):
        result = by_rating(sample_reviews, max_rating=5, min_rating=1)
        assert len(result) == 5

    def test_no_matches(self, sample_reviews):
        # min > max is illogical but should return empty
        result = by_rating(sample_reviews, max_rating=1, min_rating=5)
        assert result == []


# ---------------------------------------------------------------------------
# by_keywords
# ---------------------------------------------------------------------------

class TestByKeywords:
    def test_single_keyword(self, sample_reviews):
        result = by_keywords(sample_reviews, ["crash"])
        assert len(result) == 1
        assert result[0].id == "1"

    def test_multiple_keywords_or_logic(self, sample_reviews):
        result = by_keywords(sample_reviews, ["crash", "slow"])
        assert [r.id for r in result] == ["1", "2"]

    def test_case_insensitive(self, sample_reviews):
        result = by_keywords(sample_reviews, ["CRASH"])
        assert len(result) == 1

    def test_matches_title_too(self, sample_reviews):
        result = by_keywords(sample_reviews, ["terrible"])
        assert result[0].id == "1"

    def test_no_matches(self, sample_reviews):
        result = by_keywords(sample_reviews, ["nonexistent"])
        assert result == []

    def test_empty_keywords(self, sample_reviews):
        result = by_keywords(sample_reviews, [])
        assert result == []


# ---------------------------------------------------------------------------
# by_days
# ---------------------------------------------------------------------------

class TestByDays:
    def test_last_7_days(self, sample_reviews):
        result = by_days(sample_reviews, 7)
        assert [r.id for r in result] == ["1"]

    def test_last_20_days(self, sample_reviews):
        result = by_days(sample_reviews, 20)
        assert [r.id for r in result] == ["1", "2"]

    def test_last_365_days(self, sample_reviews):
        result = by_days(sample_reviews, 365)
        assert len(result) == 5

    def test_unparseable_date_included(self):
        r = _make_review(date="not-a-date")
        result = by_days([r], 7)
        assert len(result) == 1  # kept to avoid silent data loss


# ---------------------------------------------------------------------------
# by_version
# ---------------------------------------------------------------------------

class TestByVersion:
    def test_exact_match(self, sample_reviews):
        result = by_version(sample_reviews, "2.0")
        assert [r.id for r in result] == ["1", "2"]

    def test_no_match(self, sample_reviews):
        result = by_version(sample_reviews, "99.0")
        assert result == []


# ---------------------------------------------------------------------------
# sort_reviews
# ---------------------------------------------------------------------------

class TestSortReviews:
    def test_sort_by_date_newest_first(self, sample_reviews):
        result = sort_reviews(sample_reviews, "date")
        assert result[0].id == "1"
        assert result[-1].id == "5"

    def test_sort_by_rating_lowest_first(self, sample_reviews):
        result = sort_reviews(sample_reviews, "rating")
        assert result[0].rating == 1
        assert result[-1].rating == 5

    def test_sort_by_votes_most_helpful_first(self, sample_reviews):
        result = sort_reviews(sample_reviews, "votes")
        assert result[0].id == "5"   # vote_sum=20
        assert result[1].id == "1"   # vote_sum=10

    def test_sort_does_not_mutate_original(self, sample_reviews):
        original_ids = [r.id for r in sample_reviews]
        sort_reviews(sample_reviews, "votes")
        assert [r.id for r in sample_reviews] == original_ids


# ---------------------------------------------------------------------------
# apply_filters (integration)
# ---------------------------------------------------------------------------

class TestApplyFilters:
    def test_no_filters(self, sample_reviews):
        result = apply_filters(sample_reviews)
        assert len(result) == 5

    def test_combined_rating_and_keywords(self, sample_reviews):
        result = apply_filters(sample_reviews, max_rating=2, keywords=["slow"])
        assert len(result) == 1
        assert result[0].id == "2"

    def test_min_and_max_stars(self, sample_reviews):
        result = apply_filters(sample_reviews, min_rating=3, max_rating=3)
        assert len(result) == 1
        assert result[0].id == "3"

    def test_filters_then_sort(self, sample_reviews):
        result = apply_filters(sample_reviews, max_rating=3, sort_by="votes")
        assert result[0].id == "1"  # vote_sum=10, highest among 1-3 star

    def test_all_filters_combined(self, sample_reviews):
        result = apply_filters(
            sample_reviews,
            max_rating=2,
            days=20,
            keywords=["crash", "slow"],
            sort_by="rating",
        )
        assert [r.id for r in result] == ["1", "2"]
