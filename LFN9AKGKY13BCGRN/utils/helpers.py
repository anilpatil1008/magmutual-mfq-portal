from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.constants import DEFAULT_ROLE


def init_state() -> None:
    defaults = {
        "active_page": "Dashboard",
        "selected_claim_id": None,
        "active_role": DEFAULT_ROLE,
        "notifications": 3,
        "mfq_edit_mode": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def to_df(rows) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    return pd.DataFrame(rows)


def set_page(page: str) -> None:
    st.session_state.active_page = page


def select_claim(claim_id: str) -> None:
    st.session_state.selected_claim_id = claim_id
    st.session_state.active_page = "Claim Details"
    st.session_state.current_view = "Claim Details"


def score_bucket(score: float) -> str:
    if score >= 90:
        return "badge-success"
    if score >= 80:
        return "badge-warning"
    return "badge-danger"
