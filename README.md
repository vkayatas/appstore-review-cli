# appstore-review-cli

**Scrape Apple App Store reviews from the terminal. No API keys, no servers, no setup friction.**

Pull reviews for any iOS app, filter by rating/keywords/date, and get clean output you can pipe into an AI agent or analyze yourself.

## Quick Start

```bash
# Install
uv sync            # or: pip install -e .

# 1. Find an app (returns the numeric ID you need)
appstore-reviews search "Slack"
#  ID           Rating    Reviews  Name
#  803453959      4.3⭐  1,247,800  Slack

# 2. Get negative reviews from the last 30 days
appstore-reviews reviews 803453959 --stars 2 --days 30

# 3. Filter by keywords
appstore-reviews reviews 803453959 --keywords crash,freeze,notification

# 4. Combine filters (they stack with AND logic)
appstore-reviews reviews 803453959 --stars 2 --days 30 --keywords crash,freeze
```

Three commands to go from app name → filtered reviews.

## What Can You Do With This?

### Find what users hate about a competitor
```bash
appstore-reviews reviews 803453959 --stars 2 --days 30 --format text
```
Look for patterns: "I wish it had…", "missing feature", "switched to X". These are feature gaps you can build into your own product.

### Hunt for bugs in any app
```bash
appstore-reviews reviews 803453959 --keywords crash,bug,freeze,error,slow --stars 2
```
Surface the technical failures users are reporting. Group by symptom, identify affected versions.

### Feed reviews to an AI agent for analysis
```bash
# Pipe directly to a local model
appstore-reviews reviews 803453959 --stars 2 --format text \
  | ollama run qwen3.5:4b "Summarize the top 5 complaints:"

# Or save for later
appstore-reviews reviews 803453959 --stars 2 --format json > reviews.json
```

### Get review stats
```bash
appstore-reviews reviews 803453959 --stats
```
Shows rating distribution so you can see the big picture before diving into individual reviews.

## All Options

**Search:**
```
appstore-reviews search "app name"
    --limit 10             Max results (default: 5)
    --format json          Output as json instead of table
```

**Reviews:**
```
appstore-reviews reviews <APP_ID>
    --stars 2              Max star rating to include (1-2 = negative only)
    --days 30              Only reviews from the last N days
    --keywords crash,bug   Only reviews containing these words (case-insensitive)
    --version 5.0.1        Only reviews for a specific app version
    --pages 5              Pages to fetch (1-10, default 3, max useful: 10 = ~500 reviews)
    --format json          Output as json | text | markdown (default: text)
    --stats                Show rating distribution
    --country de           App Store region (default: us)
```

All filters stack with AND logic — combine `--stars`, `--keywords`, `--days`, and `--version` to narrow results.

**Country codes:** `us` (default), `gb`, `de`, `fr`, `jp`, `au`, `ca`, `nl`, `br`, `kr`

## Good to Know

- **Output streams**: Review data goes to stdout, progress/status to stderr. Safe to pipe directly.
- **Review limit**: Apple's RSS feed returns a max of ~500 reviews per country (10 pages × 50). This is an Apple limitation.
- **No reviews?** "No reviews match the given filters" means filters are too narrow. Try fewer keywords, more days, or a higher star ceiling.

## Setup

```bash
# With uv (recommended)
uv sync

# Or with pip
pip install -e .
```

After install, the `appstore-reviews` command works globally. You can also run directly without installing:
```bash
python3 cli.py search "Slack"
python3 cli.py reviews 803453959 --stars 2
```

## Works With Any AI Coding Agent

This tool integrates with coding agents by design — every agent can run terminal commands, and that's the only integration needed.

| Agent | How it works |
|-------|-------------|
| **Claude Code** | Reads `CLAUDE.md` in this repo automatically. Just ask: *"What are Slack users complaining about?"* |
| **GitHub Copilot** | Discovers `SKILL.md` automatically. Ask about app reviews and it invokes the CLI. |
| **Cursor / Windsurf / Others** | Point the agent at `appstore-reviews --help` — it figures out the rest. |

No MCP server, no protocol boilerplate, no running processes. Just a CLI that outputs clean text.

## Architecture

```
appinsight/
├── cli.py          # CLI logic (entry point)
├── scraper.py      # Apple RSS/JSON feed parser
├── filters.py      # Rating, date, keyword, version filters
└── formatters.py   # JSON, markdown, plain text output
cli.py              # Thin wrapper (python3 cli.py still works)
SKILL.md            # GitHub Copilot skill definition
CLAUDE.md           # Claude Code integration
```

## Roadmap

- [ ] Google Play Store support
- [ ] Multi-app comparison (`compare` command)
- [ ] Built-in Ollama analysis modes (gap finder, bug hunter)
- [ ] Export to CSV
- [ ] Version diff (sentiment changes between releases)
