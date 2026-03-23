"""Multi-app comparison - fetch reviews for multiple apps and compare side by side."""

import csv
import io
import json
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
    app_ids: list[str],
    country: str = "us",
    pages: int = 3,
    max_rating: int | None = None,
    min_rating: int | None = None,
    keywords: list[str] | None = None,
    days: int | None = None,
    sort_by: str | None = None,
    store: str = "apple",
    format: str = "text",
) -> str:
    """Fetch reviews for multiple apps and produce a comparison report."""
    if store == "google":
        from .google_play import lookup_play, fetch_play_reviews
        _lookup = lambda aid, **kw: lookup_play(aid, **kw)
        _fetch = lambda aid, **kw: fetch_play_reviews(aid, **kw)
    else:
        _lookup = lambda aid, **kw: lookup_app(aid, **kw)
        _fetch = lambda aid, **kw: fetch_reviews(aid, **kw)

    app_data: list[dict] = []

    for app_id in app_ids:
        # Lookup app info
        try:
            app = _lookup(app_id, country=country)
        except requests.RequestException:
            app = None

        name = app.name if app else str(app_id)
        print(f"Fetching reviews for: {name}...", file=sys.stderr)

        # Fetch and filter
        reviews = _fetch(app_id, country=country, pages=pages)
        filtered = apply_filters(
            reviews,
            max_rating=max_rating,
            min_rating=min_rating,
            keywords=keywords,
            days=days,
            sort_by=sort_by,
        )

        ratings = [r.rating for r in filtered]
        filtered_avg = sum(ratings) / len(ratings) if ratings else 0.0
        dist = {str(i): ratings.count(i) for i in range(1, 6)}

        app_data.append({
            "app_id": app_id,
            "name": name,
            "app": app,
            "avg_rating": app.avg_rating if app else None,
            "rating_count": app.rating_count if app else None,
            "total_fetched": len(reviews),
            "total_filtered": len(filtered),
            "filtered_avg_rating": round(filtered_avg, 2),
            "rating_distribution": dist,
            "reviews": filtered,
            "top_categories": _categorize_complaints(filtered),
            "top_keywords": _top_keywords(filtered, n=8),
        })

    # Shared vs unique complaints
    shared_complaints: list[str] = []
    unique_complaints: dict[str, list[str]] = {}
    if len(app_data) >= 2 and all(d["reviews"] for d in app_data):
        all_categories = [set(d["top_categories"].keys()) for d in app_data]
        shared = set.intersection(*all_categories) if all_categories else set()
        shared_complaints = sorted(shared)
        for d, cats in zip(app_data, all_categories):
            unique = sorted(cats - shared)
            if unique:
                unique_complaints[d["name"]] = unique

    if format == "json":
        return _compare_to_json(app_data, shared_complaints, unique_complaints)
    if format == "csv":
        return _compare_to_csv(app_data)
    return _compare_to_text(app_data, shared_complaints, unique_complaints)


def _compare_to_json(
    app_data: list[dict],
    shared_complaints: list[str],
    unique_complaints: dict[str, list[str]],
) -> str:
    data = {
        "apps": [
            {
                "app_id": d["app_id"],
                "name": d["name"],
                "avg_rating": d["avg_rating"],
                "rating_count": d["rating_count"],
                "filtered_count": d["total_filtered"],
                "filtered_avg_rating": d["filtered_avg_rating"],
                "rating_distribution": d["rating_distribution"],
                "top_categories": d["top_categories"],
                "top_keywords": [[w, c] for w, c in d["top_keywords"]],
            }
            for d in app_data
        ],
        "shared_complaints": shared_complaints,
        "unique_complaints": unique_complaints,
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def _compare_to_csv(app_data: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "app_id", "name", "avg_rating", "rating_count", "filtered_count",
        "filtered_avg_rating", "1_star", "2_star", "3_star", "4_star", "5_star",
        "top_categories", "top_keywords",
    ])
    for d in app_data:
        dist = d["rating_distribution"]
        cats = "; ".join(f"{k}: {v}" for k, v in d["top_categories"].items())
        kws = "; ".join(f"{w} ({c})" for w, c in d["top_keywords"])
        writer.writerow([
            d["app_id"], d["name"], d["avg_rating"], d["rating_count"],
            d["total_filtered"], d["filtered_avg_rating"],
            dist["1"], dist["2"], dist["3"], dist["4"], dist["5"],
            cats, kws,
        ])
    return buf.getvalue()


def _compare_to_text(
    app_data: list[dict],
    shared_complaints: list[str],
    unique_complaints: dict[str, list[str]],
) -> str:
    """Format the comparison as the original text report."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("COMPARISON REPORT")
    lines.append("=" * 60)

    # Overview table
    lines.append("")
    lines.append(f"{'App':<30} {'Rating':>7} {'Reviews':>10} {'Filtered':>10}")
    lines.append("-" * 60)
    for d in app_data:
        rating_str = f"{d['avg_rating']:.1f}/5" if d["avg_rating"] is not None else "N/A"
        count_str = f"{d['rating_count']:,}" if d["rating_count"] is not None else "N/A"
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
        lines.append(f"  Average rating (filtered): {d['filtered_avg_rating']:.1f}/5")
        dist = d["rating_distribution"]
        for stars in range(5, 0, -1):
            count = int(dist[str(stars)])
            if count > 0:
                bar = "█" * min(count, 30)
                lines.append(f"    {stars}★ {count:>4}  {bar}")

        # Top complaint categories
        categories = d["top_categories"]
        if categories:
            lines.append("  Top complaint categories:")
            for cat, count in list(categories.items())[:5]:
                pct = count / d["total_filtered"] * 100
                lines.append(f"    {cat:<25} {count:>4} ({pct:.0f}%)")

        # Top words
        top_words = d["top_keywords"]
        if top_words:
            word_str = ", ".join(f"{w} ({c})" for w, c in top_words)
            lines.append(f"  Top words: {word_str}")

    # Shared vs unique complaints
    if shared_complaints or unique_complaints:
        lines.append("")
        lines.append("--- Comparison ---")
        if shared_complaints:
            lines.append(f"  Shared complaints: {', '.join(shared_complaints)}")
        for name, unique in unique_complaints.items():
            lines.append(f"  Unique to {name}: {', '.join(unique)}")

    lines.append("")
    return "\n".join(lines)
