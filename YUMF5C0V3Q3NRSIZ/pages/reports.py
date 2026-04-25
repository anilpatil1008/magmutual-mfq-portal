import streamlit as st

from services.snowflake_service import get_report_metrics


def render(session, role: str, username: str):
    st.subheader("Reports & Analytics")
    metrics = get_report_metrics(session, role, username)
    if (
        metrics["status"].empty
        and metrics["priority"].empty
        and metrics["specialty"].empty
        and metrics["faculty"].empty
    ):
        st.info("No report data is available for your role yet.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Claims by Status")
        if metrics["status"].empty:
            st.caption("No status data.")
        else:
            st.bar_chart(metrics["status"].set_index("STATUS"))
        st.markdown("#### Claims by Priority")
        if metrics["priority"].empty:
            st.caption("No priority data.")
        else:
            st.bar_chart(metrics["priority"].set_index("PRIORITY"))
    with c2:
        st.markdown("#### Claims by Specialty")
        if metrics["specialty"].empty:
            st.caption("No specialty data.")
        else:
            st.bar_chart(metrics["specialty"].set_index("SPECIALTY"))
        st.markdown("#### Faculty Performance")
        if metrics["faculty"].empty:
            st.caption("No faculty performance data.")
        else:
            st.dataframe(metrics["faculty"], use_container_width=True)
