from __future__ import annotations

import json
import logging
import os
from html import escape
from time import perf_counter

import pandas as pd
import streamlit as st

from services.claim_service import (
    get_assignable_faculty,
    get_claim_review_workspace,
    get_editable_section_ids_for_user,
    save_claim_assignment,
    save_mfq_answer,
    update_claim_status,
)
from services.rbac_service import can_edit_claim

logger = logging.getLogger(__name__)


@st.cache_data(ttl=120, show_spinner=False)
def _get_cached_claim_review_workspace(claim_id: str, refresh_nonce: int = 0) -> dict:
    from services.snowflake_service import get_session
    _ = refresh_nonce
    return get_claim_review_workspace(get_session(), claim_id)


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
                st.session_state[f"open_assign_modal_{claim_id}"] = True

            if st.button("Approve", type="secondary", use_container_width=True):
                    update_claim_status(session, claim_id, "Approved")
                    st.success("Claim approved.")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def _go_back_to_dashboard() -> None:
    st.session_state["selected_claim_id"] = None
    st.session_state["current_view"] = "dashboard"
    st.session_state["active_page"] = "Dashboard"


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
        ),
        unsafe_allow_html=True,
    )

    if overall is None and section_conf.empty:
        st.markdown(
            "<div class='confidence-empty-state'>AI confidence data is not available for this claim.</div></section>",
            unsafe_allow_html=True,
        )
        return

    if section_conf.empty:
        st.markdown(
            "<div class='confidence-empty-state'>Section confidence scores are unavailable for this claim.</div></section>",
            unsafe_allow_html=True,
        )
        return

    st.markdown("<div class='confidence-grid-title'>SECTION-WISE CONFIDENCE</div>", unsafe_allow_html=True)
    st.markdown("<div class='confidence-grid'>", unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)

    note = "All sections are high confidence."
    if moderate_or_low_sections:
        note = f"Moderate confidence: {', '.join(moderate_or_low_sections)}"
    st.markdown(f"<div class='confidence-note'>● {escape(note)}</div></section>", unsafe_allow_html=True)


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


def extract_answer_json_value(raw):
    parsed = _normalize_answer_value(raw)
    if isinstance(parsed, dict):
        for key in ("value", "answer", "selected", "text"):
            value = parsed.get(key)
            if value not in (None, ""):
                return value
        return ""
    return parsed


def _safe_widget_key(prefix: str, claim_id: str, section_id: str, question: pd.Series, index: int) -> str:
    question_id = question.get("QUESTION_ID") or question.get("question_id")
    question_key = question.get("QUESTION_KEY") or question.get("question_key")
    section_key = question.get("SECTION_KEY") or question.get("section_key")
    section_part = section_id or str(section_key or "section")
    return (
        f"{prefix}_{claim_id}_{section_part}_{question_id or 'question'}_"
        f"{question_key or 'question_key'}_{index}"
    )


def _is_visible(row: pd.Series, answer_by_question: dict[str, str]) -> bool:
    parent_id = str(row.get("PARENT_QUESTION_ID", "") or "").strip()
    if not parent_id:
        return True

    parent_answer = str(answer_by_question.get(parent_id, "") or "").strip().upper()
    if not parent_answer:
        return True

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


def _question_is_editable(
    can_edit: bool,
    edit_mode: bool,
    section_id: str,
    editable_section_ids: set[str] | None,
    visibility_match: bool,
) -> bool:
    if not can_edit or not edit_mode or not visibility_match:
        return False
    if editable_section_ids is None:
        return True
    return section_id in editable_section_ids


def _confidence_for_question(row: pd.Series, section_confidence_by_name: dict[str, float | None]) -> float | None:
    question_conf = row.get("CONFIDENCE_SCORE")
    if question_conf is not None and not (isinstance(question_conf, float) and pd.isna(question_conf)):
        return float(question_conf)
    section_name = str(row.get("SECTION_NAME", "") or "").strip()
    section_conf = section_confidence_by_name.get(section_name)
    if section_conf is None or (isinstance(section_conf, float) and pd.isna(section_conf)):
        return None
    return float(section_conf)


def _is_section_three_subsection(section_id: str, section_name: str) -> bool:
    normalized_id = section_id.strip().upper()
    normalized_name = section_name.strip().lower()
    return normalized_id.startswith("SEC_III") or "detailed case evaluation" in normalized_name


def _normalize_section_three_title(section_id: str, section_name: str) -> str:
    normalized_id = section_id.strip().upper()
    title_by_section_id = {
        "SEC_III_A": "Patient Intake / Assessment",
        "SEC_III_B": "Diagnostic Work Up",
        "SEC_III_C": "Treatment",
        "SEC_III_D": "Procedures / Surgeries",
        "SEC_III_E": "Monitoring and Follow-up",
        "SEC_III_F": "Additional Contributing Factors",
    }
    if normalized_id in title_by_section_id:
        return title_by_section_id[normalized_id]
    fallback = str(section_name or "").replace("Section III:", "").strip()
    if " - " in fallback:
        fallback = fallback.split(" - ", 1)[1].strip()
    return fallback or "Section III Subsection"


def _build_assignable_sections(sections_df: pd.DataFrame) -> list[dict[str, str]]:
    if sections_df.empty:
        return []
    section_rows = (
        sections_df[["SECTION_ORDER", "SECTION_ID", "SECTION_NAME"]]
        .dropna(subset=["SECTION_ID"])
        .drop_duplicates(subset=["SECTION_ID"])
        .sort_values(["SECTION_ORDER", "SECTION_ID"])
    )
    options: list[dict[str, str]] = []
    for _, row in section_rows.iterrows():
        section_id = str(row.get("SECTION_ID", "") or "").strip()
        if not section_id:
            continue
        raw_name = str(row.get("SECTION_NAME", "") or "").strip()
        if _is_section_three_subsection(section_id, raw_name):
            label = f"Section III: {_normalize_section_three_title(section_id, raw_name)}"
        else:
            label = raw_name or section_id
        options.append({"id": section_id, "label": label})
    return options


@st.dialog("Assign Medical Faculty", width="large")
def _render_assign_faculty_modal(session, ctx, claim_id: str, sections_df: pd.DataFrame) -> None:
    st.markdown("Select the MFQ sections to review and assign a faculty member.")
    section_options = _build_assignable_sections(sections_df)
    faculty_options = get_assignable_faculty(session)

    selected_section_ids_key = "selected_mfq_sections"
    selected_faculty_key = f"assign_selected_faculty_{claim_id}"
    select_all_key = f"assign_select_all_{claim_id}"
    if selected_section_ids_key not in st.session_state:
        st.session_state[selected_section_ids_key] = []
    if selected_faculty_key not in st.session_state:
        st.session_state[selected_faculty_key] = ""

    all_section_ids = [item["id"] for item in section_options]
    selected_set = set(st.session_state.get(selected_section_ids_key, []))
    selected_set = {sid for sid in selected_set if sid in all_section_ids}
    st.session_state[selected_section_ids_key] = sorted(selected_set)

    st.markdown("<div class='assign-modal-section-head'>", unsafe_allow_html=True)
    title_col, count_col = st.columns([4, 1.2], vertical_alignment="center")
    with title_col:
        st.markdown("**Sections for Review**")
    with count_col:
        st.markdown(f"<div class='assign-selected-count'>{len(selected_set)} selected</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    is_all_selected = bool(all_section_ids) and len(st.session_state[selected_section_ids_key]) == len(all_section_ids)
    st.session_state[select_all_key] = is_all_selected
    select_all_clicked = st.checkbox("Select All", key=select_all_key)

    if select_all_clicked != is_all_selected:
        st.session_state[selected_section_ids_key] = all_section_ids if select_all_clicked else []

    selected_set = set(st.session_state[selected_section_ids_key])
    with st.container(border=True, height=260):
        for item in section_options:
            widget_key = f"assign_sec_{claim_id}_{item['id']}"
            expected_checked = item["id"] in selected_set
            if st.session_state.get(widget_key) != expected_checked:
                st.session_state[widget_key] = expected_checked
            is_checked = st.checkbox(
                item["label"],
                key=widget_key,
            )
            if is_checked:
                selected_set.add(item["id"])
            else:
                selected_set.discard(item["id"])

    st.session_state[selected_section_ids_key] = [sid for sid in all_section_ids if sid in selected_set]

    st.markdown("**Faculty Member**")
    faculty_map = {item["USER_ID"]: item["DISPLAY_NAME"] for item in faculty_options}
    faculty_ids = list(faculty_map.keys())
    placeholder = "Select faculty member..."
    select_options = ["", *faculty_ids]
    current_faculty = st.session_state.get(selected_faculty_key, "")
    if current_faculty not in set(select_options):
        current_faculty = ""
    chosen_faculty = st.selectbox(
        "Faculty Member",
        options=select_options,
        index=select_options.index(current_faculty),
        format_func=lambda v: placeholder if not v else faculty_map.get(v, v),
        key=f"faculty_dropdown_{claim_id}",
        label_visibility="collapsed",
    )
    st.session_state[selected_faculty_key] = chosen_faculty

    selection_count = len(st.session_state[selected_section_ids_key])
    can_assign = selection_count > 0 and bool(chosen_faculty)

    footer_cols = st.columns([3.2, 1.1, 1.8], vertical_alignment="center")
    with footer_cols[1]:
        if st.button("Cancel", key=f"cancel_assign_{claim_id}", use_container_width=True):
            st.session_state[f"open_assign_modal_{claim_id}"] = False
            st.rerun()
    with footer_cols[2]:
        assign_clicked = st.button(
            f"Assign Claim ({selection_count} sections)",
            type="primary",
            disabled=not can_assign,
            key=f"confirm_assign_{claim_id}",
            use_container_width=True,
        )
    if assign_clicked:
        success, message = save_claim_assignment(
            session=session,
            claim_id=claim_id,
            faculty_user_id=chosen_faculty,
            section_ids=st.session_state[selected_section_ids_key],
            assigned_by_username=ctx.username,
        )
        if success:
            st.session_state[f"open_assign_modal_{claim_id}"] = False
            st.success(message)
            st.rerun()
        st.error(message)


def _render_questions(
    sections_df: pd.DataFrame,
    section_confidence_df: pd.DataFrame,
    can_edit: bool,
    edit_mode: bool,
    editable_section_ids: set[str] | None,
) -> list[dict]:
    if sections_df.empty:
        st.info("MFQ form is unavailable for this claim.")
        return []

    working_df = sections_df.sort_values(["SECTION_ORDER", "QUESTION_ORDER"]).copy()
    rendered_questions: list[dict] = []
    answer_by_question: dict[str, str] = {}
    for _, seed_row in working_df.iterrows():
        answer_by_question[str(seed_row.get("QUESTION_ID", "") or "")] = str(seed_row.get("DISPLAY_ANSWER", "") or "")

    section_confidence_by_name: dict[str, float | None] = {}
    if not section_confidence_df.empty:
        for _, conf_row in section_confidence_df.iterrows():
            section_name = str(conf_row.get("SECTION_NAME", "") or "").strip()
            if section_name:
                section_confidence_by_name[section_name] = conf_row.get(
                    "CONFIDENCE_SCORE_PCT",
                    conf_row.get("CONFIDENCE_SCORE"),
                )

    def section_confidence_for(section_name: str, section_df: pd.DataFrame) -> float | None:
        section_confidence_raw = (
            pd.to_numeric(section_df.get("SECTION_CONFIDENCE"), errors="coerce").dropna()
            if "SECTION_CONFIDENCE" in section_df.columns
            else pd.Series(dtype="float64")
        )
        if not section_confidence_raw.empty:
            return float(section_confidence_raw.iloc[0])
        looked_up = section_confidence_by_name.get(section_name.strip())
        if looked_up is None or (isinstance(looked_up, float) and pd.isna(looked_up)):
            return None
        return float(looked_up)

    grouped = list(working_df.groupby(["SECTION_ORDER", "SECTION_ID", "SECTION_NAME"], dropna=False))
    section_three_groups: list[tuple[tuple, pd.DataFrame]] = []
    primary_groups: list[tuple[tuple, pd.DataFrame]] = []
    for grouped_item in grouped:
        (_, group_section_id, group_section_name), _section_df = grouped_item
        if _is_section_three_subsection(str(group_section_id or ""), str(group_section_name or "")):
            section_three_groups.append(grouped_item)
        else:
            primary_groups.append(grouped_item)

    question_index = 0

    def render_question_input(row: pd.Series, section_id: str, is_child: bool, idx: int) -> None:
        nonlocal question_index
        question_id = str(row.get("QUESTION_ID", ""))
        answer_id = str(row.get("ANSWER_ID", "") or "")
        claim_id = str(row.get("CLAIM_ID", "") or "")
        defendant_id = str(row.get("DEFENDANT_ID", "") or "")
        section_id_value = str(row.get("SECTION_ID", "") or section_id or row.get("SECTION_KEY", "") or "")
        answer_text = row.get("ANSWER_TEXT")
        allowed_values = row.get("ALLOWED_VALUES_LIST", []) or []
        answer_type = str(row.get("ANSWER_TYPE", "")).upper()
        confidence_score = _confidence_for_question(row, section_confidence_by_name)

        visibility_match = _is_visible(row, answer_by_question)
        question_order = escape(str(row.get("QUESTION_ORDER", "")))
        question_text = str(row.get("QUESTION_TEXT", "") or "").strip() or "Question text not available"

        if is_child:
            st.markdown("<div class='mfq-child-question'></div>", unsafe_allow_html=True)
        confidence_badge_html = ""
        if not is_child:
            confidence_badge_html = (
                f"<span class='mfq-confidence-badge tone-{_tone_for_conf(confidence_score)}'>{_fmt_conf(confidence_score)}</span>"
            )
        with st.container(border=False):
            st.markdown(
                "<div class='mfq-question-header'>"
                f"<div class='mfq-question-content mfq-question-text'>{question_order}. {escape(question_text)}</div>"
                f"{confidence_badge_html}"
                "</div>",
                unsafe_allow_html=True,
            )
            if row.get("CONFIDENCE_REASON"):
                st.caption(str(row.get("CONFIDENCE_REASON")))

            answer_value = answer_text or extract_answer_json_value(row.get("ANSWER_JSON")) or ""
            text_value = _normalize_answer_value(answer_value)
            is_editable = _question_is_editable(
                can_edit=can_edit,
                edit_mode=edit_mode,
                section_id=section_id_value,
                editable_section_ids=editable_section_ids,
                visibility_match=visibility_match,
            )
            is_disabled = not is_editable
            answer_widget_key = _safe_widget_key("ans", claim_id, section_id_value, row, idx)

            st.markdown("<div class='mfq-answer-wrap'></div>", unsafe_allow_html=True)
            with st.container(border=False):
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
                    new_value = st.radio("Answer", safe_values, index=selected_idx, horizontal=True, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"CHOICE"} and allowed_values:
                    safe_values = [str(v) for v in allowed_values]
                    current_value = str(text_value)
                    if current_value not in safe_values:
                        safe_values = ["", *safe_values]
                        selected_idx = 0
                    else:
                        selected_idx = safe_values.index(current_value)
                    new_value = st.radio("Answer", safe_values, index=selected_idx, horizontal=True, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"MULTISELECT"} and allowed_values:
                    existing = text_value if isinstance(text_value, list) else extract_answer_json_value(row.get("ANSWER_JSON"))
                    existing_values = existing if isinstance(existing, list) else []
                    new_value = st.multiselect("Answer", options=[str(v) for v in allowed_values], default=[str(v) for v in existing_values], key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"RATING_1_9"}:
                    options = [str(v) for v in allowed_values] or [str(i) for i in range(1, 10)]
                    current_value = str(text_value)
                    if current_value not in options:
                        options = ["", *options]
                        selected_idx = 0
                    else:
                        selected_idx = options.index(current_value)
                    new_value = st.selectbox("Answer", options=options, index=selected_idx, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"RATING_1_5"}:
                    options = [str(v) for v in allowed_values] or [str(i) for i in range(1, 6)]
                    current_value = str(text_value)
                    if current_value not in options:
                        options = ["", *options]
                        selected_idx = 0
                    else:
                        selected_idx = options.index(current_value)
                    new_value = st.selectbox("Answer", options=options, index=selected_idx, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"SELECT"} and allowed_values:
                    options = [str(v) for v in allowed_values]
                    current_value = str(text_value)
                    if current_value not in options:
                        options = ["", *options]
                        selected_idx = 0
                    else:
                        selected_idx = options.index(current_value)
                    new_value = st.selectbox("Answer", options=options, index=selected_idx, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                else:
                    new_value = st.text_area("Answer", value=str(text_value), key=answer_widget_key, placeholder="No answer currently extracted", label_visibility="collapsed", disabled=is_disabled)

        answer_by_question[question_id] = ", ".join(new_value) if isinstance(new_value, list) else str(new_value)
        rendered_questions.append({
            "answer_id": answer_id,
            "claim_id": claim_id,
            "defendant_id": defendant_id,
            "question_id": question_id,
            "section_id": section_id_value,
            "answer_type": answer_type,
            "widget_key": answer_widget_key,
            "editable": is_editable,
        })
        question_index += 1

    def render_section_questions(section_id: str, section_df: pd.DataFrame, show_question_cards: bool) -> None:
        rows = list(section_df.sort_values("QUESTION_ORDER").iterrows())
        children_by_parent: dict[str, list[pd.Series]] = {}
        root_questions: list[pd.Series] = []
        for _, row in rows:
            parent_id = str(row.get("PARENT_QUESTION_ID", "") or "").strip()
            if parent_id:
                children_by_parent.setdefault(parent_id, []).append(row)
            else:
                root_questions.append(row)

        known_parent_ids = {str(q.get("QUESTION_ID", "") or "").strip() for q in root_questions}
        for parent_id, children in children_by_parent.items():
            if parent_id not in known_parent_ids:
                root_questions.extend(children)

        if not rows:
            st.warning("No questions found for this section.")
            return

        for parent in root_questions:
            parent_id = str(parent.get("QUESTION_ID", "") or "").strip()
            child_rows = children_by_parent.get(parent_id, [])
            if show_question_cards:
                st.markdown("<div class='mfq-question-card'></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    render_question_input(parent, section_id=section_id, is_child=False, idx=question_index)
                    for child_row in child_rows:
                        render_question_input(child_row, section_id=section_id, is_child=True, idx=question_index)
            else:
                st.markdown("<div class='mfq-section-iii-question-group'>", unsafe_allow_html=True)
                render_question_input(parent, section_id=section_id, is_child=False, idx=question_index)
                for child_row in child_rows:
                    render_question_input(child_row, section_id=section_id, is_child=True, idx=question_index)
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='mfq-sections-root'>", unsafe_allow_html=True)
    for section_idx, ((_, section_id, section_name), section_df) in enumerate(primary_groups):
        section_name_value = str(section_name or "Untitled Section")
        section_confidence = section_confidence_for(section_name_value, section_df)
        default_open = section_idx == 0 or (section_confidence is not None and section_confidence < 85)
        with st.expander(f"{section_name_value} · {_fmt_conf(section_confidence)}", expanded=default_open):
            render_section_questions(str(section_id or ""), section_df, show_question_cards=True)

    if section_three_groups:
        section_three_conf = [section_confidence_for(str(n or ""), df) for (_, _, n), df in section_three_groups]
        valid_conf = [c for c in section_three_conf if c is not None]
        section_three_header_conf = (sum(valid_conf) / len(valid_conf)) if valid_conf else None
        default_open_idx = 0
        for idx, conf in enumerate(section_three_conf):
            if conf is not None and conf < 85:
                default_open_idx = idx

        st.markdown("<section class='mfq-section-iii-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='mfq-section-iii-header'>"
            "<span class='mfq-section-iii-title'>Section III: Detailed Case Evaluation</span>"
            f"<span class='mfq-confidence-badge tone-{_tone_for_conf(section_three_header_conf)}'>{_fmt_conf(section_three_header_conf)}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        for subsection_idx, ((_, section_id, section_name), section_df) in enumerate(section_three_groups):
            subsection_name = _normalize_section_three_title(str(section_id or ""), str(section_name or ""))
            subsection_conf = section_confidence_for(str(section_name or ""), section_df)
            title_html = (
                "<span class='mfq-section-iii-row-title'>" + escape(subsection_name) + "</span>"
                + f"<span class='mfq-section-iii-row-conf mfq-confidence-badge tone-{_tone_for_conf(subsection_conf)}'>{_fmt_conf(subsection_conf)}</span>"
            )
            st.markdown("<div class='mfq-section-iii-row'>", unsafe_allow_html=True)
            with st.expander(title_html, expanded=subsection_idx == default_open_idx):
                render_section_questions(str(section_id or ""), section_df, show_question_cards=False)
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</section>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    return rendered_questions


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


def _is_debug_mode_enabled() -> bool:
    if bool(st.session_state.get("debug_mode", False)):
        return True
    return str(os.getenv("APP_DEBUG", "")).strip().lower() == "true"


def render(session, ctx) -> None:
    claim_id = st.session_state.get("selected_claim_id")
    logger.info("render_claim_details called claim_id=%s", claim_id)
    if not claim_id:
        st.warning("No claim is selected. Open a claim from Dashboard or Claims page.")
        return

    _render_breadcrumb(str(claim_id))

    toolbar_col, _ = st.columns([2, 6])
    with toolbar_col:
        if st.button("Refresh answers", key=f"refresh_answers_{claim_id}", type="tertiary"):
            st.session_state[f"mfq_refresh_nonce_{claim_id}"] = st.session_state.get(f"mfq_refresh_nonce_{claim_id}", 0) + 1
            st.rerun()

    with st.spinner("Loading claim details..."):
        started = perf_counter()
        refresh_nonce = int(st.session_state.get(f"mfq_refresh_nonce_{claim_id}", 0))
        workspace = _get_cached_claim_review_workspace(str(claim_id), refresh_nonce=refresh_nonce)
        logger.info("claim_details.workspace_load_ms=%d claim_id=%s", int((perf_counter() - started) * 1000), claim_id)
    claim = workspace.get("claim")
    missing_objects = workspace.get("missing_objects", [])
    if not claim:
        if "MFQ_CLAIM_DETAIL_VW" in missing_objects:
            st.error("MFQ_CLAIM_DETAIL_VW not found in current Snowflake database/schema.")
        else:
            st.error(
                f"Claim {claim_id} was not found in MFQ_CLAIM_DETAIL_VW.\n"
                "Please verify CLAIM_ID exists in the source claims table."
            )
        _render_missing_objects(missing_objects)
        return

    _render_header(session, ctx, str(claim_id), claim)
    if st.session_state.get(f"open_assign_modal_{claim_id}", False):
        _render_assign_faculty_modal(
            session=session,
            ctx=ctx,
            claim_id=str(claim_id),
            sections_df=workspace.get("sections", pd.DataFrame()),
        )
    _render_missing_objects(workspace.get("missing_objects", []))
    st.session_state["review_snowflake_objects"] = workspace.get("used_objects", [])
    st.session_state["review_missing_objects"] = workspace.get("missing_objects", [])
    debug_enabled = _is_debug_mode_enabled() and bool(st.session_state.get("debug_mfq_binding", False))
    if _is_debug_mode_enabled():
        if st.checkbox("Developer debug (MFQ binding)", key="debug_mfq_binding"):
            debug_enabled = True
    if debug_enabled:
        sections_df = workspace.get("sections", pd.DataFrame())
        display_answer_series = (
            sections_df["DISPLAY_ANSWER"] if (not sections_df.empty and "DISPLAY_ANSWER" in sections_df.columns) else pd.Series(dtype="object")
        )
        non_empty_mask = display_answer_series.astype(str).str.strip() != "" if not display_answer_series.empty else pd.Series(dtype="bool")
        question_keys = sorted(
            {
                str(v).strip()
                for v in sections_df.get("QUESTION_KEY", pd.Series(dtype="object")).dropna().tolist()
                if str(v).strip()
            }
        ) if not sections_df.empty else []
        answer_keys = sorted(
            {
                str(v).strip()
                for v in sections_df.loc[non_empty_mask, "QUESTION_KEY"].dropna().tolist()
            }
        ) if (not sections_df.empty and "QUESTION_KEY" in sections_df.columns and not non_empty_mask.empty) else []
        missing_ui_keys = [k for k in question_keys if k not in set(answer_keys)]
        with st.expander("MFQ binding debug", expanded=False):
            st.json(
                {
                    "selected_claim_id": str(claim_id),
                    "selected_file_number": claim.get("FILE_NUMBER"),
                    "answer_table": "MFQ_ANSWERS",
                    "answer_rows_returned": int(non_empty_mask.sum()) if not non_empty_mask.empty else 0,
                    "first_10_answer_keys": answer_keys[:10],
                    "first_10_missing_ui_keys": missing_ui_keys[:10],
                }
            )

    tabs = st.tabs(["MFQ Form", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"])
    edit_key = f"mfq_edit_mode_{claim_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False

    with tabs[0]:
        can_edit = can_edit_claim(
            str(claim.get("STATUS", "")),
            claim.get("ASSIGNED_TO"),
            ctx.username,
        )
        editable_section_ids = get_editable_section_ids_for_user(session, str(claim_id), ctx.username)
        save_clicked = False
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
                if not st.session_state[edit_key]:
                    if st.button(
                        "✎ Edit",
                        key="mfq_edit_btn",
                        type="secondary",
                        use_container_width=True,
                        disabled=not can_edit,
                    ):
                        st.session_state[edit_key] = True
                        st.rerun()
                    if not can_edit:
                        st.caption("Read-only")
                else:
                    save_clicked = st.button("Save Draft", key="mfq_save_btn", type="primary", use_container_width=True)
                    cancel_clicked = st.button("Cancel", key="mfq_cancel_btn", type="secondary", use_container_width=True)
                    if cancel_clicked:
                        st.session_state[edit_key] = False
                        st.rerun()

        _render_confidence_panel(workspace)
        _render_synopsis_panel(workspace.get("synopsis", {}))
        rendered_questions = _render_questions(
            workspace.get("sections", pd.DataFrame()),
            workspace.get("section_confidence", pd.DataFrame()),
            can_edit=can_edit,
            edit_mode=bool(st.session_state[edit_key]),
            editable_section_ids=editable_section_ids,
        )
        if st.session_state[edit_key] and save_clicked:
            for question in rendered_questions:
                if not question.get("editable"):
                    continue
                value = st.session_state.get(question["widget_key"])
                save_mfq_answer(
                    session=session,
                    claim_id=question["claim_id"],
                    defendant_id=question["defendant_id"],
                    question_id=question["question_id"],
                    answer_value=value,
                    user_id=ctx.username,
                )
            st.session_state[edit_key] = False
            st.success("MFQ answers saved successfully.")
            st.rerun()

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
