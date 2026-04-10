"""
Welcome Page — First Launch + Privacy Disclosure
=================================================
Shown when no users are registered. Introduces Aria with trust-first
language, explains features, and includes privacy disclosure step.
"""

import streamlit as st
from ui import copy as C
from ui.components import (
    onboarding_hero, feature_grid, trust_banner,
    permission_card, disclaimer_bar,
)


def render():
    """Render the welcome flow (welcome + privacy disclosure)."""

    # Two-step welcome: 1=welcome, 2=privacy disclosure
    welcome_step = st.session_state.get("welcome_step", 1)

    if welcome_step == 1:
        _render_welcome()
    else:
        _render_privacy_disclosure()


def _render_welcome():
    """Step 1: Hero introduction."""

    st.markdown('<div class="onboard-container fade-in-up">', unsafe_allow_html=True)

    # Hero
    st.markdown(onboarding_hero(C.WELCOME_TITLE, C.WELCOME_SUBTITLE), unsafe_allow_html=True)

    # Feature grid
    st.markdown(feature_grid([
        ("🦴", "Posture", "Camera-based posture tracking with gentle reminders"),
        ("👁️", "Eye Health", "Blink rate monitoring to prevent eye fatigue"),
        ("🎙️", "Voice Patterns", "Optional voice stress analysis during speaking"),
        ("⌨️", "Typing Rhythm", "Keyboard pattern analysis for stress signals"),
    ]), unsafe_allow_html=True)

    # Trust banner
    st.markdown(trust_banner(C.LOCAL_PROCESSING, icon="🔒"), unsafe_allow_html=True)

    # CTA
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.button(C.WELCOME_CTA, key="welcome_start", use_container_width=True):
        st.session_state.welcome_step = 2
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Secondary
    st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
    if st.button(C.WELCOME_LOGIN, key="welcome_login", use_container_width=True):
        st.session_state.page = "login"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(
        f'<div style="text-align:center;margin-top:20px;font-size:0.68rem;color:var(--text-muted);line-height:1.6">'
        f'Built for NTU SC1304 · AI for Social Good<br>'
        f'{C.DISCLAIMER}'
        f'</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_privacy_disclosure():
    """Step 2: Privacy disclosure with permission explanations."""

    st.markdown('<div class="onboard-container fade-in-up">', unsafe_allow_html=True)

    # Hero
    st.markdown(onboarding_hero(C.PRIVACY_TITLE, C.PRIVACY_SUBTITLE), unsafe_allow_html=True)

    # Permission cards
    st.markdown(permission_card(
        "📷", C.PRIVACY_CAMERA_TITLE, C.PRIVACY_CAMERA_DESC,
        C.PRIVACY_CAMERA_NOT
    ), unsafe_allow_html=True)

    st.markdown(permission_card(
        "🎙️", C.PRIVACY_MIC_TITLE, C.PRIVACY_MIC_DESC,
        C.PRIVACY_MIC_NOT
    ), unsafe_allow_html=True)

    st.markdown(permission_card(
        "⌨️", C.PRIVACY_KEYBOARD_TITLE, C.PRIVACY_KEYBOARD_DESC,
        C.PRIVACY_KEYBOARD_NOT
    ), unsafe_allow_html=True)

    # Local processing note
    st.markdown(trust_banner(C.PRIVACY_LOCAL, icon="🔒"), unsafe_allow_html=True)

    # Change later note
    st.markdown(
        f'<p style="text-align:center;font-size:0.72rem;color:var(--text-muted);margin:8px 0">'
        f'{C.PRIVACY_CHANGE_LATER}</p>', unsafe_allow_html=True)

    # Continue
    st.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.button(C.PRIVACY_CONTINUE, key="privacy_continue", use_container_width=True):
        st.session_state.page = "registration"
        st.session_state.pop("welcome_step", None)
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Back
    st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
    if st.button("← Back", key="privacy_back", use_container_width=True):
        st.session_state.welcome_step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
