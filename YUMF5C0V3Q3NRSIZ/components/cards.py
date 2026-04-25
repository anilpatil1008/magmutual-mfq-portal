import html

import streamlit as st


KPI_ICON_CONFIG = {
    "Total Active Claims": {
        "icon_class": "kpi-icon-claims",
        "svg_path": "M14 2H6a2 2 0 0 0-2 2v16l4-3 4 3 4-3 4 3V8z M8 6h4 M8 10h8 M8 14h5",
    },
    "MFQ Generated": {
        "icon_class": "kpi-icon-generated",
        "svg_path": "M12 2 2 20h20L12 2z M12 8v5 M12 17h.01",
    },
    "Assigned": {
        "icon_class": "kpi-icon-assigned",
        "svg_path": "M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z",
    },
    "Approved": {
        "icon_class": "kpi-icon-approved",
        "svg_path": "M9 12l2 2 4-4 M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z",
    },
    "Rejected": {
        "icon_class": "kpi-icon-rejected",
        "svg_path": "m15 9-6 6 M9 9l6 6 M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z",
    },
}


DEFAULT_ICON = KPI_ICON_CONFIG["Total Active Claims"]


def render_kpi_card(title: str, value: int | str, icon: str, icon_class: str) -> str:
    safe_title = html.escape(str(title))
    safe_value = html.escape(str(value))

    return f"""
    <article class='kpi-card'>
        <div class='kpi-main'>
            <div class='kpi-label'>{safe_title}</div>
            <div class='kpi-value'>{safe_value}</div>
        </div>
        <div class='kpi-icon-wrap {icon_class}'>
            <svg class='kpi-icon' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>
                <path d='{icon}' stroke='currentColor' stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'></path>
            </svg>
        </div>
    </article>
    """


def render_kpi_cards(metrics: dict) -> None:
    cards_html = []
    for title, value in metrics.items():
        icon_cfg = KPI_ICON_CONFIG.get(title, DEFAULT_ICON)
        cards_html.append(
            render_kpi_card(
                title=title,
                value=value,
                icon=icon_cfg["svg_path"],
                icon_class=icon_cfg["icon_class"],
            )
        )

    grid_html = f"""
    <section class='kpi-grid' aria-label='Dashboard KPIs'>
        {''.join(cards_html)}
    </section>
    """
    st.markdown(grid_html, unsafe_allow_html=True)


def render_claim_header(claim: dict) -> None:
    st.markdown(
        f"""
        <div class='claim-header-card'>
            <div class='claim-title'>Claim {claim['CLAIM_ID']} - {claim['PATIENT_NAME']}</div>
            <div class='claim-grid'>
                <div><b>Defendant:</b> {claim['DEFENDANT_NAME']}</div>
                <div><b>File Number:</b> {claim['FILE_NUMBER']}</div>
                <div><b>Specialty:</b> {claim['SPECIALTY']}</div>
                <div><b>Date Requested:</b> {claim['DATE_REQUESTED']}</div>
                <div><b>Contact:</b> {claim['CONTACT_DETAILS']}</div>
                <div><b>Status:</b> {claim['STATUS']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
