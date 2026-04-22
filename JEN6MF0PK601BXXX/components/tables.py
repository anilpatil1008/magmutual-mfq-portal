from __future__ import annotations

import html
import streamlit as st


def _safe(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def status_chip(status: str) -> str:
    mapping = {
        "MFQ Generated": "chip chip-blue",
        "Assigned": "chip chip-blue",
        "Approved": "chip chip-green",
        "Rejected": "chip chip-red",
    }
    css = mapping.get(str(status), "chip chip-gray")
    return f'<span class="{css}">{_safe(status)}</span>'


def priority_chip(priority: str) -> str:
    mapping = {
        "Critical": "chip chip-red",
        "High": "chip chip-yellow",
        "Medium": "chip chip-blue",
        "Low": "chip chip-gray",
    }
    css = mapping.get(str(priority), "chip chip-gray")
    return f'<span class="{css}">{_safe(priority)}</span>'


def confidence_chip(score) -> str:
    value = float(score or 0)
    if value >= 90:
        css = "chip chip-green"
    elif value >= 80:
        css = "chip chip-yellow"
    else:
        css = "chip chip-red"
    return f'<span class="{css}">{value:.0f}%</span>'


def render_claims_table(queue_df, on_review, on_regenerate) -> None:
    st.markdown("""<div class="section-card">""", unsafe_allow_html=True)

    header_left, header_right = st.columns([5, 1.7])

    with header_left:
        st.markdown(
            """
            <div class="section-title">Recent Claims</div>
            <div class="section-subtitle">Latest claims submitted for assessment.</div>
            """,
            unsafe_allow_html=True,
        )

    with header_right:
        st.markdown("""<div class="claims-search-wrap">""", unsafe_allow_html=True)
        st.text_input(
            "Search claims",
            placeholder="Search by patient, file #...",
            label_visibility="collapsed",
            key="claims_table_inline_search",
        )
        st.markdown("""</div>""", unsafe_allow_html=True)

    st.markdown("""<hr class="row-divider">""", unsafe_allow_html=True)

    if queue_df.empty:
        st.info("No claims found")
        st.markdown("""</div>""", unsafe_allow_html=True)
        return

    header = st.columns([1.2, 3.1, 1.4, 1.2, 1.4, 1.2, 1.9])
    header[0].markdown("""<div class="table-head">CLAIM ID</div>""", unsafe_allow_html=True)
    header[1].markdown("""<div class="table-head">PATIENT / DEFENDANT</div>""", unsafe_allow_html=True)
    header[2].markdown("""<div class="table-head">STATUS</div>""", unsafe_allow_html=True)
    header[3].markdown("""<div class="table-head">PRIORITY</div>""", unsafe_allow_html=True)
    header[4].markdown("""<div class="table-head">DATE REQUESTED</div>""", unsafe_allow_html=True)
    header[5].markdown("""<div class="table-head">AI CONFIDENCE</div>""", unsafe_allow_html=True)
    header[6].markdown("""<div class="table-head">ACTION</div>""", unsafe_allow_html=True)

    st.markdown("""<hr class="row-divider">""", unsafe_allow_html=True)

    for idx, (_, row) in enumerate(queue_df.iterrows()):
        row_key = f"{row['CLAIM_ID']}_{idx}"
        cols = st.columns([1.2, 3.1, 1.4, 1.2, 1.4, 1.2, 1.9])

        cols[0].markdown(f"**{_safe(row['FILE_NUMBER'])}**")
        cols[1].markdown(
            f"""
            **{_safe(row['PATIENT_NAME'])}**  
            <span class="claim-subtext">vs. {_safe(row['DEFENDANT_NAME'])}<br>({_safe(row['DEFENDANT_SPECIALTY'])})</span>
            """,
            unsafe_allow_html=True,
        )
        cols[2].markdown(status_chip(row["STATUS"]), unsafe_allow_html=True)
        cols[3].markdown(priority_chip(row["PRIORITY"]), unsafe_allow_html=True)
        cols[4].write(str(row["DATE_REQUESTED"]))
        cols[5].markdown(confidence_chip(row["AI_CONFIDENCE"]), unsafe_allow_html=True)

        action_col1, action_col2 = cols[6].columns([1.2, 1])

        if bool(row["CAN_REGENERATE"]):
            if action_col1.button("Regenerate", key=f"regen_{row_key}", use_container_width=True):
                on_regenerate(row["CLAIM_ID"])
        else:
            action_col1.write("")

        if action_col2.button("Review", key=f"review_{row_key}", use_container_width=True):
            on_review(row["CLAIM_ID"])

        st.markdown("""<hr class="row-divider">""", unsafe_allow_html=True)

    st.markdown("""</div>""", unsafe_allow_html=True)