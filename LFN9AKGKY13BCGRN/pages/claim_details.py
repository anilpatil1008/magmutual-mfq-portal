from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from services.claim_service import get_claim_review_workspace, save_section_answer, update_claim_status


def _fmt_conf(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "N/A"
    score = float(value)
    if 0 <= score <= 1:
        score *= 100
    return f"{max(0, min(score, 100)):.0f}%"


def _tone_for_conf(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "na"
    score = float(value)
    if 0 <= score <= 1:
        score *= 100
    if score >= 90:
        return "high"
    if score >= 80:
        return "medium"
    return "low"


def _render_header(claim: dict) -> None:
    status = escape(str(claim.get("STATUS", "Unknown")))
    priority = escape(str(claim.get("PRIORITY", "Unknown")))
    patient = escape(str(claim.get("PATIENT_NAME", "Unknown Patient")))
    defendant = escape(str(claim.get("DEFENDANT_NAME", "Unknown Defendant")))

    st.markdown(
        (
            "<section class='review-header-card'>"
            f"<div class='review-headline'>{patient} <span class='review-vs'>vs</span> {defendant}</div>"
            "<div class='review-badges'>"
            f"<span class='review-pill review-status'>{status}</span>"
            f"<span class='review-pill review-priority'>{priority}</span>"
            "</div>"
            "<div class='review-meta-grid'>"
            f"<div><div class='review-meta-label'>File Number</div><div>{escape(str(claim.get('FILE_NUMBER', '—')))}</div></div>"
            f"<div><div class='review-meta-label'>Defendant Specialty</div><div>{escape(str(claim.get('SPECIALTY', '—')))}</div></div>"
            f"<div><div class='review-meta-label'>Date Requested</div><div>{escape(str(claim.get('DATE_REQUESTED', '—')))}</div></div>"
            f"<div><div class='review-meta-label'>Assigned To</div><div>{escape(str(claim.get('ASSIGNED_TO', 'Unassigned')))}</div></div>"
            "</div>"
            "</section>"
        ),
        unsafe_allow_html=True,
    )


def _render_actions(session, ctx, claim_id: str) -> None:
    with st.container(key="review_action_bar"):
        c1, c2, _ = st.columns([1.3, 1.0, 4.0])
        if c1.button("Assign to Faculty", type="primary", use_container_width=True):
            update_claim_status(session, claim_id, "Assigned", assigned_to=ctx.username)
            st.success("Claim assigned to faculty queue.")
            st.rerun()

        if c2.button("Approve", type="primary", use_container_width=True):
            update_claim_status(session, claim_id, "Approved")
            st.success("Claim approved.")
            st.rerun()


def _render_confidence_panel(workspace: dict) -> None:
    overall = workspace.get("overall_confidence")
    section_conf = workspace.get("section_confidence", pd.DataFrame())

    st.markdown("### AI Confidence Analysis")
    left, right = st.columns([5, 2], vertical_alignment="center")
    with left:
        st.markdown(
            "<div class='review-subtle'>AI extraction confidence is calculated from section-level answers.</div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"<div class='overall-confidence'>Overall <span>{_fmt_conf(overall)}</span></div>",
            unsafe_allow_html=True,
        )

    if section_conf.empty:
        st.info("Section confidence scores are unavailable for this claim.")
        return

    for _, row in section_conf.iterrows():
        score = row.get("CONFIDENCE_SCORE")
        st.markdown(
            (
                "<div class='section-confidence-row'>"
                f"<div class='section-confidence-title'>{escape(str(row.get('SECTION_NAME', 'Unknown Section')))}</div>"
                f"<div class='section-confidence-score tone-{_tone_for_conf(score)}'>{_fmt_conf(score)}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.progress(max(0.0, min((float(score) if score is not None else 0.0), 1.0)) if score is not None and float(score) <= 1 else max(0.0, min((float(score or 0.0) / 100.0), 1.0)))


def _render_synopsis_panel(synopsis: dict) -> None:
    st.markdown("### Claim Synopsis")
    synopsis_text = str(synopsis.get("BRIEF_SYNOPSIS", "") or "").strip()
    injury = str(synopsis.get("ALLEGED_INJURY_TERMS", "") or "").strip()
    allegations = str(synopsis.get("ALLEGATION_SUMMARY", "") or "").strip()

    if not synopsis_text and not injury and not allegations:
        st.info("Synopsis fields are not available for this claim.")
        return

    if synopsis_text:
        st.markdown(f"**Synopsis**\n\n{escape(synopsis_text)}")
    if injury:
        st.markdown(f"**Alleged Injury**\n\n{escape(injury)}")
    if allegations:
        st.markdown(f"**Allegations**\n\n{escape(allegations)}")


def _render_questions(session, sections_df: pd.DataFrame) -> None:
    if sections_df.empty:
        st.info("MFQ form is unavailable for this claim.")
        return

    grouped = sections_df.groupby(["SECTION_ORDER", "SECTION_NAME"], dropna=False)
    for (_, section_name), section_df in grouped:
        with st.expander(str(section_name), expanded=False):
            for _, row in section_df.sort_values("QUESTION_ORDER").iterrows():
                question_id = str(row.get("QUESTION_ID", ""))
                answer_id = str(row.get("ANSWER_ID", "") or question_id)
                answer_text = str(row.get("ANSWER_TEXT", "") or "")
                allowed_values = row.get("ALLOWED_VALUES_LIST", []) or []
                answer_type = str(row.get("ANSWER_TYPE", "")).upper()

                st.markdown(
                    f"**{escape(str(row.get('QUESTION_ORDER', '')))}. {escape(str(row.get('QUESTION_TEXT', '')))}**"
                )
                st.markdown(
                    f"<span class='confidence-chip tone-{_tone_for_conf(row.get('CONFIDENCE_SCORE'))}'>Confidence {_fmt_conf(row.get('CONFIDENCE_SCORE'))}</span>",
                    unsafe_allow_html=True,
                )

                if answer_type in {"RADIO", "SELECT", "BOOLEAN"} and allowed_values:
                    safe_values = [str(v) for v in allowed_values]
                    selected_idx = 0
                    if answer_text and answer_text in safe_values:
                        selected_idx = safe_values.index(answer_text)
                    new_value = st.radio(
                        "Answer",
                        safe_values,
                        index=selected_idx,
                        horizontal=True,
                        key=f"ans_choice_{answer_id}",
                        label_visibility="collapsed",
                    )
                else:
                    new_value = st.text_area(
                        "Answer",
                        value=answer_text,
                        key=f"ans_text_{answer_id}",
                        placeholder="No answer currently extracted",
                        label_visibility="collapsed",
                    )

                if st.button("Save Answer", key=f"save_{answer_id}", type="tertiary"):
                    save_section_answer(session, answer_id, new_value)
                    st.success("Answer updated.")
                    st.rerun()
                st.divider()


def _render_text_tab(text: str, empty_msg: str) -> None:
    if text:
        st.write(text)
    else:
        st.info(empty_msg)


def _render_docs_tab(documents: pd.DataFrame) -> None:
    if documents.empty:
        st.info("No claim documents found.")
        return
    cols = [c for c in ["FILE_NAME", "DOC_TYPE", "OCR_STATUS", "CREATED_TS"] if c in documents.columns]
    st.dataframe(documents[cols], use_container_width=True, hide_index=True)


def _render_missing_objects(missing_objects: list[str]) -> None:
    if not missing_objects:
        return
    st.warning("Some Snowflake objects were not found. Showing partial data.")
    st.markdown("\n".join([f"- `{obj}`" for obj in missing_objects]))


def render(session, ctx) -> None:
    claim_id = st.session_state.get("selected_claim_id")
    if not claim_id:
        st.info("Open a claim from Dashboard or Claims page.")
        return

    st.markdown(f"<div class='review-breadcrumb'>← Back to Dashboard / <strong>{escape(str(claim_id))}</strong></div>", unsafe_allow_html=True)

    workspace = get_claim_review_workspace(session, str(claim_id))
    claim = workspace.get("claim")
    if not claim:
        st.error(f"Claim {claim_id} not found in claim detail view.")
        _render_missing_objects(workspace.get("missing_objects", []))
        return

    _render_header(claim)
    _render_actions(session, ctx, str(claim_id))
    _render_missing_objects(workspace.get("missing_objects", []))
    st.session_state["review_snowflake_objects"] = workspace.get("used_objects", [])
    st.session_state["review_missing_objects"] = workspace.get("missing_objects", [])

    tabs = st.tabs(["MFQ Form", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"])

    with tabs[0]:
        left, right = st.columns([2.2, 1.0], vertical_alignment="top")
        with left:
            _render_confidence_panel(workspace)
            st.markdown("### Medical Faculty Questionnaire")
            _render_questions(session, workspace.get("sections", pd.DataFrame()))
        with right:
            _render_synopsis_panel(workspace.get("synopsis", {}))

    with tabs[1]:
        _render_text_tab(workspace.get("summaries", {}).get("RECORDS_SUMMARY", ""), "No records summary available.")
    with tabs[2]:
        _render_text_tab(workspace.get("summaries", {}).get("MEDCRON", ""), "No MedCron summary available.")
    with tabs[3]:
        _render_text_tab(workspace.get("summaries", {}).get("LEGAL_MEMO", ""), "No legal memo available.")
    with tabs[4]:
        enquiries_df = workspace.get("enquiries", pd.DataFrame())
        if enquiries_df.empty:
            st.info("No enquiries data available for this claim.")
        else:
            st.dataframe(enquiries_df, use_container_width=True, hide_index=True)
    with tabs[5]:
        st.text_area("AI Assist Prompt", placeholder="Ask for claim-level insights from available summaries and MFQ answers")
        st.caption("AI Assist is placeholder UI and requires downstream service wiring.")
    with tabs[6]:
        _render_docs_tab(workspace.get("documents", pd.DataFrame()))
