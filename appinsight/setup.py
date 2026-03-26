"""Setup command - install agent instruction files into the user's project."""

import os
import sys
from importlib import resources


# Map agent names to (source file in package, target path relative to cwd or home)
AGENTS = {
    "copilot": {
        "source": "copilot.md",
        "targets": [
            (os.path.join(".github", "skills", "appstore-reviews", "SKILL.md"),
             ".github/skills/appstore-reviews/ (auto-discovered by Copilot)"),
        ],
        "global_targets": [
            (os.path.join(".copilot", "skills", "appstore-reviews", "SKILL.md"),
             "~/.copilot/skills/appstore-reviews/ (available across all projects)"),
        ],
        "scripts_dir": os.path.join("appstore-reviews"),
    },
    "claude": {
        "source": "claude.md",
        "targets": [
            (os.path.join(".claude", "skills", "appstore-reviews", "SKILL.md"),
             ".claude/skills/appstore-reviews/ (auto-discovered by Claude)"),
        ],
        "global_targets": [
            (os.path.join(".claude", "skills", "appstore-reviews", "SKILL.md"),
             "~/.claude/skills/appstore-reviews/ (available across all projects)"),
        ],
        "scripts_dir": os.path.join("appstore-reviews"),
    },
    "cursor": {
        "source": "claude.md",
        "targets": [
            (os.path.join(".cursor", "rules", "appstore-reviews.md"), ".cursor/rules/ (read as agent rules)"),
        ],
    },
    "windsurf": {
        "source": "claude.md",
        "targets": [
            (".windsurfrules", "Project root (read as Windsurf rules)"),
        ],
    },
}


# Bundled scripts to install alongside SKILL.md in skill directories
SCRIPTS = {
    "run.sh": "scripts/run.sh",
}


def _read_instruction(filename: str) -> str:
    """Read a bundled instruction file from the package."""
    ref = resources.files("appinsight.instructions").joinpath(filename)
    return ref.read_text(encoding="utf-8")


def _read_script(filename: str) -> str:
    """Read a bundled script file from the package."""
    ref = resources.files("appinsight.instructions").joinpath("scripts", filename)
    return ref.read_text(encoding="utf-8")


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (---...---) from the start of a document."""
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end == -1:
        return text
    # Skip past the closing --- and any trailing newline
    end = text.index("\n", end) + 1 if "\n" in text[end:] else end + 3
    return text[end:].lstrip("\n")


def cmd_setup(args):
    """Install agent instruction files into the current project or globally."""
    agent = args.agent

    if agent not in AGENTS:
        print(f"Unknown agent: {agent}", file=sys.stderr)
        print(f"Available: {', '.join(AGENTS)}", file=sys.stderr)
        sys.exit(1)

    config = AGENTS[agent]
    content = _read_instruction(config["source"])

    # Choose project or global targets
    use_global = getattr(args, "global", False)
    if use_global:
        if "global_targets" not in config:
            print(f"Error: --global is not supported for {agent}.", file=sys.stderr)
            sys.exit(1)
        targets = config["global_targets"]
        base_dir = os.path.expanduser("~")
    else:
        targets = config["targets"]
        base_dir = os.getcwd()

    for target_path, description in targets:
        full_path = os.path.join(base_dir, target_path)

        # Check if file already exists
        if os.path.exists(full_path):
            if not args.force and not args.append:
                display = os.path.join("~", target_path) if use_global else target_path
                print(f"Already exists: {display}", file=sys.stderr)
                print(f"  Use --force to overwrite, or --append to add to existing file.", file=sys.stderr)
                sys.exit(1)

        # Create parent directories if needed
        parent = os.path.dirname(full_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        display = os.path.join("~", target_path) if use_global else target_path
        if args.append and os.path.exists(full_path):
            # Strip YAML frontmatter to avoid a second frontmatter block
            append_content = _strip_frontmatter(content)
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n\n")
                f.write(append_content)
            print(f"Appended to: {display}", file=sys.stderr)
        else:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created: {display}", file=sys.stderr)

        print(f"  -> {description}", file=sys.stderr)

    # Install bundled scripts alongside SKILL.md (for skill-directory agents only)
    if "scripts_dir" in config:
        for script_name, script_rel_path in SCRIPTS.items():
            script_content = _read_script(script_name)
            for target_path, _ in targets:
                skill_dir = os.path.dirname(os.path.join(base_dir, target_path))
                script_full_path = os.path.join(skill_dir, script_rel_path)
                script_parent = os.path.dirname(script_full_path)
                os.makedirs(script_parent, exist_ok=True)
                with open(script_full_path, "w", encoding="utf-8") as f:
                    f.write(script_content)
                os.chmod(script_full_path, 0o755)

    scope = "globally" if use_global else "in this project"
    print(f"\nDone! Your {agent} agent now knows about appstore-reviews ({scope}).", file=sys.stderr)
