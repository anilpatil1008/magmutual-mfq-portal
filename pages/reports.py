import streamlit as st

from services.snowflake_service import get_report_metrics


def render(session, role: str, username: str):
    st.subheader("Reports & Analytics")
    metrics = get_report_metrics(session, role, username)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Claims by Status")
        st.bar_chart(metrics["status"].set_index("STATUS"))
        st.markdown("#### Claims by Priority")
        st.bar_chart(metrics["priority"].set_index("PRIORITY"))
    with c2:
        st.markdown("#### Claims by Specialty")
        st.bar_chart(metrics["specialty"].set_index("SPECIALTY"))
        st.markdown("#### Faculty Performance")
        st.dataframe(metrics["faculty"], use_container_width=True)
