"""Tests for appinsight.scraper - RSS entry parsing and data classes."""

from appinsight.scrapers.appstore import _parse_entry, Review, AppInfo


# ---------------------------------------------------------------------------
# _parse_entry
# ---------------------------------------------------------------------------

class TestParseEntry:
    def test_valid_entry(self):
        entry = {
            "id": {"label": "12345"},
            "title": {"label": "Great app"},
            "content": {"label": "Works perfectly"},
            "im:rating": {"label": "5"},
            "author": {"name": {"label": "john"}},
            "updated": {"label": "2025-03-15T10:00:00-07:00"},
            "im:version": {"label": "3.2.1"},
            "im:voteSum": {"label": "10"},
            "im:voteCount": {"label": "15"},
        }
        review = _parse_entry(entry)
        assert review is not None
        assert review.id == "12345"
        assert review.rating == 5
        assert review.author == "john"
        assert review.version == "3.2.1"
        assert review.vote_sum == 10

    def test_app_metadata_entry_returns_none(self):
        """App Store feed includes one entry per page that's app metadata, not a review."""
        entry = {
            "id": {"label": "some-app-id"},
            "title": {"label": "My App"},
            "content": {"label": "App description"},
            # No im:rating - this is app metadata
        }
        assert _parse_entry(entry) is None

    def test_missing_optional_fields(self):
        entry = {
            "im:rating": {"label": "3"},
            # Everything else missing
        }
        review = _parse_entry(entry)
        assert review is not None
        assert review.rating == 3
        assert review.title == ""
        assert review.author == ""
        assert review.vote_sum == 0

    def test_invalid_rating_returns_none(self):
        entry = {
            "im:rating": {"label": "not-a-number"},
        }
        assert _parse_entry(entry) is None

    def test_empty_entry(self):
        assert _parse_entry({}) is None


# ---------------------------------------------------------------------------
# Review dataclass
# ---------------------------------------------------------------------------

class TestReview:
    def test_to_dict(self):
        r = Review(
            id="1", title="T", content="C", rating=3,
            author="a", date="2025-01-01", version="1.0",
            vote_sum=1, vote_count=2,
        )
        d = r.to_dict()
        assert d["id"] == "1"
        assert d["rating"] == 3
        assert isinstance(d, dict)


# ---------------------------------------------------------------------------
# AppInfo dataclass
# ---------------------------------------------------------------------------

class TestAppInfo:
    def test_to_dict(self):
        a = AppInfo(
            app_id=123, name="Test", developer="Dev",
            avg_rating=4.5, rating_count=1000,
            version="1.0", bundle_id="com.test",
        )
        d = a.to_dict()
        assert d["app_id"] == 123
        assert d["name"] == "Test"
