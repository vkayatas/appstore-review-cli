#!/usr/bin/env python3
"""AppInsight CLI — Scrape and filter App Store reviews from the terminal.

Usage:
    python3 cli.py search "WhatsApp"
    python3 cli.py reviews 310633997 --stars 2 --days 30
    python3 cli.py reviews 310633997 --keywords crash,freeze --format json
"""

import argparse
import sys

import requests

from .scraper import search_app, lookup_app, fetch_reviews
from .filters import apply_filters
from .formatters import to_json, to_csv, to_markdown, to_text, summary_stats
from .analyzer import analyze, check_ollama, list_models
from .compare import compare_apps
from .version_diff import version_diff
from .trend import trend as trend_report
from .setup import cmd_setup, AGENTS

STORES = ["apple", "google"]


def cmd_search(args):
    """Search the App Store or Google Play by name."""
    try:
        if args.store == "google":
            from .google_play import search_play
            apps = search_play(args.query, country=args.country, limit=args.limit)
        else:
            apps = search_app(args.query, country=args.country, limit=args.limit)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Error: Failed to search: {e}", file=sys.stderr)
        sys.exit(1)

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

    try:
        if args.store == "google":
            from .google_play import lookup_play, fetch_play_reviews
            app = lookup_play(app_id, country=args.country)
            reviews = fetch_play_reviews(app_id, country=args.country, pages=args.pages)
        else:
            try:
                int(app_id)
            except ValueError:
                print(f"Error: Apple App Store IDs must be numeric (got '{app_id}'). "
                      "Did you mean --store google?", file=sys.stderr)
                sys.exit(1)
            try:
                app = lookup_app(app_id, country=args.country)
            except requests.RequestException:
                app = None
            reviews = fetch_reviews(app_id, country=args.country, pages=args.pages)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if app:
        print(f"Fetching reviews for: {app.name} (by {app.developer})", file=sys.stderr)
    else:
        print(f"Fetching reviews for app ID: {app_id}", file=sys.stderr)
    print(f"Fetched {len(reviews)} reviews", file=sys.stderr)

    # Apply filters
    keywords = args.keywords.split(",") if args.keywords else None
    reviews = apply_filters(
        reviews,
        max_rating=args.stars,
        min_rating=args.min_stars,
        keywords=keywords,
        days=args.days,
        version=args.version,
        sort_by=args.sort,
    )
    print(f"After filtering: {len(reviews)} reviews", file=sys.stderr)

    # Stats always go to stderr so they don't pollute the data output
    if args.stats:
        print("\n" + summary_stats(reviews), file=sys.stderr)

    # Output
    if args.format == "json":
        print(to_json(reviews))
    elif args.format == "csv":
        print(to_csv(reviews), end="")
    elif args.format == "markdown":
        print(to_markdown(reviews))
    else:
        print(to_text(reviews))


def cmd_analyze(args):
    """Fetch reviews, filter, and analyze with a local LLM via Ollama."""
    # Show available models if requested (before Ollama check so it works even as a quick probe)
    if args.list_models:
        if not check_ollama():
            print("Ollama is not running. Start it with: ollama serve", file=sys.stderr)
            print("Install from: https://ollama.com/download", file=sys.stderr)
            sys.exit(1)
        models = list_models()
        if models:
            print("Available Ollama models:")
            for m in models:
                print(f"  {m}")
        else:
            print("No models found. Pull one with: ollama pull qwen3.5:4b")
        return

    app_id = args.app_id

    # Check Ollama
    if not check_ollama():
        print("Error: Ollama is not running. Start it with: ollama serve", file=sys.stderr)
        print("Install from: https://ollama.com/download", file=sys.stderr)
        sys.exit(1)

    # Fetch
    try:
        if args.store == "google":
            from .google_play import lookup_play, fetch_play_reviews
            app = lookup_play(args.app_id, country=args.country)
            reviews = fetch_play_reviews(args.app_id, country=args.country, pages=args.pages)
        else:
            try:
                int(args.app_id)
            except ValueError:
                print(f"Error: Apple App Store IDs must be numeric (got '{args.app_id}'). "
                      "Did you mean --store google?", file=sys.stderr)
                sys.exit(1)
            try:
                app = lookup_app(app_id, country=args.country)
            except requests.RequestException:
                app = None
            reviews = fetch_reviews(app_id, country=args.country, pages=args.pages)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if app:
        print(f"Fetching reviews for: {app.name} (by {app.developer})", file=sys.stderr)
    else:
        print(f"Fetching reviews for app ID: {app_id}", file=sys.stderr)
    print(f"Fetched {len(reviews)} reviews", file=sys.stderr)

    # Apply filters
    keywords = args.keywords.split(",") if args.keywords else None
    reviews = apply_filters(
        reviews,
        max_rating=args.stars,
        min_rating=args.min_stars,
        keywords=keywords,
        days=args.days,
        version=args.version,
        sort_by=args.sort,
    )
    print(f"After filtering: {len(reviews)} reviews", file=sys.stderr)

    if not reviews:
        print("No reviews match the given filters. Try relaxing your filters.", file=sys.stderr)
        sys.exit(0)

    # Stats
    if args.stats:
        print("\n" + summary_stats(reviews), file=sys.stderr)

    # Analyze
    print(f"\nAnalyzing with {args.model} (mode: {args.mode})...\n", file=sys.stderr)
    result = analyze(reviews, mode=args.mode, model=args.model, stream=True)

    # Also print to stdout (streaming went to stderr)
    print(result)


def to_json_apps(apps):
    """Quick JSON serializer for app search results."""
    import json
    return json.dumps([a.to_dict() for a in apps], indent=2, ensure_ascii=False)


def cmd_compare(args):
    """Compare reviews across multiple apps."""
    if args.store == "apple":
        for aid in args.app_ids:
            try:
                int(aid)
            except ValueError:
                print(f"Error: Apple App Store IDs must be numeric (got '{aid}'). "
                      "Did you mean --store google?", file=sys.stderr)
                sys.exit(1)
    keywords = args.keywords.split(",") if args.keywords else None
    try:
        result = compare_apps(
            app_ids=args.app_ids,
            country=args.country,
            pages=args.pages,
            max_rating=args.stars,
            min_rating=args.min_stars,
            keywords=keywords,
            days=args.days,
            sort_by=args.sort,
            store=args.store,
            format=args.format,
        )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(result)


def cmd_version_diff(args):
    """Compare sentiment between app versions."""
    if args.store == "apple":
        try:
            int(args.app_id)
        except ValueError:
            print(f"Error: Apple App Store IDs must be numeric (got '{args.app_id}'). "
                  "Did you mean --store google?", file=sys.stderr)
            sys.exit(1)
    keywords = args.keywords.split(",") if args.keywords else None
    try:
        result = version_diff(
            app_id=args.app_id,
            country=args.country,
            pages=args.pages,
            old_version=args.old,
            new_version=args.new,
            max_rating=args.stars,
            min_rating=args.min_stars,
            keywords=keywords,
            days=args.days,
            store=args.store,
            format=args.format,
        )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(result)


def cmd_trend(args):
    """Show rating trend over time."""
    if args.store == "apple":
        try:
            int(args.app_id)
        except ValueError:
            print(f"Error: Apple App Store IDs must be numeric (got '{args.app_id}'). "
                  "Did you mean --store google?", file=sys.stderr)
            sys.exit(1)
    keywords = args.keywords.split(",") if args.keywords else None
    try:
        result = trend_report(
            app_id=args.app_id,
            country=args.country,
            pages=args.pages,
            period=args.period,
            max_rating=args.stars,
            min_rating=args.min_stars,
            keywords=keywords,
            days=args.days,
            store=args.store,
            format=args.format,
        )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(result)


def main():
    parser = argparse.ArgumentParser(
        prog="appstore-reviews",
        description="Scrape and filter App Store & Google Play reviews. Built for coding agents.",
    )
    parser.add_argument("--country", default="us", help="ISO country code (default: us)")
    parser.add_argument("--store", choices=STORES, default="apple",
                        help="App store: apple (default) or google")

    sub = parser.add_subparsers(dest="command", required=True)

    # --- search ---
    p_search = sub.add_parser("search", help="Search for an app by name")
    p_search.add_argument("query", help="App name to search for")
    p_search.add_argument("--limit", type=int, default=5, help="Max results (default: 5)")
    p_search.add_argument("--format", choices=["table", "json"], default="table")

    # --- reviews ---
    p_reviews = sub.add_parser("reviews", help="Fetch and filter reviews")
    p_reviews.add_argument("app_id", help="Numeric App Store ID or Google Play package name")
    p_reviews.add_argument("--stars", type=int, default=None, choices=range(1, 6),
                           help="Max star rating to include (e.g. 2 = 1-2 stars)", metavar="STARS")
    p_reviews.add_argument("--min-stars", type=int, default=None, choices=range(1, 6),
                           help="Min star rating to include (e.g. 3 = 3+ stars)", metavar="STARS")
    p_reviews.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_reviews.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_reviews.add_argument("--version", default=None, help="Filter by app version")
    p_reviews.add_argument("--pages", type=int, default=3, choices=range(1, 11),
                           help="Pages to fetch, 1-10 (default: 3)", metavar="PAGES")
    p_reviews.add_argument("--format", choices=["text", "json", "csv", "markdown"], default="text")
    p_reviews.add_argument("--sort", choices=["date", "rating", "votes"], default=None,
                           help="Sort order: date (newest), rating (lowest), votes (most helpful)")
    p_reviews.add_argument("--stats", action="store_true", help="Show rating distribution stats")

    # --- analyze ---
    p_analyze = sub.add_parser("analyze", help="Fetch reviews and analyze with a local LLM (Ollama)")
    p_analyze.add_argument("app_id", nargs="?", default=None,
                           help="Numeric App Store ID or Google Play package name")
    p_analyze.add_argument("--mode", choices=["summary", "gaps", "bugs"], default="summary",
                           help="Analysis mode: summary, gaps (feature gaps), bugs (technical issues)")
    p_analyze.add_argument("--model", default="qwen3.5:4b", help="Ollama model to use (default: qwen3.5:4b)")
    p_analyze.add_argument("--stars", type=int, default=None, choices=range(1, 6),
                           help="Max star rating to include", metavar="STARS")
    p_analyze.add_argument("--min-stars", type=int, default=None, choices=range(1, 6),
                           help="Min star rating to include", metavar="STARS")
    p_analyze.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_analyze.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_analyze.add_argument("--version", default=None, help="Filter by app version")
    p_analyze.add_argument("--pages", type=int, default=3, choices=range(1, 11),
                           help="Pages to fetch, 1-10 (default: 3)", metavar="PAGES")
    p_analyze.add_argument("--sort", choices=["date", "rating", "votes"], default=None,
                           help="Sort order: date (newest), rating (lowest), votes (most helpful)")
    p_analyze.add_argument("--stats", action="store_true", help="Show rating distribution before analysis")
    p_analyze.add_argument("--list-models", action="store_true", help="List available Ollama models and exit")

    # --- setup ---
    p_setup = sub.add_parser("setup", help="Install agent instruction files into your project")
    p_setup.add_argument("agent", choices=list(AGENTS.keys()),
                         help="Agent to set up: copilot, claude, cursor, windsurf")
    p_setup.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_setup.add_argument("--append", action="store_true", help="Append to existing files instead of overwriting")

    # --- compare ---
    p_compare = sub.add_parser("compare", help="Compare reviews across multiple apps")
    p_compare.add_argument("app_ids", nargs="+",
                           help="Two or more app IDs (numeric for Apple, package name for Google)")
    p_compare.add_argument("--stars", type=int, default=None, choices=range(1, 6),
                           help="Max star rating to include", metavar="STARS")
    p_compare.add_argument("--min-stars", type=int, default=None, choices=range(1, 6),
                           help="Min star rating to include", metavar="STARS")
    p_compare.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_compare.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_compare.add_argument("--pages", type=int, default=3, choices=range(1, 11),
                           help="Pages to fetch per app, 1-10 (default: 3)", metavar="PAGES")
    p_compare.add_argument("--sort", choices=["date", "rating", "votes"], default=None,
                           help="Sort order: date (newest), rating (lowest), votes (most helpful)")
    p_compare.add_argument("--format", choices=["text", "json", "csv"], default="text",
                           help="Output format: text (default), json, csv")

    # --- version-diff ---
    p_vdiff = sub.add_parser("version-diff", help="Compare sentiment between app versions")
    p_vdiff.add_argument("app_id",
                         help="Numeric App Store ID or Google Play package name")
    p_vdiff.add_argument("--old", default=None, help="Old version to compare (auto-detected if omitted)")
    p_vdiff.add_argument("--new", default=None, help="New version to compare (auto-detected if omitted)")
    p_vdiff.add_argument("--stars", type=int, default=None, choices=range(1, 6),
                         help="Max star rating to include", metavar="STARS")
    p_vdiff.add_argument("--min-stars", type=int, default=None, choices=range(1, 6),
                         help="Min star rating to include", metavar="STARS")
    p_vdiff.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_vdiff.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_vdiff.add_argument("--pages", type=int, default=5, choices=range(1, 11),
                         help="Pages to fetch (1-10, default: 5)", metavar="PAGES")
    p_vdiff.add_argument("--format", choices=["text", "json", "csv"], default="text",
                         help="Output format: text (default), json, csv")

    # --- trend ---
    p_trend = sub.add_parser("trend", help="Show rating trend over time")
    p_trend.add_argument("app_id",
                         help="Numeric App Store ID or Google Play package name")
    p_trend.add_argument("--period", choices=["week", "month"], default="week",
                         help="Group by: week (default) or month")
    p_trend.add_argument("--stars", type=int, default=None, choices=range(1, 6),
                         help="Max star rating to include", metavar="STARS")
    p_trend.add_argument("--min-stars", type=int, default=None, choices=range(1, 6),
                         help="Min star rating to include", metavar="STARS")
    p_trend.add_argument("--days", type=int, default=None, help="Only reviews from the last N days")
    p_trend.add_argument("--keywords", default=None, help="Comma-separated keywords to filter by")
    p_trend.add_argument("--pages", type=int, default=5, choices=range(1, 11),
                         help="Pages to fetch (1-10, default: 5)", metavar="PAGES")
    p_trend.add_argument("--format", choices=["text", "json", "csv"], default="text",
                         help="Output format: text (default), json, csv")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "reviews":
        cmd_reviews(args)
    elif args.command == "analyze":
        if args.app_id is None and not args.list_models:
            p_analyze.error("app_id is required (unless using --list-models)")
        cmd_analyze(args)
    elif args.command == "setup":
        cmd_setup(args)
    elif args.command == "compare":
        if len(args.app_ids) < 2:
            p_compare.error("compare requires at least 2 app IDs")
        cmd_compare(args)
    elif args.command == "version-diff":
        cmd_version_diff(args)
    elif args.command == "trend":
        cmd_trend(args)


if __name__ == "__main__":
    main()
