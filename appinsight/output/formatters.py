"""Output formatters - JSON, CSV, markdown table, and plain text."""

import csv
import io
import json

from appinsight.scrapers.appstore import Review


def to_json(reviews: list[Review], pretty: bool = True) -> str:
    """Serialize reviews to JSON string."""
    data = [r.to_dict() for r in reviews]
    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    return json.dumps(data, ensure_ascii=False)


def to_csv(reviews: list[Review]) -> str:
    """Format reviews as CSV - ready for pandas.read_csv() or spreadsheet import."""
    if not reviews:
        return ""

    fieldnames = ["id", "rating", "date", "version", "author", "title", "content", "vote_sum", "vote_count"]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_NONNUMERIC)
    writer.writeheader()
    for r in reviews:
        d = r.to_dict()
        # Shorten date for cleaner CSV
        if len(d.get("date", "")) >= 10:
            d["date"] = d["date"][:10]
        writer.writerow(d)
    return output.getvalue()


def to_markdown(reviews: list[Review]) -> str:
    """Format reviews as a markdown table."""
    if not reviews:
        return "_No reviews match the given filters._"

    lines = [
        "| Rating | Date | Version | Title | Content (excerpt) |",
        "|--------|------|---------|-------|--------------------|",
    ]
    for r in reviews:
        date_short = r.date[:10] if len(r.date) >= 10 else r.date
        excerpt = r.content[:120].replace("\n", " ")
        if len(r.content) > 120:
            excerpt += "..."
        title = r.title.replace("|", "\\|")
        excerpt = excerpt.replace("|", "\\|")
        lines.append(f"| {'⭐' * r.rating} | {date_short} | {r.version} | {title} | {excerpt} |")

    return "\n".join(lines)


def to_text(reviews: list[Review]) -> str:
    """Format reviews as plain text - one per block, easy for LLMs to read."""
    if not reviews:
        return "No reviews match the given filters."

    blocks = []
    for i, r in enumerate(reviews, 1):
        date_short = r.date[:10] if len(r.date) >= 10 else r.date
        block = (
            f"--- Review {i} ---\n"
            f"Rating: {r.rating}/5\n"
            f"Date: {date_short}\n"
            f"Version: {r.version}\n"
            f"Title: {r.title}\n"
            f"Content: {r.content}\n"
        )
        blocks.append(block)
    return "\n".join(blocks)


def summary_stats(reviews: list[Review]) -> str:
    """Generate a quick stats summary."""
    if not reviews:
        return "No reviews to summarize."

    total = len(reviews)
    ratings = [r.rating for r in reviews]
    avg = sum(ratings) / total
    dist = {i: ratings.count(i) for i in range(1, 6)}

    lines = [
        f"Total reviews: {total}",
        f"Average rating: {avg:.1f}/5",
        "Distribution:",
    ]
    for stars in range(5, 0, -1):
        count = dist[stars]
        bar = "█" * count + "░" * (total - count) if total <= 50 else "█" * int(count / total * 30)
        lines.append(f"  {stars}⭐ {count:>4}  {bar}")

    return "\n".join(lines)
