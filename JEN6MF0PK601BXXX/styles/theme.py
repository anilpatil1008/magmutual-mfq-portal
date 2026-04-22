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

        .block-container {
            max-width: 100% !important;
            padding-top: 0 !important;
            padding-right: 1.75rem !important;
            padding-bottom: 1.5rem !important;
            padding-left: 1.75rem !important;
        }

        section.main > div {
            padding-top: 0 !important;
        }

        html, body, [data-testid="stAppViewContainer"] {
            scroll-behavior: smooth;
        }

        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e6ebf3;
            width: 228px !important;
            min-width: 228px !important;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-top: 0 !important;
            padding-right: 0.8rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.8rem !important;
        }

        div[data-testid="stSidebarHeader"] {
            min-height: 26px !important;
            height: 26px !important;
            padding-top: 0.15rem !important;
            padding-bottom: 0 !important;
            margin-bottom: 0 !important;
        }

        div[data-testid="stSidebarHeader"] > div {
            min-height: 26px !important;
            height: 26px !important;
            align-items: flex-start !important;
        }

        div[data-testid="stSidebarNav"] {
            display: none !important;
        }

        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: -0.1rem !important;
            margin-bottom: 1.35rem;
            padding: 0 0.55rem 0.05rem 0.55rem;
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

        section[data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"],
        section[data-testid="stSidebar"] .stButton button svg {
            width: 16px !important;
            height: 16px !important;
            min-width: 16px !important;
            min-height: 16px !important;
            flex-shrink: 0 !important;
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

        .topbar-anchor {
            height: 0 !important;
            margin: 0 !important;
            padding: 0 0.08rem 0 0.10rem !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
            position: fixed !important;
            top: 0 !important;
            left: 228px !important;
            right: 0 !important;
            z-index: 999 !important;
            min-height: 48px !important;
            background: #ffffff !important;
            border-bottom: 1px solid #e6ebf3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0.12rem 1rem !important;
            margin: 0 !important;
            align-items: center !important;
            overflow: visible !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) > div {
            width: 100% !important;
        }

        
        .app-topbar {
            position: fixed;
            top: 0;
            left: 228px;
            right: 0;
            z-index: 999;
            height: 58px;
            background: #ffffff;
            border-bottom: 1px solid #e6ebf3;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding: 0 1rem;
            box-sizing: border-box;
        }

        .app-topbar-right {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.55rem;
            min-width: 0;
            margin-left: auto;
        }

        .app-role-pill {
            height: 34px;
            padding: 0 0.8rem;
            border-radius: 12px;
            border: 1px solid #dbe4f0;
            background: #ffffff;
            color: #172033;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            font-size: 13px;
            font-weight: 600;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
            flex-shrink: 0;
        }

        .app-notification-pill {
            position: relative;
            width: 34px;
            min-width: 34px;
            height: 34px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-left: 1px solid #e6ebf3;
            padding-left: 0.5rem;
            box-sizing: content-box;
            flex-shrink: 0;
        }

        .app-notification-icon {
            font-size: 18px;
            line-height: 1;
            color: #4b5565;
        }

        .app-notification-badge {
            position: absolute;
            top: -2px;
            right: -1px;
            min-width: 18px;
            height: 18px;
            padding: 0 4px;
            border-radius: 999px;
            background: #ef4444;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }

        .app-profile-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            min-width: 0;
            max-width: 240px;
            height: 34px;
            padding-left: 0.7rem;
            border-left: 1px solid #e6ebf3;
            box-sizing: border-box;
            flex-shrink: 0;
        }

        .app-profile-avatar {
            width: 30px;
            min-width: 30px;
            height: 30px;
            border-radius: 999px;
            background: #0b2f6b;
            color: #ffffff;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 800;
        }

        .app-profile-name {
            color: #172033;
            font-size: 13px;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 140px;
        }

        .app-profile-chevron {
            color: #667085;
            font-size: 11px;
            line-height: 1;
            flex-shrink: 0;
        }

.fixed-topbar-offset {
            display: block;
            width: 100%;
            height: 72px;
        }

        .topbar-spacer {
            height: 1px;
        }

        div[data-testid="stColumn"]:has(.topbar-role-wrap),
        div[data-testid="stColumn"]:has(.topbar-info-wrap) {
            min-width: 0 !important;
            overflow: visible !important;
        }

        .topbar-role-wrap {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            min-height: 36px;
            width: 100%;
            min-width: 0;
        }

        .topbar-role-wrap [data-testid="stPopover"] {
            width: 100% !important;
            min-width: 0 !important;
        }

        .topbar-role-wrap [data-testid="stPopover"] > div,
        .topbar-role-wrap [data-testid="stPopover"] > div > button {
            width: 100% !important;
            min-width: 0 !important;
        }

        div[data-testid="stPopover"] > div > button {
            min-height: 36px !important;
            height: 36px !important;
            white-space: nowrap !important;
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            color: #172033 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            font-weight: 600 !important;
            padding: 0 0.55rem !important;
            overflow: hidden !important;
        }

        div[data-testid="stPopover"] > div > button p {
            margin: 0 !important;
            font-size: 13px !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button {
            padding-left: 0.45rem !important;
            padding-right: 0.45rem !important;
            justify-content: flex-start !important;
            min-width: 150px !important;
            max-width: 150px !important;
            max-width: 100% !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button p {
            font-size: 12px !important;
        }

        .role-switch-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin: 0 0 0.65rem 0;
        }

        div[data-testid="stPopoverContent"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 0.15rem !important;
            min-width: 190px !important;
        }

        .topbar-info-wrap {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.18rem;
            min-height: 36px;
            width: 100%;
            min-width: 0;
            margin-left: auto;
            overflow: visible !important;
            flex-wrap: nowrap !important;
        }

        .notification-pill {
            position: relative;
            width: 32px;
            min-width: 32px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-left: 1px solid #e6ebf3;
            padding-left: 0.18rem;
            box-sizing: border-box;
        }

        .notification-icon {
            font-size: 18px;
            line-height: 1;
            color: #4b5565;
        }

        .notification-badge {
            position: absolute;
            top: -2px;
            right: -1px;
            min-width: 18px;
            height: 18px;
            padding: 0 4px;
            border-radius: 999px;
            background: #ef4444;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
        }

        .profile-card {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.22rem;
            min-height: 36px;
            min-width: 0;
            max-width: 100%;
            padding-left: 0.42rem;
            border-left: 1px solid #e6ebf3;
            overflow: hidden;
            box-sizing: border-box;
        }

        .profile-avatar {
            width: 32px;
            min-width: 32px;
            height: 32px;
            border-radius: 999px;
            background: #0b2f6b;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 800;
            flex-shrink: 0;
        }

        .profile-details {
            min-width: 0;
            max-width: 74px;
            overflow: hidden;
        }

        .profile-name {
            color: #172033;
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .profile-chevron {
            color: #667085;
            font-size: 11px;
            line-height: 1;
            flex-shrink: 0;
        }

        .dashboard-action-btn .stButton,
        .dashboard-action-btn [data-testid="stPopover"] {
            width: 100% !important;
        }

        .dashboard-action-btn .stButton button,
        .dashboard-action-btn div[data-testid="stPopover"] > div > button {
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

        div[data-testid="stSelectbox"] > div[data-baseweb="select"] {
            min-height: 42px !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            border: 1px solid #dbe4f0 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
        }

        .main .block-container > div:first-child {
            margin-top: 0.35rem !important;
        }

        div[data-testid="stVerticalBlock"] > div:has(.topbar-anchor) {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }



        @media (max-width: 1280px) {
            .brand-text {
                font-size: 1.48rem !important;
            }

            .profile-details {
                max-width: 50px !important;
            }

            .profile-name {
                font-size: 10.5px !important;
            }

            div[data-testid="stPopover"] > div > button p {
                font-size: 12px !important;
            }
        }

        @media (max-width: 1400px) {
            div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }

            div[data-testid="stPopover"] > div > button {
                padding-left: 0.55rem !important;
                padding-right: 0.55rem !important;
            }

            div[data-testid="stPopover"] > div > button p {
                font-size: 13px !important;
            }

            .topbar-info-wrap {
                gap: 0.35rem !important;
            }

            .notification-pill {
                width: 32px !important;
                min-width: 32px !important;
                padding-left: 0.12rem !important;
            }

            .profile-card {
                gap: 0.35rem !important;
                padding-left: 0.4rem !important;
            }

            .profile-details {
                max-width: 118px !important;
            }

            .profile-name {
                font-size: 12px !important;
            }
        }

                @media (max-width: 1100px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
                left: 228px !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .fixed-topbar-offset {
                height: 58px;
            }

            .profile-details {
                display: none !important;
            }

            .profile-card {
                gap: 0.25rem !important;
                padding-left: 0.35rem !important;
            }
        }

        .topbar-anchor {
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
            position: fixed !important;
            top: 0 !important;
            left: 228px !important;
            right: 0 !important;
            z-index: 999 !important;
            min-height: 58px !important;
            background: #ffffff !important;
            border-bottom: 1px solid #e6ebf3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0.34rem 0.40rem 0.34rem 0.32rem !important;
            margin: 0 !important;
            align-items: center !important;
            overflow: visible !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) > div {
            width: 100% !important;
        }

        .topbar-spacer {
            height: 1px;
        }

        .fixed-topbar-offset {
            display: block;
            width: 100%;
            height: 72px;
        }

        div[data-testid="stColumn"]:has(.topbar-role-wrap),
        div[data-testid="stColumn"]:has(.topbar-notification-wrap),
        div[data-testid="stColumn"]:has(.topbar-profile-wrap) {
            min-width: 0 !important;
            overflow: visible !important;
        }

        
        .topbar-role-wrap,
        .topbar-notification-wrap,
        .topbar-profile-wrap {
            flex-shrink: 1 !important;
        }

        .topbar-role-wrap [data-testid="stPopover"] > div > button,
        .topbar-notification-wrap [data-testid="stPopover"] > div > button,
        .topbar-profile-wrap [data-testid="stPopover"] > div > button {
            overflow: hidden !important;
        }

.topbar-role-wrap,
        .topbar-notification-wrap,
        .topbar-profile-wrap {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            min-width: 0;
            width: 100%;
            height: 38px;
        }

        .topbar-role-wrap [data-testid="stPopover"],
        .topbar-profile-wrap [data-testid="stPopover"],
        .topbar-notification-wrap [data-testid="stPopover"] {
            width: 100% !important;
        }

        .topbar-role-wrap [data-testid="stPopover"] > div,
        .topbar-role-wrap [data-testid="stPopover"] > div > button,
        .topbar-profile-wrap [data-testid="stPopover"] > div,
        .topbar-profile-wrap [data-testid="stPopover"] > div > button,
        .topbar-notification-wrap [data-testid="stPopover"] > div,
        .topbar-notification-wrap [data-testid="stPopover"] > div > button {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button,
        .topbar-profile-wrap div[data-testid="stPopover"] > div > button,
        .topbar-notification-wrap div[data-testid="stPopover"] > div > button {
            min-height: 38px !important;
            height: 38px !important;
            white-space: nowrap !important;
            background: #ffffff !important;
            color: #172033 !important;
            font-weight: 600 !important;
            overflow: hidden !important;
            display: flex !important;
            align-items: center !important;
        }

        .topbar-notification-wrap div[data-testid="stPopover"] > div > button {
            max-width: 44px !important;
            margin-left: auto !important;
            text-align: center !important;
            justify-content: center !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }

        .topbar-role-wrap {
            padding-right: 0.08rem;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button {
            border-radius: 12px !important;
            border: 1px solid #dbe4f0 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0 0.65rem !important;
            justify-content: center !important;
        }

        .topbar-notification-wrap {
            border-left: 1px solid #e6ebf3;
            border-right: 1px solid #e6ebf3;
            padding: 0 0.10rem;
        }

        .topbar-notification-wrap div[data-testid="stPopover"] > div > button {
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            font-size: 17px !important;
            min-width: 36px !important;
        }

        .topbar-profile-wrap {
            padding-left: 0.04rem;
        }

        .topbar-profile-wrap div[data-testid="stPopover"] > div > button {
            border: none !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            background: transparent !important;
            justify-content: center !important;
            padding: 0 !important;
            max-width: 56px !important;
            min-width: 92px !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button {
            margin-left: auto !important;
        }

        .topbar-profile-wrap div[data-testid="stPopover"] > div > button {
            margin-left: auto !important;
        }

        .topbar-role-wrap div[data-testid="stPopover"] > div > button p,
        .topbar-profile-wrap div[data-testid="stPopover"] > div > button p,
        .topbar-notification-wrap div[data-testid="stPopover"] > div > button p {
            margin: 0 !important;
            font-size: 11px !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            color: #172033 !important;
        }

        .topbar-notification-wrap div[data-testid="stPopover"] > div > button p {
            text-align: center !important;
        }

        div[data-testid="stPopoverContent"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 0.2rem !important;
        }

        

        .popover-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin: 0 0 0.65rem 0;
        }

        .empty-popover-text {
            color: #6f7d93;
            font-size: 14px;
            padding: 0.35rem 0 0.25rem 0;
        }

        .notification-list {
            max-height: 340px;
            overflow-y: auto;
        }

        .notification-item {
            display: flex;
            gap: 0.7rem;
            padding: 0.7rem 0;
            border-top: 1px solid #eef2f7;
        }

        .notification-item:first-child {
            border-top: none;
            padding-top: 0.15rem;
        }

        .notif-icon {
            width: 20px;
            min-width: 20px;
            height: 20px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 800;
            line-height: 1;
            margin-top: 0.15rem;
        }

        .notif-icon-danger {
            background: #fdeaea;
            color: #d92d20;
        }

        .notif-icon-success {
            background: #e8f7ee;
            color: #067647;
        }

        .notif-icon-info {
            background: #edf3ff;
            color: #2457d6;
        }

        .notification-content {
            min-width: 0;
        }

        .notification-claim {
            color: #0b2f6b;
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .notification-message {
            color: #172033;
            font-size: 13px;
            line-height: 1.35;
        }

        .notification-date {
            color: #6f7d93;
            font-size: 12px;
            margin-top: 0.2rem;
        }

        .profile-popover {
            min-width: 250px;
            padding: 0.2rem;
        }

        .profile-popover-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #eef2f7;
        }

        .profile-avatar-lg {
            width: 40px;
            min-width: 40px;
            height: 40px;
            border-radius: 999px;
            background: #0b2f6b;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 800;
        }

        .profile-popover-meta {
            min-width: 0;
        }

        .profile-popover-name {
            color: #172033;
            font-size: 18px;
            font-weight: 800;
            line-height: 1.2;
        }

        .profile-popover-email {
            color: #6f7d93;
            font-size: 14px;
            line-height: 1.35;
            margin-top: 0.15rem;
        }

        .profile-role-row {
            color: #0b2f6b;
            font-size: 14px;
            font-weight: 700;
            padding-top: 0.85rem;
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


        /* MM_DYNAMIC_TOPBAR_V47_START */
        .topbar-anchor {
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
            position: fixed !important;
            top: 0 !important;
            left: 228px !important;
            right: 0 !important;
            z-index: 1001 !important;
            min-height: 56px !important;
            background: #ffffff !important;
            border-bottom: 1px solid #e6ebf3 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0.35rem 0.55rem 0.35rem 0.45rem !important;
            margin: 0 !important;
            align-items: center !important;
            overflow: visible !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) > div {
            width: 100% !important;
        }

        .topbar-spacer {
            height: 1px;
        }

        .fixed-topbar-offset {
            display: block;
            width: 100%;
            height: 70px;
        }

        div[data-testid="stColumn"]:has(.mm-topbar-role-wrap),
        div[data-testid="stColumn"]:has(.mm-topbar-bell-wrap),
        div[data-testid="stColumn"]:has(.mm-topbar-profile-wrap) {
            min-width: 0 !important;
            overflow: visible !important;
        }

        .mm-topbar-role-wrap,
        .mm-topbar-bell-wrap,
        .mm-topbar-profile-wrap {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            width: 100%;
            min-width: 0;
            height: 36px;
        }

        .mm-topbar-role-wrap [data-testid="stPopover"],
        .mm-topbar-bell-wrap [data-testid="stPopover"],
        .mm-topbar-profile-wrap [data-testid="stPopover"] {
            width: 100% !important;
        }

        .mm-topbar-role-wrap [data-testid="stPopover"] > div,
        .mm-topbar-role-wrap [data-testid="stPopover"] > div > button,
        .mm-topbar-bell-wrap [data-testid="stPopover"] > div,
        .mm-topbar-bell-wrap [data-testid="stPopover"] > div > button,
        .mm-topbar-profile-wrap [data-testid="stPopover"] > div,
        .mm-topbar-profile-wrap [data-testid="stPopover"] > div > button {
            width: 100% !important;
            min-width: 0 !important;
            max-width: 100% !important;
        }

        .mm-topbar-role-wrap div[data-testid="stPopover"] > div > button {
            min-width: 150px !important;
            max-width: 150px !important;
            min-height: 36px !important;
            height: 36px !important;
            border-radius: 10px !important;
            border: 1px solid #dbe4f0 !important;
            background: #ffffff !important;
            color: #172033 !important;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04) !important;
            padding: 0 0.65rem !important;
            justify-content: center !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        .mm-topbar-bell-wrap {
            border-left: 1px solid #e6ebf3;
            border-right: 1px solid #e6ebf3;
            padding: 0 0.15rem;
        }

        .mm-topbar-bell-wrap div[data-testid="stPopover"] > div > button {
            min-width: 38px !important;
            max-width: 38px !important;
            min-height: 36px !important;
            height: 36px !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            padding: 0 !important;
            justify-content: center !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        .mm-topbar-profile-wrap {
            padding-left: 0.20rem;
        }

        .mm-topbar-profile-wrap div[data-testid="stPopover"] > div > button {
            min-width: 124px !important;
            max-width: 124px !important;
            min-height: 36px !important;
            height: 36px !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            padding: 0 0.05rem !important;
            justify-content: flex-start !important;
            white-space: nowrap !important;
            overflow: hidden !important;
        }

        .mm-topbar-role-wrap div[data-testid="stPopover"] > div > button p,
        .mm-topbar-bell-wrap div[data-testid="stPopover"] > div > button p,
        .mm-topbar-profile-wrap div[data-testid="stPopover"] > div > button p {
            margin: 0 !important;
            font-size: 12px !important;
            line-height: 1 !important;
            color: #172033 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .mm-topbar-bell-wrap div[data-testid="stPopover"] > div > button p {
            text-align: center !important;
            font-size: 16px !important;
        }

        div[data-testid="stPopoverContent"] {
            border-radius: 14px !important;
            border: 1px solid #e3e9f2 !important;
            box-shadow: 0 8px 20px rgba(16, 24, 40, 0.12) !important;
            padding: 0.2rem !important;
        }

        .mm-popover-title {
            color: #7b8798;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            margin: 0 0 0.65rem 0;
        }

        .mm-empty-popover {
            color: #6f7d93;
            font-size: 14px;
            padding: 0.35rem 0 0.25rem 0;
        }

        .mm-role-switch-menu .stButton {
            width: 100% !important;
        }

        .mm-role-switch-menu .stButton button {
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

        .mm-role-switch-menu .stButton button p {
            font-size: 15px !important;
            margin: 0 !important;
        }

        .mm-role-switch-menu .stButton button[kind="primary"] {
            background: #ffffff !important;
            color: #172033 !important;
        }

        .mm-role-switch-menu .stButton button[kind="primary"]:hover {
            background: #f6f8fb !important;
            color: #172033 !important;
        }

        .mm-role-switch-menu .stButton button[kind="secondary"] {
            background: #eef2f7 !important;
            color: #0b2f6b !important;
            border-color: transparent !important;
        }

        .mm-role-switch-menu .stButton button[kind="secondary"]:hover {
            background: #e8edf5 !important;
            color: #0b2f6b !important;
        }

        .mm-notification-list {
            max-height: 340px;
            overflow-y: auto;
        }

        .mm-notification-item {
            display: flex;
            gap: 0.7rem;
            padding: 0.7rem 0;
            border-top: 1px solid #eef2f7;
        }

        .mm-notification-item:first-child {
            border-top: none;
            padding-top: 0.15rem;
        }

        .mm-notif-icon {
            width: 20px;
            min-width: 20px;
            height: 20px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 800;
            line-height: 1;
            margin-top: 0.15rem;
        }

        .mm-notif-danger {
            background: #fdeaea;
            color: #d92d20;
        }

        .mm-notif-success {
            background: #e8f7ee;
            color: #067647;
        }

        .mm-notif-info {
            background: #edf3ff;
            color: #2457d6;
        }

        .mm-notification-body {
            min-width: 0;
        }

        .mm-notification-claim {
            color: #0b2f6b;
            font-size: 14px;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .mm-notification-message {
            color: #172033;
            font-size: 13px;
            line-height: 1.35;
        }

        .mm-notification-date {
            color: #6f7d93;
            font-size: 12px;
            margin-top: 0.2rem;
        }

        .mm-profile-popover {
            min-width: 250px;
            padding: 0.2rem;
        }

        .mm-profile-popover-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid #eef2f7;
        }

        .mm-profile-avatar-lg {
            width: 40px;
            min-width: 40px;
            height: 40px;
            border-radius: 999px;
            background: #0b2f6b;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            font-weight: 800;
        }

        .mm-profile-meta {
            min-width: 0;
        }

        .mm-profile-name-lg {
            color: #172033;
            font-size: 18px;
            font-weight: 800;
            line-height: 1.2;
        }

        .mm-profile-email {
            color: #6f7d93;
            font-size: 14px;
            line-height: 1.35;
            margin-top: 0.15rem;
        }

        .mm-profile-role-row {
            color: #0b2f6b;
            font-size: 14px;
            font-weight: 700;
            padding-top: 0.85rem;
        }

        @media (max-width: 1280px) {
            div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
                padding-left: 0.3rem !important;
                padding-right: 0.35rem !important;
            }

            .mm-topbar-role-wrap div[data-testid="stPopover"] > div > button {
                min-width: 144px !important;
                max-width: 144px !important;
            }

            .mm-topbar-profile-wrap div[data-testid="stPopover"] > div > button {
                min-width: 112px !important;
                max-width: 112px !important;
            }

            .mm-topbar-role-wrap div[data-testid="stPopover"] > div > button p,
            .mm-topbar-profile-wrap div[data-testid="stPopover"] > div > button p {
                font-size: 11px !important;
            }
        }
        /* MM_DYNAMIC_TOPBAR_V47_END */

        .page-title {
            font-size: 2.25rem;
            line-height: 1.1;
            font-weight: 800;
            color: #13213d;
            margin: 0.3rem 0 0.3rem 0;
        }

        .page-subtitle {
            color: #6f7d93;
            font-size: 1rem;
            margin-bottom: 1.2rem;
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
            height: 44px;
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



        @media (max-width: 1400px) {
            div[data-testid="stHorizontalBlock"]:has(.topbar-spacer) {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }

            div[data-testid="stPopover"] > div > button {
                padding-left: 0.55rem !important;
                padding-right: 0.55rem !important;
            }

            div[data-testid="stPopover"] > div > button p {
                font-size: 13px !important;
            }

            .topbar-info-wrap {
                gap: 0.35rem !important;
            }

            .notification-pill {
                width: 32px !important;
                min-width: 32px !important;
                padding-left: 0.12rem !important;
            }

            .profile-card {
                gap: 0.35rem !important;
                padding-left: 0.4rem !important;
            }

            .profile-details {
                max-width: 60px !important;
            }

            .profile-name {
                font-size: 12px !important;
            }
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
