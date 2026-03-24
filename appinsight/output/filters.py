"""Filters for narrowing down reviews before analysis."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from appinsight.scrapers.appstore import Review


def by_rating(reviews: list[Review], max_rating: int = 2, min_rating: int = 1) -> list[Review]:
    """Keep only reviews within the given rating range (inclusive)."""
    return [r for r in reviews if min_rating <= r.rating <= max_rating]


def by_keywords(reviews: list[Review], keywords: list[str]) -> list[Review]:
    """Keep reviews whose title or content contains any of the keywords (case-insensitive)."""
    lower_keywords = [k.lower() for k in keywords]
    results = []
    for r in reviews:
        text = f"{r.title} {r.content}".lower()
        if any(kw in text for kw in lower_keywords):
            results.append(r)
    return results


def by_days(reviews: list[Review], days: int) -> list[Review]:
    """Keep only reviews from the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    results = []
    for r in reviews:
        try:
            review_date = datetime.fromisoformat(r.date)
            if review_date.tzinfo is None:
                review_date = review_date.replace(tzinfo=timezone.utc)
            if review_date >= cutoff:
                results.append(r)
        except (ValueError, TypeError):
            # If we can't parse the date, include the review to avoid silent data loss
            results.append(r)
    return results


def by_version(reviews: list[Review], version: str) -> list[Review]:
    """Keep only reviews for a specific app version."""
    return [r for r in reviews if r.version == version]


def sort_reviews(reviews: list[Review], sort_by: str = "date") -> list[Review]:
    """Sort reviews by the given field.

    Args:
        sort_by: 'date' (newest first), 'rating' (lowest first), 'votes' (most helpful first)
    """
    if sort_by == "rating":
        return sorted(reviews, key=lambda r: r.rating)
    elif sort_by == "votes":
        return sorted(reviews, key=lambda r: r.vote_sum, reverse=True)
    else:  # date (default) - newest first
        return sorted(reviews, key=lambda r: r.date, reverse=True)


def apply_filters(
    reviews: list[Review],
    max_rating: Optional[int] = None,
    min_rating: Optional[int] = None,
    keywords: Optional[list[str]] = None,
    days: Optional[int] = None,
    version: Optional[str] = None,
    sort_by: Optional[str] = None,
) -> list[Review]:
    """Apply all specified filters in sequence, then optionally sort."""
    result = reviews
    if max_rating is not None or min_rating is not None:
        result = by_rating(
            result,
            max_rating=max_rating if max_rating is not None else 5,
            min_rating=min_rating if min_rating is not None else 1,
        )
    if keywords:
        result = by_keywords(result, keywords)
    if days is not None:
        result = by_days(result, days)
    if version is not None:
        result = by_version(result, version)
    if sort_by is not None:
        result = sort_reviews(result, sort_by)
    return result
