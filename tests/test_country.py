"""Tests for country name/alias resolution."""

from appinsight.cli import resolve_country


class TestResolveCountry:
    def test_iso_code_passthrough(self):
        assert resolve_country("us") == "us"
        assert resolve_country("de") == "de"
        assert resolve_country("gb") == "gb"

    def test_uppercase_code(self):
        assert resolve_country("US") == "us"
        assert resolve_country("DE") == "de"

    def test_full_country_name(self):
        assert resolve_country("germany") == "de"
        assert resolve_country("france") == "fr"
        assert resolve_country("japan") == "jp"
        assert resolve_country("united states") == "us"
        assert resolve_country("united kingdom") == "gb"

    def test_common_aliases(self):
        assert resolve_country("uk") == "gb"
        assert resolve_country("usa") == "us"
        assert resolve_country("holland") == "nl"
        assert resolve_country("uae") == "ae"

    def test_case_insensitive(self):
        assert resolve_country("Germany") == "de"
        assert resolve_country("JAPAN") == "jp"
        assert resolve_country("United Kingdom") == "gb"

    def test_whitespace_stripped(self):
        assert resolve_country("  germany  ") == "de"
        assert resolve_country(" us ") == "us"

    def test_unknown_two_letter_accepted(self):
        """Unknown 2-letter codes are passed through (App Store may support them)."""
        result = resolve_country("zz")
        assert result == "zz"

    def test_unknown_name_warns(self, capsys):
        """Unknown names produce a warning but still return the lowered value."""
        result = resolve_country("narnia")
        assert result == "narnia"
        captured = capsys.readouterr()
        assert "Unknown country" in captured.err
        assert "Common values" in captured.err
