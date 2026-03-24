# appstore-review-cli

[![CI](https://github.com/vkayatas/appstore-review-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/vkayatas/appstore-review-cli/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/appstore-review-cli)](https://pypi.org/project/appstore-review-cli/)
[![Python](https://img.shields.io/pypi/pyversions/appstore-review-cli)](https://pypi.org/project/appstore-review-cli/)
[![Downloads](https://img.shields.io/pypi/dm/appstore-review-cli)](https://pypi.org/project/appstore-review-cli/)
[![License: MIT](https://img.shields.io/pypi/l/appstore-review-cli)](https://github.com/vkayatas/appstore-review-cli/blob/main/LICENSE)
[![Typed](https://img.shields.io/badge/typing-typed-blue)](https://peps.python.org/pep-0561/)

[![Copilot](https://img.shields.io/badge/Copilot-ready-blue?logo=githubcopilot)](https://github.com/vkayatas/appstore-review-cli#agent-integration)
[![Claude Code](https://img.shields.io/badge/Claude_Code-ready-orange?logo=anthropic)](https://github.com/vkayatas/appstore-review-cli#agent-integration)
[![Cursor](https://img.shields.io/badge/Cursor-ready-purple)](https://github.com/vkayatas/appstore-review-cli#agent-integration)
[![Windsurf](https://img.shields.io/badge/Windsurf-ready-teal)](https://github.com/vkayatas/appstore-review-cli#agent-integration)

**Turn App Store and Google Play reviews into product intelligence - from the terminal or through your AI coding agent.**

App store reviews are the largest public dataset of unfiltered user feedback. But reading them on the store websites is painful: no filtering, no export, no way to search across versions or countries. This tool fixes that.

<p align="center">
  <img src="https://raw.githubusercontent.com/vkayatas/appstore-review-cli/master/docs/hero_img.png" alt="appstore-review-cli - Turn App Store reviews into AI-ready insights" width="600">
</p>

## Why Use This?

- **Two stores**: Apple App Store and Google Play - same filters, same output, one tool.
- **Competitor research**: Pull 1-star reviews for any app and find the feature gaps your product can fill.
- **Bug triage**: Filter reviews by keywords like "crash", "freeze", "login" and group by app version.
- **Version monitoring**: Compare sentiment between releases - see what got better, what got worse, and what's new.
- **Multi-country insights**: Same app, different markets - compare complaints across `us`, `de`, `jp`, etc.
- **AI-native**: Your coding agent (Copilot, Claude Code, Cursor) can fetch and analyze reviews in natural language. No Ollama needed - the agent IS the LLM.

No API keys. No accounts. No servers. Just `pip install` and go.

## Install

```bash
pip install appstore-review-cli
```

For Google Play support:
```bash
pip install "appstore-review-cli[google]"
```

## Quick Start

```bash
# Find an app
appstore-reviews search "Slack"

# Get negative reviews from the last 30 days
appstore-reviews reviews 803453959 --stars 2 --days 30

# Filter by keywords
appstore-reviews reviews 803453959 --keywords crash,freeze --stars 2

# Sort by most helpful
appstore-reviews reviews 803453959 --stars 2 --sort votes

# Get only 3-star reviews (the nuanced ones)
appstore-reviews reviews 803453959 --min-stars 3 --stars 3

# Export to CSV or JSON
appstore-reviews reviews 803453959 --stars 2 --format csv > reviews.csv
appstore-reviews reviews 803453959 --stars 2 --format json > reviews.json

# Compare two apps side by side
appstore-reviews compare 803453959 310633997 --stars 2 --pages 3

# Google Play - use --store google with package names
appstore-reviews --store google search "Slack"
appstore-reviews --store google reviews com.Slack --stars 2 --days 30
appstore-reviews --store google compare com.Slack com.microsoft.teams --stars 2

# Compare sentiment between app versions
appstore-reviews version-diff 803453959 --pages 5
appstore-reviews version-diff 803453959 --old 4.23.0 --new 4.29.149

# Show rating trend over time (weekly or monthly)
appstore-reviews trend 803453959 --pages 5
appstore-reviews trend 803453959 --period month --stars 2

# Export compare/version-diff/trend to JSON or CSV
appstore-reviews compare 803453959 310633997 --format json > compare.json
appstore-reviews version-diff 803453959 --format csv > diff.csv
appstore-reviews trend 803453959 --format csv > trend.csv
```

## Agent Integration

One command to teach your AI coding agent every command, filter, and workflow:

```bash
appstore-reviews setup copilot      # GitHub Copilot → creates SKILL.md
appstore-reviews setup claude       # Claude Code    → creates CLAUDE.md
appstore-reviews setup cursor       # Cursor         → creates .cursor/rules/appstore-reviews.md
appstore-reviews setup windsurf     # Windsurf       → creates .windsurfrules
```

Then just ask in natural language:

- *"What are the top complaints about Slack this month?"*
- *"Find crash reports for WhatsApp in the last 30 days"*
- *"Compare Notion vs Obsidian - what do users hate about each?"*
- *"What features are German Duolingo users requesting?"*

The agent runs the CLI, fetches reviews, and analyzes them directly. No Ollama, no extra setup.

Use `--force` to overwrite an existing file, `--append` to add to one.

### Without an agent

Use the built-in Ollama analysis, or pipe to any LLM:

```bash
# Ollama (local, private)
ollama pull qwen3.5:4b
appstore-reviews analyze 803453959 --stars 2 --mode summary
appstore-reviews analyze 803453959 --stars 2 --mode gaps
appstore-reviews analyze 803453959 --stars 2 --mode bugs --keywords crash,freeze

# Or pipe raw output to any tool
appstore-reviews reviews 803453959 --stars 2 --format text | your-llm "Summarize:"
```

## All Options

### Global flags (apply to all commands)

| Flag | Description |
|------|-------------|
| `--store google` | Use Google Play instead of Apple App Store (default: `apple`) |
| `--country de` | Store region (default: `us`) |

### `search` - Find an app by name

| Flag | Description |
|------|-------------|
| `--limit 10` | Max results (default: 5) |
| `--format json` | Output as JSON instead of table |
| `--country de` | App Store region (default: `us`) |

For Google Play, app IDs are package names (e.g. `com.Slack`). For Apple, they're numeric (e.g. `803453959`).

### `reviews <APP_ID>` - Fetch and filter reviews

| Flag | Description |
|------|-------------|
| `--stars 2` | Max star rating to include (1-5). `2` = 1-2 stars |
| `--min-stars 3` | Min star rating (1-5). `--min-stars 3 --stars 3` = only 3★ |
| `--days 30` | Only reviews from the last N days |
| `--keywords crash,bug` | Only reviews containing these words (case-insensitive) |
| `--version 5.0.1` | Only reviews for a specific app version |
| `--pages 5` | Pages to fetch (1-10, default 3; 10 ≈ 500 reviews) |
| `--format text` | Output as `text` \| `json` \| `csv` \| `markdown` |
| `--sort votes` | Sort by: `date` (newest) \| `rating` (lowest) \| `votes` (most helpful) |
| `--stats` | Show rating distribution |
| `--country de` | App Store region (default: `us`) |

All filters stack with AND logic.

### `analyze <APP_ID>` - LLM analysis via Ollama

| Flag | Description |
|------|-------------|
| `--mode summary` | Analysis type: `summary` \| `gaps` \| `bugs` |
| `--model qwen3.5:4b` | Ollama model to use |
| `--list-models` | Show available Ollama models |

Plus all the same filters as `reviews` (`--stars`, `--min-stars`, `--days`, `--keywords`, `--version`, `--pages`, `--sort`, `--stats`, `--country`).

### `compare <APP_ID> <APP_ID> [...]` - Compare multiple apps

| Flag | Description |
|------|-------------|
| `--stars 2` | Max star rating to include (1-5) |
| `--min-stars 3` | Min star rating (1-5) |
| `--days 30` | Only reviews from the last N days |
| `--keywords crash,bug` | Only reviews containing these words |
| `--pages 5` | Pages to fetch per app (1-10, default 3) |
| `--sort votes` | Sort by: `date` \| `rating` \| `votes` |
| `--country de` | App Store region (default: `us`) |
| `--format json` | Output format: `text` (default) \| `json` \| `csv` |

Outputs: overview table, per-app rating distribution, top complaint categories, top keywords, shared vs unique complaints.

### `version-diff <APP_ID>` - Compare sentiment between versions

| Flag | Description |
|------|-------------|
| `--old 4.23.0` | Old version to compare (auto-detected if omitted) |
| `--new 4.29.149` | New version to compare (auto-detected if omitted) |
| `--stars 2` | Max star rating to include (1-5) |
| `--min-stars 3` | Min star rating (1-5) |
| `--days 90` | Only reviews from the last N days |
| `--keywords crash,bug` | Only reviews containing these words |
| `--pages 5` | Pages to fetch (1-10, default 5) |
| `--format json` | Output format: `text` (default) \| `json` \| `csv` |

Outputs: version comparison table, rating distributions, complaint category changes (with arrows), new/resolved issues, top keywords per version. Versions are auto-detected from the two most reviewed if not specified.

### `trend <APP_ID>` - Show rating trend over time

| Flag | Description |
|------|-------------|
| `--period week` | Group by `week` (default) or `month` |
| `--stars 2` | Max star rating to include (1-5) |
| `--min-stars 3` | Min star rating (1-5) |
| `--days 90` | Only reviews from the last N days |
| `--keywords crash,bug` | Only reviews containing these words |
| `--pages 5` | Pages to fetch (1-10, default 5) |
| `--format json` | Output format: `text` (default) \| `json` \| `csv` |

Outputs: per-period table with average rating, review count, trend arrows (▲/▼), ASCII sparkline bars, mini star distributions, and overall trend summary.

### `setup <agent>` - Install agent instructions

| Argument / Flag | Description |
|-----------------|-------------|
| `copilot` | Creates `SKILL.md` for GitHub Copilot |
| `claude` | Creates `CLAUDE.md` for Claude Code |
| `cursor` | Creates `.cursor/rules/appstore-reviews.md` |
| `windsurf` | Creates `.windsurfrules` |
| `--force` | Overwrite existing file |
| `--append` | Append to existing file |

**Country codes:** `us` (default), `gb`, `de`, `fr`, `jp`, `au`, `ca`, `nl`, `br`, `kr`

## Python API

```python
from appinsight import get_reviews, get_reviews_df, search

# Search
apps = search("Slack", limit=3)

# As dicts (no pandas needed)
reviews = get_reviews(618783545, stars=2, days=30)

# As pandas DataFrame
df = get_reviews_df(618783545, stars=2, pages=5)
df.groupby("version")["rating"].mean()
df[df["content"].str.contains("crash", case=False)]
# Google Play
reviews = get_reviews("com.Slack", stars=2, days=30, store="google")
df = get_reviews_df("com.Slack", stars=2, pages=5, store="google")
```

Install with pandas: `pip install appstore-review-cli[pandas]`
Install with Google Play: `pip install appstore-review-cli[google]`

## Good to Know

- **Pipe-safe**: Data goes to stdout, progress to stderr.
- **Review limit**: Apple returns max ~500 reviews per country (10 pages × 50). This is Apple's limit.
- **Deduplication**: Reviews are automatically deduplicated across pages.
- **Validation**: `--stars`/`--min-stars` accept 1-5, `--pages` accepts 1-10. Invalid values are rejected.
- **Google Play search**: The first search result sometimes lacks a package name (library limitation). Use the package name directly if your app doesn't appear (find it in the Google Play URL).
- **No results?** Filters are too narrow - try fewer keywords, more days, or a higher star ceiling.

## Development

```bash
git clone https://github.com/vkayatas/appstore-review-cli.git
cd appstore-review-cli
uv sync
uv run pytest
```
