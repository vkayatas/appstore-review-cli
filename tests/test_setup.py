"""Tests for appinsight.setup - skill file installation, append, force, global, and frontmatter."""

import argparse
import os
import re
import stat

import pytest

from appinsight.setup import AGENTS, SCRIPTS, cmd_setup, _read_instruction, _read_script, _strip_frontmatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(agent, force=False, append=False, use_global=False):
    """Build a minimal args namespace matching what argparse would produce."""
    ns = argparse.Namespace()
    ns.agent = agent
    ns.force = force
    ns.append = append
    setattr(ns, "global", use_global)
    return ns


# ---------------------------------------------------------------------------
# Fresh install
# ---------------------------------------------------------------------------

class TestFreshInstall:
    def test_copilot_creates_skill_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot"))
        skill = tmp_path / ".github" / "skills" / "appstore-reviews" / "SKILL.md"
        assert skill.exists()
        content = skill.read_text()
        assert "appstore-reviews" in content

    def test_claude_creates_skill_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("claude"))
        skill = tmp_path / ".claude" / "skills" / "appstore-reviews" / "SKILL.md"
        assert skill.exists()

    def test_cursor_creates_rules_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("cursor"))
        rules = tmp_path / ".cursor" / "rules" / "appstore-reviews.md"
        assert rules.exists()

    def test_windsurf_creates_rules_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("windsurf"))
        rules = tmp_path / ".windsurfrules"
        assert rules.exists()


# ---------------------------------------------------------------------------
# Append behavior
# ---------------------------------------------------------------------------

class TestAppend:
    def test_append_on_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot"))
        skill = tmp_path / ".github" / "skills" / "appstore-reviews" / "SKILL.md"
        original = skill.read_text()

        cmd_setup(_make_args("copilot", append=True))
        appended = skill.read_text()
        assert len(appended) > len(original)
        # Appended content should be present
        assert appended.count("## Step 1") == 2
        # Must have exactly one YAML frontmatter block (two --- delimiters)
        lines = appended.split("\n")
        fence_count = sum(1 for line in lines if line.strip() == "---")
        assert fence_count == 2, f"Expected 2 frontmatter fences, got {fence_count}"

    def test_append_on_nonexistent_file_creates_it(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot", append=True))
        skill = tmp_path / ".github" / "skills" / "appstore-reviews" / "SKILL.md"
        assert skill.exists()

    def test_existing_file_without_flags_exits(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot"))
        with pytest.raises(SystemExit):
            cmd_setup(_make_args("copilot"))


# ---------------------------------------------------------------------------
# Force overwrite
# ---------------------------------------------------------------------------

class TestForce:
    def test_force_overwrites_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot"))
        skill = tmp_path / ".github" / "skills" / "appstore-reviews" / "SKILL.md"
        original = skill.read_text()

        cmd_setup(_make_args("copilot", force=True))
        overwritten = skill.read_text()
        # Force should overwrite, not append - content length should be the same
        assert len(overwritten) == len(original)


# ---------------------------------------------------------------------------
# Global install
# ---------------------------------------------------------------------------

class TestGlobal:
    def test_copilot_global_writes_to_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path) + p[1:])
        cmd_setup(_make_args("copilot", use_global=True))
        skill = tmp_path / ".copilot" / "skills" / "appstore-reviews" / "SKILL.md"
        assert skill.exists()

    def test_claude_global_writes_to_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path) + p[1:])
        cmd_setup(_make_args("claude", use_global=True))
        skill = tmp_path / ".claude" / "skills" / "appstore-reviews" / "SKILL.md"
        assert skill.exists()

    def test_cursor_global_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            cmd_setup(_make_args("cursor", use_global=True))

    def test_windsurf_global_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(SystemExit):
            cmd_setup(_make_args("windsurf", use_global=True))


# ---------------------------------------------------------------------------
# Bundled helper scripts
# ---------------------------------------------------------------------------

class TestBundledScripts:
    def test_copilot_installs_run_sh(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("copilot"))
        script = tmp_path / ".github" / "skills" / "appstore-reviews" / "scripts" / "run.sh"
        assert script.exists()
        # Should be executable
        assert script.stat().st_mode & stat.S_IXUSR

    def test_claude_installs_run_sh(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("claude"))
        script = tmp_path / ".claude" / "skills" / "appstore-reviews" / "scripts" / "run.sh"
        assert script.exists()

    def test_cursor_does_not_install_scripts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("cursor"))
        # Cursor uses a flat rules file, no scripts directory expected
        scripts_dir = tmp_path / ".cursor" / "rules" / "scripts"
        assert not scripts_dir.exists()

    def test_windsurf_does_not_install_scripts(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cmd_setup(_make_args("windsurf"))
        scripts_dir = tmp_path / "scripts"
        assert not scripts_dir.exists()


# ---------------------------------------------------------------------------
# Frontmatter and content validation
# ---------------------------------------------------------------------------

class TestFrontmatter:
    """Validate that bundled instruction files have correct YAML frontmatter."""

    @pytest.fixture(params=["copilot.md", "claude.md"])
    def instruction_content(self, request):
        return _read_instruction(request.param)

    def test_has_yaml_frontmatter(self, instruction_content):
        assert instruction_content.startswith("---\n")
        end = instruction_content.index("---", 4)
        assert end > 4

    def test_has_required_keys(self, instruction_content):
        end = instruction_content.index("---", 4)
        frontmatter = instruction_content[4:end]
        assert "name:" in frontmatter
        assert "description:" in frontmatter
        assert "compatibility:" in frontmatter

    def test_name_is_appstore_reviews(self, instruction_content):
        end = instruction_content.index("---", 4)
        frontmatter = instruction_content[4:end]
        match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
        assert match
        assert match.group(1).strip() == "appstore-reviews"

    def test_compatibility_matches_pyproject(self, instruction_content):
        """Compatibility text should reference the same Python version as pyproject.toml."""
        end = instruction_content.index("---", 4)
        frontmatter = instruction_content[4:end]
        match = re.search(r'compatibility:.*Python (\d+\.\d+)\+', frontmatter)
        assert match, "No Python version found in compatibility field"
        skill_version = match.group(1)
        # Read the requires-python from pyproject.toml
        pyproject = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
        with open(pyproject) as f:
            toml_text = f.read()
        req_match = re.search(r'requires-python\s*=\s*">=(\d+\.\d+)"', toml_text)
        assert req_match, "No requires-python found in pyproject.toml"
        assert skill_version == req_match.group(1), (
            f"Skill says Python {skill_version}+ but pyproject.toml says >={req_match.group(1)}"
        )

    def test_content_references_correct_cli_name(self, instruction_content):
        assert "appstore-reviews" in instruction_content
        assert "appstore-review-cli" in instruction_content


class TestBundledScriptContent:
    def test_run_sh_is_readable(self):
        content = _read_script("run.sh")
        assert "#!/bin/bash" in content
        assert "appstore-reviews" in content


# ---------------------------------------------------------------------------
# _strip_frontmatter helper
# ---------------------------------------------------------------------------

class TestStripFrontmatter:
    def test_strips_yaml_frontmatter(self):
        text = "---\nname: test\n---\n# Body\nContent here"
        result = _strip_frontmatter(text)
        assert "---" not in result
        assert result.startswith("# Body")

    def test_no_frontmatter_unchanged(self):
        text = "# Just a heading\nSome content"
        assert _strip_frontmatter(text) == text

    def test_incomplete_frontmatter_unchanged(self):
        text = "---\nname: test\nno closing fence"
        assert _strip_frontmatter(text) == text
