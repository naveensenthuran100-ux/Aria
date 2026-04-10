"""
Aria — AI Wellness Companion
==============================
Main application entry point.
Slim router that delegates to UI page modules via a side-rail layout.
"""

import os
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from streamlit_webrtc import RTCConfiguration
from src.vision import face_id

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Aria — AI Wellness Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject design system CSS ─────────────────────────────────────────────────
from ui.theme import inject_css
_dark = st.session_state.get("dark_mode", False)
inject_css(dark=_dark)

# ── TURN/STUN config for WebRTC ──────────────────────────────────────────────
_ice_servers = [
    {"urls": ["stun:stun.l.google.com:19302"]},
    {"urls": ["stun:stun1.l.google.com:19302"]},
]
_turn_user = os.getenv("TURN_USERNAME", "")
_turn_cred = os.getenv("TURN_CREDENTIAL", "")
if _turn_user and _turn_cred:
    _turn_urls = [
        "turn:a.relay.metered.ca:80",
        "turn:a.relay.metered.ca:80?transport=tcp",
        "turn:a.relay.metered.ca:443",
        "turn:a.relay.metered.ca:443?transport=tcp",
        "turns:a.relay.metered.ca:443",
    ]
    for _u in _turn_urls:
        _ice_servers.append({
            "urls": _u,
            "username": _turn_user,
            "credential": _turn_cred,
        })
    print(f"[TURN] Configured {len(_turn_urls)} TURN servers with user={_turn_user[:4]}...")
else:
    print("[TURN] WARNING: No TURN_USERNAME/TURN_CREDENTIAL set — remote video may not work")

RTC_CONFIG = RTCConfiguration({"iceServers": _ice_servers})

# ── Session state defaults ────────────────────────────────────────────────────
for key, default in [
    ("running", False),
    ("paused", False),
    ("messages", []),
    ("session_started", False),
    ("report_path", None),
    ("session_start_ts", None),
    ("user_bbox_cache", None),
    ("active_user", None),
    ("page", None),
    ("webrtc_key", 0),
    ("show_skeleton", False),
    ("_mic_active", False),
    ("typing_enabled", True),
    ("dark_mode", False),
    ("reflection_response", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Auto-detect initial page ─────────────────────────────────────────────────
if st.session_state.page is None:
    _existing = face_id.get_registered_users()
    if _existing and len(_existing) == 1:
        st.session_state.page = "home"
        st.session_state.active_user = _existing[0]
    elif _existing:
        st.session_state.page = "login"
    else:
        st.session_state.page = "welcome"

# ── Sidebar Navigation ────────────────────────────────────────────────────────
from ui.layout import render_sidebar
render_sidebar()

# ── Page Router ───────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "welcome":
    from ui.pages import welcome
    welcome.render()

elif page == "registration":
    from ui.pages import registration
    registration.render()

elif page == "login":
    from ui.pages import login
    login.render()

elif page in ("home", "dashboard"):
    # With the new architecture, "home" defaults to the dashboard view.
    from ui.pages import dashboard
    dashboard.render()

elif page == "monitoring":
    from ui.pages import monitoring
    monitoring.render(rtc_config=RTC_CONFIG)

elif page == "chat":
    from ui.pages import chat
    chat.render()

elif page == "history":
    from ui.pages import history
    history.render()

elif page == "settings":
    from ui.pages import settings
    settings.render()

else:
    st.session_state.page = "welcome"
    st.rerun()
