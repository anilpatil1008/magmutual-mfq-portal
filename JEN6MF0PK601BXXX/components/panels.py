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
            <div class="claim-header-top">
                <div class="claim-title-row">
                    <div class="claim-title">
                        {_safe(row['PATIENT_NAME'])} <span class="claim-vs">vs</span> {_safe(row['DEFENDANT_NAME'])}
                    </div>
                    <div class="claim-badge-wrap">
                        <span class="claim-badge">{_status_chip(row['STATUS'])}</span>
                        <span class="claim-badge">{_priority_chip(row['PRIORITY'])}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        st.markdown("""<div class="claim-actions"></div>""", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if role_key in {"CLAIMS_ANALYST", "ADMIN"}:
            b1.markdown("""<div class="btn-primary"></div>""", unsafe_allow_html=True)
            if b1.button("Assign to Faculty", key="assign_faculty_btn"):
                st.info("Connect this to assignment workflow.")
            b2.markdown("""<div class="btn-success"></div>""", unsafe_allow_html=True)
            if b2.button("Approve", type="primary", key=f"approve_{row['CLAIM_ID']}"):
                approve_claim(row["CLAIM_ID"])
                st.success("Claim approved")
                st.rerun()

    st.markdown("""<div class="claim-meta-grid">""", unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(f"""<div class="claim-meta-item"><div class="claim-meta-label">FILE NUMBER</div><div class="claim-meta-value">{_safe(row['FILE_NUMBER'])}</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="claim-meta-item"><div class="claim-meta-label">DEFENDANT SPECIALTY</div><div class="claim-meta-value">{_safe(row['DEFENDANT_SPECIALTY'])}</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="claim-meta-item"><div class="claim-meta-label">DATE REQUESTED</div><div class="claim-meta-value">{_safe(row['DATE_REQUESTED'])}</div></div>""", unsafe_allow_html=True)
    c4.markdown("""<div class="claim-meta-item"><div class="claim-meta-label">MAGMUTUAL CONTACT</div><div class="claim-meta-value">Sarah Johnson</div></div>""", unsafe_allow_html=True)
    c5.markdown("""<div class="claim-meta-item"><div class="claim-meta-label">CONTACT EMAIL</div><div class="claim-meta-value"><a href="mailto:analyst@magmutual.com">analyst@magmutual.com</a></div></div>""", unsafe_allow_html=True)
    st.markdown("""</div>""", unsafe_allow_html=True)

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
