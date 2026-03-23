"""Setup command — install agent instruction files into the user's project."""

import os
import sys
from importlib import resources


# Map agent names to (source file in package, target path relative to cwd)
AGENTS = {
    "copilot": {
        "source": "copilot.md",
        "targets": [
            ("SKILL.md", "Project root (auto-discovered by Copilot as a workspace skill)"),
        ],
    },
    "claude": {
        "source": "claude.md",
        "targets": [
            ("CLAUDE.md", "Project root (auto-read by Claude Code on every session)"),
        ],
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


def _read_instruction(filename: str) -> str:
    """Read a bundled instruction file from the package."""
    ref = resources.files("appinsight.instructions").joinpath(filename)
    return ref.read_text(encoding="utf-8")


def cmd_setup(args):
    """Install agent instruction files into the current project."""
    agent = args.agent

    if agent not in AGENTS:
        print(f"Unknown agent: {agent}", file=sys.stderr)
        print(f"Available: {', '.join(AGENTS)}", file=sys.stderr)
        sys.exit(1)

    config = AGENTS[agent]
    content = _read_instruction(config["source"])

    for target_path, description in config["targets"]:
        full_path = os.path.join(os.getcwd(), target_path)

        # Check if file already exists
        if os.path.exists(full_path):
            if not args.force:
                print(f"Already exists: {target_path}", file=sys.stderr)
                print(f"  Use --force to overwrite, or --append to add to existing file.", file=sys.stderr)
                sys.exit(1)

        # Create parent directories if needed
        parent = os.path.dirname(full_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        if args.append and os.path.exists(full_path):
            with open(full_path, "a", encoding="utf-8") as f:
                f.write("\n\n")
                f.write(content)
            print(f"Appended to: {target_path}", file=sys.stderr)
        else:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created: {target_path}", file=sys.stderr)

        print(f"  → {description}", file=sys.stderr)

    print(f"\nDone! Your {agent} agent now knows about appstore-reviews.", file=sys.stderr)
