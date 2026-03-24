"""Tests for appinsight.formatters - JSON, CSV, markdown, text, and stats output."""

import csv
import io
import json

import pytest

from appinsight.scrapers.appstore import Review
from appinsight.output.formatters import to_json, to_csv, to_markdown, to_text, summary_stats


def _make_review(**overrides) -> Review:
    defaults = {
        "id": "100",
        "title": "Test Title",
        "content": "Test content body",
        "rating": 3,
        "author": "tester",
        "date": "2025-01-15T12:00:00+00:00",
        "version": "2.1",
        "vote_sum": 5,
        "vote_count": 8,
    }
    defaults.update(overrides)
    return Review(**defaults)


@pytest.fixture
def reviews():
    return [
        _make_review(id="1", rating=1, title="Terrible", content="Crashes all the time"),
        _make_review(id="2", rating=4, title="Good app", content="Works fine mostly"),
        _make_review(id="3", rating=2, title="Pipe | char", content="Content with | pipes"),
    ]


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------

class TestToJson:
    def test_valid_json(self, reviews):
        result = to_json(reviews)
        data = json.loads(result)
        assert len(data) == 3

    def test_fields_present(self, reviews):
        data = json.loads(to_json(reviews))
        expected_keys = {"id", "title", "content", "rating", "author", "date", "version", "vote_sum", "vote_count"}
        assert set(data[0].keys()) == expected_keys

    def test_empty_list(self):
        data = json.loads(to_json([]))
        assert data == []

    def test_compact_mode(self, reviews):
        result = to_json(reviews, pretty=False)
        assert "\n" not in result  # single line


# ---------------------------------------------------------------------------
# to_csv
# ---------------------------------------------------------------------------

class TestToCsv:
    def test_valid_csv(self, reviews):
        result = to_csv(reviews)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 3

    def test_header_fields(self, reviews):
        result = to_csv(reviews)
        reader = csv.DictReader(io.StringIO(result))
        assert "rating" in reader.fieldnames
        assert "content" in reader.fieldnames

    def test_date_truncated(self, reviews):
        result = to_csv(reviews)
        reader = csv.DictReader(io.StringIO(result))
        row = next(reader)
        assert row["date"] == "2025-01-15"

    def test_empty_list(self):
        assert to_csv([]) == ""


# ---------------------------------------------------------------------------
# to_markdown
# ---------------------------------------------------------------------------

class TestToMarkdown:
    def test_contains_header_row(self, reviews):
        result = to_markdown(reviews)
        assert "| Rating |" in result
        assert "|--------|" in result

    def test_pipe_chars_escaped(self, reviews):
        result = to_markdown(reviews)
        # The review with "Pipe | char" title should have escaped pipe
        assert "Pipe \\| char" in result

    def test_empty_list(self):
        assert "No reviews" in to_markdown([])

    def test_long_content_truncated(self):
        r = _make_review(content="A" * 200)
        result = to_markdown([r])
        assert "..." in result


# ---------------------------------------------------------------------------
# to_text
# ---------------------------------------------------------------------------

class TestToText:
    def test_contains_review_blocks(self, reviews):
        result = to_text(reviews)
        assert "--- Review 1 ---" in result
        assert "--- Review 3 ---" in result

    def test_fields_present(self, reviews):
        result = to_text(reviews)
        assert "Rating: 1/5" in result
        assert "Title: Terrible" in result

    def test_empty_list(self):
        assert "No reviews" in to_text([])


# ---------------------------------------------------------------------------
# summary_stats
# ---------------------------------------------------------------------------

class TestSummaryStats:
    def test_total_count(self, reviews):
        result = summary_stats(reviews)
        assert "Total reviews: 3" in result

    def test_average_rating(self, reviews):
        result = summary_stats(reviews)
        # (1+4+2)/3 = 2.3
        assert "2.3/5" in result

    def test_distribution_lines(self, reviews):
        result = summary_stats(reviews)
        assert "1⭐" in result
        assert "5⭐" in result

    def test_empty_list(self):
        assert "No reviews" in summary_stats([])
