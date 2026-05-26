from __future__ import annotations


def classify_claim_bucket(days_since_submission: int | float | None) -> str:
    """Classify a claim into lifecycle buckets based on claim age.

    Buckets are intentionally broad to support dashboard grouping:
    - ``new``: 0-7 days
    - ``in_progress``: 8-30 days
    - ``stale``: older than 30 days
    - ``unknown``: missing/invalid age input
    """

    if days_since_submission is None:
        return "unknown"

    try:
        age = float(days_since_submission)
    except (TypeError, ValueError):
        return "unknown"

    if age < 0:
        return "unknown"
    if age <= 7:
        return "new"
    if age <= 30:
        return "in_progress"
    return "stale"
