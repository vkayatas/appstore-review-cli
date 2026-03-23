"""Trend - show rating trends over time (weekly or monthly)."""

import sys
from collections import OrderedDict
from datetime import datetime, timezone

import requests

from .scraper import fetch_reviews, lookup_app, Review
from .filters import apply_filters


def _parse_date(date_str: str) -> datetime | None:
    """Parse an ISO date string into a datetime."""
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _group_by_period(
    reviews: list[Review], period: str
) -> OrderedDict[str, list[Review]]:
    """Group reviews by time period, ordered chronologically.

    Args:
        period: 'week' or 'month'
    """
    groups: dict[str, list[Review]] = {}
    for r in reviews:
        dt = _parse_date(r.date)
        if dt is None:
            continue
        if period == "week":
            # ISO week: YYYY-W##
            iso = dt.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
        else:
            key = f"{dt.year}-{dt.month:02d}"
        groups.setdefault(key, []).append(r)

    return OrderedDict(sorted(groups.items()))


def _sparkline(values: list[float], width: int = 20) -> str:
    """Generate an ASCII sparkline bar for a rating value (1-5)."""
    if not values:
        return ""
    avg = sum(values) / len(values)
    filled = round((avg - 1) / 4 * width)  # Scale 1-5 to 0-width
    return "█" * filled + "░" * (width - filled)


def trend(
    app_id: str,
    country: str = "us",
    pages: int = 5,
    period: str = "week",
    max_rating: int | None = None,
    min_rating: int | None = None,
    keywords: list[str] | None = None,
    days: int | None = None,
    store: str = "apple",
) -> str:
    """Fetch reviews and show rating trend over time."""
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

    # Apply filters
    filtered = apply_filters(
        reviews,
        max_rating=max_rating,
        min_rating=min_rating,
        keywords=keywords,
        days=days,
    )
    print(f"After filtering: {len(filtered)} reviews", file=sys.stderr)

    if not filtered:
        return "No reviews match the given filters."

    # Group by period
    groups = _group_by_period(filtered, period)
    if not groups:
        return "No reviews with parseable dates found."

    # Compute overall stats
    all_ratings = [r.rating for r in filtered]
    overall_avg = sum(all_ratings) / len(all_ratings)

    # Build report
    period_label = "Week" if period == "week" else "Month"
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"RATING TREND: {name} (by {period_label.lower()})")
    lines.append("=" * 60)
    lines.append(f"  Overall: {overall_avg:.2f}★ across {len(filtered)} reviews")
    lines.append("")

    lines.append(f"  {period_label:<12} {'Avg':>5} {'Count':>6}  {'Trend':<22} {'Dist'}")
    lines.append(f"  {'-'*60}")

    prev_avg = None
    for key, revs in groups.items():
        ratings = [r.rating for r in revs]
        avg = sum(ratings) / len(ratings)
        bar = _sparkline(ratings)

        # Direction arrow
        if prev_avg is not None:
            delta = avg - prev_avg
            if delta > 0.3:
                arrow = " ▲"
            elif delta < -0.3:
                arrow = " ▼"
            else:
                arrow = "  "
        else:
            arrow = "  "

        # Mini distribution
        dist = ""
        for s in range(1, 6):
            c = ratings.count(s)
            if c > 0:
                dist += f"{s}★:{c} "

        lines.append(f"  {key:<12} {avg:>4.1f}★ {len(revs):>5}{arrow}  {bar}  {dist.strip()}")
        prev_avg = avg

    # Trend summary
    keys = list(groups.keys())
    if len(keys) >= 2:
        first_revs = groups[keys[0]]
        last_revs = groups[keys[-1]]
        first_avg = sum(r.rating for r in first_revs) / len(first_revs)
        last_avg = sum(r.rating for r in last_revs) / len(last_revs)
        change = last_avg - first_avg
        sign = "+" if change >= 0 else ""
        if abs(change) > 0.3:
            direction = "improving" if change > 0 else "declining"
        else:
            direction = "stable"

        lines.append("")
        lines.append(f"  Trend: {direction} ({sign}{change:.2f}★ from {keys[0]} to {keys[-1]})")

    lines.append("")
    return "\n".join(lines)
