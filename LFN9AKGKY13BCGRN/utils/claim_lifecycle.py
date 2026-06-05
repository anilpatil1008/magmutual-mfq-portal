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
MFQ_STATUS_FIELD = "MFQ_STATUS"
APPROVED_STATUS = "APPROVED"


def claim_bucket_sql_predicate(claim_bucket: str) -> tuple[str, list[str]]:
    """Return SQL predicate pieces for dashboard claim buckets.

    History Claims are claims whose visible MFQ Status is Approved; Ongoing
    Claims are everything else. Keep this aligned with approved_claim_status().
    """
    normalized_bucket = str(claim_bucket or "").strip().lower()
    if normalized_bucket == "history":
        return "UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) = ?", [APPROVED_STATUS]
    if normalized_bucket == "ongoing":
        return "UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) <> ?", [APPROVED_STATUS]
    return "", []


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def approved_claim_status(row: pd.Series) -> bool:
    """Return True only when the row's MFQ Status column is Approved.

    History Claims are driven by the visible MFQ Status column, so do not
    fall back to claim/workflow/status fields that can describe a different
    lifecycle state for the same claim.
    """
    if MFQ_STATUS_FIELD not in row.index:
        return False

    status = str(row.get(MFQ_STATUS_FIELD) or "").strip()
    return status.upper() == APPROVED_STATUS


def classify_claim_bucket(row: pd.Series) -> str:
    if approved_claim_status(row):
        return "history"

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

