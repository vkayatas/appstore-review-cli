"""Review analyzer using local LLMs via Ollama.

Provides built-in analysis modes (summary, gaps, bugs) so users don't
have to pipe output manually. Uses the Ollama REST API — no extra
Python packages needed beyond `requests`.
"""

import json
import sys

import requests

from .scraper import Review

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:4b"

# System prompts per analysis mode
PROMPTS = {
    "summary": (
        "You are an app review analyst. Summarize the following App Store reviews "
        "into a concise report. Group by theme (UX, bugs, missing features, praise). "
        "Rank themes by how often they appear. Cite specific reviews as evidence. "
        "Keep the summary under 500 words. Be direct — no filler."
    ),
    "gaps": (
        "You are a product strategist analyzing negative App Store reviews. "
        "Identify feature gaps — things users wish the app had, features competitors "
        "do better, and missing functionality. Group by feature category, rank by "
        "frequency, and cite specific reviews. Output a prioritized list of gaps "
        "the development team should address."
    ),
    "bugs": (
        "You are a QA engineer analyzing App Store reviews for technical issues. "
        "Identify bugs, crashes, performance problems, and errors. Group by symptom "
        "(crashes, slow performance, data loss, UI glitches). Note affected versions "
        "where mentioned. Rank by severity and frequency. Output an actionable bug report."
    ),
}


def check_ollama() -> bool:
    """Check if Ollama is running and reachable."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


def list_models() -> list[str]:
    """List available Ollama models."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        return [m["name"] for m in resp.json().get("models", [])]
    except (requests.ConnectionError, requests.HTTPError):
        return []


def format_reviews_for_prompt(reviews: list[Review], max_reviews: int = 50) -> str:
    """Format reviews into a compact text block for the LLM prompt."""
    # Limit to avoid exceeding context window on small models
    if len(reviews) > max_reviews:
        print(f"Note: Sending {max_reviews} of {len(reviews)} reviews to LLM (context window limit)", file=sys.stderr)
    subset = reviews[:max_reviews]
    blocks = []
    for i, r in enumerate(subset, 1):
        date_short = r.date[:10] if len(r.date) >= 10 else r.date
        blocks.append(
            f"[{i}] {r.rating}★ | {date_short} | v{r.version}\n"
            f"Title: {r.title}\n"
            f"{r.content}\n"
        )
    text = "\n".join(blocks)
    if len(reviews) > max_reviews:
        text += f"\n(Showing {max_reviews} of {len(reviews)} reviews)\n"
    return text


def analyze(
    reviews: list[Review],
    mode: str = "summary",
    model: str = DEFAULT_MODEL,
    stream: bool = True,
) -> str:
    """Send reviews to Ollama for analysis.

    Args:
        reviews: List of Review objects to analyze.
        mode: Analysis mode — 'summary', 'gaps', or 'bugs'.
        model: Ollama model name.
        stream: If True, print tokens as they arrive and return full text.

    Returns:
        The complete analysis text.
    """
    if not reviews:
        return "No reviews to analyze."

    system_prompt = PROMPTS.get(mode, PROMPTS["summary"])
    review_text = format_reviews_for_prompt(reviews)
    user_prompt = f"Here are {len(reviews)} App Store reviews to analyze:\n\n{review_text}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": stream,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            stream=stream,
            timeout=None,  # No timeout — model loading + inference can take minutes
        )
        resp.raise_for_status()
    except requests.ConnectionError:
        return "Error: Cannot connect to Ollama. Is it running? Start with: ollama serve"
    except requests.HTTPError as e:
        return f"Error: Ollama returned {e.response.status_code}. Is the model '{model}' pulled?"

    if stream:
        full_text = []
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    print(token, end="", flush=True, file=sys.stderr)
                    full_text.append(token)
                if chunk.get("done"):
                    break
        print(file=sys.stderr)  # newline after streaming
        return "".join(full_text)
    else:
        data = resp.json()
        return data.get("message", {}).get("content", "")
