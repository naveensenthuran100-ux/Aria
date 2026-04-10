"""
Login Page — User Selection
============================
Shown when multiple users exist. User selects their profile.
"""

import streamlit as st

from src.vision import face_id
from src.audio import voice_id
from src.vision.emotion import load_user_calibration
from ui import copy as C
from ui.components import onboarding_hero, trust_banner


def render():
    """Render the login / user selection screen."""

    _users = face_id.get_registered_users()
    if not _users:
        st.session_state.page = "registration"
        st.rerun()

    st.markdown('<div class="onboard-container fade-in-up">', unsafe_allow_html=True)

    # Hero
    st.markdown(onboarding_hero(C.LOGIN_TITLE, C.LOGIN_SUBTITLE), unsafe_allow_html=True)

    # User cards
    for user in _users:
        _voice = user in voice_id.get_enrolled_speakers()
        _v_text = "Face + Voice" if _voice else "Face only"

        st.markdown(
            f'<div class="aria-card" style="padding:16px 18px">'
            f'<div style="display:flex;align-items:center;gap:14px">'
            f'<div style="width:44px;height:44px;border-radius:14px;background:var(--primary-subtle);'
            f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;'
            f'border:1px solid var(--primary-border);flex-shrink:0">👤</div>'
            f'<div>'
            f'<span style="font-weight:700;color:var(--text-primary);font-size:0.95rem">{user}</span>'
            f'<br><span style="color:var(--text-muted);font-size:0.7rem;font-weight:500">{_v_text}</span>'
            f'</div>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

        if st.button(f"Continue as {user}", key=f"login_{user}", use_container_width=True):
            st.session_state.active_user = user
            st.session_state.page = "home"
            st.session_state.user_bbox_cache = None
            load_user_calibration(user)
            st.rerun()

    # Add new user
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
    if st.button(C.LOGIN_NEW_USER, key="login_new_user", use_container_width=True):
        st.session_state.page = "registration"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Trust
    st.markdown(trust_banner(
        "Each profile stores only a mathematical embedding of your face — not photos. "
        "Profiles can be deleted at any time from Settings.",
        icon="🔒"
    ), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
