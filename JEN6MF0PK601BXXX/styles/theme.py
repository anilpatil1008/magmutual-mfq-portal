import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: #f5f7fb;
            color: #172033;
            font-family: Inter, "Segoe UI", Arial, sans-serif;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0 !important;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        html, body, [data-testid="stAppViewContainer"] {
            scroll-behavior: smooth;
        }

        .block-container {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-right: 1.5rem !important;
            padding-bottom: 1.25rem !important;
            padding-left: 1.5rem !important;
        }

        section.main > div {
            padding-top: 0 !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e6ebf3;
            width: 228px !important;
            min-width: 228px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 0.1rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.8rem !important;
        }

        div[data-testid="stSidebarHeader"] {
            min-height: 24px !important;
            height: 24px !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stSidebarHeader"] > div {
            min-height: 24px !important;
            height: 24px !important;
            align-items: flex-start !important;
        }

        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Sidebar collapse fix */
        section[data-testid="stSidebar"][aria-expanded="false"] {
            width: 0 !important;
            min-width: 0 !important;
            border-right: none !important;
        }

        section[data-testid="stSidebar"][aria-expanded="false"] + div,
        section[data-testid="stSidebar"][aria-expanded="false"] ~ div {
            margin-left: 0 !important;
            left: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        section[data-testid="stSidebar"][aria-expanded="false"] ~ div .block-container {
            padding-left: 1.5rem !important;
        }

        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: 228px !important;
            min-width: 228px !important;
        }

        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 0 !important;
            margin-bottom: 1.35rem;
            padding: 0 0.5rem 0.05rem 0.5rem;
        }

        .brand-mark {
            width: 28px;
            min-width: 28px;
            height: 38px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .brand-mark-svg {
            width: 100%;
            height: 100%;
            display: block;
            filter: drop-shadow(0 2px 4px rgba(11, 47, 107, 0.16));
        }

        .brand-text-wrap {
            min-width: 0;
            display: flex;
            align-items: center;
        }

        .brand-text {
            font-size: 1.62rem;
            line-height: 1;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #0b2f6b;
            white-space: nowrap;
        }

        .nav-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin: 0.1rem 0 0.85rem 0.55rem;
        }

        section[data-testid="stSidebar"] .stButton {
            width: 100% !important;
        }

        section[data-testid="stSidebar"] .stButton button {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            border-radius: 12px !important;
            min-height: 44px !important;
            height: 44px !important;
            padding: 0 0.7rem !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            text-align: left !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            margin-bottom: 0.55rem !important;
        }

        section[data-testid="stSidebar"] .stButton button > div {
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 0.55rem !important;
        }

        section[data-testid="stSidebar"] .stButton button p {
            margin: 0 !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            line-height: 1.1 !important;
        }

        section[data-testid="stSidebar"] .stButton button[kind="primary"] {
            background: #0b2f6b !important;
            color: #ffffff !important;
        }

        section[data-testid="stSidebar"] .stButton button[kind="secondary"] {
            background: #ffffff !important;
            color: #2f3b52 !important;
        }

        section[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover {
            background: #f2f6fc !important;
            border-color: #dbe4f0 !important;
            color: #0b2f6b !important;
        }

        /* Topbar */
        .element-container:has(.topbar-inline-card) {
            margin-top: -0.35rem !important;
            margin-bottom: 0 !important;
        }

        .topbar-inline-card {
            background: #ffffff;
            border-bottom: 1px solid #e6ebf3;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            padding: 0.12rem 0.95rem 0.4rem 0.95rem;
            margin: 0 -1.5rem 0.6rem -1.5rem;
        }

        .topbar-role-wrap div[data-testid="stSelectbox"] {
            width: 190px !important;
            min-width: 190px !important;
            max-width: 190px !important;
            margin-left: auto !important;
        }

        .topbar-role-wrap div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            min-height: 40px !important;
            height: 40px !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        .topbar-role-wrap div[data-testid="stSelectbox"] div[role="button"] {
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #172033 !important;
        }

        div[role="listbox"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 6px !important;
            background: #ffffff !important;
        }

        div[role="option"] {
            border-radius: 10px !important;
            min-height: 40px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #172033 !important;
            padding: 8px 12px !important;
        }

        div[role="option"][aria-selected="true"] {
            background: #edf3ff !important;
            color: #0b2f6b !important;
        }

        div[role="option"]:hover {
            background: #f5f8fc !important;
        }

        div[data-testid="stPopover"] > div > button {
            min-height: 40px !important;
            height: 40px !important;
            border-radius: 12px !important;
        }

        /* Page title */
        .page-title {
            font-size: 2.25rem;
            line-height: 1.1;
            font-weight: 800;
            color: #13213d;
            margin: 0 0 0.25rem 0;
        }

        .page-subtitle {
            color: #6f7d93;
            font-size: 1rem;
            margin-bottom: 0;
        }

        /* Metric cards */
        .metric-card {
            background: #ffffff;
            border: 1px solid #e3e9f2;
            border-radius: 18px;
            padding: 1.25rem 1.3rem;
            min-height: 148px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .metric-card-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
        }

        .metric-label {
            color: #5e6c84;
            font-size: 15px;
            line-height: 1.35;
            white-space: pre-line;
        }

        .metric-icon {
            width: 56px;
            height: 56px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 23px;
            font-weight: 900;
            flex-shrink: 0;
            background: #edf3ff;
            color: #3366ff;
        }

        .metric-icon.icon-clock {
            background: #eeefff;
            color: #5b5ce6;
        }

        .metric-icon.icon-success {
            background: #e8f7ee;
            color: #0c8b58;
        }

        .metric-icon.icon-danger {
            background: #fdeaea;
            color: #d92d20;
        }

        .metric-value {
            color: #111b34;
            font-size: 2rem;
            line-height: 1;
            font-weight: 800;
            margin-top: 0.6rem;
        }

        .metric-subtitle {
            color: #11a75c;
            font-size: 13px;
            font-weight: 700;
            margin-top: 0.35rem;
            min-height: 18px;
        }

        .metric-subtitle-empty {
            color: transparent;
        }

        /* Section cards */
        .section-card,
        .content-card,
        .claim-header-card {
            background: #ffffff;
            border: 1px solid #e3e9f2;
            border-radius: 18px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }

        .section-card {
            margin-top: 1.6rem;
            padding: 1.35rem 1.4rem 0.6rem 1.4rem;
        }

        .content-card,
        .claim-header-card {
            padding: 1.2rem;
            margin-top: 1rem;
        }

        .section-title {
            color: #16233b;
            font-size: 1.65rem;
            font-weight: 800;
            line-height: 1.15;
        }

        .section-title-sm {
            font-size: 1.9rem;
            margin-bottom: 0.15rem;
        }

        .section-subtitle {
            color: #6f7d93;
            font-size: 14px;
            margin-top: 0.25rem;
        }

        .claims-section-gap {
            height: 1.1rem;
        }

        /* Table / bordered blocks */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #e3e9f2 !important;
            border-radius: 18px !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0.6rem 0.95rem 0.35rem 0.95rem !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background: transparent !important;
        }

        div[data-testid="stTextInput"] input {
            height: 42px !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding-left: 0.85rem !important;
        }

        div[data-testid="stMultiSelect"] > div[data-baseweb="select"],
        div[data-testid="stPopover"] button,
        .stPopover button {
            border-radius: 12px !important;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stPopover button {
            height: 42px !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }

        section.main .stButton > button[kind="primary"] {
            background: #0b2f6b !important;
            color: #ffffff !important;
            border: 1px solid #0b2f6b !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        section.main .stButton > button[kind="primary"]:hover {
            background: #123c83 !important;
            border-color: #123c83 !important;
            color: #ffffff !important;
        }

        section.main .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #d92d20 !important;
            border: 1px solid #f2b7b3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        section.main .stButton > button[kind="secondary"]:hover {
            background: #fff5f5 !important;
            border-color: #e98b83 !important;
            color: #c81e1e !important;
        }


        .topbar-spacer {
            min-height: 1px;
        }

        .topbar-inline-card [data-testid="column"] {
            display: flex;
            align-items: center;
            justify-content: flex-end;
        }

        .topbar-inline-card [data-testid="column"]:first-child {
            justify-content: flex-start;
        }

        .topbar-bell-wrap,
        .topbar-profile-wrap {
            width: 100%;
            display: flex;
            justify-content: flex-end;
        }

        .topbar-bell-wrap div[data-testid="stPopover"] > div > button {
            min-width: 64px !important;
            padding: 0 0.8rem !important;
        }

        .topbar-profile-wrap div[data-testid="stPopover"] > div > button {
            min-width: 150px !important;
            padding: 0 0.85rem !important;
        }

        .page-header-block {
            margin: 0 !important;
            padding: 0 !important;
        }

        .dashboard-header-wrap {
            margin-bottom: 0.55rem;
        }

        .dashboard-toolbar {
            padding-top: 0.15rem;
        }

        .dashboard-action-btn {
            width: 100%;
        }

        .dashboard-action-btn .stPopover,
        .dashboard-action-btn .stButton {
            width: 100%;
        }

        .dashboard-action-btn .stPopover > div,
        .dashboard-action-btn .stButton > div {
            width: 100%;
        }

        .dashboard-action-btn button {
            width: 100% !important;
            white-space: nowrap !important;
        }

        .claims-page-wrap {
            margin-bottom: 0.35rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
            min-width: 0;
        }

        @media (max-width: 1024px) {
            .block-container {
                padding-left: 0.95rem !important;
                padding-right: 0.95rem !important;
            }

            .topbar-inline-card {
                padding-top: 0.08rem;
                padding-bottom: 0.45rem;
            }

            .topbar-role-wrap div[data-testid="stSelectbox"] {
                width: 170px !important;
                min-width: 170px !important;
                max-width: 170px !important;
            }

            .page-title {
                font-size: 1.95rem;
            }
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }

            .topbar-inline-card {
                margin-left: -0.8rem;
                margin-right: -0.8rem;
                padding-left: 0.8rem;
                padding-right: 0.8rem;
            }

            .page-title {
                font-size: 1.7rem;
            }

            .page-subtitle {
                font-size: 0.95rem;
            }

            .metric-card {
                min-height: 132px;
                padding: 1rem 1rem;
            }

            .metric-value {
                font-size: 1.75rem;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding-left: 0.7rem !important;
                padding-right: 0.7rem !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] .table-head {
                font-size: 11px !important;
            }

            .claim-person-name,
            .claim-file-no,
            .table-value,
            .chip {
                font-size: 12px !important;
            }

            .claim-subtext {
                font-size: 11px !important;
                line-height: 1.25 !important;
            }
        }

        @media (max-width: 1366px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .topbar-inline-card {
                margin-left: -1rem;
                margin-right: -1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )