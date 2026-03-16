# appstore-review-cli — App Store Review Scraper

This project contains a CLI tool for scraping Apple App Store reviews. Use it to analyze competitor apps, find user complaints, and identify feature gaps.

## Quick Reference

Search for an app:
```bash
appstore-reviews search "app name"
```
Fallback: `python3 cli.py search "app name"`

Fetch negative reviews:
```bash
appstore-reviews reviews <APP_ID> --stars 2 --days 30 --format text
```

Fetch reviews with keyword filter:
```bash
appstore-reviews reviews <APP_ID> --keywords crash,bug,slow --format text
```

All options: `appstore-reviews reviews --help`

## Analysis Patterns

When asked to analyze reviews, fetch them first with the CLI, then reason over the output:
- **Gap Finder**: Use `--stars 2` and look for "wish it had", "missing", "competitor does X"
- **Bug Hunter**: Use `--stars 2 --keywords crash,bug,freeze,error,broken,slow`
