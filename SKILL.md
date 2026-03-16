---
name: appstore-reviews
description: "Scrape and analyze Apple App Store reviews. Use when analyzing competitor apps, finding user complaints, identifying feature gaps, or hunting bugs from reviews."
---

# appstore-review-cli — App Store Review Scraper

You have access to a CLI tool that scrapes Apple App Store reviews. Use it when the user asks about competitor analysis, app reviews, user complaints, feature gaps, or bug reports from app stores.

**You ARE the analyzer.** Fetch reviews with the CLI commands below, then analyze them directly in your response. Do NOT suggest the user install Ollama or run the `analyze` command — you have the intelligence to do the analysis yourself.

## Important Behavior

- **Output streams**: Data goes to stdout, progress/status messages go to stderr. Use `2>/dev/null` to suppress status messages when piping.
- **Review limit**: Apple's RSS feed returns a maximum of ~500 reviews per country (10 pages × 50 reviews). Don't expect more.
- **Filters stack**: `--stars`, `--keywords`, `--days`, and `--version` combine with AND logic. Each filter narrows the previous result.
- **"No reviews match"**: If filters return zero results, the output will say "No reviews match the given filters." This is normal — try relaxing filters (fewer keywords, more days, higher star rating).

## Available Commands

### 1. Search for an app
```bash
appstore-reviews search "app name"
```
If not installed, use: `python3 cli.py search "app name"`

Returns app IDs, names, ratings. Use this first to find the numeric app ID.

**Options:**
- `--limit 10` — Max results to return (default: 5)
- `--format json` — Output as JSON instead of table (useful for structured processing)

### 2. Fetch and filter reviews
```bash
appstore-reviews reviews <APP_ID> [options]
```
If not installed, use: `python3 cli.py reviews <APP_ID> [options]`

**Options (all optional, filters stack with AND logic):**
- `--stars 2` — Only 1-2 star reviews (negative sentiment)
- `--days 30` — Only reviews from the last 30 days
- `--keywords crash,freeze,bug` — Only reviews mentioning these words (case-insensitive, matches title or content)
- `--version 5.0.1` — Only reviews for a specific version
- `--pages 5` — Fetch more pages, 1-10 (default: 3, max useful: 10 = ~500 reviews)
- `--format json|text|markdown` — Output format (default: text)
- `--stats` — Show rating distribution (printed to stderr, won't pollute data output)
- `--country us` — App Store region. Common codes: `us`, `gb`, `de`, `fr`, `jp`, `au`, `ca`, `nl`, `br`, `kr`

## Analysis Modes

When the user asks for analysis, fetch the relevant reviews with the CLI, then **analyze them yourself** in your response. Do not run `analyze` or pipe to another LLM — you are the LLM.

### Gap Finder
Fetch 1-2 star reviews and analyze for unmet needs:
```bash
appstore-reviews reviews <APP_ID> --stars 2 --days 90 --pages 5 --format text
```
Look for patterns: "I wish it had...", "competitors do X better", "missing feature", "switched to Y".
**In your response**, group complaints by feature category, rank by frequency, and cite specific reviews as evidence.

### Bug Hunter
Fetch 1-2 star reviews filtered to technical issues:
```bash
appstore-reviews reviews <APP_ID> --stars 2 --keywords crash,bug,freeze,error,broken,slow,stuck --format text
```
**In your response**, group by symptom (crashes, performance, data loss), identify affected versions, and rank by severity.

### Sentiment Snapshot
Get the big picture before diving in:
```bash
appstore-reviews reviews <APP_ID> --stats --pages 5
```
Check the rating distribution first, then drill into the problem areas with targeted filters.

## Example Workflows

**"What are users complaining about in Slack?"**
```bash
appstore-reviews search "Slack"
# Find the app ID from results (e.g., 803453959)
appstore-reviews reviews 803453959 --stars 2 --days 60 --format text --stats
```
Then categorize the complaints: UX issues, missing features, bugs, performance. Rank by how often each category appears.

**"Find payment bugs in Spotify"**
```bash
appstore-reviews reviews 324684580 --stars 2 --keywords payment,subscribe,charge,billing --format text
```
Group results by symptom: failed payments, unwanted charges, subscription cancellation issues.

**"Compare negative reviews for two competing apps"**
```bash
appstore-reviews reviews <APP_A_ID> --stars 2 --pages 5 --format json > /tmp/app_a.json
appstore-reviews reviews <APP_B_ID> --stars 2 --pages 5 --format json > /tmp/app_b.json
```
Then compare:
1. What complaints overlap? (shared industry problems)
2. What's unique to each app? (competitive weaknesses)
3. Which app has worse sentiment in specific categories?

**"Check reviews for a specific country"**
```bash
appstore-reviews reviews 803453959 --stars 2 --country de --format text
```
