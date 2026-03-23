"""AppInsight - App Store review scraper and analyzer for coding agents."""

__version__ = "0.1.3"

# Convenience imports for programmatic use
from .dataframe import search, get_reviews, get_reviews_df

__all__ = ["search", "get_reviews", "get_reviews_df"]
