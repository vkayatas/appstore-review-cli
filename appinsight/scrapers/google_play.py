"""Google Play Store review scraper using google-play-scraper.

Optional dependency: pip install appstore-review-cli[google]
"""

import sys
from datetime import timezone
from typing import Optional

from .appstore import Review, AppInfo


def _get_gps():
    """Import google-play-scraper or raise a helpful error."""
    try:
        import google_play_scraper
        return google_play_scraper
    except ImportError:
        raise ImportError(
            "google-play-scraper is required for --store google. "
            "Install with: pip install appstore-review-cli[google]"
        )


def search_play(query: str, country: str = "us", limit: int = 5) -> list[AppInfo]:
    """Search Google Play by name and return matching apps."""
    gps = _get_gps()
    results = gps.search(query, n_hits=limit, lang="en", country=country)
    apps = []
    for r in results:
        app_id = r.get("appId")
        if not app_id:
            continue  # First "featured" result sometimes lacks appId
        apps.append(AppInfo(
            app_id=app_id,
            name=r.get("title", ""),
            developer=r.get("developer", ""),
            avg_rating=r.get("score", 0.0) or 0.0,
            rating_count=0,  # search results don't include count
            version="",
            bundle_id=app_id,
        ))
    return apps


def lookup_play(app_id: str, country: str = "us") -> Optional[AppInfo]:
    """Look up a Google Play app by package name."""
    gps = _get_gps()
    try:
        info = gps.app(app_id, lang="en", country=country)
    except Exception:
        return None

    return AppInfo(
        app_id=app_id,
        name=info.get("title", ""),
        developer=info.get("developer", ""),
        avg_rating=info.get("score", 0.0) or 0.0,
        rating_count=info.get("ratings", 0) or 0,
        version=info.get("version", ""),
        bundle_id=app_id,
    )


def fetch_play_reviews(
    app_id: str,
    country: str = "us",
    pages: int = 3,
) -> list[Review]:
    """Fetch reviews from Google Play.

    Args:
        app_id: Package name (e.g. "com.Slack").
        country: ISO 2-letter country code.
        pages: Number of pages (1-10, ~50 reviews each to match Apple).

    Returns:
        List of Review objects, newest first.
    """
    gps = _get_gps()
    from google_play_scraper import Sort

    count = max(1, min(pages, 10)) * 50

    try:
        result, _ = gps.reviews(
            app_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=count,
        )
    except Exception as e:
        print(f"Warning: Failed to fetch Google Play reviews: {e}", file=sys.stderr)
        return []

    seen: set[str] = set()
    reviews: list[Review] = []
    for r in result:
        rid = r.get("reviewId", "")
        if rid in seen:
            continue
        seen.add(rid)

        at = r.get("at")
        date_str = ""
        if at and hasattr(at, "isoformat"):
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            date_str = at.isoformat()

        reviews.append(Review(
            id=rid,
            title="",  # Google Play reviews don't have separate titles
            content=r.get("content", "") or "",
            rating=r.get("score", 0),
            author=r.get("userName", "") or "",
            date=date_str,
            version=r.get("reviewCreatedVersion") or r.get("appVersion") or "",
            vote_sum=r.get("thumbsUpCount", 0) or 0,
            vote_count=r.get("thumbsUpCount", 0) or 0,
        ))

    return reviews
