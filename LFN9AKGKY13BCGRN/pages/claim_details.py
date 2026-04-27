from __future__ import annotations

import json
from html import escape

import pandas as pd
import streamlit as st

from services.claim_service import get_claim_review_workspace, save_section_answer, update_claim_status
from services.rbac_service import can_edit_claim


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


def _render_header(session, ctx, claim_id: str, claim: dict) -> None:
    status = escape(str(claim.get("STATUS", "Unknown")))
    priority = escape(str(claim.get("PRIORITY", "Unknown")))
    patient = escape(str(claim.get("PATIENT_NAME", "Unknown Patient")))
    defendant = escape(str(claim.get("DEFENDANT_NAME", "Unknown Defendant")))
    assigned_to = str(claim.get("ASSIGNED_TO", "") or "").strip()
    assign_label = "Reassign to Faculty" if assigned_to else "Assign to Faculty"

    with st.container(key="review_header_card"):
        left_col, action_col = st.columns([6.2, 1.3], vertical_alignment="top")
        with left_col:
            st.markdown("<div class='review-headline-wrap'>", unsafe_allow_html=True)
            st.markdown(
                (
                    f"<div class='review-headline'>{patient} <span class='review-vs'>vs</span> {defendant}</div>"
                    "<div class='review-badges'>"
                    f"<span class='review-pill review-status'>{status}</span>"
                    f"<span class='review-pill review-priority'>{priority}</span>"
                    "</div>"
                    "<div class='review-meta-grid claim-meta-grid'>"
                    f"<div><div class='review-meta-label'>File Number</div><div>{escape(str(claim.get('FILE_NUMBER', '—')))}</div></div>"
                    f"<div><div class='review-meta-label'>Defendant Specialty</div><div>{escape(str(claim.get('SPECIALTY', '—')))}</div></div>"
                    f"<div><div class='review-meta-label'>Date Requested</div><div>{escape(str(claim.get('DATE_REQUESTED', '—')))}</div></div>"
                    f"<div><div class='review-meta-label'>Assigned To</div><div>{escape(str(claim.get('ASSIGNED_TO', 'Unassigned')))}</div></div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with action_col:
            st.markdown("<div class='review-header-actions claim-header-actions'>", unsafe_allow_html=True)
            if st.button(assign_label, type="primary", use_container_width=True):
                update_claim_status(session, claim_id, "Assigned", assigned_to=ctx.username)
                st.success("Claim assigned to faculty queue.")
                st.rerun()

            if st.button("Approve", type="secondary", use_container_width=True):
                update_claim_status(session, claim_id, "Approved")
                st.success("Claim approved.")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _go_back_to_dashboard() -> None:
    st.session_state["selected_claim_id"] = None
    st.session_state["active_page"] = "Dashboard"
    st.rerun()


def _render_breadcrumb(claim_id: str) -> None:
    with st.container(key="review_breadcrumb_row"):
        st.markdown("<div class='review-breadcrumb'>", unsafe_allow_html=True)
        st.button(
            f"← Back to Dashboard / {escape(str(claim_id))}",
            key="review_back_to_dashboard",
            on_click=_go_back_to_dashboard,
            type="tertiary",
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_confidence_panel(workspace: dict) -> None:
    summary = workspace.get("confidence_summary", {})
    overall = summary.get("overall_confidence")
    recommendation = str(summary.get("recommendation", "Faculty Review Recommended"))
    explanation = str(summary.get("explanation", ""))
    section_conf = workspace.get("section_confidence", pd.DataFrame())

    if overall is None and section_conf.empty:
        st.info("AI confidence data is not available for this claim.")
        return

    badge_tone = "high" if recommendation == "No Faculty Review Needed" else "medium"
    st.markdown(
        (
            "<section class='confidence-card'>"
            "<div class='confidence-header'>"
            "<div class='confidence-header-left'>"
            "<span class='confidence-title'>⚕ AI Confidence Analysis</span>"
            "<span class='confidence-collapse' aria-hidden='true'>⌃</span>"
            "</div>"
            "<div class='confidence-header-right'>"
            f"<span class='confidence-badge tone-{badge_tone}'>{escape(recommendation)}</span>"
            f"<span class='confidence-overall'>Overall <strong>{_fmt_conf(overall)}</strong></span>"
            "</div>"
            "</div>"
            "<div class='confidence-message-box'>"
            "<div class='confidence-message-title'>🛡 "
            f"{escape(recommendation)}</div>"
            f"<div class='confidence-message-sub'>{escape(explanation)}</div>"
            "</div>"
            "</section>"
        ),
        unsafe_allow_html=True,
    )

    if section_conf.empty:
        st.info("Section confidence scores are unavailable for this claim.")
        return

    st.markdown("<div class='confidence-grid-title'>SECTION-WISE CONFIDENCE</div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="small")
    moderate_or_low_sections: list[str] = []
    ordered_rows = list(section_conf.iterrows())
    midpoint = (len(ordered_rows) + 1) // 2
    split_rows = [ordered_rows[:midpoint], ordered_rows[midpoint:]]

    for col, rows in zip([left, right], split_rows):
        with col:
            for _, row in rows:
                section_name = str(row.get("SECTION_NAME", "Unknown Section"))
                score = row.get("CONFIDENCE_SCORE_PCT", row.get("CONFIDENCE_SCORE"))
                tone = _tone_for_conf(score)
                score_pct = float(score) if score is not None and not pd.isna(score) else 0.0
                width_pct = max(0.0, min(score_pct, 100.0))
                if tone in {"medium", "low"}:
                    moderate_or_low_sections.append(section_name)
                st.markdown(
                    (
                        "<div class='confidence-row'>"
                        "<div class='confidence-row-top'>"
                        f"<span>{escape(section_name)}</span>"
                        f"<span class='tone-{tone}'>{_fmt_conf(score)}</span>"
                        "</div>"
                        f"<div class='confidence-progress'><span class='tone-{tone}' style='width:{width_pct:.0f}%'></span></div>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )

    note = "All sections are high confidence."
    if moderate_or_low_sections:
        note = f"Moderate confidence: {', '.join(moderate_or_low_sections)}"
    st.markdown(f"<div class='confidence-note'>● {escape(note)}</div>", unsafe_allow_html=True)


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


def _normalize_answer_value(raw):
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return ""
    if isinstance(raw, list):
        return [str(v) for v in raw]
    if isinstance(raw, dict):
        return raw
    text = str(raw).strip()
    if not text:
        return ""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, (list, dict, str)):
            return parsed
    except Exception:
        pass
    return text


def _safe_widget_key(prefix: str, claim_id: str, section_id: str, question: pd.Series, index: int) -> str:
    question_id = question.get("QUESTION_ID") or question.get("question_id")
    question_key = question.get("QUESTION_KEY") or question.get("question_key")
    display_order = question.get("QUESTION_ORDER") or question.get("DISPLAY_ORDER") or index
    section_key = question.get("SECTION_KEY") or question.get("section_key")
    section_part = section_id or str(section_key or "section")
    unique_part = question_id or question_key or f"{section_part}_{display_order}_{index}"
    return f"{prefix}_{claim_id}_{section_part}_{unique_part}_{index}"


def _is_visible(row: pd.Series, answer_by_question: dict[str, str]) -> bool:
    parent_id = str(row.get("PARENT_QUESTION_ID", "") or "").strip()
    if not parent_id:
        return True

    parent_answer = str(answer_by_question.get(parent_id, "") or "").strip().upper()
    if not parent_answer:
        return False

    rule_raw = row.get("VISIBILITY_RULE")
    if rule_raw is None or (isinstance(rule_raw, float) and pd.isna(rule_raw)):
        return True

    if isinstance(rule_raw, dict):
        rule = rule_raw
    else:
        try:
            rule = json.loads(str(rule_raw))
        except Exception:
            return True

    allowed = [str(v).upper() for v in rule.get("parent_answer_in", [])] if isinstance(rule, dict) else []
    if not allowed:
        return True
    return parent_answer in allowed


def _render_questions(session, sections_df: pd.DataFrame, can_edit: bool, edit_mode: bool) -> None:
    if sections_df.empty:
        st.info("MFQ form is unavailable for this claim.")
        return

    working_df = sections_df.sort_values(["SECTION_ORDER", "QUESTION_ORDER"]).copy()
    answer_by_question: dict[str, str] = {}
    for _, seed_row in working_df.iterrows():
        answer_by_question[str(seed_row.get("QUESTION_ID", "") or "")] = str(seed_row.get("DISPLAY_ANSWER", "") or "")

    grouped = working_df.groupby(["SECTION_ORDER", "SECTION_NAME"], dropna=False)
    for (_, section_name), section_df in grouped:
        with st.expander(str(section_name), expanded=False):
            ordered_section_df = section_df.sort_values("QUESTION_ORDER")
            for idx, (_, row) in enumerate(ordered_section_df.iterrows()):
                if not _is_visible(row, answer_by_question):
                    continue
                question_id = str(row.get("QUESTION_ID", ""))
                answer_id = str(row.get("ANSWER_ID", "") or "")
                claim_id = str(row.get("CLAIM_ID", "") or "")
                defendant_id = str(row.get("DEFENDANT_ID", "") or "")
                section_id = str(row.get("SECTION_ID", "") or row.get("SECTION_KEY", "") or "")
                answer_text = row.get("DISPLAY_ANSWER", "")
                allowed_values = row.get("ALLOWED_VALUES_LIST", []) or []
                answer_type = str(row.get("ANSWER_TYPE", "")).upper()

                st.markdown(
                    f"**{escape(str(row.get('QUESTION_ORDER', '')))}. {escape(str(row.get('QUESTION_TEXT', '')))}**"
                )
                st.markdown(
                    f"<span class='confidence-chip tone-{_tone_for_conf(row.get('CONFIDENCE_SCORE'))}'>Confidence {_fmt_conf(row.get('CONFIDENCE_SCORE'))}</span>",
                    unsafe_allow_html=True,
                )

                text_value = _normalize_answer_value(answer_text)
                is_disabled = not (can_edit and edit_mode)
                if answer_type in {"YES_NO", "YES_NO_UNCLEAR", "YES_NO_UNCLEAR_NA"}:
                    type_options = {
                        "YES_NO": ["YES", "NO"],
                        "YES_NO_UNCLEAR": ["YES", "NO", "UNCLEAR"],
                        "YES_NO_UNCLEAR_NA": ["YES", "NO", "UNCLEAR", "N/A"],
                    }
                    safe_values = [str(v).upper() for v in allowed_values] or type_options[answer_type]
                    current_value = str(text_value).upper()
                    if current_value not in safe_values:
                        safe_values = ["", *safe_values]
                        selected_idx = 0
                    else:
                        selected_idx = safe_values.index(current_value)
                    new_value = st.radio(
                        "Answer",
                        safe_values,
                        index=selected_idx,
                        horizontal=True,
                        key=_safe_widget_key("ans_radio", claim_id, section_id, row, idx),
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )
                elif answer_type in {"CHOICE"} and allowed_values:
                    safe_values = [str(v) for v in allowed_values]
                    current_value = str(text_value)
                    if current_value not in safe_values:
                        safe_values = ["", *safe_values]
                        selected_idx = 0
                    else:
                        selected_idx = safe_values.index(current_value)
                    new_value = st.radio(
                        "Answer",
                        safe_values,
                        index=selected_idx,
                        horizontal=True,
                        key=_safe_widget_key("ans_radio", claim_id, section_id, row, idx),
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )
                elif answer_type in {"MULTISELECT"} and allowed_values:
                    existing = text_value if isinstance(text_value, list) else _normalize_answer_value(row.get("ANSWER_JSON"))
                    existing_values = existing if isinstance(existing, list) else []
                    new_value = st.multiselect(
                        "Answer",
                        options=[str(v) for v in allowed_values],
                        default=[str(v) for v in existing_values],
                        key=_safe_widget_key("ans_multi", claim_id, section_id, row, idx),
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )
                elif answer_type in {"RATING_1_9"}:
                    options = [str(v) for v in allowed_values] or [str(i) for i in range(1, 10)]
                    current_value = str(text_value)
                    if current_value not in options:
                        options = ["", *options]
                        selected_idx = 0
                    else:
                        selected_idx = options.index(current_value)
                    new_value = st.radio(
                        "Answer",
                        options=options,
                        index=selected_idx,
                        horizontal=True,
                        key=_safe_widget_key("ans_rating", claim_id, section_id, row, idx),
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )
                elif answer_type in {"RATING_1_5"}:
                    options = [str(v) for v in allowed_values] or [str(i) for i in range(1, 6)]
                    current_value = str(text_value)
                    if current_value not in options:
                        options = ["", *options]
                        selected_idx = 0
                    else:
                        selected_idx = options.index(current_value)
                    new_value = st.radio(
                        "Answer",
                        options=options,
                        index=selected_idx,
                        horizontal=True,
                        key=_safe_widget_key("ans_rating", claim_id, section_id, row, idx),
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )
                else:
                    new_value = st.text_area(
                        "Answer",
                        value=str(text_value),
                        key=_safe_widget_key("ans_text", claim_id, section_id, row, idx),
                        placeholder="No answer currently extracted",
                        label_visibility="collapsed",
                        disabled=is_disabled,
                    )

                answer_by_question[question_id] = ", ".join(new_value) if isinstance(new_value, list) else str(new_value)
                if can_edit and edit_mode and st.button(
                    "Save Answer",
                    key=_safe_widget_key("save", claim_id, section_id, row, idx),
                    type="tertiary",
                ):
                    save_section_answer(
                        session,
                        answer_id,
                        ", ".join(new_value) if isinstance(new_value, list) else str(new_value),
                        claim_id=claim_id,
                        defendant_id=defendant_id,
                        question_id=question_id,
                    )
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

    _render_breadcrumb(str(claim_id))

    workspace = get_claim_review_workspace(session, str(claim_id))
    claim = workspace.get("claim")
    if not claim:
        st.error(f"Claim {claim_id} not found in claim detail view.")
        _render_missing_objects(workspace.get("missing_objects", []))
        return

    _render_header(session, ctx, str(claim_id), claim)
    _render_missing_objects(workspace.get("missing_objects", []))
    st.session_state["review_snowflake_objects"] = workspace.get("used_objects", [])
    st.session_state["review_missing_objects"] = workspace.get("missing_objects", [])

    tabs = st.tabs(["MFQ Form", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"])
    edit_key = f"mfq_edit_mode_{claim_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    with tabs[0]:
        can_edit = can_edit_claim(
            ctx.app_role,
            str(claim.get("STATUS", "")),
            claim.get("ASSIGNED_TO"),
            ctx.username,
        )
        with st.container(key="mfq_header_card"):
            title_col, edit_col = st.columns([7.4, 1.4], vertical_alignment="center")
            with title_col:
                st.markdown(
                    (
                        "<section class='mfq-page'>"
                        "<div class='mfq-header'>"
                        "<div class='mfq-header-left'><h2>Medical Faculty Questionnaire</h2>"
                        "<p>Complete evaluation based on accepted medical practice standards.</p></div>"
                        "</div>"
                        "</section>"
                    ),
                    unsafe_allow_html=True,
                )
            with edit_col:
                edit_label = "Done" if st.session_state[edit_key] else "✎ Edit"
                if st.button(
                    edit_label,
                    key="mfq_edit_btn",
                    type="secondary",
                    use_container_width=True,
                    disabled=not can_edit,
                ):
                    st.session_state[edit_key] = not st.session_state[edit_key]
                    st.rerun()
                if not can_edit:
                    st.caption("Read-only")

        _render_confidence_panel(workspace)
        _render_synopsis_panel(workspace.get("synopsis", {}))
        _render_questions(
            session,
            workspace.get("sections", pd.DataFrame()),
            can_edit=can_edit,
            edit_mode=bool(st.session_state[edit_key]),
        )

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
