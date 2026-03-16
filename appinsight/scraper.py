"""Apple App Store review scraper using the public RSS/JSON feed.

No API key required. Uses the iTunes RSS feed which returns up to
500 reviews per country (10 pages × 50 reviews).
"""

import json
import sys
import time
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import requests

REVIEWS_URL = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/page={page}/id={app_id}/sortby=mostrecent/json"
)
SEARCH_URL = "https://itunes.apple.com/search"
LOOKUP_URL = "https://itunes.apple.com/lookup"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}
REQUEST_DELAY = 1.5  # seconds between page fetches to avoid rate limits


@dataclass
class Review:
    id: str
    title: str
    content: str
    rating: int
    author: str
    date: str
    version: str
    vote_sum: int
    vote_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AppInfo:
    app_id: int
    name: str
    developer: str
    avg_rating: float
    rating_count: int
    version: str
    bundle_id: str

    def to_dict(self) -> dict:
        return asdict(self)


def search_app(query: str, country: str = "us", limit: int = 5) -> list[AppInfo]:
    """Search the App Store by name and return matching apps."""
    resp = requests.get(
        SEARCH_URL,
        params={
            "term": query,
            "entity": "software",
            "country": country,
            "limit": limit,
        },
        headers=DEFAULT_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        print("Warning: App Store returned invalid JSON for search", file=sys.stderr)
        return []

    results = []
    for r in data.get("results", []):
        results.append(
            AppInfo(
                app_id=r["trackId"],
                name=r["trackName"],
                developer=r.get("artistName", ""),
                avg_rating=r.get("averageUserRating", 0.0),
                rating_count=r.get("userRatingCount", 0),
                version=r.get("version", ""),
                bundle_id=r.get("bundleId", ""),
            )
        )
    return results


def lookup_app(app_id: int, country: str = "us") -> Optional[AppInfo]:
    """Look up an app by its numeric ID."""
    resp = requests.get(
        LOOKUP_URL,
        params={"id": app_id, "country": country},
        headers=DEFAULT_HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    try:
        data = resp.json()
    except (json.JSONDecodeError, ValueError):
        print("Warning: App Store returned invalid JSON for lookup", file=sys.stderr)
        return None

    results = data.get("results", [])
    if not results:
        return None

    r = results[0]
    return AppInfo(
        app_id=r["trackId"],
        name=r["trackName"],
        developer=r.get("artistName", ""),
        avg_rating=r.get("averageUserRating", 0.0),
        rating_count=r.get("userRatingCount", 0),
        version=r.get("version", ""),
        bundle_id=r.get("bundleId", ""),
    )


def _parse_entry(entry: dict) -> Optional[Review]:
    """Parse a single RSS feed entry into a Review. Returns None for app metadata entries."""
    # App metadata entries don't have im:rating
    if "im:rating" not in entry:
        return None

    try:
        return Review(
            id=entry.get("id", {}).get("label", ""),
            title=entry.get("title", {}).get("label", ""),
            content=entry.get("content", {}).get("label", ""),
            rating=int(entry["im:rating"]["label"]),
            author=entry.get("author", {}).get("name", {}).get("label", ""),
            date=entry.get("updated", {}).get("label", ""),
            version=entry.get("im:version", {}).get("label", ""),
            vote_sum=int(entry.get("im:voteSum", {}).get("label", "0")),
            vote_count=int(entry.get("im:voteCount", {}).get("label", "0")),
        )
    except (KeyError, ValueError, TypeError):
        return None


def fetch_reviews(
    app_id: int,
    country: str = "us",
    pages: int = 10,
) -> list[Review]:
    """Fetch reviews from the Apple App Store RSS feed.

    Args:
        app_id: Numeric App Store ID.
        country: ISO 2-letter country code.
        pages: Number of pages to fetch (1-10, 50 reviews each).

    Returns:
        List of Review objects, most recent first.
    """
    pages = max(1, min(10, pages))
    all_reviews: list[Review] = []
    seen_ids: set[str] = set()

    for page in range(1, pages + 1):
        url = REVIEWS_URL.format(country=country, page=page, app_id=app_id)

        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch page {page}: {e}", file=sys.stderr)
            break

        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            print(f"Warning: Invalid JSON on page {page}, skipping", file=sys.stderr)
            break

        entries = data.get("feed", {}).get("entry", [])

        if not entries:
            break

        for entry in entries:
            review = _parse_entry(entry)
            if review and review.id not in seen_ids:
                seen_ids.add(review.id)
                all_reviews.append(review)

        # Don't hammer Apple's servers
        if page < pages:
            time.sleep(REQUEST_DELAY)

    return all_reviews
