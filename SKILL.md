---
name: appstore-reviews
description: "Scrape and analyze Apple App Store reviews. Use when analyzing competitor apps, finding user complaints, identifying feature gaps, or hunting bugs from reviews."
---

# appstore-review-cli — App Store Review Scraper

You have access to a CLI tool that scrapes Apple App Store reviews. Use it when the user asks about competitor analysis, app reviews, user complaints, feature gaps, or bug reports from app stores.

## Available Commands

### 1. Search for an app
```bash
appstore-reviews search "app name"
```
If not installed, use: `python3 cli.py search "app name"`

Returns app IDs, names, ratings. Use this first to find the numeric app ID.

### 2. Fetch and filter reviews
```bash
appstore-reviews reviews <APP_ID> [options]
```
If not installed, use: `python3 cli.py reviews <APP_ID> [options]`

**Options:**
- `--stars 2` — Only 1-2 star reviews (negative sentiment)
- `--days 30` — Only reviews from the last 30 days
- `--keywords crash,freeze,bug` — Only reviews mentioning these words
- `--version 5.0.1` — Only reviews for a specific version
- `--pages 5` — Fetch more pages (1-10, default 3)
- `--format json|text|markdown` — Output format
- `--stats` — Show rating distribution
- `--country de` — Use a different App Store region

## Analysis Modes

When the user asks for analysis, first fetch the relevant reviews, then apply one of these approaches:

### Gap Finder
Fetch 1-2 star reviews. Look for patterns of "I wish it had...", "competitors do X better", "missing feature". Group by feature category and rank by frequency.

### Bug Hunter
Fetch 1-2 star reviews with `--keywords crash,bug,freeze,error,broken,slow,stuck`. Group by symptom, identify affected versions, and rank by severity.

## Example Workflows

**"What are users complaining about in Slack?"**
```bash
python3 cli.py search "Slack"
# Find the app ID from results
python3 cli.py reviews 803453959 --stars 2 --days 60 --format text --stats
```

**"Find payment bugs in Spotify"**
```bash
python3 cli.py reviews 324684580 --stars 2 --keywords payment,subscribe,charge,billing --format text
```

**"Compare negative reviews for two apps"**
```bash
python3 cli.py reviews <APP_A_ID> --stars 2 --format json > /tmp/app_a.json
python3 cli.py reviews <APP_B_ID> --stars 2 --format json > /tmp/app_b.json
```
Then compare the two JSON outputs for overlapping and unique complaints.
