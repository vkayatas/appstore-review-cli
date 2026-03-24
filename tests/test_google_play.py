"""Tests for appinsight.scrapers.google_play - Google Play review mapping logic."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from appinsight.scrapers.google_play import search_play, lookup_play, fetch_play_reviews
from appinsight.scrapers.appstore import Review, AppInfo


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _gp_search_results():
    return [
        {
            "appId": None,  # Featured result - no appId
            "title": "Slack",
            "developer": "Slack Technologies",
            "score": 4.5,
        },
        {
            "appId": "com.Slack",
            "title": "Slack",
            "developer": "Slack Technologies",
            "score": 4.5,
        },
        {
            "appId": "com.Slack.intune",
            "title": "Slack for Intune",
            "developer": "Slack Technologies",
            "score": 4.2,
        },
    ]


def _gp_app_info():
    return {
        "title": "Slack",
        "developer": "SLACK TECHNOLOGIES L.L.C.",
        "score": 4.67,
        "ratings": 182000,
        "version": "26.03.30.0",
    }


def _gp_reviews_result():
    return [
        {
            "reviewId": "abc-123",
            "userName": "Alice",
            "content": "App crashes a lot",
            "score": 1,
            "thumbsUpCount": 5,
            "reviewCreatedVersion": "26.03.30.0",
            "appVersion": "26.03.30.0",
            "at": datetime(2025, 6, 15, 10, 0, 0),
        },
        {
            "reviewId": "def-456",
            "userName": "Bob",
            "content": "Slow loading",
            "score": 2,
            "thumbsUpCount": 0,
            "reviewCreatedVersion": None,
            "appVersion": "26.02.20.0",
            "at": datetime(2025, 6, 14, 8, 30, 0, tzinfo=timezone.utc),
        },
        {
            "reviewId": "abc-123",  # Duplicate
            "userName": "Alice",
            "content": "App crashes a lot",
            "score": 1,
            "thumbsUpCount": 5,
            "reviewCreatedVersion": "26.03.30.0",
            "appVersion": "26.03.30.0",
            "at": datetime(2025, 6, 15, 10, 0, 0),
        },
    ]


# ---------------------------------------------------------------------------
# search_play
# ---------------------------------------------------------------------------

class TestSearchPlay:
    @patch("appinsight.scrapers.google_play._get_gps")
    def test_returns_apps(self, mock_gps):
        gps = MagicMock()
        gps.search.return_value = _gp_search_results()
        mock_gps.return_value = gps

        results = search_play("Slack")
        assert len(results) == 2  # Skips the None appId result
        assert all(isinstance(a, AppInfo) for a in results)

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_skips_null_appid(self, mock_gps):
        gps = MagicMock()
        gps.search.return_value = _gp_search_results()
        mock_gps.return_value = gps

        results = search_play("Slack")
        app_ids = [a.app_id for a in results]
        assert None not in app_ids
        assert "com.Slack" in app_ids

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_maps_fields(self, mock_gps):
        gps = MagicMock()
        gps.search.return_value = [_gp_search_results()[1]]
        mock_gps.return_value = gps

        r = search_play("Slack")[0]
        assert r.app_id == "com.Slack"
        assert r.name == "Slack"
        assert r.developer == "Slack Technologies"
        assert r.avg_rating == 4.5


# ---------------------------------------------------------------------------
# lookup_play
# ---------------------------------------------------------------------------

class TestLookupPlay:
    @patch("appinsight.scrapers.google_play._get_gps")
    def test_returns_app_info(self, mock_gps):
        gps = MagicMock()
        gps.app.return_value = _gp_app_info()
        mock_gps.return_value = gps

        result = lookup_play("com.Slack")
        assert isinstance(result, AppInfo)
        assert result.app_id == "com.Slack"
        assert result.name == "Slack"
        assert result.rating_count == 182000

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_returns_none_on_error(self, mock_gps):
        gps = MagicMock()
        gps.app.side_effect = Exception("Not found")
        mock_gps.return_value = gps

        assert lookup_play("com.nonexistent") is None


# ---------------------------------------------------------------------------
# fetch_play_reviews
# ---------------------------------------------------------------------------

class TestFetchPlayReviews:
    @patch("appinsight.scrapers.google_play._get_gps")
    def test_returns_reviews(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.reviews.return_value = (_gp_reviews_result(), "token123")
        mock_gps.return_value = gps

        with patch("appinsight.scrapers.google_play.Sort", mock_sort, create=True):
            # Need to patch the google_play_scraper.Sort import
            import appinsight.scrapers.google_play as gp_module
            with patch.dict("sys.modules", {"google_play_scraper": gps}):
                gps.Sort = mock_sort
                reviews = fetch_play_reviews("com.Slack", pages=1)

        assert len(reviews) == 2  # 3 results but 1 is duplicate
        assert all(isinstance(r, Review) for r in reviews)

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_deduplicates(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.Sort = mock_sort
        gps.reviews.return_value = (_gp_reviews_result(), None)
        mock_gps.return_value = gps

        with patch.dict("sys.modules", {"google_play_scraper": gps}):
            reviews = fetch_play_reviews("com.Slack", pages=1)

        ids = [r.id for r in reviews]
        assert len(ids) == len(set(ids))

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_maps_fields(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.Sort = mock_sort
        gps.reviews.return_value = ([_gp_reviews_result()[1]], None)
        mock_gps.return_value = gps

        with patch.dict("sys.modules", {"google_play_scraper": gps}):
            reviews = fetch_play_reviews("com.Slack", pages=1)

        r = reviews[0]
        assert r.id == "def-456"
        assert r.author == "Bob"
        assert r.content == "Slow loading"
        assert r.rating == 2
        assert r.vote_sum == 0
        assert r.version == "26.02.20.0"
        assert r.title == ""  # Google Play has no title

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_handles_datetime_with_timezone(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.Sort = mock_sort
        gps.reviews.return_value = ([_gp_reviews_result()[1]], None)
        mock_gps.return_value = gps

        with patch.dict("sys.modules", {"google_play_scraper": gps}):
            reviews = fetch_play_reviews("com.Slack", pages=1)

        assert "2025-06-14" in reviews[0].date

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_handles_datetime_without_timezone(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.Sort = mock_sort
        gps.reviews.return_value = ([_gp_reviews_result()[0]], None)
        mock_gps.return_value = gps

        with patch.dict("sys.modules", {"google_play_scraper": gps}):
            reviews = fetch_play_reviews("com.Slack", pages=1)

        # Should still produce a valid date with UTC timezone added
        assert "2025-06-15" in reviews[0].date

    @patch("appinsight.scrapers.google_play._get_gps")
    def test_fetch_error_returns_empty(self, mock_gps):
        gps = MagicMock()
        mock_sort = MagicMock()
        mock_sort.NEWEST = 1
        gps.Sort = mock_sort
        gps.reviews.side_effect = Exception("Network error")
        mock_gps.return_value = gps

        with patch.dict("sys.modules", {"google_play_scraper": gps}):
            reviews = fetch_play_reviews("com.Slack", pages=1)

        assert reviews == []
