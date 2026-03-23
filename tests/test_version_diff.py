"""Tests for appinsight.version_diff - version comparison logic."""

import pytest

from appinsight.scraper import Review
from appinsight.version_diff import _group_by_version, _pick_versions


def _make_review(**overrides) -> Review:
    defaults = {
        "id": "1",
        "title": "Test",
        "content": "Some content",
        "rating": 3,
        "author": "user1",
        "date": "2025-06-01T00:00:00+00:00",
        "version": "2.0",
        "vote_sum": 0,
        "vote_count": 0,
    }
    defaults.update(overrides)
    return Review(**defaults)


@pytest.fixture
def multi_version_reviews():
    return [
        _make_review(id="1", version="1.0", rating=4, content="Good app works well"),
        _make_review(id="2", version="1.0", rating=3, content="OK but could improve"),
        _make_review(id="3", version="1.0", rating=2, content="App crashes sometimes"),
        _make_review(id="4", version="2.0", rating=1, content="Everything is broken crashes"),
        _make_review(id="5", version="2.0", rating=2, content="Very slow and laggy now"),
        _make_review(id="6", version="2.0", rating=1, content="Login doesn't work error"),
        _make_review(id="7", version="2.0", rating=3, content="Some bugs but OK"),
        _make_review(id="8", version="", rating=5, content="Great no version"),
    ]


class TestGroupByVersion:
    def test_groups_correctly(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        assert "1.0" in groups
        assert "2.0" in groups
        assert len(groups["1.0"]) == 3
        assert len(groups["2.0"]) == 4

    def test_ignores_empty_version(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        assert "" not in groups

    def test_empty_reviews(self):
        assert _group_by_version([]) == {}


class TestPickVersions:
    def test_explicit_both(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        old, new = _pick_versions(groups, "1.0", "2.0")
        assert old == "1.0"
        assert new == "2.0"

    def test_auto_detect(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        old, new = _pick_versions(groups, None, None)
        # 2.0 has 4 reviews (most), 1.0 has 3 - so new=2.0, old=1.0
        assert new == "2.0"
        assert old == "1.0"

    def test_only_new_specified(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        old, new = _pick_versions(groups, None, "1.0")
        assert new == "1.0"
        assert old == "2.0"  # Auto-picked the other most reviewed

    def test_only_old_specified(self, multi_version_reviews):
        groups = _group_by_version(multi_version_reviews)
        old, new = _pick_versions(groups, "1.0", None)
        assert old == "1.0"
        assert new == "2.0"

    def test_single_version_raises(self):
        reviews = [_make_review(version="1.0")]
        groups = _group_by_version(reviews)
        with pytest.raises(ValueError, match="at least 2 versions"):
            _pick_versions(groups, None, None)

    def test_no_versions_raises(self):
        with pytest.raises(ValueError, match="at least 2 versions"):
            _pick_versions({}, None, None)
