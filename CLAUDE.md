# appstore-review-cli — App Store Review Scraper

This project contains a CLI tool for scraping Apple App Store reviews. Use it to analyze competitor apps, find user complaints, and identify feature gaps.

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

## Analysis Patterns

When asked to analyze reviews, fetch them first with the CLI, then reason over the output:
- **Gap Finder**: Use `--stars 2` and look for "wish it had", "missing", "competitor does X". Group by feature category and rank by frequency.
- **Bug Hunter**: Use `--stars 2 --keywords crash,bug,freeze,error,broken,slow`. Group by symptom, identify affected versions, rank by severity.
- **Sentiment Snapshot**: Run with `--stats --pages 5` first to see the rating distribution before drilling into details.
