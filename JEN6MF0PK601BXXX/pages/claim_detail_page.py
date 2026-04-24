from __future__ import annotations

import html
import streamlit as st

from components.mfq import (
    render_ai_confidence_panel,
    render_claim_synopsis_panel,
    render_mfq_section_navigation,
    render_mfq_questionnaire,
)
from components.panels import render_claim_header_card, render_claim_tabs
from repositories.claim_repository import get_claim_header
from repositories.mfq_repository import (
    get_claim_summaries,
    get_current_answers,
    get_questions_by_section,
    get_section_confidence,
    get_sections,
)
from services.mfq_service import get_editable_sections


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def render_claim_detail_page(user_id: str, role_key: str) -> None:
    claim_id = st.session_state.get("selected_claim_id")

    if not claim_id:
        st.warning("No claim selected.")
        return

    header_df = get_claim_header(claim_id)
    if header_df.empty:
        st.error("Claim not found.")
        return

    row = header_df.iloc[0]
    defendant_id = row["DEFENDANT_ID"]

    st.markdown('<div class="review-page"></div>', unsafe_allow_html=True)
    st.markdown('<div class="review-breadcrumb"></div>', unsafe_allow_html=True)

    breadcrumb_label = f"← Back to Dashboard  /  {_safe(row['FILE_NUMBER'])}"
    if st.button(breadcrumb_label, key="back_to_dashboard_btn"):
        st.session_state.page = "Dashboard"
        st.session_state.selected_claim_id = None
        st.rerun()

    render_claim_header_card(row=row, role_key=role_key)

    selected_tab = render_claim_tabs()

    if selected_tab == "MFQ Form":
        sections_df = get_sections()
        section_conf_df = get_section_confidence(claim_id, defendant_id)
        render_ai_confidence_panel(section_conf_df, float(row["AI_CONFIDENCE"]))

        left, right = st.columns([1.05, 2.4])

        with left:
            render_claim_synopsis_panel(row)
            render_mfq_section_navigation(sections_df, section_conf_df)

        with right:
            answers_df = get_current_answers(claim_id, defendant_id)
            answers_map = {r["QUESTION_ID"]: r for _, r in answers_df.iterrows()}
            editable_sections = get_editable_sections(claim_id, user_id, role_key)

            render_mfq_questionnaire(
                claim_id=claim_id,
                defendant_id=defendant_id,
                sections_df=sections_df,
                answers_map=answers_map,
                editable_sections=editable_sections,
                get_questions_by_section_fn=get_questions_by_section,
                user_id=user_id,
            )
    else:
        summaries_df = get_claim_summaries(claim_id, defendant_id)
        summary_map = {r["SUMMARY_TYPE"]: r["SUMMARY_TEXT"] for _, r in summaries_df.iterrows()}

        st.markdown("""<div class="content-card">""", unsafe_allow_html=True)

        if selected_tab == "Records Summary":
            st.subheader("Records Summary")
            st.write(summary_map.get("RECORDS_SUMMARY", "No records summary available"))
        elif selected_tab == "MedCron":
            st.subheader("MedCron")
            st.write(summary_map.get("MEDCRON", "No MedCron summary available"))
        elif selected_tab == "Legal Memo":
            st.subheader("Legal Memo")
            st.write(summary_map.get("LEGAL_MEMO", "No legal memo summary available"))
        elif selected_tab == "Enquiries":
            st.subheader("Enquiries")
            q = st.text_area("Ask a role-safe question", key="claim_detail_enquiry")
            if st.button("Ask", key="claim_detail_enquiry_btn"):
                st.info("Connect this to RBAC-safe RAG or Cortex workflow.")
        elif selected_tab == "AI Assist":
            st.subheader("AI Assist")
            st.write("Use this tab for guided AI analysis and evidence lookup.")
        elif selected_tab == "Documents":
            st.subheader("Documents")
            st.write("Add document viewer and PDF download links here.")

        st.markdown("""</div>""", unsafe_allow_html=True)
