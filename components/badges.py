import streamlit as st

from utils.constants import PRIORITY_COLORS, STATUS_COLORS
from utils.helpers import score_bucket


def render_badge(label: str, css_class: str) -> str:
    return f"<span class='badge {css_class}'>{label}</span>"


def status_badge(status: str) -> str:
    return render_badge(status, STATUS_COLORS.get(status, "badge-muted"))


def priority_badge(priority: str) -> str:
    return render_badge(priority, PRIORITY_COLORS.get(priority, "badge-muted"))


def confidence_badge(score: float) -> str:
    return render_badge(f"{score:.0f}%", score_bucket(score))


def show_html(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)
