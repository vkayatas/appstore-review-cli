"""Tests for appinsight.compare - multi-app comparison logic."""

import pytest

from appinsight.scraper import Review
from appinsight.compare import _top_keywords, _categorize_complaints


def _make_review(**overrides) -> Review:
    defaults = {
        "id": "1",
        "title": "Bad app",
        "content": "Does not work",
        "rating": 2,
        "author": "user1",
        "date": "2025-06-01T00:00:00+00:00",
        "version": "1.0",
        "vote_sum": 0,
        "vote_count": 0,
    }
    defaults.update(overrides)
    return Review(**defaults)


@pytest.fixture
def crash_reviews():
    return [
        _make_review(id="1", title="Crashes constantly", content="App crashes every time I open it"),
        _make_review(id="2", title="So slow", content="Very slow and laggy since the update"),
        _make_review(id="3", title="Broken", content="Login doesn't work, keeps showing error"),
        _make_review(id="4", title="Missing feature", content="I wish it had dark mode, please add it"),
        _make_review(id="5", title="Freeze", content="Screen freezes when loading notifications"),
    ]


class TestCategorizeComplaints:
    def test_detects_crashes(self, crash_reviews):
        cats = _categorize_complaints(crash_reviews)
        assert "Crashes/Freezes" in cats
        assert cats["Crashes/Freezes"] >= 2

    def test_detects_performance(self, crash_reviews):
        cats = _categorize_complaints(crash_reviews)
        assert "Performance" in cats

    def test_detects_missing_features(self, crash_reviews):
        cats = _categorize_complaints(crash_reviews)
        assert "Missing Features" in cats

    def test_detects_login(self, crash_reviews):
        cats = _categorize_complaints(crash_reviews)
        assert "Login/Auth" in cats

    def test_sorted_by_count(self, crash_reviews):
        cats = _categorize_complaints(crash_reviews)
        counts = list(cats.values())
        assert counts == sorted(counts, reverse=True)

    def test_empty_reviews(self):
        assert _categorize_complaints([]) == {}


class TestTopKeywords:
    def test_returns_common_words(self, crash_reviews):
        top = _top_keywords(crash_reviews, n=5)
        words = [w for w, _ in top]
        assert len(top) == 5
        # "crash" or "slow" or "work" should appear
        assert any(w in words for w in ["crash", "crashes", "slow"])

    def test_excludes_stop_words(self, crash_reviews):
        top = _top_keywords(crash_reviews, n=20)
        words = [w for w, _ in top]
        assert "the" not in words
        assert "and" not in words

    def test_empty_reviews(self):
        assert _top_keywords([], n=5) == []

    def test_short_words_excluded(self):
        r = _make_review(title="", content="it is ok no")
        top = _top_keywords([r], n=10)
        words = [w for w, _ in top]
        # "it", "is", "ok", "no" are all <= 2 chars or stop words
        assert len(words) == 0
