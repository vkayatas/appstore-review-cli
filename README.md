# appstore-review-cli

**Scrape Apple App Store reviews from the terminal. No API keys, no servers, no setup friction.**

Pull reviews for any iOS app, filter by rating/keywords/date, and either let your AI agent analyze them or use the built-in Ollama-powered analysis.

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

## Two Ways to Analyze Reviews

### Path 1: Using an AI coding agent (no extra setup)

If you're using Claude Code, GitHub Copilot, Cursor, or any AI coding agent — **you don't need Ollama**. The agent IS the LLM. Just ask it to fetch and analyze:

> "What are Slack users complaining about this month?"

The agent runs `appstore-reviews reviews ...` to get the data, then analyzes it directly. That's the entire workflow. The review data is clean text the agent can reason over.

### Path 2: Standalone with Ollama (built-in analysis)

If you're working without an AI agent, or want analysis directly in the terminal:

```bash
# Install Ollama: https://ollama.com/download
ollama pull qwen3.5:4b

# Summarize negative reviews
appstore-reviews analyze 803453959 --stars 2 --mode summary

# Find feature gaps
appstore-reviews analyze 803453959 --stars 2 --mode gaps

# Find bugs and crashes
appstore-reviews analyze 803453959 --stars 2 --mode bugs --keywords crash,freeze
```

The `analyze` command fetches reviews, applies your filters, and sends them to a local Ollama model for analysis. No data leaves your machine.

```
appstore-reviews analyze <APP_ID>
    --mode summary|gaps|bugs   Analysis type (default: summary)
    --model qwen3.5:4b         Ollama model to use
    --stars, --days, --keywords, --version, --pages   Same filters as reviews
    --list-models              Show available Ollama models
```

**Don't have Ollama?** You can always pipe raw output to any LLM you prefer:
```bash
appstore-reviews reviews 803453959 --stars 2 --format text | your-llm-command "Summarize:"
```

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

### Get review stats
```bash
appstore-reviews reviews 803453959 --stats
```
Shows rating distribution so you can see the big picture before diving into individual reviews.

### Save for later
```bash
appstore-reviews reviews 803453959 --stars 2 --format json > reviews.json
```

## Usage Examples

Here are real-world scenarios showing how to use the tool:

### Competitor research for a new messaging app
```bash
# Find the big players
appstore-reviews search "messaging" --limit 10

# Pull negative reviews for each
appstore-reviews reviews 310633997 --stars 2 --days 60 --format text   # WhatsApp
appstore-reviews reviews 686449807 --stars 2 --days 60 --format text   # Telegram

# Or analyze directly with Ollama
appstore-reviews analyze 310633997 --stars 2 --days 60 --mode gaps
```

### Check how a specific app version was received
```bash
appstore-reviews reviews 803453959 --version 26.03.20 --stats --format text
```

### Monitor a specific issue across countries
```bash
# Check the same app in multiple regions
appstore-reviews reviews 803453959 --keywords login,auth,password --country us
appstore-reviews reviews 803453959 --keywords login,auth,password --country gb
appstore-reviews reviews 803453959 --keywords login,auth,password --country de
```

### Get JSON for further processing
```bash
# Export to JSON and process with jq
appstore-reviews reviews 803453959 --stars 2 --format json | jq '.[] | .title'

# Save filtered reviews
appstore-reviews reviews 803453959 --stars 1 --days 7 --format json > this_week_1star.json
```

### Ask your AI agent (no Ollama needed)
With Claude Code, Copilot, or Cursor — just ask in natural language:
- *"What are the top 5 complaints about Slack this month?"*
- *"Find crash-related bugs in the latest version of Spotify"*
- *"Compare Notion vs Obsidian — what do users hate about each?"*
- *"What features are German Duolingo users requesting?"*

The agent handles the search, filtering, and analysis for you.

## All Options

**Search:**
```
appstore-reviews search "app name"
    --limit 10             Max results (default: 5)
    --format json          Output as json instead of table
    --country de           App Store region (default: us)
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

This tool integrates with coding agents by design — every agent can run terminal commands, and that's the only integration needed. The agent fetches the reviews, then analyzes them with its own intelligence. No Ollama required.

| Agent | How it works |
|-------|-------------|
| **Claude Code** | Reads `CLAUDE.md` in this repo automatically. Just ask: *"What are Slack users complaining about?"* |
| **GitHub Copilot** | Discovers `SKILL.md` automatically. Ask about app reviews and it invokes the CLI. |
| **Cursor / Windsurf / Others** | Point the agent at `appstore-reviews --help` — it figures out the rest. |
| **No agent?** | Use `appstore-reviews analyze` with Ollama, or pipe output to any LLM. |

## Architecture

```
appinsight/
├── cli.py          # CLI logic (entry point)
├── scraper.py      # Apple RSS/JSON feed parser
├── filters.py      # Rating, date, keyword, version filters
├── formatters.py   # JSON, markdown, plain text output
└── analyzer.py     # Ollama integration for built-in analysis
cli.py              # Thin wrapper (python3 cli.py still works)
SKILL.md            # GitHub Copilot skill definition
CLAUDE.md           # Claude Code integration
```

## Roadmap

- [ ] Google Play Store support
- [ ] Multi-app comparison (`compare` command)
- [ ] Export to CSV
- [ ] Version diff (sentiment changes between releases)
- [ ] More analysis modes (trend detection, sentiment over time)
