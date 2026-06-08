from __future__ import annotations

import json
import logging
import os
import re
from html import escape
from time import perf_counter

import pandas as pd
import streamlit as st

from services.claim_service import (
    build_mfq_workspace_for_claim,
    get_assignable_faculty,
    get_claim_detail_by_id,
    get_claim_documents_by_claim_id,
    get_claim_history_by_claim_id,
    get_claim_summaries_by_claim_id,
    get_editable_section_ids_for_user,
    save_claim_assignment,
    save_mfq_answer,
    update_claim_status,
)
from services.rbac_service import can_edit_claim, get_current_role

logger = logging.getLogger(__name__)


DETAIL_TAB_OPTIONS = ["MFQ Form", "Records Summary", "MedCron", "Legal Memo", "Enquiries", "AI Assist", "Documents"]


def _ensure_claim_cache(cache_name: str) -> dict:
    cache = st.session_state.get(cache_name)
    if not isinstance(cache, dict):
        cache = {}
        st.session_state[cache_name] = cache
    return cache


def _cached_per_claim(cache_name: str, claim_id: str, loader, *, label: str):
    cache = _ensure_claim_cache(cache_name)
    if claim_id in cache:
        logger.info("%s_cache_hit claim_id=%s", cache_name, claim_id)
        return cache[claim_id]
    started = perf_counter()
    with st.spinner(label):
        value = loader()
    cache[claim_id] = value
    logger.info("%s_load_ms=%d claim_id=%s", cache_name, int((perf_counter() - started) * 1000), claim_id)
    return value


def _invalidate_claim_caches(claim_id: str, *cache_names: str) -> None:
    for cache_name in cache_names:
        _ensure_claim_cache(cache_name).pop(str(claim_id), None)


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


def _safe_display(value, fallback: str = "-") -> str:
    """Return a UI-safe text value, hiding null-like pandas/Python values."""
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "null"}:
        return fallback
    return text


def _first_safe_display(claim: dict, keys: tuple[str, ...], fallback: str = "-") -> str:
    for key in keys:
        value = _safe_display(claim.get(key), fallback="")
        if value:
            return value
    return fallback


def _normalize_for_rule(value) -> str:
    """Normalize MFQ statuses and Snowflake role names for visibility rules."""
    return re.sub(r"[\s_]+", " ", _safe_display(value, fallback="")).strip().upper()


def _current_role_for_actions(session, ctx) -> str:
    """Resolve the current role from selected session state, context, or Snowflake."""
    selected_role = _safe_display(st.session_state.get("selected_sf_role"), fallback="")
    if selected_role:
        return selected_role
    context_role = _safe_display(getattr(ctx, "sf_role", ""), fallback="")
    if context_role:
        return context_role
    return _safe_display(get_current_role(session), fallback="")


def get_claim_detail_actions(claim_status, mfq_status, current_role) -> list[str]:
    """Return top-card actions using MFQ_STATUS only.

    claim_status is retained for backward-compatible call sites/tests, but it
    must not influence the Claim Details header badge or action decisions.
    """
    del claim_status
    normalized_mfq_status = _normalize_for_rule(mfq_status)
    role = _normalize_for_rule(current_role)

    if normalized_mfq_status == "APPROVED":
        return []
    if normalized_mfq_status == "REJECTED":
        if role in {"CLAIM OPS", "CLAIM ANALYST SUPERVISOR"}:
            return ["assign_to_faculty"]
        return []
    if normalized_mfq_status == "MFQ GENERATED" and role == "CLAIM OPS":
        return ["assign_to_faculty", "approve"]
    return []


def _render_header(session, ctx, claim_id: str, claim: dict) -> None:
    claim_id_display = _safe_display(claim.get("CLAIM_ID"), fallback=_safe_display(claim_id))
    file_number = _safe_display(claim.get("FILE_NUMBER"), fallback=claim_id_display)
    raw_mfq_status = claim.get("MFQ_STATUS")
    status = _safe_display(raw_mfq_status, fallback="Unknown")
    normalized_mfq_status = _normalize_for_rule(raw_mfq_status)
    priority = _safe_display(claim.get("PRIORITY"), fallback="")
    patient_defendant = _safe_display(claim.get("PATIENT_DEFENDANT"), fallback="")
    patient = _safe_display(claim.get("PATIENT_NAME"), fallback="")
    defendant = _safe_display(claim.get("DEFENDANT_NAME"), fallback="")
    title = patient_defendant or (
        f"{patient} / {defendant}"
        if patient and defendant
        else patient or defendant or "Unknown Patient vs Unknown Defendant"
    )
    specialty = _first_safe_display(
        claim,
        ("DEFENDANT_SPECIALTY", "DEFENDANT_SPECIALITY", "SPECIALTY", "SPECIALITY"),
    )
    date_requested = _safe_display(claim.get("DATE_REQUESTED"))
    assigned_to = _safe_display(claim.get("ASSIGNED_TO"), fallback="")
    assigned_to_display = assigned_to or "Unassigned"
    assign_label = "Assign"
    claim_action_status = claim.get("CLAIM_STATUS", claim.get("STATUS"))
    current_role = _current_role_for_actions(session, ctx)
    actions = get_claim_detail_actions(
        claim_status=claim_action_status,
        mfq_status=raw_mfq_status,
        current_role=current_role,
    )
    logger.info(
        "claim_detail_top_card_state selected_claim_id=%s raw_mfq_status=%s normalized_mfq_status=%s current_role=%s normalized_role=%s visible_buttons=%s",
        claim_id,
        _safe_display(raw_mfq_status, fallback=""),
        normalized_mfq_status,
        _safe_display(current_role, fallback=""),
        _normalize_for_rule(current_role),
        actions,
    )

    with st.container(key="review_header_card"):
        left_col, action_col = st.columns([6.2, 1.3], vertical_alignment="top")
        with left_col:
            st.markdown("<div class='review-headline-wrap'>", unsafe_allow_html=True)
            priority_badge_html = (
                f"<span class='review-pill review-priority'>{escape(priority)}</span>"
                if priority
                else ""
            )
            title_html = escape(title).replace(" / ", " <span class='review-vs'>vs</span> ")
            st.markdown(
                (
                    f"<div class='review-headline'>{title_html}</div>"
                    "<div class='review-badges'>"
                    f"<span class='review-pill review-status'>{escape(status)}</span>"
                    f"{priority_badge_html}"
                    "</div>"
                    "<div class='review-meta-grid claim-meta-grid'>"
                    f"<div><div class='review-meta-label'>File Number</div><div>{escape(file_number)}</div></div>"
                    f"<div><div class='review-meta-label'>Defendant Specialty</div><div>{escape(specialty)}</div></div>"
                    f"<div><div class='review-meta-label'>Date Requested</div><div>{escape(date_requested)}</div></div>"
                    f"<div><div class='review-meta-label'>Contact</div><div>{escape(assigned_to_display)}</div></div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with action_col:
            if actions:
                st.markdown("<div class='review-header-actions claim-header-actions'>", unsafe_allow_html=True)
                if "assign_to_faculty" in actions and st.button(assign_label, type="primary", use_container_width=True):
                    st.session_state[f"open_assign_modal_{claim_id}"] = True

                if "approve" in actions and st.button("Approve", type="secondary", use_container_width=True):
                    update_claim_status(session, claim_id, "Approved")
                    _invalidate_claim_caches(claim_id, "claim_details_cache", "claim_history_cache")
                    st.success("Claim approved.")
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)


def _go_back_to_dashboard() -> None:
    st.session_state["active_page"] = "Dashboard"
    st.session_state["current_view"] = "Dashboard"
    st.session_state["selected_claim_id"] = None
    st.session_state["last_review_event"] = None
    st.session_state["last_processed_review_claim_id"] = None
    for key in list(st.session_state.keys()):
        if key.endswith("_recent_claims_last_review_event_id"):
            st.session_state.pop(key, None)
    st.query_params.clear()
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
    del index
    question_id = question.get("QUESTION_ID") or question.get("question_id") or "question"
    section_key = question.get("SECTION_KEY") or question.get("section_key")
    section_part = section_id or str(section_key or "section")
    safe_parts = [str(part).strip().replace(" ", "_").replace("/", "_") for part in (prefix, claim_id, section_part, question_id)]
    return "_".join(safe_parts)


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
            _invalidate_claim_caches(claim_id, "claim_details_cache", "claim_history_cache", "mfq_answers_cache", "mfq_form_cache")
            st.success(message)
            st.rerun()
        st.error(message)


def _render_questions(
    sections_df: pd.DataFrame,
    section_confidence_df: pd.DataFrame,
    can_edit: bool,
    edit_mode: bool,
    editable_section_ids: set[str] | None,
    claim_id: str,
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
        row_claim_id = str(row.get("CLAIM_ID", "") or "")
        effective_claim_id = row_claim_id or str(claim_id)
        defendant_id = str(row.get("DEFENDANT_ID", "") or "")
        section_id_value = str(row.get("SECTION_ID", "") or section_id or row.get("SECTION_KEY", "") or "")
        answer_text = row.get("ANSWER_TEXT")
        allowed_values = row.get("ALLOWED_VALUES_LIST", []) or []
        answer_type = str(row.get("ANSWER_TYPE", "")).upper()
        confidence_score = _confidence_for_question(row, section_confidence_by_name)

        visibility_match = _is_visible(row, answer_by_question)
        question_number = row.get("QUESTION_NUMBER")
        question_order_value = question_number if _safe_display(question_number, fallback="") else row.get("QUESTION_ORDER", "")
        question_order = escape(str(question_order_value))
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
            rationale_text = row.get("RATIONALE_TEXT") or row.get("CONFIDENCE_REASON")
            if rationale_text:
                st.caption(str(rationale_text))

            answer_value = row.get("DISPLAY_ANSWER") or row.get("ANSWER_VALUE") or answer_text or extract_answer_json_value(row.get("ANSWER_JSON")) or ""
            text_value = _normalize_answer_value(answer_value)
            is_editable = _question_is_editable(
                can_edit=can_edit,
                edit_mode=edit_mode,
                section_id=section_id_value,
                editable_section_ids=editable_section_ids,
                visibility_match=visibility_match,
            )
            is_disabled = not is_editable
            answer_widget_key = _safe_widget_key("ans", effective_claim_id, section_id_value, row, idx)

            st.markdown("<div class='mfq-answer-wrap'></div>", unsafe_allow_html=True)
            with st.container(border=False):
                if answer_type in {"BOOLEAN", "YES_NO", "YES_NO_UNCLEAR", "YES_NO_UNCLEAR_NA"}:
                    type_options = {
                        "BOOLEAN": ["Yes", "No"],
                        "YES_NO": ["YES", "NO"],
                        "YES_NO_UNCLEAR": ["YES", "NO", "UNCLEAR"],
                        "YES_NO_UNCLEAR_NA": ["YES", "NO", "UNCLEAR", "N/A"],
                    }
                    safe_values = [str(v) for v in allowed_values] or type_options[answer_type]
                    current_value = str(text_value)
                    upper_index = {value.upper(): value for value in safe_values}
                    if current_value not in safe_values and current_value.upper() in upper_index:
                        current_value = upper_index[current_value.upper()]
                    if current_value not in safe_values:
                        safe_values = ["", *safe_values]
                        selected_idx = 0
                    else:
                        selected_idx = safe_values.index(current_value)
                    new_value = st.radio("Answer", safe_values, index=selected_idx, horizontal=True, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"RADIO", "SINGLE_SELECT", "CHOICE"} and allowed_values:
                    safe_values = [str(v) for v in allowed_values]
                    current_value = str(text_value)
                    if current_value not in safe_values:
                        safe_values = ["", *safe_values]
                        selected_idx = 0
                    else:
                        selected_idx = safe_values.index(current_value)
                    new_value = st.radio("Answer", safe_values, index=selected_idx, horizontal=True, key=answer_widget_key, label_visibility="collapsed", disabled=is_disabled)
                elif answer_type in {"MULTI_SELECT", "MULTISELECT"} and allowed_values:
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
                elif answer_type in {"TEXT"}:
                    new_value = st.text_input("Answer", value=str(text_value), key=answer_widget_key, placeholder="No answer currently extracted", label_visibility="collapsed", disabled=is_disabled)
                else:
                    new_value = st.text_area("Answer", value=str(text_value), key=answer_widget_key, placeholder="No answer currently extracted", label_visibility="collapsed", disabled=is_disabled)

        answer_by_question[question_id] = ", ".join(new_value) if isinstance(new_value, list) else str(new_value)
        rendered_questions.append({
            "answer_id": answer_id,
            "claim_id": effective_claim_id,
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


def _render_summary_tab(session, claim_id: str, claim: dict) -> None:
    summaries = _cached_per_claim(
        "claim_summary_cache",
        claim_id,
        lambda: get_claim_summaries_by_claim_id(session, claim_id),
        label="Loading summary...",
    )
    st.markdown("### Claim Summary")
    detail_cols = st.columns(4)
    detail_items = [
        ("Claim Type", _safe_display(claim.get("CLAIM_TYPE"))),
        ("Workflow Status", _first_safe_display(claim, ("WORKFLOW_STATUS", "MFQ_STATUS", "STATUS"))),
        ("AI Confidence", _fmt_conf(claim.get("AI_CONFIDENCE"))),
        ("File Number", _safe_display(claim.get("FILE_NUMBER"))),
    ]
    for col, (label, value) in zip(detail_cols, detail_items):
        col.markdown(
            f"<div class='claim-detail-mini-card'><span>{escape(label)}</span><strong>{escape(value)}</strong></div>",
            unsafe_allow_html=True,
        )
    _render_text_tab(summaries.get("RECORD_SUMMARY", summaries.get("RECORDS_SUMMARY", "")), "No records summary available.")


def _render_mfq_tab(session, ctx, claim_id: str, claim: dict) -> None:
    workspace = _cached_per_claim(
        "mfq_form_cache",
        claim_id,
        lambda: build_mfq_workspace_for_claim(session, claim_id),
        label="Loading MFQ form...",
    )
    edit_key = f"mfq_edit_mode_{claim_id}"
    if edit_key not in st.session_state:
        st.session_state[edit_key] = False
    can_edit = can_edit_claim(str(claim.get("MFQ_STATUS", "")), claim.get("ASSIGNED_TO"), ctx.username)
    editable_section_ids = get_editable_section_ids_for_user(session, str(claim_id), ctx.username)
    save_clicked = False
    with st.container(key="mfq_header_card"):
        title_col, edit_col = st.columns([7.4, 1.4], vertical_alignment="center")
        with title_col:
            st.markdown(
                "<section class='mfq-page'><div class='mfq-header'><div class='mfq-header-left'><h2>Medical Faculty Questionnaire</h2><p>Complete evaluation based on accepted medical practice standards.</p></div></div></section>",
                unsafe_allow_html=True,
            )
        with edit_col:
            if not st.session_state[edit_key]:
                if st.button("✎ Edit", key="mfq_edit_btn", type="secondary", use_container_width=True, disabled=not can_edit):
                    st.session_state[edit_key] = True
                    st.rerun()
                if not can_edit:
                    st.caption("Read-only")
            else:
                save_clicked = st.button("Save Draft", key="mfq_save_btn", type="primary", use_container_width=True)
                if st.button("Cancel", key="mfq_cancel_btn", type="secondary", use_container_width=True):
                    st.session_state[edit_key] = False
                    st.rerun()

    if workspace.get("missing_objects"):
        st.error(
            "MFQ Form tables are missing or not authorized. "
            "Please verify access to MFQ_SECTIONS, MFQ_QUESTIONS, and MFQ_ANSWERS."
        )
        _render_missing_objects(workspace.get("missing_objects", []))
        return

    _render_confidence_panel(workspace)
    synopsis_fields = {
        key: claim.get(key)
        for key in ("BRIEF_SYNOPSIS", "ALLEGED_INJURY_TERMS", "ALLEGATION_SUMMARY")
        if _safe_display(claim.get(key), fallback="")
    }
    if synopsis_fields:
        synopsis_col, questions_col = st.columns([1, 2.15], gap="large")
        with synopsis_col:
            with st.container(key=f"mfq_synopsis_card_{claim_id}"):
                _render_synopsis_panel(claim)
        with questions_col:
            rendered_questions = _render_questions(
                workspace.get("sections", pd.DataFrame()),
                workspace.get("section_confidence", pd.DataFrame()),
                can_edit=can_edit,
                edit_mode=bool(st.session_state[edit_key]),
                editable_section_ids=editable_section_ids,
                claim_id=claim_id,
            )
    else:
        rendered_questions = _render_questions(
            workspace.get("sections", pd.DataFrame()),
            workspace.get("section_confidence", pd.DataFrame()),
            can_edit=can_edit,
            edit_mode=bool(st.session_state[edit_key]),
            editable_section_ids=editable_section_ids,
            claim_id=claim_id,
        )
    if st.session_state[edit_key] and save_clicked:
        for question in rendered_questions:
            if not question.get("editable"):
                continue
            save_mfq_answer(
                session=session,
                claim_id=question["claim_id"] or claim_id,
                defendant_id=question["defendant_id"],
                question_id=question["question_id"],
                answer_value=st.session_state.get(question["widget_key"]),
                user_id=ctx.username,
                section_id=question.get("section_id"),
            )
        _invalidate_claim_caches(claim_id, "mfq_answers_cache", "mfq_form_cache")
        st.session_state[edit_key] = False
        st.success("MFQ answers saved successfully.")
        st.rerun()


def _render_history_tab(session, claim_id: str) -> None:
    history_df = _cached_per_claim(
        "claim_history_cache",
        claim_id,
        lambda: get_claim_history_by_claim_id(session, claim_id),
        label="Loading claim history...",
    )
    if history_df.empty:
        st.info("No history data available for this claim.")
    else:
        st.dataframe(history_df, use_container_width=True, hide_index=True)


def _render_documents_lazy_tab(session, claim_id: str) -> None:
    documents_df = _cached_per_claim(
        "claim_documents_cache",
        claim_id,
        lambda: get_claim_documents_by_claim_id(session, claim_id),
        label="Loading documents...",
    )
    _render_docs_tab(documents_df)


def render(session, ctx) -> None:
    claim_id = str(st.session_state.get("selected_claim_id") or "").strip()
    logger.info("render_claim_details called claim_id=%s", claim_id)
    if not claim_id:
        st.warning("No claim is selected. Open a claim from Dashboard or Claims page.")
        return

    _render_breadcrumb(claim_id)
    header_slot = st.empty()
    claim = _cached_per_claim(
        "claim_details_cache",
        claim_id,
        lambda: get_claim_detail_by_id(session, claim_id),
        label="Loading claim header...",
    )
    if not claim:
        st.error(
            f"Claim {claim_id} was not found in MFQ_CLAIM_DETAIL_VW. "
            "Please verify CLAIM_ID exists in the source claims table."
        )
        return

    review_started = st.session_state.get("review_click_started_at")
    if isinstance(review_started, (int, float)):
        logger.info("review_click_to_claim_header_ms=%d claim_id=%s", int((perf_counter() - review_started) * 1000), claim_id)
        st.session_state.pop("review_click_started_at", None)

    with header_slot.container():
        _render_header(session, ctx, claim_id, claim)

    if st.session_state.get(f"open_assign_modal_{claim_id}", False):
        mfq_workspace = _cached_per_claim(
            "mfq_form_cache",
            claim_id,
            lambda: build_mfq_workspace_for_claim(session, claim_id),
            label="Loading assignable MFQ sections...",
        )
        _render_assign_faculty_modal(
            session=session,
            ctx=ctx,
            claim_id=claim_id,
            sections_df=mfq_workspace.get("sections", pd.DataFrame()),
        )

    tab_key = f"claim_details_active_tab_{claim_id}"
    if st.session_state.get(tab_key) not in DETAIL_TAB_OPTIONS:
        st.session_state[tab_key] = DETAIL_TAB_OPTIONS[0]
    selected_tab = st.radio(
        "Claim details section",
        DETAIL_TAB_OPTIONS,
        key=tab_key,
        horizontal=True,
        label_visibility="collapsed",
    )

    if selected_tab == "MFQ Form":
        _render_mfq_tab(session, ctx, claim_id, claim)
    elif selected_tab == "Records Summary":
        _render_summary_tab(session, claim_id, claim)
    elif selected_tab == "Documents":
        _render_documents_lazy_tab(session, claim_id)
    elif selected_tab == "MedCron":
        summaries = _cached_per_claim("claim_summary_cache", claim_id, lambda: get_claim_summaries_by_claim_id(session, claim_id), label="Loading MedCron...")
        _render_text_tab(summaries.get("MEDCRON", ""), "No MedCron summary available.")
    elif selected_tab == "Legal Memo":
        summaries = _cached_per_claim("claim_summary_cache", claim_id, lambda: get_claim_summaries_by_claim_id(session, claim_id), label="Loading legal memo...")
        _render_text_tab(summaries.get("LEGAL_MEMO", ""), "No legal memo available.")
    elif selected_tab == "Enquiries":
        _render_history_tab(session, claim_id)
    elif selected_tab == "AI Assist":
        st.text_area("AI Assist Prompt", placeholder="Ask for claim-level insights from available summaries and MFQ answers")
        st.caption("AI Assist is placeholder UI and requires downstream service wiring.")
