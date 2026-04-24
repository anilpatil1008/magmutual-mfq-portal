from __future__ import annotations

import html
import json
from typing import Dict

import streamlit as st

from services.mfq_service import guidance_from_confidence, save_answer


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _confidence_bucket(score: float) -> str:
    if score >= 90:
        return "high"
    if score >= 80:
        return "moderate"
    return "low"


def _score_chip(score) -> str:
    value = float(score or 0)
    bucket = _confidence_bucket(value)
    colors = {
        "high": ("#e8f7ee", "#067647"),
        "moderate": ("#fff1d6", "#b54708"),
        "low": ("#fde7e7", "#d92d20"),
    }
    bg, fg = colors[bucket]
    return f"<span class='score-chip' style='background:{bg};color:{fg};'>✣ {value:.0f}%</span>"


def _confidence_bar(section_name: str, score: float) -> str:
    bucket = _confidence_bucket(score)
    bar_color = {"high": "#12b76a", "moderate": "#f79009", "low": "#f04438"}[bucket]
    return f"""
    <div class='section-confidence-box'>
        <div class='section-confidence-top'>
            <span>{_safe(section_name)}</span>
            <span class='section-confidence-score'>{score:.0f}%</span>
        </div>
        <div class='section-confidence-track'>
            <div class='section-confidence-fill' style='width:{score:.0f}%;background:{bar_color};'></div>
        </div>
    </div>
    """


def parse_allowed_values(raw_value):
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(x) for x in raw_value]
    try:
        if hasattr(raw_value, "tolist"):
            return [str(x) for x in raw_value.tolist()]
        return [str(x) for x in json.loads(raw_value)]
    except Exception:
        return []


def render_ai_confidence_panel(section_confidence_df, overall_score: float) -> None:
    guidance = guidance_from_confidence(overall_score)

    st.markdown("""<div class="content-card confidence-card">""", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="confidence-header">
            <div class="confidence-title">✣ AI Confidence Analysis</div>
            <div class="confidence-right">
                <span class="confidence-guidance">{_safe(guidance)}</span>
                <span class="confidence-overall">Overall {overall_score:.0f}%</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if section_confidence_df.empty:
        st.caption("No section confidence available")
        st.markdown("""</div>""", unsafe_allow_html=True)
        return

    low_sections = []
    moderate_sections = []

    col1, col2 = st.columns(2)
    rows = list(section_confidence_df.iterrows())
    for idx, (_, row) in enumerate(rows):
        target = col1 if idx % 2 == 0 else col2
        score = float(row["CONFIDENCE_SCORE"])
        section_name = str(row["SECTION_KEY"]).replace("_", " ").title()

        if score < 80:
            low_sections.append(section_name)
        elif score < 90:
            moderate_sections.append(section_name)

        with target:
            st.markdown(_confidence_bar(section_name, score), unsafe_allow_html=True)

    notes = []
    if low_sections:
        notes.append(f"<li><span class='danger'>Needs review:</span> {', '.join(low_sections)}</li>")
    if moderate_sections:
        notes.append(f"<li><span class='warn'>Moderate confidence:</span> {', '.join(moderate_sections)}</li>")

    if notes:
        st.markdown(f"<div class='confidence-warning-box'><ul class='confidence-notes'>{''.join(notes)}</ul></div>", unsafe_allow_html=True)

    st.markdown("""</div>""", unsafe_allow_html=True)


def render_claim_synopsis_panel(row) -> None:
    st.markdown("""<div class="content-card synopsis-card">""", unsafe_allow_html=True)
    st.markdown("""<div class="synopsis-title">⚠ Claim Synopsis</div>""", unsafe_allow_html=True)
    st.markdown(f"<div class='synopsis-block'><div class='synopsis-label'>SYNOPSIS</div><div>{_safe(row['BRIEF_SYNOPSIS'])}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='synopsis-block'><div class='synopsis-label'>ALLEGED INJURY</div><div>{_safe(row['ALLEGED_INJURY_TERMS'])}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='synopsis-block'><div class='synopsis-label'>ALLEGATIONS</div><div>{_safe(row['ALLEGATION_SUMMARY'])}</div></div>", unsafe_allow_html=True)
    st.markdown("""</div>""", unsafe_allow_html=True)


def render_mfq_section_navigation(sections_df, section_conf_df) -> None:
    scores = {}
    for _, row in section_conf_df.iterrows():
        scores[str(row["SECTION_KEY"]).upper()] = float(row["CONFIDENCE_SCORE"])

    st.markdown("""<div class="content-card section-nav-card"><div class="synopsis-title">MFQ Sections</div>""", unsafe_allow_html=True)
    for _, section in sections_df.iterrows():
        section_key = str(section["SECTION_KEY"])
        score = scores.get(section_key.upper())
        chip = _score_chip(score) if score is not None else ""
        selected_key = st.session_state.get("selected_mfq_section", str(sections_df.iloc[0]["SECTION_KEY"]))
        css_class = "section-nav-btn active" if selected_key == section_key else "section-nav-btn"
        if st.button(
            f"{section['SECTION_NAME']}",
            key=f"section_nav_{section_key}",
            use_container_width=True,
            help=f"Open {section['SECTION_NAME']}",
        ):
            st.session_state.selected_mfq_section = section_key
            st.rerun()
        st.markdown(f"<div class='{css_class}'>{chip}</div>", unsafe_allow_html=True)
    st.markdown("""</div>""", unsafe_allow_html=True)


def render_single_question(question, answer, claim_id, defendant_id, user_id, is_editable: bool, suffix: str) -> None:
    answer_text = "" if answer is None else (answer.get("ANSWER_TEXT") or answer.get("ANSWER_RAW") or "")
    answer_raw = "" if answer is None else (answer.get("ANSWER_RAW") or "")
    confidence = None if answer is None else answer.get("CONFIDENCE_SCORE")

    st.markdown("""<div class="question-card">""", unsafe_allow_html=True)

    q_left, q_right = st.columns([6, 1])
    q_left.markdown(f"**{_safe(question['QUESTION_TEXT'])}**")
    if confidence is not None:
        q_right.markdown(_score_chip(confidence), unsafe_allow_html=True)

    answer_type = str(question["ANSWER_TYPE"]).upper()

    if answer_type == "RADIO":
        allowed = parse_allowed_values(question["ALLOWED_VALUES"])
        default_options = ["Yes", "No", "Unclear", "Not Applicable"]
        options = default_options if not allowed else list(dict.fromkeys(default_options + allowed))

        current_index = options.index(answer_raw) if answer_raw in options else 0

        radio_key = f"radio_{question['QUESTION_ID']}_{suffix}"
        text_key = f"text_{question['QUESTION_ID']}_{suffix}"
        save_key = f"save_{question['QUESTION_ID']}_{suffix}"

        selected = st.radio(
            f"Answer {question['QUESTION_ID']}",
            options,
            index=current_index,
            horizontal=True,
            disabled=not is_editable,
            key=radio_key,
            label_visibility="collapsed",
        )

        rationale = st.text_area(
            f"Rationale {question['QUESTION_ID']}",
            value=answer_text,
            disabled=not is_editable,
            key=text_key,
            height=80,
            label_visibility="collapsed",
            placeholder="Explain if Yes, No, or Unclear...",
        )

        if selected in {"Yes", "No", "Unclear", "Not Applicable"}:
            fu_col_1, fu_col_2 = st.columns(2)
            fu_col_1.radio(
                "Was this a deviation from acceptable practice?",
                ["Yes", "No", "Unclear"],
                horizontal=True,
                key=f"fu1_{question['QUESTION_ID']}_{suffix}",
                label_visibility="visible",
                disabled=not is_editable,
            )
            fu_col_2.radio(
                "Did it likely impact patient care/outcome?",
                ["Yes", "No", "Unclear"],
                horizontal=True,
                key=f"fu2_{question['QUESTION_ID']}_{suffix}",
                label_visibility="visible",
                disabled=not is_editable,
            )

        if is_editable and st.button("Save", key=save_key):
            save_answer(
                claim_id=claim_id,
                defendant_id=defendant_id,
                question_id=question["QUESTION_ID"],
                question_key=question["QUESTION_KEY"],
                answer_raw=selected,
                answer_text=rationale,
                user_id=user_id,
            )
            st.success("Saved")
            st.rerun()
    else:
        text_key = f"text_{question['QUESTION_ID']}_{suffix}"
        save_key = f"save_{question['QUESTION_ID']}_{suffix}"

        updated = st.text_area(
            f"Answer {question['QUESTION_ID']}",
            value=answer_text,
            disabled=not is_editable,
            key=text_key,
            height=110,
            label_visibility="collapsed",
            placeholder="Add details...",
        )

        if is_editable and st.button("Save", key=save_key):
            save_answer(
                claim_id=claim_id,
                defendant_id=defendant_id,
                question_id=question["QUESTION_ID"],
                question_key=question["QUESTION_KEY"],
                answer_raw=updated,
                answer_text=updated,
                user_id=user_id,
            )
            st.success("Saved")
            st.rerun()

    st.markdown("""</div>""", unsafe_allow_html=True)


def render_mfq_questionnaire(
    claim_id: str,
    defendant_id: str,
    sections_df,
    answers_map: Dict,
    editable_sections,
    get_questions_by_section_fn,
    user_id: str,
    show_title: bool = True,
) -> None:
    if show_title:
        st.markdown("""<div class="content-card mfq-title-card">""", unsafe_allow_html=True)
        title_col, action_col = st.columns([5, 1])
        title_col.markdown("""<div class="mfq-title">Medical Faculty Questionnaire</div>""", unsafe_allow_html=True)
        title_col.markdown("""<div class="mfq-subtitle">Complete evaluation based on accepted medical practice standards.</div>""", unsafe_allow_html=True)
        action_col.button("✎  Edit", key="mfq_edit_btn", use_container_width=True)
        st.markdown("""</div>""", unsafe_allow_html=True)

    if sections_df.empty:
        st.info("No questionnaire sections available")
        return

    if "selected_mfq_section" not in st.session_state:
        st.session_state.selected_mfq_section = str(sections_df.iloc[0]["SECTION_KEY"])

    selected_key = st.session_state.selected_mfq_section

    st.markdown("""<div class='content-card eval-shell'><div class='eval-header'>Section III: Detailed Case Evaluation</div>""", unsafe_allow_html=True)
    for section_idx, (_, section) in enumerate(sections_df.iterrows()):
        section_key = section["SECTION_KEY"]
        section_name = section["SECTION_NAME"]
        is_open = section_key == selected_key

        arrow = "▾" if is_open else "▸"
        if st.button(f"{section_name} {arrow}", key=f"accordion_{section_key}", use_container_width=True):
            st.session_state.selected_mfq_section = section_key
            st.rerun()

        if not is_open:
            continue

        is_editable = section_key in editable_sections
        if not is_editable:
            st.caption("Read-only for current role or assignment")

        q_df = get_questions_by_section_fn(section["SECTION_ID"])
        for question_idx, (_, question) in enumerate(q_df.iterrows()):
            answer = answers_map.get(question["QUESTION_ID"])
            render_single_question(
                question=question,
                answer=answer,
                claim_id=claim_id,
                defendant_id=defendant_id,
                user_id=user_id,
                is_editable=is_editable,
                suffix=f"{section_idx}_{question_idx}",
            )

    st.markdown("""</div>""", unsafe_allow_html=True)
