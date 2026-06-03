import pandas as pd

from utils.claim_lifecycle import approved_claim_status, classify_claim_bucket


def test_approved_claim_status_uses_case_insensitive_claim_status():
    assert approved_claim_status(pd.Series({"CLAIM_STATUS": "approved", "MFQ_STATUS": "Rejected"}))
    assert approved_claim_status(pd.Series({"CLAIM_STATUS": " APPROVED "}))


def test_approved_claim_status_falls_back_to_mfq_status():
    assert approved_claim_status(pd.Series({"MFQ_STATUS": "Approved"}))
    assert not approved_claim_status(pd.Series({"MFQ_STATUS": "Assigned"}))


def test_history_filter_excludes_non_approved_history_statuses():
    queue = pd.DataFrame(
        [
            {"CLAIM_ID": "CLM-1", "CLAIM_STATUS": "Approved"},
            {"CLAIM_ID": "CLM-2", "CLAIM_STATUS": "Rejected"},
            {"CLAIM_ID": "CLM-3", "CLAIM_STATUS": "Assigned"},
            {"CLAIM_ID": "CLM-4", "CLAIM_STATUS": "On Hold"},
            {"CLAIM_ID": "CLM-5", "CLAIM_STATUS": "Initiated"},
            {"CLAIM_ID": "CLM-6", "CLAIM_STATUS": "MFQ Generated"},
        ]
    )

    queue["CLAIM_BUCKET"] = queue.apply(classify_claim_bucket, axis=1)
    history_df = queue[queue["CLAIM_BUCKET"] == "history"]
    history_df = history_df[history_df.apply(approved_claim_status, axis=1)]

    assert history_df["CLAIM_ID"].tolist() == ["CLM-1"]
