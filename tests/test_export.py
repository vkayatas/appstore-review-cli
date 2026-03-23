"""Tests for JSON/CSV export in compare, version_diff, and trend."""

import csv
import io
import json
from unittest.mock import patch

import pytest

from appinsight.scraper import Review, AppInfo
from appinsight.compare import compare_apps, _compare_to_json, _compare_to_csv
from appinsight.version_diff import version_diff, _vdiff_to_csv
from appinsight.trend import trend, _trend_to_csv


def _make_review(date="2025-01-15T00:00:00+00:00", rating=2, version="1.0", **kw):
    defaults = dict(
        id="1", title="Bad app", content="App crashes on startup",
        rating=rating, author="user1", date=date, version=version,
        vote_sum=0, vote_count=0,
    )
    defaults.update(kw)
    return Review(**defaults)


MOCK_APP = AppInfo(
    app_id="123", name="TestApp", developer="Dev",
    avg_rating=3.5, rating_count=1000, version="1.0", bundle_id="com.test",
)

MOCK_REVIEWS = [
    _make_review(id="1", rating=1, version="1.0", date="2025-01-06T00:00:00+00:00"),
    _make_review(id="2", rating=2, version="1.0", date="2025-01-07T00:00:00+00:00"),
    _make_review(id="3", rating=4, version="2.0", date="2025-01-13T00:00:00+00:00"),
    _make_review(id="4", rating=5, version="2.0", date="2025-01-14T00:00:00+00:00"),
    _make_review(id="5", rating=3, version="2.0", date="2025-01-15T00:00:00+00:00"),
]


# ==================== compare ====================

class TestCompareExport:
    @patch("appinsight.compare.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.compare.lookup_app", return_value=MOCK_APP)
    def test_compare_json_valid(self, mock_lookup, mock_fetch):
        result = compare_apps(["123", "456"], format="json")
        data = json.loads(result)
        assert "apps" in data
        assert len(data["apps"]) == 2
        assert "shared_complaints" in data
        assert "unique_complaints" in data
        for app in data["apps"]:
            assert "app_id" in app
            assert "filtered_avg_rating" in app
            assert "rating_distribution" in app

    @patch("appinsight.compare.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.compare.lookup_app", return_value=MOCK_APP)
    def test_compare_csv_valid(self, mock_lookup, mock_fetch):
        result = compare_apps(["123", "456"], format="csv")
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[0][0] == "app_id"  # header
        assert len(rows) == 3  # header + 2 apps
        assert rows[1][0] == "123"
        assert rows[2][0] == "456"

    @patch("appinsight.compare.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.compare.lookup_app", return_value=MOCK_APP)
    def test_compare_text_default(self, mock_lookup, mock_fetch):
        result = compare_apps(["123", "456"])
        assert "COMPARISON REPORT" in result

    @patch("appinsight.compare.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.compare.lookup_app", return_value=MOCK_APP)
    def test_compare_json_rating_distribution(self, mock_lookup, mock_fetch):
        result = compare_apps(["123"], format="json")
        data = json.loads(result)
        dist = data["apps"][0]["rating_distribution"]
        assert all(k in dist for k in ["1", "2", "3", "4", "5"])


# ==================== version-diff ====================

class TestVersionDiffExport:
    @patch("appinsight.version_diff.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.version_diff.lookup_app", return_value=MOCK_APP)
    def test_vdiff_json_valid(self, mock_lookup, mock_fetch):
        result = version_diff("123", format="json")
        data = json.loads(result)
        assert "old_version" in data
        assert "new_version" in data
        assert "delta" in data
        assert "sentiment" in data
        assert "category_changes" in data
        assert "old" in data and "new" in data
        assert "avg_rating" in data["old"]
        assert "rating_distribution" in data["new"]

    @patch("appinsight.version_diff.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.version_diff.lookup_app", return_value=MOCK_APP)
    def test_vdiff_csv_valid(self, mock_lookup, mock_fetch):
        result = version_diff("123", format="csv")
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[0] == ["category", "old_pct", "new_pct", "change_pct"]

    @patch("appinsight.version_diff.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.version_diff.lookup_app", return_value=MOCK_APP)
    def test_vdiff_text_default(self, mock_lookup, mock_fetch):
        result = version_diff("123")
        assert "VERSION DIFF" in result

    @patch("appinsight.version_diff.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.version_diff.lookup_app", return_value=MOCK_APP)
    def test_vdiff_json_new_resolved_issues(self, mock_lookup, mock_fetch):
        result = version_diff("123", format="json")
        data = json.loads(result)
        assert "new_issues" in data
        assert "resolved_issues" in data
        assert isinstance(data["new_issues"], list)


# ==================== trend ====================

class TestTrendExport:
    @patch("appinsight.trend.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.trend.lookup_app", return_value=MOCK_APP)
    def test_trend_json_valid(self, mock_lookup, mock_fetch):
        result = trend("123", format="json")
        data = json.loads(result)
        assert "app_name" in data
        assert "overall_avg" in data
        assert "total_reviews" in data
        assert "periods" in data
        assert len(data["periods"]) >= 1
        p = data["periods"][0]
        assert "period" in p
        assert "avg_rating" in p
        assert "count" in p
        assert "rating_distribution" in p

    @patch("appinsight.trend.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.trend.lookup_app", return_value=MOCK_APP)
    def test_trend_csv_valid(self, mock_lookup, mock_fetch):
        result = trend("123", format="csv")
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[0][0] == "period"
        assert "avg_rating" in rows[0]
        assert len(rows) >= 2  # header + at least 1 period

    @patch("appinsight.trend.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.trend.lookup_app", return_value=MOCK_APP)
    def test_trend_text_default(self, mock_lookup, mock_fetch):
        result = trend("123")
        assert "RATING TREND" in result

    @patch("appinsight.trend.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.trend.lookup_app", return_value=MOCK_APP)
    def test_trend_json_overall_trend(self, mock_lookup, mock_fetch):
        result = trend("123", format="json")
        data = json.loads(result)
        assert "overall_trend" in data
        assert "trend_delta" in data

    @patch("appinsight.trend.fetch_reviews", return_value=MOCK_REVIEWS)
    @patch("appinsight.trend.lookup_app", return_value=MOCK_APP)
    def test_trend_csv_star_columns(self, mock_lookup, mock_fetch):
        result = trend("123", format="csv")
        reader = csv.reader(io.StringIO(result))
        header = next(reader)
        assert "1_star" in header
        assert "5_star" in header
