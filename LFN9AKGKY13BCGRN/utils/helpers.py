from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.constants import DEFAULT_ROLE
from utils.navigation import navigate_to_claim_details


def init_state() -> None:
    defaults = {
        "active_page": "Dashboard",
        "selected_claim_id": None,
        "current_view": "dashboard",
        "active_sidebar_item": "Dashboard",
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
    navigate_to_claim_details(str(claim_id))


def score_bucket(score: float) -> str:
    if score >= 90:
        return "badge-success"
    if score >= 80:
        return "badge-warning"
    return "badge-danger"
