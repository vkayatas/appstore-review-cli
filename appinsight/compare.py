"""Multi-app comparison - fetch reviews for multiple apps and compare side by side."""

import sys
from collections import Counter

import requests

from .scraper import fetch_reviews, lookup_app, AppInfo
from .filters import apply_filters
from .formatters import summary_stats
from .scraper import Review


def _top_keywords(reviews: list[Review], n: int = 10) -> list[tuple[str, int]]:
    """Extract the most common meaningful words from review content."""
    stop_words = {
        "the", "a", "an", "is", "it", "i", "my", "me", "to", "and", "of", "in",
        "for", "on", "was", "that", "this", "with", "but", "not", "have", "has",
        "had", "are", "be", "been", "so", "if", "at", "do", "did", "just", "no",
        "or", "as", "can", "you", "its", "from", "they", "all", "very", "would",
        "get", "got", "one", "use", "even", "app", "im", "dont", "ive", "when",
        "more", "than", "like", "what", "there", "about", "after", "your", "will",
        "how", "up", "out", "also", "only", "time", "still", "back", "some",
        "much", "really", "now", "every", "too", "any", "other", "could",
    }
    word_count: Counter = Counter()
    for r in reviews:
        words = f"{r.title} {r.content}".lower().split()
        for w in words:
            cleaned = "".join(c for c in w if c.isalpha())
            if len(cleaned) >= 3 and cleaned not in stop_words:
                word_count[cleaned] += 1
    return word_count.most_common(n)


def _categorize_complaints(reviews: list[Review]) -> dict[str, int]:
    """Categorize reviews by common complaint themes."""
    categories = {
        "Crashes/Freezes": ["crash", "freeze", "frozen", "stuck", "hang"],
        "Performance": ["slow", "lag", "loading", "battery", "drain", "memory"],
        "Bugs": ["bug", "glitch", "error", "broken", "doesn't work", "not working"],
        "UI/UX": ["confusing", "interface", "design", "layout", "ugly", "hard to use", "unintuitive"],
        "Missing Features": ["wish", "missing", "need", "should have", "please add", "no option"],
        "Notifications": ["notification", "alert", "push", "notify"],
        "Login/Auth": ["login", "password", "sign in", "authentication", "account"],
        "Updates": ["update", "version", "changed", "worse", "downgrade", "rollback"],
    }
    counts: dict[str, int] = {}
    for category, keywords in categories.items():
        count = 0
        for r in reviews:
            text = f"{r.title} {r.content}".lower()
            if any(kw in text for kw in keywords):
                count += 1
        if count > 0:
            counts[category] = count
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def compare_apps(
    app_ids: list[int],
    country: str = "us",
    pages: int = 3,
    max_rating: int | None = None,
    min_rating: int | None = None,
    keywords: list[str] | None = None,
    days: int | None = None,
    sort_by: str | None = None,
) -> str:
    """Fetch reviews for multiple apps and produce a comparison report."""
    app_data: list[dict] = []

    for app_id in app_ids:
        # Lookup app info
        try:
            app = lookup_app(app_id, country=country)
        except requests.RequestException:
            app = None

        name = app.name if app else str(app_id)
        print(f"Fetching reviews for: {name}...", file=sys.stderr)

        # Fetch and filter
        reviews = fetch_reviews(app_id, country=country, pages=pages)
        filtered = apply_filters(
            reviews,
            max_rating=max_rating,
            min_rating=min_rating,
            keywords=keywords,
            days=days,
            sort_by=sort_by,
        )

        app_data.append({
            "app_id": app_id,
            "name": name,
            "app": app,
            "total_fetched": len(reviews),
            "total_filtered": len(filtered),
            "reviews": filtered,
        })

    # Build comparison report
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("COMPARISON REPORT")
    lines.append("=" * 60)

    # Overview table
    lines.append("")
    lines.append(f"{'App':<30} {'Rating':>7} {'Reviews':>10} {'Filtered':>10}")
    lines.append("-" * 60)
    for d in app_data:
        rating_str = f"{d['app'].avg_rating:.1f}/5" if d["app"] else "N/A"
        count_str = f"{d['app'].rating_count:,}" if d["app"] else "N/A"
        lines.append(f"{d['name']:<30} {rating_str:>7} {count_str:>10} {d['total_filtered']:>10}")

    # Per-app breakdown
    for d in app_data:
        lines.append("")
        lines.append(f"--- {d['name']} ---")

        if not d["reviews"]:
            lines.append("  No reviews match the given filters.")
            continue

        # Rating distribution
        lines.append(f"  Filtered reviews: {d['total_filtered']}")
        ratings = [r.rating for r in d["reviews"]]
        avg = sum(ratings) / len(ratings)
        lines.append(f"  Average rating (filtered): {avg:.1f}/5")
        dist = {i: ratings.count(i) for i in range(1, 6)}
        for stars in range(5, 0, -1):
            count = dist[stars]
            if count > 0:
                bar = "█" * min(count, 30)
                lines.append(f"    {stars}★ {count:>4}  {bar}")

        # Top complaint categories
        categories = _categorize_complaints(d["reviews"])
        if categories:
            lines.append("  Top complaint categories:")
            for cat, count in list(categories.items())[:5]:
                pct = count / d["total_filtered"] * 100
                lines.append(f"    {cat:<25} {count:>4} ({pct:.0f}%)")

        # Top words
        top_words = _top_keywords(d["reviews"], n=8)
        if top_words:
            word_str = ", ".join(f"{w} ({c})" for w, c in top_words)
            lines.append(f"  Top words: {word_str}")

    # Shared vs unique complaints
    if len(app_data) >= 2 and all(d["reviews"] for d in app_data):
        lines.append("")
        lines.append("--- Comparison ---")

        all_categories = [set(_categorize_complaints(d["reviews"]).keys()) for d in app_data]
        shared = set.intersection(*all_categories) if all_categories else set()
        if shared:
            lines.append(f"  Shared complaints: {', '.join(sorted(shared))}")

        for d, cats in zip(app_data, all_categories):
            unique = cats - shared
            if unique:
                lines.append(f"  Unique to {d['name']}: {', '.join(sorted(unique))}")

    lines.append("")
    return "\n".join(lines)
