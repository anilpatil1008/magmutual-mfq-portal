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
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        .block-container {
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-right: 1.75rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 1.75rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 1rem !important;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e6ebf3;
            width: 228px !important;
            min-width: 228px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.8rem !important;
        }


        div[data-testid="stSidebarNav"] {
            display: none !important;
        }


        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 2rem;
            padding: 0.2rem 0.55rem 0 0.55rem;
            font-size: 1.9rem;
            font-weight: 800;
            color: #0b2f6b;
        }

        .brand-drop {
            width: 18px;
            height: 30px;
            background: #0b2f6b;
            border-radius: 50% 50% 50% 50% / 65% 65% 35% 35%;
            display: inline-block;
        }

        .nav-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin: 0.2rem 0 0.8rem 0.55rem;
        }

        section[data-testid="stSidebar"] .stButton button {
            justify-content: flex-start !important;
            border-radius: 10px !important;
            height: 44px !important;
            padding: 0 0.9rem !important;
            font-weight: 700 !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            margin-bottom: 0.35rem !important;
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

        section[data-testid="stSidebar"] .stButton button[kind="primary"] {
            background: #0b2f6b !important;
            color: #ffffff !important;
        }

        .topbar-spacer {
            height: 1px;
        }

        div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            min-height: 42px !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            border: 1px solid #dbe4f0 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        .notification-pill {
            min-height: 42px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.35rem;
            padding: 0 0.85rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid #dbe4f0;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            margin-top: 1px;
        }

        .notification-icon {
            font-size: 1rem;
            line-height: 1;
        }

        .notification-count {
            font-size: 0.9rem;
            font-weight: 800;
            color: #172033;
        }

        .profile-card {
            min-height: 42px;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.45rem 0.7rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid #dbe4f0;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }

        .profile-avatar {
            width: 34px;
            height: 34px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #0b2f6b;
            color: #ffffff;
            font-size: 13px;
            font-weight: 800;
            flex-shrink: 0;
        }

        .profile-details {
            min-width: 0;
        }

        .profile-name {
            color: #172033;
            font-size: 14px;
            line-height: 1.15;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .profile-email {
            color: #6f7d93;
            font-size: 12px;
            line-height: 1.2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .page-title {
            font-size: 2.25rem;
            line-height: 1.1;
            font-weight: 800;
            color: #13213d;
            margin: 1rem 0 0.35rem 0;
        }

        .page-subtitle {
            color: #6f7d93;
            font-size: 1rem;
            margin-bottom: 0.9rem;
        }

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

        section.main .stButton > button[kind="tertiary"] {
            background: transparent !important;
            color: #0b2f6b !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 0.25rem !important;
            height: 32px !important;
            min-height: 32px !important;
            justify-content: flex-end !important;
            text-align: right !important;
            font-weight: 700 !important;
        }

        section.main .stButton > button[kind="tertiary"]:hover {
            background: transparent !important;
            color: #123c83 !important;
            border: none !important;
            box-shadow: none !important;
            text-decoration: underline !important;
        }


        .table-divider {
            width: calc(100% + 2.8rem);
            margin: 1rem -1.4rem;
            border-top: 1px solid #edf1f7;
        }

        .table-divider-tight {
            margin-top: 0.7rem;
            margin-bottom: 0.55rem;
        }

        .table-divider-row {
            margin-top: 0.85rem;
            margin-bottom: 0.85rem;
        }

        .table-head {
            color: #667085;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.02em;
            padding-bottom: 0.15rem;
        }

        .table-head-right {
            text-align: right;
        }

        .claim-file-no,
        .table-value {
            color: #172033;
            font-size: 14px;
            line-height: 1.4;
        }

        .date-value {
            color: #4b5565;
            font-weight: 500;
        }

        .claim-file-no,
        .claim-person-name {
            font-weight: 700;
        }

        .claim-person-wrap {
            padding-right: 0.35rem;
        }

        .claim-subtext {
            color: #6f7d93;
            font-size: 13px;
            line-height: 1.45;
            margin-top: 0.12rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
        }

        .confidence-chip {
            min-width: 72px;
        }

        .chip-blue { background: #e7efff; color: #2457d6; }
        .chip-red { background: #fde7e7; color: #d92d20; }
        .chip-green { background: #e8f7ee; color: #067647; }
        .chip-yellow { background: #fff1d6; color: #b54708; }
        .chip-gray { background: #eef2f7; color: #475467; }

        .action-spacer {
            height: 42px;
        }

        .dashboard-action-wrap {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            min-height: 32px;
        }

        .dashboard-action-wrap .stButton {
            width: auto !important;
        }

        .dashboard-action-wrap .stButton > button {
            width: auto !important;
        }

        .claims-table-card div[data-testid="stTextInput"] input {
            padding-left: 2.2rem !important;
        }

        @media (max-width: 1100px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .metric-card {
                min-height: 134px;
                padding: 1rem;
            }

            .page-title {
                font-size: 1.9rem;
            }

            .section-title-sm {
                font-size: 1.55rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
