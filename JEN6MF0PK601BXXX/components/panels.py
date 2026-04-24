from __future__ import annotations

import html
import streamlit as st

from services.claim_service import approve_claim


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _status_chip(status: str) -> str:
    mapping = {
        "MFQ Generated": ("#e7efff", "#2457d6"),
        "Assigned": ("#e7efff", "#2457d6"),
        "Approved": ("#e8f7ee", "#067647"),
        "Rejected": ("#fde7e7", "#d92d20"),
    }
    bg, fg = mapping.get(str(status), ("#eef2f7", "#475467"))
    return f"<span class='inline-chip' style='background:{bg};color:{fg};'>{_safe(status)}</span>"


def _priority_chip(priority: str) -> str:
    mapping = {
        "Critical": ("#fde7e7", "#d92d20"),
        "High": ("#fff1d6", "#b54708"),
        "Medium": ("#e7efff", "#2457d6"),
        "Low": ("#eef2f7", "#475467"),
    }
    bg, fg = mapping.get(str(priority), ("#eef2f7", "#475467"))
    return f"<span class='inline-chip' style='background:{bg};color:{fg};'>{_safe(priority)}</span>"


def render_claim_header_card(row, role_key: str) -> None:
    st.markdown("""<div class="claim-header-card">""", unsafe_allow_html=True)

    top_left, top_right = st.columns([5, 2])

    with top_left:
        st.markdown(
            f"""
            <div class="claim-main-title">
                {_safe(row['PATIENT_NAME'])} <span class="vs-text">vs</span> {_safe(row['DEFENDANT_NAME'])}
                {_status_chip(row['STATUS'])}
                {_priority_chip(row['PRIORITY'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        b1, b2 = st.columns(2)
        if role_key in {"CLAIMS_ANALYST", "ADMIN"}:
            if b1.button("Assign to Faculty", use_container_width=True, key="assign_faculty_btn"):
                st.info("Connect this to assignment workflow.")
            if b2.button("Approve", use_container_width=True, key=f"approve_{row['CLAIM_ID']}"):
                approve_claim(row["CLAIM_ID"])
                st.success("Claim approved")
                st.rerun()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f"**FILE NUMBER**  \n{_safe(row['FILE_NUMBER'])}")
    c2.markdown(f"**DEFENDANT SPECIALTY**  \n{_safe(row['DEFENDANT_SPECIALTY'])}")
    c3.markdown(f"**DATE REQUESTED**  \n{_safe(row['DATE_REQUESTED'])}")
    c4.markdown("**MAGMUTUAL CONTACT**  \nSarah Johnson")
    c5.markdown("**CONTACT EMAIL**  \nanalyst@magmutual.com")

    st.markdown("""</div>""", unsafe_allow_html=True)


def render_claim_tabs() -> str:
    tabs = [
        "MFQ Form",
        "Records Summary",
        "MedCron",
        "Legal Memo",
        "Enquiries",
        "AI Assist",
        "Documents",
    ]

    current = st.radio(
        "Claim detail tabs",
        tabs,
        key="claim_detail_tab",
        horizontal=True,
        label_visibility="collapsed",
    )
    return current
