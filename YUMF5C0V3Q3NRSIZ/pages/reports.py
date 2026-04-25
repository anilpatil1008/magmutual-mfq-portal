import streamlit as st

from services.snowflake_service import get_report_metrics


def render(session, role: str, username: str):
    st.subheader("Reports Dashboard")
    metrics = get_report_metrics(session, role, username)

    top_a, top_b, top_c = st.columns(3)
    top_a.metric("Open Claims", int(metrics["status"]["COUNT"].sum()))
    top_b.metric("Specialties Covered", int(metrics["specialty"]["SPECIALTY"].nunique()))
    top_c.metric("Faculty in Rotation", int(metrics["faculty"]["ASSIGNED_TO"].nunique()))

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

    st.markdown("#### Exports")
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Download Status Report",
            data=metrics["status"].to_csv(index=False),
            file_name="claims_status_report.csv",
            mime="text/csv",
        )
    with e2:
        st.download_button(
            "Download Faculty Performance",
            data=metrics["faculty"].to_csv(index=False),
            file_name="faculty_performance.csv",
            mime="text/csv",
        )
