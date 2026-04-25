import streamlit as st

from components.cards import render_claim_header
from components.forms import render_mfq_sections
from services.snowflake_service import get_claim_by_id, get_mfq_sections, update_claim_status


def _render_actions(session, claim: dict, role: str):
    status = claim["STATUS"]
    st.markdown("### Actions")
    c1, c2, c3 = st.columns(3)

    if status == "MFQ Generated" and role in {"Claim Analyst", "Advice Team"}:
        if c1.button("Assign to Faculty"):
            update_claim_status(session, claim["CLAIM_ID"], "Assigned", assigned_to="FACULTY_1")
            st.success("Claim assigned to faculty.")
        if c2.button("Approve"):
            update_claim_status(session, claim["CLAIM_ID"], "Approved")
            st.success("Claim approved.")

    elif status == "Assigned" and role in {"Claim Analyst", "Advice Team"}:
        if c1.button("Reassign"):
            update_claim_status(session, claim["CLAIM_ID"], "Assigned", assigned_to="FACULTY_2")
            st.success("Claim reassigned.")

    elif status == "Assigned" and role == "Medical Faculty":
        if c1.button("Approve"):
            update_claim_status(session, claim["CLAIM_ID"], "Approved")
            st.success("Claim approved.")
        if c2.button("Reject"):
            update_claim_status(session, claim["CLAIM_ID"], "Rejected")
            st.error("Claim rejected and sent back.")

    elif status == "Rejected" and role in {"Claim Analyst", "Advice Team"}:
        if c1.button("Assign to Faculty"):
            update_claim_status(session, claim["CLAIM_ID"], "Assigned", assigned_to="FACULTY_3")
            st.success("Rejected claim re-assigned.")
    else:
        st.caption("No further actions available for this status/role combination.")


def render(session, role: str, _username: str, claim_id: str | None):
    st.subheader("Claim Details")
    if not claim_id:
        st.info("Select a claim from Dashboard/Claims to review details.")
        return

    claim_df = get_claim_by_id(session, claim_id)
    if claim_df.empty:
        st.error("Claim not found.")
        return

    claim = claim_df.iloc[0].to_dict()
    render_claim_header(claim)
    _render_actions(session, claim, role)

    tabs = st.tabs(["MFQ Form Review", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"])

    with tabs[0]:
        st.toggle("Edit mode", key="mfq_edit_mode")
        mfq = get_mfq_sections(session, claim_id)
        render_mfq_sections(mfq, editable=st.session_state.mfq_edit_mode)

    with tabs[1]:
        st.write(claim.get("RECORDS_SUMMARY", "No records summary available."))
    with tabs[2]:
        st.write(claim.get("MEDCRON_TEXT", "No MedCron data available."))
    with tabs[3]:
        st.write(claim.get("LEGAL_MEMO_TEXT", "No legal memo available."))
    with tabs[4]:
        st.text_area("Raise Query / Resolution", placeholder="Type question for analyst/faculty")
        st.button("Post Message")
    with tabs[5]:
        prompt = st.text_input("Ask AI Assist")
        if st.button("Ask") and prompt:
            st.info("AI Assist response is RBAC constrained and sourced from claim documents.")
    with tabs[6]:
        st.write("Download PDF exports")
        st.download_button("Download MFQ Form", data="MFQ content", file_name=f"MFQ_{claim_id}.txt")
