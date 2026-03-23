"""Python API for working with App Store reviews as data.

Use this module to fetch reviews programmatically and get them as
dictionaries or pandas DataFrames — ideal for notebooks and data analysis.

Usage:
    from appinsight.dataframe import get_reviews, get_reviews_df

    # As list of dicts (no pandas needed)
    reviews = get_reviews(618783545, stars=2, days=30)

    # As pandas DataFrame
    df = get_reviews_df(618783545, stars=2, days=30)
    df.groupby("version")["rating"].mean()
"""

from typing import Optional

from .scraper import fetch_reviews, search_app, lookup_app
from .filters import apply_filters


def search(query: str, country: str = "us", limit: int = 5, store: str = "apple") -> list[dict]:
    """Search the App Store or Google Play and return results as a list of dicts."""
    if store == "google":
        from .google_play import search_play
        apps = search_play(query, country=country, limit=limit)
    else:
        apps = search_app(query, country=country, limit=limit)
    return [a.to_dict() for a in apps]


def get_reviews(
    app_id: str,
    stars: Optional[int] = None,
    min_stars: Optional[int] = None,
    days: Optional[int] = None,
    keywords: Optional[list[str]] = None,
    version: Optional[str] = None,
    sort_by: Optional[str] = None,
    country: str = "us",
    pages: int = 3,
    store: str = "apple",
) -> list[dict]:
    """Fetch filtered reviews as a list of dicts.

    Works without pandas. Each dict has keys:
    id, title, content, rating, author, date, version, vote_sum, vote_count
    """
    if store == "google":
        from .google_play import fetch_play_reviews
        raw = fetch_play_reviews(app_id, country=country, pages=pages)
    else:
        raw = fetch_reviews(app_id, country=country, pages=pages)
    filtered = apply_filters(
        raw,
        max_rating=stars,
        min_rating=min_stars,
        keywords=keywords,
        days=days,
        version=version,
        sort_by=sort_by,
    )
    return [r.to_dict() for r in filtered]


def get_reviews_df(
    app_id: str,
    stars: Optional[int] = None,
    min_stars: Optional[int] = None,
    days: Optional[int] = None,
    keywords: Optional[list[str]] = None,
    version: Optional[str] = None,
    sort_by: Optional[str] = None,
    country: str = "us",
    pages: int = 3,
    store: str = "apple",
):
    """Fetch filtered reviews as a pandas DataFrame.

    Requires pandas: pip install appstore-review-cli[pandas]

    Columns: id, title, content, rating, author, date, version, vote_sum, vote_count
    The 'date' column is automatically converted to datetime.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "pandas is required for get_reviews_df(). "
            "Install with: pip install appstore-review-cli[pandas]"
        )

    data = get_reviews(
        app_id,
        stars=stars,
        min_stars=min_stars,
        days=days,
        keywords=keywords,
        version=version,
        sort_by=sort_by,
        country=country,
        pages=pages,
        store=store,
    )

    if not data:
        return pd.DataFrame(columns=[
            "id", "title", "content", "rating", "author",
            "date", "version", "vote_sum", "vote_count",
        ])

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["rating"] = df["rating"].astype(int)
    return df
