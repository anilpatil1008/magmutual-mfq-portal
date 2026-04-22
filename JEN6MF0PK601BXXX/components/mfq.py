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


def _score_chip(score) -> str:
    value = float(score or 0)
    if value >= 90:
        bg, fg = "#e8f7ee", "#067647"
    elif value >= 80:
        bg, fg = "#fff1d6", "#b54708"
    else:
        bg, fg = "#fde7e7", "#d92d20"
    return f"<span class='score-chip' style='background:{bg};color:{fg};'>{value:.0f}%</span>"


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
            <div class="confidence-title">AI Confidence Analysis</div>
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

    col1, col2 = st.columns(2)
    rows = list(section_confidence_df.iterrows())
    for idx, (_, row) in enumerate(rows):
        target = col1 if idx % 2 == 0 else col2
        with target:
            score = float(row["CONFIDENCE_SCORE"])
            st.markdown(
                f"""
                <div class="section-confidence-box">
                    <div class="section-confidence-top">
                        <span>{_safe(str(row['SECTION_KEY']).replace('_', ' ').title())}</span>
                        <span>{score:.0f}%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(score / 100.0)

    st.markdown("""</div>""", unsafe_allow_html=True)


def render_claim_synopsis_panel(row) -> None:
    st.markdown("""<div class="content-card synopsis-card">""", unsafe_allow_html=True)
    st.markdown("""<div class="synopsis-title">Claim Synopsis</div>""", unsafe_allow_html=True)
    st.markdown(f"**SYNOPSIS**  \n{_safe(row['BRIEF_SYNOPSIS'])}")
    st.markdown(f"**ALLEGED INJURY**  \n{_safe(row['ALLEGED_INJURY_TERMS'])}")
    st.markdown(f"**ALLEGATIONS**  \n{_safe(row['ALLEGATION_SUMMARY'])}")
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
        options = parse_allowed_values(question["ALLOWED_VALUES"])
        options_display = [""] + options
        current_index = options_display.index(answer_raw) if answer_raw in options_display else 0

        radio_key = f"radio_{question['QUESTION_ID']}_{suffix}"
        text_key = f"text_{question['QUESTION_ID']}_{suffix}"
        save_key = f"save_{question['QUESTION_ID']}_{suffix}"

        selected = st.radio(
            f"Answer {question['QUESTION_ID']}",
            options_display,
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
            height=90,
            label_visibility="collapsed",
            placeholder="Explain here...",
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
) -> None:
    st.markdown("""<div class="content-card">""", unsafe_allow_html=True)
    st.markdown("""<div class="mfq-title">Medical Faculty Questionnaire</div>""", unsafe_allow_html=True)
    st.markdown("""<div class="mfq-subtitle">Complete evaluation based on accepted medical practice standards.</div>""", unsafe_allow_html=True)
    st.markdown("""</div>""", unsafe_allow_html=True)

    for section_idx, (_, section) in enumerate(sections_df.iterrows()):
        section_key = section["SECTION_KEY"]
        section_name = section["SECTION_NAME"]
        is_editable = section_key in editable_sections

        with st.expander(section_name, expanded=section["DISPLAY_ORDER"] <= 3):
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