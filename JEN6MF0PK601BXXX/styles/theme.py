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

        .block-container {
            max-width: 100% !important;
            padding-top: 1rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            padding-bottom: 1.2rem !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        #MainMenu, footer {
            visibility: hidden;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e7ecf3;
            width: 230px !important;
            min-width: 230px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }

        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 24px;
            font-size: 22px;
            font-weight: 800;
            color: #0b2f6b;
        }

        .brand-drop {
            width: 16px;
            height: 28px;
            background: #0b2f6b;
            border-radius: 50% 50% 50% 50% / 62% 62% 38% 38%;
            display: inline-block;
        }

        .nav-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin: 18px 0 12px 0;
        }

        .topbar-card {
            background: #ffffff;
            border: 1px solid #e5ebf3;
            border-radius: 12px;
            padding: 8px 12px;
            min-height: 44px;
            display: flex;
            align-items: center;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }

        .topbar-user-name {
            font-weight: 800;
            color: #172033;
            font-size: 14px;
            line-height: 1.2;
            white-space: nowrap;
        }

        .topbar-user-email {
            font-size: 12px;
            color: #6f7d93;
            line-height: 1.2;
            white-space: nowrap;
        }

        .user-badge {
            display: inline-flex;
            width: 34px;
            height: 34px;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: #0b2f6b;
            color: white;
            font-weight: 800;
            flex-shrink: 0;
        }

        .page-title {
            font-size: 28px;
            font-weight: 800;
            color: #172033;
            margin-bottom: 4px;
        }

        .page-subtitle {
            color: #6f7d93;
            font-size: 14px;
            margin-bottom: 8px;
        }

        .metric-card {
            background: white;
            border: 1px solid #e5ebf3;
            border-radius: 18px;
            min-height: 145px;
            padding: 22px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        }

        .metric-icon {
            float: right;
            width: 56px;
            height: 56px;
            border-radius: 18px;
            background: #e9f0ff;
            color: #2f5bea;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: 900;
        }

        .metric-label {
            font-size: 15px;
            color: #667085;
            margin-bottom: 14px;
            line-height: 1.35;
        }

        .metric-value {
            font-size: 22px;
            font-weight: 800;
            color: #172033;
        }

        .metric-subtitle {
            color: #12b76a;
            font-size: 13px;
            font-weight: 700;
            margin-top: 10px;
        }

        .section-card {
            background: white;
            border: 1px solid #e5ebf3;
            border-radius: 18px;
            padding: 22px 22px 14px 22px;
            margin-top: 24px;
        }

        .content-card {
            background: white;
            border: 1px solid #e5ebf3;
            border-radius: 18px;
            padding: 18px;
            margin-top: 18px;
        }

        .claim-header-card {
            background: white;
            border: 1px solid #e5ebf3;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 18px;
        }

        .claims-search-wrap {
            background: #ffffff;
            border: 1px solid #dfe7f3;
            border-radius: 12px;
            padding: 4px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
        }

        .table-head {
            font-size: 12px;
            font-weight: 800;
            color: #667085;
            padding-bottom: 8px;
        }

        .row-divider {
            border: 0;
            border-top: 1px solid #edf1f7;
            margin: 12px -22px;
        }

        .chip {
            display: inline-block;
            border-radius: 999px;
            padding: 5px 11px;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
        }

        .chip-blue { background: #e7efff; color: #2457d6; }
        .chip-red { background: #fde7e7; color: #d92d20; }
        .chip-green { background: #e8f7ee; color: #067647; }
        .chip-yellow { background: #fff1d6; color: #b54708; }
        .chip-gray { background: #eef2f7; color: #475467; }

        .claim-subtext {
            color: #6f7d93;
            font-size: 13px;
            line-height: 1.45;
        }

        div[data-testid="stTextInput"] input {
            border-radius: 10px !important;
            height: 42px !important;
            border: none !important;
            box-shadow: none !important;
            background: white !important;
        }

        div[data-testid="stSelectbox"] > div,
        div[data-testid="stMultiSelect"] > div {
            border-radius: 10px !important;
        }

        .stButton > button {
            border-radius: 10px !important;
            height: 40px !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )