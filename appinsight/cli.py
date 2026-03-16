#!/usr/bin/env python3
"""AppInsight CLI — Scrape and filter App Store reviews from the terminal.

Usage:
    python3 cli.py search "WhatsApp"
    python3 cli.py reviews 310633997 --stars 2 --days 30
    python3 cli.py reviews 310633997 --keywords crash,freeze --format json
"""

import argparse
import sys

from .scraper import search_app, lookup_app, fetch_reviews
from .filters import apply_filters
from .formatters import to_json, to_markdown, to_text, summary_stats
from .analyzer import analyze, check_ollama, list_models


def cmd_search(args):
    """Search the App Store by name."""
    apps = search_app(args.query, country=args.country, limit=args.limit)
    if not apps:
        print(f"No apps found for '{args.query}'", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(to_json_apps(apps))
    else:
        print(f"{'ID':<12} {'Rating':>6} {'Reviews':>10}  Name")
        print("-" * 60)
        for a in apps:
            print(f"{a.app_id:<12} {a.avg_rating:>5.1f}⭐ {a.rating_count:>10,}  {a.name}")


def cmd_reviews(args):
    """Fetch and filter reviews."""
    app_id = args.app_id

    # Show what we're fetching
    app = lookup_app(app_id, country=args.country)
    if app:
        print(f"Fetching reviews for: {app.name} (by {app.developer})", file=sys.stderr)
    else:
        print(f"Fetching reviews for app ID: {app_id}", file=sys.stderr)

    reviews = fetch_reviews(app_id, country=args.country, pages=args.pages)
    print(f"Fetched {len(reviews)} reviews", file=sys.stderr)

    # Apply filters
    keywords = args.keywords.split(",") if args.keywords else None
    reviews = apply_filters(
        reviews,
        max_rating=args.stars,
        keywords=keywords,
        days=args.days,
        version=args.version,
    )
    print(f"After filtering: {len(reviews)} reviews", file=sys.stderr)

    # Stats always go to stderr so they don't pollute the data output
    if args.stats:
        print("\n" + summary_stats(reviews), file=sys.stderr)

    # Output
    if args.format == "json":
        print(to_json(reviews))
    elif args.format == "markdown":
        print(to_markdown(reviews))
    else:
        print(to_text(reviews))


def cmd_analyze(args):
    """Fetch reviews, filter, and analyze with a local LLM via Ollama."""
    app_id = args.app_id

    # Check Ollama first
    if not check_ollama():
        print("Error: Ollama is not running. Start it with: ollama serve", file=sys.stderr)
        print("Install from: https://ollama.com/download", file=sys.stderr)
        sys.exit(1)

    # Show available models if requested
    if args.list_models:
        models = list_models()
        if models:
            print("Available Ollama models:")
            for m in models:
                print(f"  {m}")
        else:
            print("No models found. Pull one with: ollama pull qwen3.5:4b")
        return

    # Fetch
    app = lookup_app(app_id, country=args.country)
    if app:
        print(f"Fetching reviews for: {app.name} (by {app.developer})", file=sys.stderr)
    else:
        print(f"Fetching reviews for app ID: {app_id}", file=sys.stderr)

    reviews = fetch_reviews(app_id, country=args.country, pages=args.pages)
    print(f"Fetched {len(reviews)} reviews", file=sys.stderr)

    # Apply filters
    keywords = args.keywords.split(",") if args.keywords else None
    reviews = apply_filters(
        reviews,
        max_rating=args.stars,
        keywords=keywords,
        days=args.days,
        version=args.version,
    )
    print(f"After filtering: {len(reviews)} reviews", file=sys.stderr)

    if not reviews:
        print("No reviews match the given filters. Try relaxing your filters.", file=sys.stderr)
        sys.exit(0)

    # Analyze
    print(f"\nAnalyzing with {args.model} (mode: {args.mode})...\n", file=sys.stderr)
    result = analyze(reviews, mode=args.mode, model=args.model, stream=True)

    # Also print to stdout (streaming went to stderr)
    print(result)


def to_json_apps(apps):
    """Quick JSON serializer for app search results."""
    import json
    return json.dumps([a.to_dict() for a in apps], indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        prog="appstore-reviews",
        description="Scrape and filter Apple App Store reviews. Built for coding agents.",
    )
    parser.add_argument("--country", default="us", help="ISO country code (default: us)")

    sub = parser.add_subparsers(dest="command", required=True)

    # --- search ---
    p_search = sub.add_parser("search", help="Search for an app by name")
    p_search.add_argument("query", help="App name to search for")
    p_search.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    p_search.add_argument("--format", choices=["table", "json"], default="table")

    # --- reviews ---
    p_reviews = sub.add_parser("reviews", help="Fetch and filter reviews")
    p_reviews.add_argument("app_id", type=int, help="Numeric App Store ID (use 'search' to find it)")
    p_reviews.add_argument("--stars", type=int, default=None, help="Max star rating to include (e.g. 2 = 1-2 stars)")
    p_reviews.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_reviews.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_reviews.add_argument("--version", default=None, help="Filter by app version")
    p_reviews.add_argument("--pages", type=int, default=3, help="Pages to fetch, 1-10 (default: 3)")
    p_reviews.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p_reviews.add_argument("--stats", action="store_true", help="Show rating distribution stats")

    # --- analyze ---
    p_analyze = sub.add_parser("analyze", help="Fetch reviews and analyze with a local LLM (Ollama)")
    p_analyze.add_argument("app_id", type=int, nargs="?", default=None, help="Numeric App Store ID")
    p_analyze.add_argument("--mode", choices=["summary", "gaps", "bugs"], default="summary",
                           help="Analysis mode: summary, gaps (feature gaps), bugs (technical issues)")
    p_analyze.add_argument("--model", default="qwen3.5:4b", help="Ollama model to use (default: qwen3.5:4b)")
    p_analyze.add_argument("--stars", type=int, default=None, help="Max star rating to include")
    p_analyze.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_analyze.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_analyze.add_argument("--version", default=None, help="Filter by app version")
    p_analyze.add_argument("--pages", type=int, default=3, help="Pages to fetch, 1-10 (default: 3)")
    p_analyze.add_argument("--list-models", action="store_true", help="List available Ollama models and exit")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "reviews":
        cmd_reviews(args)
    elif args.command == "analyze":
        if args.app_id is None and not args.list_models:
            p_analyze.error("app_id is required (unless using --list-models)")
        cmd_analyze(args)


if __name__ == "__main__":
    main()
