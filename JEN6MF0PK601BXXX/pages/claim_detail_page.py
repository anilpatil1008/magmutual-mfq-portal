from __future__ import annotations

import html
import json

import streamlit as st

from repositories.claim_repository import get_claim_header
from repositories.mfq_repository import (
    get_claim_summaries,
    get_current_answers,
    get_questions_by_section,
    get_section_confidence,
    get_sections,
)
from services.claim_service import approve_claim

REVIEW_TABS = [
    "MFQ Form",
    "Records Summary",
    "MedCron",
    "Legal Memo",
    "Enquiries",
    "AI Assist",
    "Documents",
]


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def _parse_allowed_values(raw_value):
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


def _bucket(score: float) -> str:
    if score >= 90:
        return "high"
    if score >= 80:
        return "moderate"
    return "low"


def _inject_review_styles() -> None:
    st.markdown(
        """
        <style>
        .review-v2-shell { margin-top: 0.15rem; }
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 1400px;
        }
        .st-key-claim_header_card [data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            box-shadow: 0 2px 10px rgba(16,24,40,.06);
            padding: 1rem 1.25rem 1.05rem !important;
        }
        .review-v2-back button {
            color: #5f6b80 !important;
            justify-content: flex-start !important;
            min-height: 24px !important;
            font-size: 12px !important;
            padding-left: 0 !important;
        }
        .review-v2-back button:hover { color: #0b2f6b !important; text-decoration: underline !important; }
        .review-v2-panel {
            background: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(16,24,40,.05);
            overflow: hidden;
        }
        .review-v2-head {
            font-size: 26px;
            line-height: 1.2;
            font-weight: 700;
            color: #13213d;
            letter-spacing: -0.01em;
            margin-bottom: 0;
        }
        .review-v2-head .vs { font-size: .72em; color: #6b7280; font-weight: 600; }
        .review-v2-title-row {
            display: flex;
            align-items: center;
            gap: .55rem;
            flex-wrap: wrap;
        }
        .review-v2-header-actions { display: flex; justify-content: flex-end; gap: .5rem; }
        .review-v2-header-actions button {
            min-height: 40px !important;
            font-size: 20px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            padding: .3rem .9rem !important;
            background: #0a3a78 !important;
            border: 1px solid #0a3a78 !important;
        }
        .review-v2-chip {
            display: inline-flex;
            align-items: center;
            font-size: 12px;
            font-weight: 700;
            border-radius: 8px;
            padding: .2rem .5rem;
            margin-left: 0;
        }
        .review-v2-meta-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .65rem .9rem;
            margin-top: .75rem;
        }
        .review-v2-meta-cell { min-width: 0; }
        .review-v2-meta-label {
            font-size: 10px;
            letter-spacing: .08em;
            color: #667085;
            font-weight: 700;
            text-transform: uppercase;
        }
        .review-v2-meta-value {
            font-size: 14px;
            font-weight: 500;
            color: #1f2937;
            line-height: 1.3;
            word-break: break-word;
        }
        .review-v2-tabs .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            border-bottom: 1px solid #dbe4f0;
            padding: 0 .5rem;
        }
        .review-v2-tabs .stTabs [data-baseweb="tab"] {
            padding: .55rem .9rem;
            min-height: 44px;
            font-size: 13px;
            font-weight: 600;
            border-bottom: 2px solid transparent;
        }
        .review-v2-tabs .stTabs [aria-selected="true"] {
            color: #0b2f6b !important;
            border-bottom-color: #0b2f6b !important;
        }

        .review-v2-title { font-size: 40px; color: #0b2f6b; font-weight: 800; line-height: 1.1; }
        .review-v2-subtitle { color: #667085; margin-top: .2rem; }
        .review-v2-confidence { background: #fffdf6; border-color: #e7cf8e; }
        .review-v2-grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .review-v2-barbox { border: 1px solid #ebf0f7; background: #fff; border-radius: 10px; padding: .45rem .55rem; }
        .review-v2-track { height: 6px; background: #edf2f8; border-radius: 99px; overflow: hidden; }
        .review-v2-fill { height: 100%; border-radius: 99px; }
        .review-v2-small { font-size: 13px; color: #475467; }

        .review-v2-synopsis { background: #f7f9fc; }
        .review-v2-synopsis h4, .review-v2-eval h4 { margin: 0; color: #0b2f6b; font-size: 35px; font-weight: 800; }
        .review-v2-synopsis .block-title { font-size: 12px; color: #475467; letter-spacing: .06em; font-weight: 700; margin-top: .9rem; }
        .review-v2-synopsis .block-value { color: #344054; line-height: 1.45; }

        .review-v2-section-btn button {
            justify-content: flex-start !important;
            border-radius: 10px !important;
            border: 1px solid #d5deeb !important;
            background: #f8fbff !important;
            color: #0b2f6b !important;
            font-weight: 700 !important;
        }

        .review-v2-eval { padding: 0 !important; }
        .review-v2-eval-head { background: #f8fafc; border-bottom: 1px solid #e4eaf3; padding: .95rem 1.15rem; }
        .review-v2-qcard {
            border: 1px solid #e4eaf3;
            border-radius: 12px;
            background: #fff;
            margin: .5rem 1rem 1rem;
            padding: .8rem;
        }
        .review-v2-badge {
            display: inline-flex; align-items: center; white-space: nowrap;
            border-radius: 8px; font-size: 12px; font-weight: 700; padding: .2rem .5rem;
        }
        .review-v2-eval textarea { background: #f8fafc !important; }

        @media (max-width: 900px) {
            .review-v2-head { font-size: 24px; }
            .review-v2-title { font-size: 26px; }
            .review-v2-meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        @media (max-width: 700px) {
            .review-v2-header-actions { justify-content: stretch; }
            .review-v2-header-actions button { width: 100%; }
            .review-v2-meta-grid { grid-template-columns: 1fr; }
            .review-v2-grid-two { grid-template-columns: 1fr; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_chip(status: str) -> str:
    mapping = {
        "MFQ Generated": ("#e7efff", "#2457d6"),
        "Assigned": ("#e7efff", "#2457d6"),
        "Approved": ("#e8f7ee", "#067647"),
        "Rejected": ("#fde7e7", "#d92d20"),
    }
    bg, fg = mapping.get(str(status), ("#eef2f7", "#475467"))
    return f"<span class='review-v2-chip' style='background:{bg};color:{fg};'>{_safe(status)}</span>"


def _priority_chip(priority: str) -> str:
    mapping = {
        "Critical": ("#fde7e7", "#d92d20"),
        "High": ("#fff1d6", "#b54708"),
        "Medium": ("#e7efff", "#2457d6"),
        "Low": ("#eef2f7", "#475467"),
    }
    bg, fg = mapping.get(str(priority), ("#eef2f7", "#475467"))
    return f"<span class='review-v2-chip' style='background:{bg};color:{fg};'>{_safe(priority)}</span>"


def _score_badge(score) -> str:
    value = float(score or 0)
    bucket = _bucket(value)
    colors = {
        "high": ("#e8f7ee", "#067647"),
        "moderate": ("#fff1d6", "#b54708"),
        "low": ("#fde7e7", "#d92d20"),
    }
    bg, fg = colors[bucket]
    return f"<span class='review-v2-badge' style='background:{bg};color:{fg};'>✣ {value:.0f}%</span>"


def _section_score_map(section_conf_df):
    scores = {}
    for _, row in section_conf_df.iterrows():
        scores[str(row["SECTION_KEY"]).upper()] = float(row["CONFIDENCE_SCORE"])
    return scores


def _render_claim_header(row, role_key: str) -> None:
    with st.container(border=True, key="claim_header_card"):
        st.markdown("<div class='review-v2-back'>", unsafe_allow_html=True)
        if st.button(
            f"← Back to Dashboard  /  {_safe(row['FILE_NUMBER'])}",
            key="back_to_dashboard_btn",
            type="tertiary",
        ):
            st.session_state.page = "Dashboard"
            st.session_state.selected_claim_id = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        left, right = st.columns([5, 2])
        left.markdown(
            f"""
            <div class='review-v2-title-row'>
              <div class='review-v2-head'>
                {_safe(row['PATIENT_NAME'])} <span class='vs'>vs</span> {_safe(row['DEFENDANT_NAME'])}
              </div>
                {_status_chip(row['STATUS'])}
                {_priority_chip(row['PRIORITY'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if role_key in {"CLAIMS_ANALYST", "ADMIN"}:
            st.markdown("<div class='review-v2-header-actions'>", unsafe_allow_html=True)
            if right.button("Reassign", key="assign_faculty_btn", use_container_width=True, type="primary"):
                st.info("Connect this to assignment workflow.")
            st.markdown("</div>", unsafe_allow_html=True)
        elif role_key == "FACULTY":
            st.markdown("<div class='review-v2-header-actions'>", unsafe_allow_html=True)
            if right.button("Approve", key=f"approve_{row['CLAIM_ID']}", use_container_width=True, type="primary"):
                approve_claim(row["CLAIM_ID"])
                st.success("Claim approved")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        metadata = [
            ("FILE NUMBER", _safe(row["FILE_NUMBER"])),
            ("DEFENDANT SPECIALTY", _safe(row["DEFENDANT_SPECIALTY"])),
            ("DATE REQUESTED", _safe(row["DATE_REQUESTED"])),
            ("REVIEWER", "Dr. Robert Martinez"),
            ("MAGMUTUAL CONTACT", "Sarah Johnson"),
            ("CONTACT EMAIL", "analyst@magmutual.com"),
        ]
        meta_html = "".join(
            [
                f"<div class='review-v2-meta-cell'><div class='review-v2-meta-label'>{label}</div><div class='review-v2-meta-value'>{value}</div></div>"
                for label, value in metadata
            ]
        )
        st.markdown(f"<div class='review-v2-meta-grid'>{meta_html}</div>", unsafe_allow_html=True)


def _render_confidence(section_conf_df, overall_score: float) -> None:
    st.markdown('<div class="review-v2-panel review-v2-confidence" style="padding:1rem 1rem .9rem;">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:center;">
            <div style="font-size:30px;font-weight:800;color:#1f2937;">✣ AI Confidence Analysis</div>
            <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;justify-content:flex-end;">
                <span class='review-v2-badge' style='background:#fff1d6;color:#b54708;border:1px solid #f0cf9a;'>Faculty Review Might Be Needed</span>
                <span style="font-weight:700;color:#6b7280;">Overall <span style="font-size:42px;color:#b54708;">{overall_score:.0f}%</span></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if section_conf_df.empty:
        st.info("No section confidence available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown("<hr style='border:none;border-top:1px solid #ead9aa;margin:.7rem 0 .8rem;'>", unsafe_allow_html=True)
    st.markdown("<div class='review-v2-small' style='font-weight:700;letter-spacing:.04em;margin-bottom:.45rem;'>SECTION-WISE CONFIDENCE</div>", unsafe_allow_html=True)

    low_sections, moderate_sections = [], []
    html_boxes = []
    for _, section in section_conf_df.iterrows():
        score = float(section["CONFIDENCE_SCORE"])
        section_name = str(section["SECTION_KEY"]).replace("_", " ").title()
        bucket = _bucket(score)
        color = {"high": "#12b76a", "moderate": "#f79009", "low": "#f04438"}[bucket]
        if bucket == "low":
            low_sections.append(f"{section_name} ({score:.0f}%)")
        elif bucket == "moderate":
            moderate_sections.append(f"{section_name} ({score:.0f}%)")
        html_boxes.append(
            f"""
            <div class='review-v2-barbox'>
                <div style='display:flex;justify-content:space-between;gap:.5rem;font-size:13px;font-weight:600;color:#1d2939;'>
                    <span>{_safe(section_name)}</span><span style='color:{color};'>{score:.0f}%</span>
                </div>
                <div class='review-v2-track'><div class='review-v2-fill' style='width:{score:.0f}%;background:{color};'></div></div>
            </div>
            """
        )

    st.markdown(f"<div class='review-v2-grid-two'>{''.join(html_boxes)}</div>", unsafe_allow_html=True)
    if low_sections or moderate_sections:
        notes = ""
        if low_sections:
            notes += f"<li><span style='color:#d92d20;font-weight:700;'>● Needs review:</span> {', '.join(low_sections)}</li>"
        if moderate_sections:
            notes += f"<li><span style='color:#b54708;font-weight:700;'>● Moderate confidence:</span> {', '.join(moderate_sections)}</li>"
        st.markdown(f"<ul class='review-v2-small' style='margin:.75rem 0 0 0.5rem;padding-left:.5rem;'>{notes}</ul>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_synopsis_and_navigation(row, sections_df, score_map) -> None:
    st.markdown('<div class="review-v2-panel review-v2-synopsis" style="padding:1rem;">', unsafe_allow_html=True)
    st.markdown("<h4>⚠ Claim Synopsis</h4>", unsafe_allow_html=True)
    st.markdown(f"<div class='block-title'>SYNOPSIS</div><div class='block-value'>{_safe(row['BRIEF_SYNOPSIS'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='block-title'>ALLEGED INJURY</div><div class='block-value'>{_safe(row['ALLEGED_INJURY_TERMS'])}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='block-title'>ALLEGATIONS</div><div class='block-value'>{_safe(row['ALLEGATION_SUMMARY'])}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="review-v2-panel" style="padding:1rem;margin-top:.75rem;">', unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:28px;'>Sections</h4>", unsafe_allow_html=True)
    if "selected_mfq_section" not in st.session_state and not sections_df.empty:
        st.session_state.selected_mfq_section = str(sections_df.iloc[0]["SECTION_KEY"])

    for _, section in sections_df.iterrows():
        section_key = str(section["SECTION_KEY"])
        section_name = str(section["SECTION_NAME"])
        score = score_map.get(section_key.upper())
        label = f"{section_name}  ({score:.0f}%)" if score is not None else section_name
        st.markdown("<div class='review-v2-section-btn'>", unsafe_allow_html=True)
        if st.button(label, key=f"review_v2_nav_{section_key}", use_container_width=True):
            st.session_state.selected_mfq_section = section_key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_question(question, answer, suffix: str) -> None:
    answer_text = "" if answer is None else (answer.get("ANSWER_TEXT") or answer.get("ANSWER_RAW") or "")
    answer_raw = "" if answer is None else (answer.get("ANSWER_RAW") or "")
    confidence = None if answer is None else answer.get("CONFIDENCE_SCORE")

    st.markdown("<div class='review-v2-qcard'>", unsafe_allow_html=True)
    qleft, qright = st.columns([6, 1])
    qleft.markdown(f"**{_safe(question['QUESTION_TEXT'])}**")
    if confidence is not None:
        qright.markdown(_score_badge(confidence), unsafe_allow_html=True)

    answer_type = str(question["ANSWER_TYPE"]).upper()
    if answer_type == "RADIO":
        default_options = ["Yes", "No", "Unclear", "Not Applicable"]
        options = _parse_allowed_values(question["ALLOWED_VALUES"])
        merged = default_options if not options else list(dict.fromkeys(default_options + options))
        idx = merged.index(answer_raw) if answer_raw in merged else 0
        st.radio(
            f"Answer {question['QUESTION_ID']}",
            merged,
            index=idx,
            horizontal=True,
            key=f"review_v2_radio_{question['QUESTION_ID']}_{suffix}",
            label_visibility="collapsed",
        )
        st.text_area(
            f"Rationale {question['QUESTION_ID']}",
            value=answer_text,
            key=f"review_v2_text_{question['QUESTION_ID']}_{suffix}",
            height=74,
            label_visibility="collapsed",
            placeholder="Explain if Yes, No, or Unclear...",
        )
        c1, c2 = st.columns(2)
        c1.radio(
            "Was this a deviation from acceptable practice?",
            ["Yes", "No", "Unclear"],
            horizontal=True,
            key=f"review_v2_fu1_{question['QUESTION_ID']}_{suffix}",
        )
        c2.radio(
            "Did it likely impact the patient's care or outcome?",
            ["Yes", "No", "Unclear"],
            horizontal=True,
            key=f"review_v2_fu2_{question['QUESTION_ID']}_{suffix}",
        )
    else:
        st.text_area(
            f"Answer {question['QUESTION_ID']}",
            value=answer_text,
            key=f"review_v2_text_{question['QUESTION_ID']}_{suffix}",
            height=110,
            label_visibility="collapsed",
            placeholder="Add details...",
        )

    st.markdown("</div>", unsafe_allow_html=True)


def _render_questionnaire(sections_df, answers_map, selected_key: str) -> None:
    st.markdown('<div class="review-v2-panel review-v2-eval">', unsafe_allow_html=True)
    st.markdown("<div class='review-v2-eval-head'><h4>Section III: Detailed Case Evaluation</h4></div>", unsafe_allow_html=True)
    for section_idx, (_, section) in enumerate(sections_df.iterrows()):
        section_key = str(section["SECTION_KEY"])
        section_name = str(section["SECTION_NAME"])
        is_open = section_key == selected_key

        with st.expander(section_name, expanded=is_open):
            if not is_open:
                if st.button(f"Open {section_name}", key=f"review_v2_open_{section_key}"):
                    st.session_state.selected_mfq_section = section_key
                    st.rerun()
                continue

            q_df = get_questions_by_section(section["SECTION_ID"])
            for q_idx, (_, question) in enumerate(q_df.iterrows()):
                _render_question(
                    question=question,
                    answer=answers_map.get(question["QUESTION_ID"]),
                    suffix=f"{section_idx}_{q_idx}",
                )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_tabbed_content(row, claim_id: str, defendant_id: str) -> None:
    st.markdown("<div style='height:.55rem;'></div>", unsafe_allow_html=True)
    tab_objects = st.tabs(REVIEW_TABS)
    with tab_objects[0]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem 1.05rem;">', unsafe_allow_html=True)
        st.markdown("<div class='review-v2-title'>Medical Faculty Questionnaire</div>", unsafe_allow_html=True)
        st.markdown("<div class='review-v2-subtitle'>Complete evaluation based on accepted medical practice standards.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        sections_df = get_sections()
        section_conf_df = get_section_confidence(claim_id, defendant_id)
        answers_df = get_current_answers(claim_id, defendant_id)
        answers_map = {r["QUESTION_ID"]: r for _, r in answers_df.iterrows()}

        _render_confidence(section_conf_df, float(row["AI_CONFIDENCE"]))

        left, right = st.columns([1.05, 2.35])
        score_map = _section_score_map(section_conf_df)
        with left:
            _render_synopsis_and_navigation(row, sections_df, score_map)

        with right:
            selected_key = st.session_state.get("selected_mfq_section", str(sections_df.iloc[0]["SECTION_KEY"]) if not sections_df.empty else "")
            _render_questionnaire(sections_df, answers_map, selected_key)
    summaries_df = get_claim_summaries(claim_id, defendant_id)
    summary_map = {r["SUMMARY_TYPE"]: r["SUMMARY_TEXT"] for _, r in summaries_df.iterrows()}

    with tab_objects[1]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("Records Summary")
        st.write(summary_map.get("RECORDS_SUMMARY", "No records summary available"))
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_objects[2]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("MedCron")
        st.write(summary_map.get("MEDCRON", "No MedCron summary available"))
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_objects[3]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("Legal Memo")
        st.write(summary_map.get("LEGAL_MEMO", "No legal memo summary available"))
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_objects[4]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("Enquiries")
        st.text_area("Ask a role-safe question", key="claim_detail_enquiry")
        st.button("Ask", key="claim_detail_enquiry_btn")
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_objects[5]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("AI Assist")
        st.write("Use this tab for guided AI analysis and evidence lookup.")
        st.markdown("</div>", unsafe_allow_html=True)
    with tab_objects[6]:
        st.markdown('<div class="review-v2-panel" style="margin-top:.85rem;padding:1rem;">', unsafe_allow_html=True)
        st.subheader("Documents")
        st.write("Add document viewer and PDF download links here.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_claim_detail_page(user_id: str, role_key: str) -> None:  # noqa: ARG001
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

    _inject_review_styles()
    st.markdown("<div class='review-v2-shell'></div>", unsafe_allow_html=True)
    _render_claim_header(row, role_key)
    _render_tabbed_content(row, claim_id, defendant_id)
