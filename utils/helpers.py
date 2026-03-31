# =============================================================================
# utils/helpers.py — Utility / Helper Functions
# =============================================================================
# PURPOSE: Shared utility functions used across the project.
# Contains: JSON session saving/loading, paper metadata formatting,
#           score-to-color mapping for UI, summary statistics.

import json
import os
import time
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# ── Session Persistence ───────────────────────────────────────────────────────

def save_session(query: str, results: list[dict], path: str = None) -> str:
    """
    Saves pipeline results to a JSON file.
    Returns the path where the file was saved.
    """
    path = path or config.LOG_FILE
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    entry = {
        "query":      query,
        "timestamp":  time.strftime("%Y-%m-%dT%H:%M:%S"),
        "num_papers": len(results),
        "results":    results,
    }

    existing = load_session(path) or []
    existing.append(entry)

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    return path


def load_session(path: str = None) -> list[dict]:
    """Loads saved session data from a JSON file. Returns [] if file not found."""
    path = path or config.LOG_FILE
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


# ── Paper Formatting ──────────────────────────────────────────────────────────

def format_paper_meta(paper: dict, max_abstract: int = None) -> dict:
    """
    Returns a display-ready version of a paper dict.
    Truncates long abstracts and formats author list.
    """
    max_chars = max_abstract or config.MAX_ABSTRACT_DISPLAY_CHARS
    abstract  = paper.get("abstract", "")
    if len(abstract) > max_chars:
        abstract = abstract[:max_chars] + " …"

    authors = paper.get("authors", [])
    if isinstance(authors, list):
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += f" et al. (+{len(authors) - 3} more)"
    else:
        author_str = str(authors)

    return {
        "title":    paper.get("title",  "Untitled"),
        "authors":  author_str,
        "abstract": abstract,
        "year":     paper.get("year",   "Unknown"),
        "source":   paper.get("source", "Unknown"),
        "url":      paper.get("url",    ""),
    }


# ── Score → UI Color Mapping ──────────────────────────────────────────────────

def score_to_color(score: float) -> str:
    """
    Maps a 0–10 score to a hex color for Streamlit UI.
        8–10 → green (accept)
        5–7  → yellow (revision)
        3–4  → orange (major revision)
        0–2  → red (reject)
    """
    if score >= 8:
        return "#28a745"   # green
    elif score >= 5:
        return "#ffc107"   # yellow
    elif score >= 3:
        return "#fd7e14"   # orange
    else:
        return "#dc3545"   # red


def verdict_emoji(verdict: str) -> str:
    """Returns an emoji corresponding to the verdict string."""
    verdict_lower = verdict.lower()
    if "accept" in verdict_lower:
        return "✅"
    elif "minor" in verdict_lower:
        return "🔄"
    elif "major" in verdict_lower:
        return "⚠️"
    elif "reject" in verdict_lower:
        return "❌"
    return "📋"


# ── Summary Statistics ─────────────────────────────────────────────────────────

def compute_summary_stats(results: list[dict]) -> dict:
    """
    Computes aggregate statistics across all paper results.
    Used by the UI summary dashboard.
    """
    if not results:
        return {}

    scores   = [r["verdict"]["score"] for r in results]
    verdicts = [r["verdict"]["verdict"] for r in results]

    verdict_counts = {}
    for v in verdicts:
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    # Label distribution across all papers
    label_counts = {"Claim": 0, "Method": 0, "Result": 0, "Limitation": 0}
    for r in results:
        for sent in r.get("classified", []):
            lbl = sent.get("label", "")
            if lbl in label_counts:
                label_counts[lbl] += 1

    return {
        "num_papers":     len(results),
        "avg_score":      round(sum(scores) / len(scores), 2),
        "max_score":      max(scores),
        "min_score":      min(scores),
        "verdict_counts": verdict_counts,
        "label_counts":   label_counts,
    }
