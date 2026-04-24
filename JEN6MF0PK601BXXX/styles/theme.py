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

        section.main {
            background: #f3f5f9 !important;
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

        .st-emotion-cache-b1pznn {
            gap: 0 !important;
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
            padding-left: 0.42rem !important;
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
        .topbar-host,
        .topbar-role-marker,
        .topbar-bell-marker,
        .topbar-profile-marker,
        .topbar-spacer {
            display: none !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) {
            background: #ffffff !important;
            border-bottom: 1px solid #e6ebf3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            margin: 0 -1.5rem 0.45rem -1.5rem !important;
            padding: 0.06rem 1.5rem !important;
            gap: 0 !important;
            position: sticky;
            top: 0;
            z-index: 40;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) > div[data-testid="element-container"] {
            margin: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) > div[data-testid="element-container"]:has(.topbar-host) {
            display: none !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: center !important;
            justify-content: flex-end !important;
            gap: 0.85rem !important;
            min-height: 36px !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"] {
            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-end !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:first-child {
            flex: 1 1 14rem !important;
            min-width: 6rem !important;
            justify-content: flex-start !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="element-container"]:has(.topbar-role-marker),
        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="element-container"]:has(.topbar-bell-marker),
        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="element-container"]:has(.topbar-profile-marker) {
            display: none !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[data-testid="stSelectbox"] {
            width: clamp(204px, 21vw, 252px) !important;
            min-width: 204px !important;
            max-width: 252px !important;
            margin-left: auto !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[data-baseweb="select"] {
            min-height: 40px !important;
            height: 40px !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[role="button"] {
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #172033 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[role="listbox"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 6px !important;
            background: #ffffff !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[role="option"] {
            border-radius: 10px !important;
            min-height: 40px !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            color: #172033 !important;
            padding: 8px 12px !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[role="option"][aria-selected="true"] {
            background: #edf3ff !important;
            color: #0b2f6b !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[role="option"]:hover {
            background: #f5f8fc !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="stPopover"] > div > button {
            min-height: 40px !important;
            height: 40px !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker),
        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) {
            flex: 0 0 auto !important;
            flex-shrink: 0 !important;
            min-width: fit-content !important;
            padding-left: 0.65rem !important;
            border-left: 1px solid #edf1f5 !important; margin-left: 0.18rem !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker) div[data-testid="stPopover"] > div > button {
            width: 88px !important;
            min-width: 88px !important;
            padding: 0 0.7rem !important;
            justify-content: center !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) {
            margin-left: auto !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) div[data-testid="stPopover"] > div > button {
            min-width: clamp(182px, 21vw, 220px) !important;
            max-width: clamp(182px, 21vw, 220px) !important;
            padding: 0 1rem !important;
            justify-content: flex-start !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"] > div[data-testid="stVerticalBlock"] {
            gap: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"] [data-testid="element-container"] {
            margin: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"] [data-testid="stSelectbox"],
        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"] [data-testid="stPopover"] {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) {
            padding-right: 0.1rem !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker) div[data-testid="stPopover"] > div > button {
            font-size: 16px !important;
        }

        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) div[data-testid="stPopover"] > div > button,
        div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[role="button"] {
            font-size: 15px !important;
        }

        @media (max-width: 1366px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) {
                margin-left: -1rem !important;
                margin-right: -1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }

        @media (max-width: 980px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:first-child {
                display: none !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="stHorizontalBlock"] {
                justify-content: flex-end !important;
                row-gap: 0.45rem !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) {
                order: 1 !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker) {
                order: 2 !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) {
                order: 3 !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker),
            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) {
                border-left: none !important;
                margin-left: 0 !important;
                padding-left: 0 !important;
            }
        }

        @media (max-width: 640px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) {
                padding-top: 0.4rem !important;
                padding-bottom: 0.4rem !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="stHorizontalBlock"] {
                justify-content: stretch !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker),
            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) {
                flex: 1 1 100% !important;
                width: 100% !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[data-testid="stSelectbox"],
            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) div[data-testid="stPopover"] > div > button {
                width: 100% !important;
                min-width: 0 !important;
                max-width: none !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-bell-marker) {
                margin-left: auto !important;
            }
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

        /* Recent claims table card */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.claims-table-shell) {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.05) !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        .claims-table-shell {
            padding: 0 !important;
        }

        .claims-table-shell .section-title-sm {
            font-size: 2rem;
            margin: 0;
            line-height: 1.2;
            padding: 1.35rem 1.55rem 0 1.55rem;
        }

        .claims-table-shell .section-subtitle {
            margin-top: 0.25rem;
            margin-bottom: 0;
            padding: 0 1.55rem 1.05rem 1.55rem;
        }

        .claims-table-shell .stTextInput {
            display: flex;
            justify-content: flex-end;
            padding: 1.1rem 1.55rem 0.85rem 0.6rem;
        }

        .claims-table-shell .stTextInput > div {
            width: min(100%, 340px);
        }

        .claims-table-shell .stTextInput input {
            height: 40px !important;
            border-radius: 10px !important;
            border: 1px solid #d7deea !important;
            background: #f9fbff !important;
            box-shadow: none !important;
            padding-left: 0.9rem !important;
            color: #314158 !important;
        }

        .table-divider {
            width: 100%;
            border-top: 1px solid #e9edf3;
        }

        .table-divider-tight {
            margin-top: 0;
        }

        .table-divider-row {
            margin: 0;
        }

        .claims-table-shell .table-head {
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.02em;
            line-height: 1.25;
            padding: 0.75rem 0;
        }

        .claims-table-shell .table-head-right {
            text-align: right;
            padding-right: 0.35rem;
        }

        .claims-table-shell div[data-testid="stHorizontalBlock"] {
            gap: 0.35rem;
        }

        .claim-file-no,
        .claim-person-name,
        .table-value {
            color: #13213d;
            font-size: 16px;
            line-height: 1.35;
        }

        .claim-file-no,
        .claim-person-wrap,
        .claims-table-shell .badge,
        .confidence-chip,
        .table-action-inline {
            padding: 0.45rem 0;
        }

        .claim-file-no {
            font-weight: 600;
        }

        .claim-person-name {
            font-weight: 500;
        }

        .claim-subtext {
            color: #6f7d93;
            font-size: 13px;
            line-height: 1.35;
            margin-top: 0.1rem;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            border: 1px solid transparent;
            font-size: 12px;
            font-weight: 600;
            line-height: 1;
            padding: 0.3rem 0.62rem;
            white-space: nowrap;
        }

        .badge-blue { background: #dbeafe; border-color: #bfd7ff; color: #0d4fd8; }
        .badge-indigo { background: #e6e9ff; border-color: #cdd3ff; color: #3747b8; }
        .badge-green { background: #dff7ea; border-color: #beeacd; color: #117a4c; }
        .badge-red { background: #fde8ea; border-color: #f9c9cf; color: #bf1d3d; }
        .badge-slate { background: #edf1f7; border-color: #dce3ee; color: #52627a; }

        .badge-red-soft { background: #fde8ea; border-color: #f8c7ce; color: #c41e3a; }
        .badge-amber { background: #fff0df; border-color: #f8d5a8; color: #b86214; }
        .badge-blue-soft { background: #e6f0ff; border-color: #c7daff; color: #2158c9; }

        .confidence-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            border-radius: 999px;
            font-size: 14px;
            font-weight: 700;
            line-height: 1;
            padding: 0.33rem 0.7rem;
        }

        .confidence-dot {
            font-size: 16px;
            line-height: 0;
        }

        .confidence-green { background: #daf3e6; color: #0c8b58; }
        .confidence-amber { background: #f9e7b4; color: #b46813; }
        .confidence-red { background: #f9d8dc; color: #c72b40; }

        .table-action-inline .stButton > div {
            display: flex;
            justify-content: flex-end;
        }

        .table-action-inline .stButton > div > button {
            min-height: 32px !important;
            height: 32px !important;
            border-radius: 8px !important;
            padding: 0 0.25rem !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            color: #0b2f6b !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            justify-content: flex-end !important;
        }

        .table-action-inline .stButton > div > button:hover {
            color: #123c83 !important;
            background: #f5f8ff !important;
        }

        .table-regenerate-btn .stButton > div > button {
            min-height: 36px !important;
            height: 36px !important;
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
            margin-top: 0 !important;
            margin-bottom: 0.35rem;
        }

        div[data-testid="stVerticalBlock"]:has(.dashboard-page-wrap) {
            background: #f6f7fb !important;
            min-height: calc(100vh - 84px);
        }

        .dashboard-page-wrap {
            display: none !important;
        }

        .dashboard-toolbar {
            padding-top: 0 !important;
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


        @media (max-width: 1366px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) {
                margin-left: -1rem !important;
                margin-right: -1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        }

        @media (max-width: 1200px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-role-marker) div[data-testid="stSelectbox"] {
                width: 182px !important;
                min-width: 182px !important;
                max-width: 182px !important;
            }

            div[data-testid="stVerticalBlock"]:has(.topbar-host) div[data-testid="column"]:has(.topbar-profile-marker) div[data-testid="stPopover"] > div > button {
                min-width: 160px !important;
                max-width: 160px !important;
            }
        }

        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"]:has(.topbar-host) {
                margin-left: -0.8rem !important;
                margin-right: -0.8rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
        }

        /* Claim detail / MFQ review */
        .review-page {
            display: none;
        }

        .review-breadcrumb {
            display: none;
        }

        div[data-testid="element-container"]:has(.review-breadcrumb) + div[data-testid="element-container"] div[data-testid="stButton"] {
            margin-bottom: 0.45rem;
        }

        div[data-testid="element-container"]:has(.review-breadcrumb) + div[data-testid="element-container"] div[data-testid="stButton"] button {
            min-height: 26px !important;
            height: 26px !important;
            border: 0 !important;
            border-radius: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            color: #6b7280 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            justify-content: flex-start !important;
            box-shadow: none !important;
        }

        div[data-testid="element-container"]:has(.review-breadcrumb) + div[data-testid="element-container"] div[data-testid="stButton"] button:hover {
            color: #1f2937 !important;
            background: transparent !important;
            text-decoration: underline !important;
        }

        .claim-header-card {
            margin-top: 0.2rem;
            padding: 1.45rem 1.7rem 1.3rem 1.7rem;
            border: 1px solid #dde4ee;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.06);
        }

        .claim-header-top {
            margin-bottom: 0.35rem;
        }

        .claim-title-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.7rem;
        }

        .claim-title {
            font-size: 2.8rem;
            line-height: 1.1;
            font-weight: 800;
            color: #13213d;
            letter-spacing: -0.02em;
        }

        .claim-vs {
            color: #5f6b80;
            font-weight: 600;
            font-size: 0.7em;
            margin: 0 0.2rem;
        }

        .claim-badge-wrap {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            transform: translateY(2px);
        }

        .claim-badge .inline-chip {
            border-radius: 8px;
        }

        .inline-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 8px;
            padding: 0.25rem 0.58rem;
            font-size: 12px;
            font-weight: 700;
            line-height: 1;
        }

        .claim-meta-grid {
            margin-top: 0.7rem;
        }

        .claim-meta-item {
            padding-top: 0.1rem;
        }

        .claim-meta-label {
            color: #667085;
            font-size: 12px;
            letter-spacing: 0.09em;
            font-weight: 600;
            margin-bottom: 0.22rem;
        }

        .claim-meta-value {
            color: #1f2937;
            font-size: 1.55rem;
            font-weight: 500;
            line-height: 1.25;
        }

        .claim-meta-value a {
            color: #2563eb;
            text-decoration: underline;
        }

        div[data-testid="column"]:has(.claim-actions) {
            display: flex;
            align-items: flex-start;
            justify-content: flex-end;
            padding-top: 0.15rem;
        }

        div[data-testid="column"]:has(.claim-actions) div[data-testid="stButton"] > div {
            display: flex;
            justify-content: flex-end;
        }

        div[data-testid="column"]:has(.claim-actions) button {
            min-height: 44px !important;
            height: 44px !important;
            min-width: 142px !important;
            padding: 0 1.1rem !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
        }

        div[data-testid="column"]:has(.btn-primary) button {
            border: 1px solid #0b3c86 !important;
            color: #0b3c86 !important;
            background: #ffffff !important;
        }

        div[data-testid="column"]:has(.btn-success) button {
            border: 1px solid #10a25f !important;
            background: #10a25f !important;
            color: #ffffff !important;
        }

        .claim-tabs-card {
            margin-top: 0.8rem;
            padding: 0 !important;
            overflow: hidden;
        }

        div[data-testid="stHorizontalBlock"]:has(input[id*="claim_detail_tab"]) {
            border-bottom: 1px solid #e4eaf3;
            margin-top: 0 !important;
        }

        div[data-testid="stRadio"]:has(input[id*="claim_detail_tab"]) label p {
            font-weight: 600 !important;
            color: #344054 !important;
        }

        div[data-testid="stRadio"]:has(input[id*="claim_detail_tab"]) [role="radiogroup"] {
            gap: 0 !important;
            width: 100%;
            display: flex;
            flex-wrap: wrap;
        }

        div[data-testid="stRadio"]:has(input[id*="claim_detail_tab"]) [role="radio"] {
            border-radius: 0 !important;
            border-bottom: 2px solid transparent !important;
            min-height: 52px !important;
            padding: 0.45rem 0.95rem !important;
        }

        div[data-testid="stRadio"]:has(input[id*="claim_detail_tab"]) [role="radio"][aria-checked="true"] {
            border-bottom-color: #0b2f6b !important;
            background: #f8fbff !important;
        }

        .mfq-title-card {
            margin-top: 0.95rem;
            margin-bottom: 0.7rem;
        }

        .mfq-title {
            font-size: 2rem;
            font-weight: 800;
            color: #0f2342;
            line-height: 1.1;
        }

        .mfq-subtitle {
            color: #667085;
            margin-top: 0.25rem;
            font-size: 0.95rem;
        }

        .confidence-card {
            background: #fffdf6;
            border-color: #f1d085;
        }

        .confidence-warning-box {
            border: 1px solid #f1d085;
            border-radius: 10px;
            background: #fffefb;
            padding: 0.25rem 0.55rem;
            margin-top: 0.45rem;
        }

        .confidence-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.8rem;
        }

        .confidence-title {
            font-size: 1.2rem;
            font-weight: 800;
            color: #1f2937;
        }

        .confidence-right {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.6rem;
        }

        .confidence-guidance {
            background: #fff1d6;
            color: #b54708;
            border: 1px solid #f0cf9a;
            border-radius: 999px;
            padding: 0.3rem 0.7rem;
            font-size: 12px;
            font-weight: 700;
        }

        .confidence-overall {
            font-weight: 800;
            font-size: 1.9rem;
            color: #067647;
        }

        .section-confidence-box {
            background: #ffffff;
            border: 1px solid #ebf0f7;
            border-radius: 10px;
            padding: 0.5rem 0.65rem;
            margin-bottom: 0.45rem;
        }

        .section-confidence-top {
            display: flex;
            justify-content: space-between;
            gap: 0.5rem;
            color: #1d2939;
            font-size: 13px;
            margin-bottom: 0.2rem;
            font-weight: 600;
        }

        .section-confidence-track {
            width: 100%;
            border-radius: 999px;
            background: #edf2f8;
            height: 6px;
            overflow: hidden;
        }

        .section-confidence-fill {
            height: 100%;
            border-radius: 999px;
        }

        .confidence-notes {
            margin: 0.55rem 0 0.5rem 0.7rem;
            padding: 0;
            color: #475467;
            font-size: 13px;
        }

        .confidence-notes .danger { color: #d92d20; font-weight: 700; }
        .confidence-notes .warn { color: #b54708; font-weight: 700; }

        .synopsis-title {
            color: #1f2a44;
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.7rem;
        }

        .synopsis-card {
            background: #f7fafc;
        }

        .synopsis-block {
            color: #344054;
            font-size: 0.98rem;
            margin-bottom: 0.8rem;
            line-height: 1.5;
        }

        .synopsis-label {
            color: #475467;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin-bottom: 0.2rem;
        }

        .section-nav-card .stButton > div > button {
            justify-content: flex-start !important;
            margin-bottom: 0.3rem !important;
            border: 1px solid #d5deeb !important;
            background: #f8fbff !important;
            color: #0b2f6b !important;
            font-weight: 700 !important;
        }

        .section-nav-btn { display: none; }

        .eval-shell {
            padding: 0 !important;
            overflow: hidden;
        }

        .eval-header {
            background: #f8fafc;
            border-bottom: 1px solid #e4eaf3;
            font-size: 1.1rem;
            font-weight: 800;
            color: #0b2f6b;
            padding: 0.9rem 1.1rem;
        }

        .eval-shell .stButton > div > button {
            justify-content: space-between !important;
            background: #f8fafc !important;
            border: 1px solid #dde4ee !important;
            margin: 0.85rem 1rem 0.25rem 1rem !important;
            color: #0f172a !important;
            font-weight: 700 !important;
            min-height: 56px !important;
        }

        .question-card {
            border: 1px solid #e4eaf3;
            border-radius: 12px;
            background: #ffffff;
            margin: 0.45rem 1rem 1rem 1rem;
            padding: 0.8rem 0.85rem;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }

        .score-chip {
            font-size: 12px;
            font-weight: 700;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            padding: 0.2rem 0.5rem;
            white-space: nowrap;
        }

        .question-card textarea {
            background: #f8fafc !important;
        }

        @media (max-width: 1200px) {
            .claim-title { font-size: 2.2rem; }
            .mfq-title { font-size: 1.6rem; }
            .eval-header { font-size: 1.35rem; }
        }

        @media (max-width: 768px) {
            .claim-header-card {
                padding: 1rem 0.95rem;
            }
            .claim-title { font-size: 1.65rem; }
            .claim-badge-wrap {
                transform: none;
            }
            .confidence-overall { font-size: 1.4rem; }
            .content-card { padding: 0.85rem; }
            .question-card { margin-left: 0.55rem; margin-right: 0.55rem; }
            div[data-testid="column"]:has(.claim-actions) {
                justify-content: flex-start;
                margin-top: 0.45rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
