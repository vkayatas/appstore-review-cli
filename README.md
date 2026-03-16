# appstore-review-cli

**Scrape App Store reviews. Filter the noise. Feed the signal to your coding agent.**

A CLI tool that pulls Apple App Store reviews, filters for negative sentiment, and outputs clean data for AI coding agents (Claude Code, GitHub Copilot, Cursor) to analyze. No API keys. No servers. No MCP overhead. Just a script that outputs text.

## Why This Exists

Every AI coding agent can run terminal commands. That's the entire integration. No MCP server to host, no protocol boilerplate, no running processes — just `python3 cli.py reviews <app_id> --stars 2` and the agent gets structured review data it can reason over.

**The insight:** Coding agents don't need a special protocol to use external tools. They need a CLI that produces clean output. This is the [cli-anything](https://github.com/nicobailey/cli-anything) philosophy applied to competitive intelligence.

### What You Get
- **Competitor gap analysis** — scrape 1-2 star reviews to find what users are begging for
- **Bug hunting** — filter by keywords like "crash", "freeze", "payment" to surface technical failures
- **Pre-filtered data** — reduce hundreds of reviews to the signal that matters *before* the LLM sees it (saves tokens, improves quality)
- **No dependencies on external services** — uses Apple's public RSS feed, no API keys

## Setup

```bash
# With uv (recommended)
uv sync

# Or with pip
pip install -e .
```

After install, the `appstore-reviews` command is available globally:
```bash
appstore-reviews search "Slack"
appstore-reviews reviews 618783545 --stars 2
```

Or run directly without installing:
```bash
uv run python3 cli.py search "Slack"
```

### For local LLM users
```bash
# Install Ollama: https://ollama.com/download
ollama run qwen3.5:4b
```

## Usage

### Find an app
```bash
python3 cli.py search "Slack"
```
```
ID           Rating    Reviews  Name
------------------------------------------------------------
803453959      4.3⭐  1,247,800  Slack
```

### Scrape negative reviews
```bash
python3 cli.py reviews 803453959 --stars 2 --days 30 --stats
```

### Filter by keywords
```bash
python3 cli.py reviews 803453959 --keywords crash,freeze,notification --format json
```

### All options
```
python3 cli.py reviews <APP_ID>
    --stars 2              Max rating (1-2 stars only)
    --days 30              Last 30 days
    --keywords crash,bug   Must contain these words
    --version 5.0.1        Specific app version
    --pages 5              Pages to fetch (1-10)
    --format json          json | text | markdown
    --stats                Show distribution
    --country de           App Store region
```

## Agent Integration

### Claude Code
Just use it. Claude Code reads the `CLAUDE.md` in this repo and knows how to call the CLI. Ask it:
> "What are Slack users complaining about this month?"

### GitHub Copilot (VS Code)
This repo includes a `SKILL.md`. Copilot auto-discovers it and can invoke the CLI when you ask about app reviews. Works via the `/appinsight` slash command.

### Cursor / Windsurf / Any Agent
Any agent that can run terminal commands can use this tool. Point it at `cli.py --help` and it figures it out.

### Pipe to LLM
```bash
# Direct pipe to a local model
python3 cli.py reviews 803453959 --stars 2 --format text | ollama run qwen3.5:4b "Summarize the top complaints:"

# Save and analyze
python3 cli.py reviews 803453959 --stars 2 --format json > reviews.json
```

## Architecture

```
appinsight/
├── __init__.py
├── cli.py          # CLI logic (entry point for pyproject.toml)
├── scraper.py      # Apple RSS/JSON feed parser (no API key needed)
├── filters.py      # Rating, date, keyword, version filters
└── formatters.py   # JSON, markdown table, plain text output
cli.py              # Thin wrapper (`python3 cli.py` still works)
pyproject.toml      # Modern Python packaging with uv
SKILL.md            # Copilot Skill definition
CLAUDE.md           # Claude Code integration
```

**Design decisions:**
- **No MCP** — MCP requires a running server process for what is fundamentally "run a command, get text." A CLI is simpler, more portable, and works with every agent.
- **No embedded LLM** — The coding agent *is* the LLM. This tool's job is to fetch and filter, not analyze. (Local LLM analysis planned for v2.)
- **Pre-filtering > post-analysis** — Filtering 500 reviews down to 30 keyword-matched 1-star reviews before the LLM sees them produces better analysis than dumping everything.

## Roadmap

- [ ] Google Play Store support
- [ ] Multi-app comparison (`compare` command)
- [ ] Built-in Ollama analysis modes (gap finder, bug hunter)
- [ ] Export to CSV
- [ ] Version diff (sentiment changes between releases)
