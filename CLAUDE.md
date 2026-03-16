# appstore-review-cli — App Store Review Scraper

This project contains a CLI tool for scraping Apple App Store reviews. Use it to analyze competitor apps, find user complaints, and identify feature gaps.

**You ARE the analyzer.** Fetch reviews with the CLI, then reason over them directly. Do NOT suggest the user install Ollama or use the `analyze` command — you can do the analysis yourself.

## Quick Reference

Search for an app:
```bash
appstore-reviews search "app name"
```
Fallback: `python3 cli.py search "app name"`

Search with more results or JSON output:
```bash
appstore-reviews search "app name" --limit 10 --format json
```

Fetch negative reviews:
```bash
appstore-reviews reviews <APP_ID> --stars 2 --days 30 --format text
```

Fetch reviews with keyword filter:
```bash
appstore-reviews reviews <APP_ID> --keywords crash,bug,slow --format text
```

Combine filters (AND logic — all filters stack):
```bash
appstore-reviews reviews <APP_ID> --stars 2 --days 30 --keywords crash,freeze --version 5.0.1
```

All options: `appstore-reviews reviews --help`

## Important Behavior

- **Output streams**: Data goes to stdout, progress/status goes to stderr. Pipe-safe by default.
- **Review limit**: Apple's RSS feed returns max ~500 reviews per country (10 pages × 50). Use `--pages 10` for maximum coverage.
- **No results?**: "No reviews match the given filters" means filters are too narrow. Try fewer keywords, more days, or higher star ceiling.
- **Country codes**: Default is `us`. Common alternatives: `gb`, `de`, `fr`, `jp`, `au`, `ca`, `nl`, `br`, `kr`.

## How to Analyze (You Do This Yourself)

When asked to analyze reviews, use the CLI to fetch them, then reason over the output directly:

1. **Gap Finder**: Use `--stars 2` and look for "wish it had", "missing", "competitor does X". Group by feature category and rank by frequency.
2. **Bug Hunter**: Use `--stars 2 --keywords crash,bug,freeze,error,broken,slow`. Group by symptom, identify affected versions, rank by severity.
3. **Sentiment Snapshot**: Run with `--stats --pages 5` first to see the rating distribution before drilling into details.

Do NOT pipe output to Ollama or another external LLM. Analyze the review text yourself and present structured findings to the user.

## Example Workflows

**User asks: "What are Slack users complaining about?"**
```bash
appstore-reviews search "Slack"
# Get the app ID → 618783545
appstore-reviews reviews 618783545 --stars 2 --days 60 --format text --stats
```
Then categorize the complaints in your response: UX issues, missing features, bugs, performance. Rank by frequency.

**User asks: "Find crash reports for WhatsApp"**
```bash
appstore-reviews search "WhatsApp"
appstore-reviews reviews <APP_ID> --stars 2 --keywords crash,freeze,error,broken,stuck --format text
```
Group by symptom in your response, note affected versions, rank by severity.

**User asks: "Compare Spotify vs Apple Music reviews"**
```bash
appstore-reviews search "Spotify"
appstore-reviews reviews 324684580 --stars 2 --pages 5 --format text
appstore-reviews search "Apple Music"
appstore-reviews reviews 1108187390 --stars 2 --pages 5 --format text
```
Compare: overlapping complaints (shared industry problems), unique weaknesses per app, which has worse sentiment in key categories.

**User asks: "What do German users think of Duolingo?"**
```bash
appstore-reviews search "Duolingo"
appstore-reviews reviews <APP_ID> --stars 2 --country de --days 90 --format text
```
Analyze with awareness that reviews may be in German.

**User asks: "What changed in the latest version of Notion?"**
```bash
appstore-reviews search "Notion"
appstore-reviews reviews <APP_ID> --days 14 --format text --stats
```
Look for mentions of recent changes, new bugs, or praise for new features.
