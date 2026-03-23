"""Version diff - compare sentiment and complaints between app versions."""

import csv
import io
import json
import sys
from collections import Counter

import requests

from .scraper import fetch_reviews, lookup_app, Review
from .filters import apply_filters
from .compare import _top_keywords, _categorize_complaints


def _group_by_version(reviews: list[Review]) -> dict[str, list[Review]]:
    """Group reviews by app version, ignoring reviews with no version."""
    groups: dict[str, list[Review]] = {}
    for r in reviews:
        v = r.version.strip()
        if v:
            groups.setdefault(v, []).append(r)
    return groups


def _pick_versions(
    groups: dict[str, list[Review]],
    old_version: str | None,
    new_version: str | None,
) -> tuple[str, str]:
    """Pick old and new versions. If not specified, use the two with the most reviews."""
    if old_version and new_version:
        return old_version, new_version

    # Sort versions by count of reviews (descending) to pick the two most reviewed
    by_count = sorted(groups.keys(), key=lambda v: len(groups[v]), reverse=True)

    if len(by_count) < 2:
        raise ValueError(
            f"Need at least 2 versions to compare, found {len(by_count)}. "
            "Try fetching more pages (--pages 10) or removing date filters."
        )

    if new_version:
        # User specified new, auto-pick old as the next most reviewed
        candidates = [v for v in by_count if v != new_version]
        return candidates[0], new_version

    if old_version:
        candidates = [v for v in by_count if v != old_version]
        return old_version, candidates[0]

    # Auto-pick: two most reviewed versions
    return by_count[1], by_count[0]


def _rating_bar(avg: float) -> str:
    """Compact visual rating bar."""
    filled = round(avg)
    return "★" * filled + "☆" * (5 - filled)


def version_diff(
    app_id: str,
    country: str = "us",
    pages: int = 5,
    old_version: str | None = None,
    new_version: str | None = None,
    max_rating: int | None = None,
    min_rating: int | None = None,
    keywords: list[str] | None = None,
    days: int | None = None,
    store: str = "apple",
    format: str = "text",
) -> str:
    """Fetch reviews and compare sentiment between two versions."""
    if store == "google":
        from .google_play import lookup_play, fetch_play_reviews
        _lookup = lambda aid, **kw: lookup_play(aid, **kw)
        _fetch = lambda aid, **kw: fetch_play_reviews(aid, **kw)
    else:
        _lookup = lambda aid, **kw: lookup_app(aid, **kw)
        _fetch = lambda aid, **kw: fetch_reviews(aid, **kw)

    # Lookup app info
    try:
        app = _lookup(app_id, country=country)
    except requests.RequestException:
        app = None

    name = app.name if app else str(app_id)
    print(f"Fetching reviews for: {name}...", file=sys.stderr)

    # Fetch reviews
    reviews = _fetch(app_id, country=country, pages=pages)
    print(f"Fetched {len(reviews)} reviews", file=sys.stderr)

    # Apply filters (except version - we need multiple versions)
    filtered = apply_filters(
        reviews,
        max_rating=max_rating,
        min_rating=min_rating,
        keywords=keywords,
        days=days,
    )
    print(f"After filtering: {len(filtered)} reviews", file=sys.stderr)

    # Group by version
    groups = _group_by_version(filtered)
    if not groups:
        return "No reviews with version info found. Try fetching more pages (--pages 10)."

    # Pick versions to compare
    try:
        old_v, new_v = _pick_versions(groups, old_version, new_version)
    except ValueError as e:
        return str(e)

    old_reviews = groups.get(old_v, [])
    new_reviews = groups.get(new_v, [])

    if not old_reviews:
        return f"No reviews found for version {old_v}."
    if not new_reviews:
        return f"No reviews found for version {new_v}."

    # Compute metrics for each version
    old_avg = sum(r.rating for r in old_reviews) / len(old_reviews)
    new_avg = sum(r.rating for r in new_reviews) / len(new_reviews)
    delta = new_avg - old_avg

    old_cats = _categorize_complaints(old_reviews)
    new_cats = _categorize_complaints(new_reviews)

    old_words = _top_keywords(old_reviews, n=8)
    new_words = _top_keywords(new_reviews, n=8)

    # Build structured data
    all_cats = set(old_cats.keys()) | set(new_cats.keys())
    category_changes = []
    for cat in all_cats:
        old_count = old_cats.get(cat, 0)
        new_count = new_cats.get(cat, 0)
        old_pct = old_count / len(old_reviews) * 100 if old_reviews else 0
        new_pct = new_count / len(new_reviews) * 100 if new_reviews else 0
        category_changes.append({
            "category": cat,
            "old_pct": round(old_pct, 1),
            "new_pct": round(new_pct, 1),
            "change_pct": round(new_pct - old_pct, 1),
        })
    category_changes.sort(key=lambda x: abs(x["change_pct"]), reverse=True)

    old_dist = {str(i): sum(1 for r in old_reviews if r.rating == i) for i in range(1, 6)}
    new_dist = {str(i): sum(1 for r in new_reviews if r.rating == i) for i in range(1, 6)}

    new_issues = sorted(set(new_cats.keys()) - set(old_cats.keys()))
    resolved_issues = sorted(set(old_cats.keys()) - set(new_cats.keys()))

    other_versions = sorted(
        [{"version": v, "count": len(rs)} for v, rs in groups.items() if v not in (old_v, new_v)],
        key=lambda x: x["count"],
        reverse=True,
    )

    direction = "improved" if delta > 0.1 else "declined" if delta < -0.1 else "unchanged"

    data = {
        "app_name": name,
        "old_version": old_v,
        "new_version": new_v,
        "sentiment": direction,
        "delta": round(delta, 2),
        "old": {
            "version": old_v,
            "review_count": len(old_reviews),
            "avg_rating": round(old_avg, 2),
            "rating_distribution": old_dist,
            "categories": old_cats,
            "top_keywords": [[w, c] for w, c in old_words],
        },
        "new": {
            "version": new_v,
            "review_count": len(new_reviews),
            "avg_rating": round(new_avg, 2),
            "rating_distribution": new_dist,
            "categories": new_cats,
            "top_keywords": [[w, c] for w, c in new_words],
        },
        "category_changes": category_changes,
        "new_issues": new_issues,
        "resolved_issues": resolved_issues,
        "other_versions": other_versions[:8],
    }

    if format == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    if format == "csv":
        return _vdiff_to_csv(data)
    return _vdiff_to_text(data, old_reviews, new_reviews, old_words, new_words, groups, old_v, new_v)

def _vdiff_to_csv(data: dict) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["category", "old_pct", "new_pct", "change_pct"])
    for ch in data["category_changes"]:
        writer.writerow([ch["category"], ch["old_pct"], ch["new_pct"], ch["change_pct"]])
    return buf.getvalue()


def _vdiff_to_text(
    data: dict,
    old_reviews: list[Review],
    new_reviews: list[Review],
    old_words: list[tuple[str, int]],
    new_words: list[tuple[str, int]],
    groups: dict[str, list[Review]],
    old_v: str,
    new_v: str,
) -> str:
    name = data["app_name"]
    old_avg = data["old"]["avg_rating"]
    new_avg = data["new"]["avg_rating"]
    delta = data["delta"]

    # Build report
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"VERSION DIFF: {name}")
    lines.append("=" * 60)

    # Overview
    delta_str = f"+{delta:.2f}" if delta >= 0 else f"{delta:.2f}"
    lines.append(f"  {old_v} -> {new_v}  (sentiment {data['sentiment']})")
    lines.append("")

    lines.append(f"  {'':20} {'Old (' + old_v + ')':>20} {'New (' + new_v + ')':>20}")
    lines.append(f"  {'-'*60}")
    lines.append(f"  {'Reviews':20} {len(old_reviews):>20} {len(new_reviews):>20}")
    lines.append(f"  {'Avg rating':20} {old_avg:>19.1f}★ {new_avg:>19.1f}★")
    lines.append(f"  {'Delta':20} {'':>20} {delta_str:>20}")

    # Rating distributions
    for label, revs in [("Old", old_reviews), ("New", new_reviews)]:
        v = old_v if label == "Old" else new_v
        lines.append("")
        lines.append(f"  {label} ({v}) rating distribution:")
        dist = {i: 0 for i in range(1, 6)}
        for r in revs:
            dist[r.rating] += 1
        for stars in range(5, 0, -1):
            count = dist[stars]
            if count > 0:
                bar = "█" * min(count, 30)
                lines.append(f"    {stars}★ {count:>4}  {bar}")

    # Category changes
    if data["category_changes"]:
        lines.append("")
        lines.append("  Complaint categories (change):")
        for ch in data["category_changes"]:
            diff_pct = ch["change_pct"]
            arrow = "▲" if diff_pct > 2 else "▼" if diff_pct < -2 else "="
            sign = "+" if diff_pct >= 0 else ""
            lines.append(f"    {arrow} {ch['category']:<25} {ch['old_pct']:>5.0f}% -> {ch['new_pct']:>5.0f}% ({sign}{diff_pct:.0f}%)")

    # New/resolved issues
    if data["new_issues"]:
        lines.append("")
        lines.append(f"  New issues in {new_v}: {', '.join(data['new_issues'])}")
    if data["resolved_issues"]:
        lines.append("")
        lines.append(f"  Resolved since {old_v}: {', '.join(data['resolved_issues'])}")

    # Top words per version
    if old_words:
        lines.append("")
        word_str = ", ".join(f"{w} ({c})" for w, c in old_words)
        lines.append(f"  Top words in {old_v}: {word_str}")
    if new_words:
        word_str = ", ".join(f"{w} ({c})" for w, c in new_words)
        lines.append(f"  Top words in {new_v}: {word_str}")

    # Other versions seen
    if data["other_versions"]:
        lines.append("")
        other_str = ", ".join(f"{v['version']} ({v['count']})" for v in data["other_versions"])
        lines.append(f"  Other versions with reviews: {other_str}")

    lines.append("")
    return "\n".join(lines)
