from __future__ import annotations

import pandas as pd

from repositories import claims_repository


def test_safe_int_returns_default_for_missing_nan_empty_and_invalid_values():
    assert claims_repository._safe_int(None) == 0
    assert claims_repository._safe_int(float("nan")) == 0
    assert claims_repository._safe_int(pd.NA) == 0
    assert claims_repository._safe_int("") == 0
    assert claims_repository._safe_int("not-a-count") == 0


def test_safe_int_converts_valid_count_values():
    assert claims_repository._safe_int(3) == 3
    assert claims_repository._safe_int(3.0) == 3
    assert claims_repository._safe_int("4") == 4


def test_filtered_claim_bucket_counts_treat_nan_counts_as_zero(monkeypatch):
    monkeypatch.setattr(claims_repository, "table_columns", lambda *_args, **_kwargs: {"MFQ_STATUS"})
    monkeypatch.setattr(
        claims_repository,
        "build_claim_filter_where_clause",
        lambda *_args, **_kwargs: ("", {}),
    )
    monkeypatch.setattr(
        claims_repository,
        "execute_query_df",
        lambda *_args, **_kwargs: pd.DataFrame(
            [{"ONGOING_COUNT": float("nan"), "HISTORY_COUNT": pd.NA}]
        ),
    )

    assert claims_repository.get_filtered_claim_bucket_counts(object(), {"date_filter": "Today"}) == {
        "ongoing": 0,
        "history": 0,
    }


def test_filtered_claims_count_treats_nan_total_count_as_zero(monkeypatch):
    monkeypatch.setattr(claims_repository, "table_columns", lambda *_args, **_kwargs: set())
    monkeypatch.setattr(
        claims_repository,
        "build_claim_filter_where_clause",
        lambda *_args, **_kwargs: ("", {}),
    )
    monkeypatch.setattr(
        claims_repository,
        "execute_query_df",
        lambda *_args, **_kwargs: pd.DataFrame([{"TOTAL_COUNT": float("nan")}]),
    )

    assert claims_repository.get_filtered_claims_count(object(), {"date_filter": "Last 7 days"}) == 0
