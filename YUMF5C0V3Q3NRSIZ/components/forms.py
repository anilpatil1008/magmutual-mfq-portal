import streamlit as st

from components.badges import confidence_badge


def render_mfq_sections(df, editable: bool = False):
    if df.empty:
        st.info("No MFQ sections found for this claim.")
        return

    section_scores = df.groupby("SECTION_NAME")["SECTION_CONFIDENCE"].mean().round(1).sort_values(ascending=False)
    st.markdown("#### Section-wise Review")
    review_cols = st.columns(4)
    for idx, (name, score) in enumerate(section_scores.items()):
        review_cols[idx % 4].markdown(
            f"<div class='section-score-card'><div class='section-score-name'>{name}</div>"
            f"<div class='section-score-value'>{score:.0f}%</div></div>",
            unsafe_allow_html=True,
        )

    for section_name, section_df in df.groupby("SECTION_NAME"):
        section_score = float(section_df["SECTION_CONFIDENCE"].iloc[0])
        with st.expander(f"{section_name} | Confidence {section_score:.0f}%", expanded=False):
            st.markdown(confidence_badge(section_score), unsafe_allow_html=True)
            for _, row in section_df.iterrows():
                col_q, col_a, col_c = st.columns([2, 3, 1])
                with col_q:
                    st.caption(f"Q: {row['QUESTION_TEXT']}")
                with col_a:
                    if editable and bool(row.get("IS_EDITABLE", True)):
                        st.text_area(
                            "Answer",
                            value=row["ANSWER_TEXT"],
                            key=f"ans_{row['QUESTION_ID']}",
                            label_visibility="collapsed",
                        )
                    else:
                        st.write(row["ANSWER_TEXT"])
                with col_c:
                    st.markdown(confidence_badge(float(row["AI_CONFIDENCE"])), unsafe_allow_html=True)
