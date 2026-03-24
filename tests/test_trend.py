"""Tests for the trend module."""

from collections import OrderedDict
from unittest.mock import patch

import pytest

from appinsight.scrapers.appstore import Review
from appinsight.commands.trend import _parse_date, _group_by_period, _sparkline, trend


def _make_review(date: str, rating: int = 3, **kwargs) -> Review:
    defaults = dict(
        id="1", title="t", content="c", rating=rating,
        author="a", date=date, version="1.0",
        vote_sum=0, vote_count=0,
    )
    defaults.update(kwargs)
    return Review(**defaults)


# ---------- _parse_date ----------

def test_parse_date_iso():
    dt = _parse_date("2025-01-15T12:00:00+00:00")
    assert dt.year == 2025 and dt.month == 1 and dt.day == 15


def test_parse_date_invalid():
    assert _parse_date("not-a-date") is None
    assert _parse_date(None) is None


# ---------- _group_by_period ----------

def test_group_by_week():
    reviews = [
        _make_review("2025-01-06T00:00:00+00:00"),  # Week 02
        _make_review("2025-01-07T00:00:00+00:00"),  # Week 02
        _make_review("2025-01-13T00:00:00+00:00"),  # Week 03
    ]
    groups = _group_by_period(reviews, "week")
    keys = list(groups.keys())
    assert len(keys) == 2
    assert len(groups[keys[0]]) == 2
    assert len(groups[keys[1]]) == 1


def test_group_by_month():
    reviews = [
        _make_review("2025-01-15T00:00:00+00:00"),
        _make_review("2025-02-15T00:00:00+00:00"),
        _make_review("2025-02-20T00:00:00+00:00"),
    ]
    groups = _group_by_period(reviews, "month")
    assert list(groups.keys()) == ["2025-01", "2025-02"]
    assert len(groups["2025-01"]) == 1
    assert len(groups["2025-02"]) == 2


def test_group_skips_unparseable():
    reviews = [
        _make_review("2025-01-15T00:00:00+00:00"),
        _make_review("bad-date"),
    ]
    groups = _group_by_period(reviews, "month")
    assert len(groups) == 1


def test_group_chronological_order():
    reviews = [
        _make_review("2025-03-01T00:00:00+00:00"),
        _make_review("2025-01-01T00:00:00+00:00"),
    ]
    groups = _group_by_period(reviews, "month")
    assert list(groups.keys()) == ["2025-01", "2025-03"]


# ---------- _sparkline ----------

def test_sparkline_min():
    bar = _sparkline([1.0], width=10)
    assert bar == "░" * 10


def test_sparkline_max():
    bar = _sparkline([5.0], width=10)
    assert bar == "█" * 10


def test_sparkline_mid():
    bar = _sparkline([3.0], width=20)
    assert "█" in bar and "░" in bar


def test_sparkline_empty():
    assert _sparkline([]) == ""


# ---------- trend (integration, mocked) ----------

MOCK_REVIEWS = [
    _make_review("2025-01-06T00:00:00+00:00", rating=2),
    _make_review("2025-01-07T00:00:00+00:00", rating=3),
    _make_review("2025-01-13T00:00:00+00:00", rating=4),
    _make_review("2025-01-14T00:00:00+00:00", rating=5),
]


@patch("appinsight.commands.trend.fetch_reviews", return_value=MOCK_REVIEWS)
@patch("appinsight.commands.trend.lookup_app", return_value=None)
def test_trend_basic(mock_lookup, mock_fetch):
    result = trend("123456", pages=1)
    assert "RATING TREND" in result
    assert "★" in result


@patch("appinsight.commands.trend.fetch_reviews", return_value=MOCK_REVIEWS)
@patch("appinsight.commands.trend.lookup_app", return_value=None)
def test_trend_month(mock_lookup, mock_fetch):
    result = trend("123456", pages=1, period="month")
    assert "2025-01" in result


@patch("appinsight.commands.trend.fetch_reviews", return_value=[])
@patch("appinsight.commands.trend.lookup_app", return_value=None)
def test_trend_no_reviews(mock_lookup, mock_fetch):
    result = trend("123456", pages=1)
    assert "No reviews" in result
