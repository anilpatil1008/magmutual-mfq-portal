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

    metadata = [
        ("FILE NUMBER", _safe(row["FILE_NUMBER"])),
        ("DEFENDANT SPECIALTY", _safe(row["DEFENDANT_SPECIALTY"])),
        ("DATE REQUESTED", _safe(row["DATE_REQUESTED"])),
        ("MAGMUTUAL CONTACT", "Sarah Johnson"),
        ("CONTACT EMAIL", '<a href="mailto:analyst@magmutual.com">analyst@magmutual.com</a>'),
    ]

    st.markdown("""<div class="claim-meta-grid">""", unsafe_allow_html=True)
    meta_cols = st.columns(len(metadata))
    for col, (label, value) in zip(meta_cols, metadata):
        col.markdown(
            f"""<div class="claim-meta-item"><div class="claim-meta-label">{label}</div><div class="claim-meta-value">{value}</div></div>""",
            unsafe_allow_html=True,
        )
    st.markdown("""</div>""", unsafe_allow_html=True)

    st.markdown("""</div>""", unsafe_allow_html=True)


def render_claim_tabs() -> str:
    tabs = [
        "🩺 MFQ Form",
        "📋 Records Summary",
        "🕒 MedCron",
        "🛡️ Legal Memo",
        "💬 Enquiries",
        "🤖 AI Assist",
        "📥 Documents",
    ]

    current = st.radio(
        "Claim detail tabs",
        tabs,
        key="claim_detail_tab",
        horizontal=True,
        label_visibility="collapsed",
    )
    return current.replace("🩺 ", "").replace("📋 ", "").replace("🕒 ", "").replace("🛡️ ", "").replace("💬 ", "").replace("🤖 ", "").replace("📥 ", "")
