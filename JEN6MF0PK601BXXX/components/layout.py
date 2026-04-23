from __future__ import annotations

import html
import streamlit as st


NAV_ITEMS = [
    ("Dashboard", "Dashboard", ":material/dashboard:"),
    ("Claims", "Claims", ":material/description:"),
    ("Reports", "Reports", ":material/bar_chart:"),
]


def safe_str(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def initials(name: str) -> str:
    parts = [part for part in str(name).split() if part.strip()]
    return "".join(part[0].upper() for part in parts[:2]) or "U"


def _switch_page(page_name: str) -> None:
    st.session_state.page = page_name
    st.session_state.selected_claim_id = None
    st.rerun()


def render_sidebar(current_role: str) -> None:
    active_page = st.session_state.get("page", "Dashboard")

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-wrap">
                <div class="brand-mark" aria-hidden="true">
                    <svg viewBox="0 0 44 56" class="brand-mark-svg" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="brandDropGradient" x1="0" y1="0" x2="1" y2="1">
                                <stop offset="0%" stop-color="#0f4c97" />
                                <stop offset="100%" stop-color="#082f6b" />
                            </linearGradient>
                        </defs>
                        <path d="M22 2C13.2 10.4 7 18.7 7 30.1C7 43.1 16.9 53 29.9 53C38.7 53 43 47.1 43 39C43 27.1 33.9 13.2 22 2Z" fill="url(#brandDropGradient)"/>
                        <path d="M18.4 7.4C11.5 14.7 6.7 21.9 6.7 31.1C6.7 43.8 15.8 52.8 27.6 52.8C14.4 50.4 7.6 35.6 12.4 23.2C14.2 18.5 17 12.9 18.4 7.4Z" fill="#0a2555" opacity="0.95"/>
                    </svg>
                </div>
                <div class="brand-text-wrap">
                    <span class="brand-text">MagMutual</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-title">NAVIGATION</div>', unsafe_allow_html=True)

        for page_key, page_label, page_icon in NAV_ITEMS:
            clicked = st.button(
                page_label,
                icon=page_icon,
                use_container_width=True,
                key=f"nav_{page_key.lower()}",
                type="primary" if active_page == page_key else "secondary",
            )
            if clicked:
                _switch_page(page_key)

        if current_role == "ADMIN":
            clicked = st.button(
                "Admin",
                icon=":material/settings:",
                use_container_width=True,
                key="nav_admin",
                type="primary" if active_page == "Admin" else "secondary",
            )
            if clicked:
                _switch_page("Admin")


def _format_created_at(value) -> str:
    if value is None:
        return ""
    return str(value)[:10]


def render_topbar(
    display_name: str,
    email: str,
    role_items: list[dict[str, str]],
    current_role: str,
    notif_df,
) -> None:
    unread = 0
    if notif_df is not None and not notif_df.empty and "IS_READ" in notif_df.columns:
        unread = int((notif_df["IS_READ"] == False).sum())

    current_label = next(
        (item["label"] for item in role_items if item["key"] == current_role),
        current_role.replace("_", " ").title(),
    )

    role_labels = [item["label"] for item in role_items]
    current_index = next((i for i, item in enumerate(role_items) if item["key"] == current_role), 0)
    bell_label = f"🔔 {unread}" if unread else "🔔"
    profile_button_label = f"{initials(display_name)}  {display_name}"

    with st.container():
        st.markdown('<div class="topbar-host"></div>', unsafe_allow_html=True)
        spacer_col, role_col, bell_col, profile_col = st.columns([6.9, 2.2, 0.8, 2.35], gap="small", vertical_alignment="center")

        with spacer_col:
            st.markdown('<div class="topbar-spacer"></div>', unsafe_allow_html=True)

        with role_col:
            st.markdown('<div class="topbar-role-marker"></div>', unsafe_allow_html=True)
            selected_label = st.selectbox(
                "Role",
                role_labels,
                index=current_index,
                label_visibility="collapsed",
                key="topbar_role_select",
            )
            selected_item = next((item for item in role_items if item["label"] == selected_label), None)
            if selected_item and selected_item["key"] != current_role:
                st.session_state.role_key = selected_item["key"]
                st.rerun()

        with bell_col:
            st.markdown('<div class="topbar-bell-marker"></div>', unsafe_allow_html=True)
            with st.popover(bell_label):
                st.markdown("### Notifications")
                if notif_df is None or notif_df.empty:
                    st.write("No notifications available.")
                else:
                    for _, row in notif_df.head(8).iterrows():
                        claim_id = safe_str(row.get("CLAIM_ID", ""))
                        message = safe_str(row.get("MESSAGE", ""))
                        created_at = safe_str(_format_created_at(row.get("CREATED_AT", "")))
                        st.markdown(
                            f"**{claim_id}**  \n{message}  \n<small>{created_at}</small>",
                            unsafe_allow_html=True,
                        )

        with profile_col:
            st.markdown('<div class="topbar-profile-marker"></div>', unsafe_allow_html=True)
            with st.popover(profile_button_label):
                st.markdown(
                    f"""
                    **{safe_str(display_name)}**  
                    {safe_str(email)}  

                    {safe_str(current_label)}
                    """,
                    unsafe_allow_html=True,
                )


def render_page_title(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-title">{safe_str(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{safe_str(subtitle)}</div>', unsafe_allow_html=True)
