import pandas as pd

from utils.claim_lifecycle import approved_claim_status, claim_bucket_sql_predicate, classify_claim_bucket


def test_approved_claim_status_uses_case_insensitive_mfq_status_only():
    assert approved_claim_status(pd.Series({"MFQ_STATUS": "Approved"}))
    assert approved_claim_status(pd.Series({"MFQ_STATUS": " APPROVED "}))
    assert not approved_claim_status(pd.Series({"CLAIM_STATUS": "approved", "MFQ_STATUS": "Rejected"}))
    assert not approved_claim_status(pd.Series({"CLAIM_STATUS": "approved"}))


def test_history_filter_excludes_non_approved_history_statuses():
    queue = pd.DataFrame(
        [
            {"CLAIM_ID": "CLM-1", "CLAIM_STATUS": "Assigned", "MFQ_STATUS": "Approved"},
            {"CLAIM_ID": "CLM-2", "CLAIM_STATUS": "Approved", "MFQ_STATUS": "Rejected"},
            {"CLAIM_ID": "CLM-3", "CLAIM_STATUS": "Approved", "MFQ_STATUS": "Assigned"},
            {"CLAIM_ID": "CLM-4", "CLAIM_STATUS": "Approved", "MFQ_STATUS": "On Hold"},
            {"CLAIM_ID": "CLM-5", "CLAIM_STATUS": "Approved", "MFQ_STATUS": "Initiated"},
            {"CLAIM_ID": "CLM-6", "CLAIM_STATUS": "Approved", "MFQ_STATUS": "MFQ Generated"},
        ]
    )

    queue["CLAIM_BUCKET"] = queue.apply(classify_claim_bucket, axis=1)
    history_df = queue[queue["CLAIM_BUCKET"] == "history"]
    history_df = history_df[history_df.apply(approved_claim_status, axis=1)]

    assert history_df["CLAIM_ID"].tolist() == ["CLM-1"]


def test_claim_bucket_sql_predicate_uses_mfq_approved_status_for_dashboard_tabs():
    history_where, history_params = claim_bucket_sql_predicate("history")
    ongoing_where, ongoing_params = claim_bucket_sql_predicate("ongoing")
    unknown_where, unknown_params = claim_bucket_sql_predicate("recent")

    assert history_where == "UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) = ?"
    assert history_params == ["APPROVED"]
    assert ongoing_where == "UPPER(TRIM(COALESCE(MFQ_STATUS, ''))) <> ?"
    assert ongoing_params == ["APPROVED"]
    assert unknown_where == ""
    assert unknown_params == []
