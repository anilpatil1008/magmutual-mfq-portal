from __future__ import annotations

from typing import Any

import pandas as pd

LIFECYCLE_FIELDS = [
    "CLAIM_LIFECYCLE_STATUS",
    "LIFECYCLE_STATUS",
    "CLAIM_BUCKET",
    "CLAIM_GROUP",
    "IS_HISTORY",
    "IS_ACTIVE",
    "STATUS_CATEGORY",
]

ONGOING_DERIVED_STATUSES = {"initiated", "assigned", "in review", "pending", "open", "mfr accepted & reviewing", "mfq generated"}
HISTORY_DERIVED_STATUSES = {"approved", "rejected", "completed", "closed", "cancelled"}


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def classify_claim_bucket(row: pd.Series) -> str:
    # TODO: Confirm final Ongoing vs History separation logic with BA/Data team.
    # TODO: Confirm which DB/API field should identify claim lifecycle status.
    # TODO: Replace derived status mapping once backend provides a dedicated lifecycle/category field.
    for field in LIFECYCLE_FIELDS:
        if field not in row.index:
            continue
        value = row.get(field)
        norm = _normalize(value)
        if field == "IS_HISTORY" and str(value).lower() in {"1", "true", "yes", "y"}:
            return "history"
        if field == "IS_ACTIVE" and str(value).lower() in {"0", "false", "no", "n"}:
            return "history"
        if any(term in norm for term in {"history", "closed", "completed"}):
            return "history"
        if norm:
            return "ongoing"

    status = _normalize(row.get("CLAIM_STATUS") or row.get("WORKFLOW_STATUS") or row.get("MFQ_STATUS") or row.get("STATUS"))
    if status in HISTORY_DERIVED_STATUSES:
        return "history"
    if status in ONGOING_DERIVED_STATUSES:
        return "ongoing"
    return "ongoing"

