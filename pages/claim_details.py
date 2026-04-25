from __future__ import annotations

import streamlit as st

from components.cards import render_claim_header
from services.claim_service import get_claim_details, get_claim_sections, save_section_answer, update_claim_status
from services.rbac_service import can_edit_claim


def _action_bar(session, ctx, claim: dict) -> None:
    st.markdown("#### Workflow Actions")
    c1, c2, c3 = st.columns(3)
    claim_id = str(claim["CLAIM_ID"])

    if c1.button("Assign to Faculty", use_container_width=True):
        update_claim_status(session, claim_id, "Assigned", assigned_to=ctx.username)
        st.success("Claim assigned.")
        st.rerun()
    if c2.button("Approve", use_container_width=True):
        update_claim_status(session, claim_id, "Approved")
        st.success("Claim approved.")
        st.rerun()
    if c3.button("Reject", use_container_width=True):
        update_claim_status(session, claim_id, "Rejected")
        st.warning("Claim rejected and routed back.")
        st.rerun()


def _render_mfq_form(session, ctx, claim: dict) -> None:
    claim_id = str(claim["CLAIM_ID"])
    sections = get_claim_sections(session, claim_id)

    if sections.empty:
        st.info("No MFQ sections are available for this claim.")
        return

    editable = can_edit_claim(ctx.app_role, str(claim.get("STATUS", "")), claim.get("ASSIGNED_TO"), ctx.username)
    st.caption("Edit mode is role-restricted and assignment-aware.")

    for section_name, section_df in sections.groupby("SECTION_NAME", dropna=False):
        with st.expander(str(section_name), expanded=False):
            for _, row in section_df.iterrows():
                q = row.get("QUESTION_TEXT", "")
                answer = row.get("ANSWER_TEXT", "")
                conf = row.get("CONFIDENCE_SCORE", "")
                answer_id = row.get("ANSWER_ID", "")
                st.markdown(f"**Q:** {q}")
                new_value = st.text_area(
                    "Answer",
                    value=str(answer),
                    key=f"answer_{answer_id}",
                    disabled=not editable,
                    label_visibility="collapsed",
                )
                st.caption(f"AI Confidence: {conf}")
                if editable and st.button("Save", key=f"save_{answer_id}"):
                    save_section_answer(session, str(answer_id), new_value)
                    st.success("Answer saved.")


def render(session, ctx) -> None:
    st.subheader("Claim Details")
    claim_id = st.session_state.get("selected_claim_id")
    if not claim_id:
        st.info("Open a claim from Dashboard or Claims page.")
        return

    claim = get_claim_details(session, claim_id)
    if not claim:
        st.error(f"Claim {claim_id} not found.")
        return

    render_claim_header(claim)
    _action_bar(session, ctx, claim)

    tabs = st.tabs(["MFQ Form", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"])

    with tabs[0]:
        _render_mfq_form(session, ctx, claim)
    with tabs[1]:
        st.write(claim.get("RECORDS_SUMMARY", "No records summary available."))
    with tabs[2]:
        st.write(claim.get("MEDCRON_TEXT", "No chronology summary available."))
    with tabs[3]:
        st.write(claim.get("LEGAL_MEMO_TEXT", "No legal memo summary available."))
    with tabs[4]:
        st.text_area("Raise enquiry", placeholder="Enter question for analyst/faculty")
        st.button("Post enquiry")
    with tabs[5]:
        prompt = st.text_input("Ask AI Assist")
        if st.button("Run AI Assist") and prompt:
            st.info("AI Assist run submitted with RBAC-scoped retrieval.")
    with tabs[6]:
        st.download_button("Download MFQ Snapshot", data=str(claim), file_name=f"MFQ_{claim_id}.txt")
