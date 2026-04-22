from __future__ import annotations

import streamlit as st
from config.settings import CONFIG
from core.constants import ROLE_CLAIMS_ANALYST


def initialize_state() -> None:
    defaults = {
        "user_id": CONFIG.default_user_id,
        "role_key": ROLE_CLAIMS_ANALYST,
        "page": "Dashboard",
        "selected_claim_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
