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
            padding-top: 0rem !important;
            padding-right: 1.75rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 1.75rem !important;
        }

        .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {
            position: fixed !important;
            top: 0 !important;
            left: 228px !important;
            right: 0 !important;
            z-index: 1000 !important;
            background: #ffffff !important;
            border-bottom: 1px solid #e6ebf3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0.6rem 1.75rem 0.55rem 1.75rem !important;
            margin: 0 !important;
            min-height: 58px !important;
            align-items: center !important;
        }

        .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type > div {
            width: 100% !important;
        }

        .fixed-topbar-offset {
            display: block;
            width: 100%;
            height: 48px;
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
            padding-top: 0.35rem !important;
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
            margin-top: 0 !important;
            margin-bottom: 1.9rem;
            padding: 0.05rem 0.55rem 0 0.55rem;
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
            margin: 0.15rem 0 0.85rem 0.55rem;
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
            padding: 0 1rem !important;
            font-weight: 700 !important;
            font-size: 16px !important;
            line-height: 1 !important;
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

        section[data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] .stButton button svg {
            width: 16px !important;
            height: 16px !important;
            min-width: 16px !important;
            min-height: 16px !important;
            flex-shrink: 0 !important;
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

        .topbar-role-wrap {
            justify-content: flex-end;
        }

        .topbar-bell-wrap,
        .topbar-profile-wrap {
            justify-content: center;
        }

        .topbar-divider-box {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 40px;
        }

        .topbar-role-wrap [data-testid="stPopover"] {
            width: 100% !important;
        }

        .topbar-role-wrap [data-testid="stPopover"] > div {
            width: 100% !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button {
            width: 100% !important;
            white-space: nowrap !important;
        }

        .dashboard-action-btn .stButton,
        .dashboard-action-btn [data-testid="stPopover"] {
            width: 100% !important;
        }

        .dashboard-action-btn .stButton button,
        .dashboard-action-btn div[data-testid="stPopover"] > div > button {
            white-space: nowrap !important;
        }

        .topbar-role-wrap,
        .topbar-bell-wrap,
        .topbar-profile-wrap {
            min-height: 40px;
            display: flex;
            align-items: center;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        .topbar-divider-box {
            border-left: 1px solid #e1e7f0;
            padding-left: 0.85rem;
            height: 42px;
        }

        div[data-testid="stPopover"] > div > button {
            min-height: 40px !important;
            height: 40px !important;
            white-space: nowrap !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            color: #172033 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            font-weight: 600 !important;
            padding: 0 0.9rem !important;
        }

        div[data-testid="stPopover"] > div > button p {
            margin: 0 !important;
            font-size: 14px !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
        }

        .dashboard-filter-btn div[data-testid="stPopover"] > div > button {
            min-width: 120px !important;
            justify-content: center !important;
        }

        .dashboard-generate-btn .stButton > button {
            min-width: 140px !important;
            justify-content: center !important;
        }

        .role-switch-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin: 0 0 0.65rem 0;
        }

        .role-switch-menu .stButton {
            width: 100% !important;
        }

        .role-switch-menu .stButton button {
            width: 100% !important;
            justify-content: flex-start !important;
            min-height: 34px !important;
            height: 34px !important;
            border-radius: 10px !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            padding: 0 0.7rem !important;
            font-size: 15px !important;
            font-weight: 500 !important;
        }

        .role-switch-menu .stButton button p {
            font-size: 15px !important;
            margin: 0 !important;
        }

        .role-switch-menu .stButton button[kind="primary"] {
            background: #ffffff !important;
            color: #172033 !important;
        }

        .role-switch-menu .stButton button[kind="primary"]:hover {
            background: #f6f8fb !important;
            color: #172033 !important;
        }

        .role-switch-menu .stButton button[kind="secondary"] {
            background: #eef2f7 !important;
            color: #0b2f6b !important;
            border-color: transparent !important;
        }

        .role-switch-menu .stButton button[kind="secondary"]:hover {
            background: #e8edf5 !important;
            color: #0b2f6b !important;
        }

        .role-switch-menu .stButton button [data-testid="stIconMaterial"],
        .role-switch-menu .stButton button svg {
            width: 15px !important;
            height: 15px !important;
            color: #0b2f6b !important;
        }

        div[data-testid="stPopoverContent"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 0.15rem !important;
            min-width: 198px !important;
        }

        div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            min-height: 42px !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            border: 1px solid #dbe4f0 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        .notification-pill {
            position: relative;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 12px;
            background: transparent;
            border: none;
            box-shadow: none;
            margin-top: 0;
        }

        .notification-icon {
            font-size: 1.05rem;
            line-height: 1;
            color: #475467;
        }

        .notification-badge {
            position: absolute;
            top: 1px;
            right: 2px;
            min-width: 17px;
            height: 17px;
            padding: 0 4px;
            border-radius: 999px;
            background: #f04438;
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }

        .profile-card {
            min-height: 40px;
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 0.65rem;
            padding: 0.2rem 0;
            border-radius: 12px;
            background: transparent;
            border: none;
            box-shadow: none;
            width: 100%;
        }

        .profile-avatar {
            width: 31px;
            height: 31px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: #0b2f6b;
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
            flex-shrink: 0;
        }

        .profile-details {
            min-width: 0;
            max-width: 125px;
        }

        .profile-name {
            color: #172033;
            font-size: 14px;
            line-height: 1.15;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .profile-chevron {
            color: #667085;
            font-size: 12px;
            line-height: 1;
            margin-left: 0.1rem;
        }

        .page-title {
            font-size: 2.25rem;
            line-height: 1.1;
            font-weight: 800;
            color: #13213d;
            margin: 0.2rem 0 0.25rem 0;
        }

        .page-subtitle {
            color: #6f7d93;
            font-size: 1rem;
            margin-bottom: 0.7rem;
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

        .claims-section-gap {
            height: 1.1rem;
        }

        .claims-table-card {
            background: transparent;
        }

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

            .block-container > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {
                left: 228px !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .fixed-topbar-offset {
                height: 52px;
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
