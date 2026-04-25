import pandas as pd
import streamlit as st

from components.badges import confidence_badge, priority_badge, status_badge
from utils.constants import REGEN_TOOLTIP
from utils.helpers import select_claim


def _format_claims_for_display(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["STATUS"] = out["STATUS"].apply(status_badge)
    out["PRIORITY"] = out["PRIORITY"].apply(priority_badge)
    out["AI_CONFIDENCE"] = out["AI_CONFIDENCE"].astype(float).apply(confidence_badge)
    out["NEW_MFQ"] = out["HAS_NEW_MFQ_VERSION"].apply(
        lambda x: "<span class='flag-red' title='{}'>●</span>".format(REGEN_TOOLTIP) if x else ""
    )
    out["ACTION"] = out["CLAIM_ID"].apply(lambda cid: f"Review | {cid}")
    return out


def render_claims_table(df: pd.DataFrame, key_prefix: str = "claims") -> None:
    if df.empty:
        st.info("No claims found.")
        return

    display_cols = [
        "CLAIM_ID",
        "PATIENT_NAME",
        "DEFENDANT_NAME",
        "STATUS",
        "PRIORITY",
        "AI_CONFIDENCE",
        "NEW_MFQ",
        "ACTION",
    ]
    styled = _format_claims_for_display(df)[display_cols]
    st.markdown(
        f"<div class='table-card'>{styled.to_html(index=False, escape=False, classes='claims-table')}</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            review_claim = st.selectbox("Review Claim", df["CLAIM_ID"].tolist(), key=f"{key_prefix}_review")
        with c2:
            regen_claim = st.selectbox("Regenerate MFQ", df[df["HAS_NEW_MFQ_VERSION"]]["CLAIM_ID"].tolist() or [""], key=f"{key_prefix}_regen")
        with c3:
            if st.button("Review", key=f"{key_prefix}_review_btn"):
                select_claim(review_claim)
                st.rerun()
            if regen_claim and st.button("Regenerate", key=f"{key_prefix}_regen_btn"):
                st.success(f"Latest MFQ loaded for claim {regen_claim}.")
