"""
Settings & Privacy Page
========================
Grouped sections: Signal Controls, Profile, Privacy & Data,
AI Transparency, Appearance, About.
"""

import io
import numpy as np
import scipy.io.wavfile
import streamlit as st

from src.vision import face_id
from src.audio import voice_id
from src.io import typing_monitor
from src.audio import voice_stress as voice_stress_mod
from src.webrtc_bridge import set_control
from ui import copy as C
from ui.components import (
    trust_banner, disclaimer_bar, section_label,
)


def render():
    """Render the settings and privacy page."""

    # Title
    st.markdown(
        f'<div style="margin-bottom:20px;">'
        f'<h1 style="font-size:1.6rem;font-weight:800;color:var(--text-primary);margin:0;letter-spacing:-0.03em;">'
        f'Settings</h1>'
        f'<p style="font-size:0.85rem;color:var(--text-muted);font-weight:500;margin:4px 0 0;">'
        f'{C.SETTINGS_SUBTITLE}</p>'
        f'</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  SIGNAL CONTROLS
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(section_label(C.SETTINGS_SIGNALS), unsafe_allow_html=True)

    st.markdown(
        f'<div class="aria-card-flat" style="padding:12px 18px">'
        f'<p style="font-size:0.72rem;color:var(--text-secondary);margin:0;line-height:1.5">'
        f'{C.SETTINGS_SIGNALS_DESC}</p>'
        f'</div>', unsafe_allow_html=True)

    # Typing toggle
    if "typing_enabled" not in st.session_state:
        st.session_state["typing_enabled"] = True
    st.toggle("⌨️  Typing speed monitor", key="typing_enabled",
              help="Monitors typing rhythm and speed to detect stress patterns.")

    # Mic toggle
    _active = st.session_state.get("active_user")
    _voice_toggle = st.toggle("🎙️  Voice stress analysis", key="_mic_active",
                              help="Analyses speech rate and patterns for stress indicators.")

    if _voice_toggle:
        if _active and _active not in voice_id.get_enrolled_speakers():
            st.warning("⚠️ Please enroll your voice below before enabling the mic.")
            st.session_state["_mic_active"] = False
        else:
            set_control("mic_active", True)
    else:
        set_control("mic_active", False)

    # Skeleton overlay
    st.toggle("🦴  Show posture skeleton overlay", key="show_skeleton",
              help="Displays the posture tracking skeleton on the camera feed.")

    # ═══════════════════════════════════════════════════════════════════════
    #  VOICE ENROLLMENT
    # ═══════════════════════════════════════════════════════════════════════
    if _active:
        _voice_enrolled = _active in voice_id.get_enrolled_speakers()
        if not _voice_enrolled:
            st.markdown(section_label("Voice Enrollment"), unsafe_allow_html=True)
            st.markdown(
                f'<div class="aria-card-flat" style="padding:12px 18px">'
                f'<p style="font-size:0.72rem;color:var(--text-secondary);margin:0;line-height:1.5">'
                f'{C.REG_VOICE_TRUST}</p>'
                f'</div>', unsafe_allow_html=True)

            st.info(f'"{C.REG_VOICE_SENTENCE}"')

            _voice_audio = st.audio_input("Record your voice", key="settings_voice_rec",
                                          label_visibility="collapsed")

            if st.button("Enroll Voice", key="settings_voice_enroll",
                         use_container_width=True, disabled=_voice_audio is None):
                with st.spinner("Processing voice…"):
                    sr, audio_data = scipy.io.wavfile.read(io.BytesIO(_voice_audio.read()))
                    audio_float = audio_data.astype(np.float32) / 32768.0
                    ok, msg = voice_id.enroll_speaker(_active, audio_float, sr)
                if ok:
                    st.success("✅ " + msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ═══════════════════════════════════════════════════════════════════════
    #  PROFILE
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(section_label(C.SETTINGS_PROFILE), unsafe_allow_html=True)

    _users = face_id.get_registered_users()

    if _active:
        _voice_enrolled = _active in voice_id.get_enrolled_speakers()
        _v_text = "Face + Voice" if _voice_enrolled else "Face only"

        st.markdown(
            f'<div class="aria-card" style="padding:16px 18px">'
            f'<div style="display:flex;align-items:center;gap:14px">'
            f'<div style="width:46px;height:46px;border-radius:14px;background:var(--primary-subtle);'
            f'display:flex;align-items:center;justify-content:center;font-size:1.2rem;'
            f'border:1px solid var(--primary-border);flex-shrink:0">👤</div>'
            f'<div>'
            f'<span style="font-weight:700;color:var(--text-primary);font-size:1rem">{_active}</span>'
            f'<br><span style="color:var(--primary);font-size:0.7rem;font-weight:600">'
            f'Active · {_v_text}</span>'
            f'</div>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

    # Switch user
    if len(_users) > 1:
        _other = [u for u in _users if u != _active]
        selected = st.selectbox("Switch to another user", _other,
                                key="settings_switch_user", index=None,
                                placeholder="Select a user…",
                                label_visibility="collapsed")
        if selected:
            st.session_state.active_user = selected
            st.session_state.user_bbox_cache = None
            st.rerun()

    # Actions
    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button(C.SETTINGS_LOGOUT, key="settings_logout", use_container_width=True):
            _logout()
        st.markdown('</div>', unsafe_allow_html=True)
    with a2:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button(C.SETTINGS_NEW_USER, key="settings_add_user", use_container_width=True):
            _go_to_registration()
        st.markdown('</div>', unsafe_allow_html=True)
    with a3:
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button(C.SETTINGS_DELETE, key="settings_delete", use_container_width=True):
            _delete_profile()
        st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  PRIVACY & DATA
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(section_label(C.SETTINGS_PRIVACY), unsafe_allow_html=True)

    with st.expander("🔍 What data does Aria collect?", expanded=False):
        st.markdown("""**Camera (when enabled):**
- Posture score from body keypoint positions
- Blink rate from eye aspect ratio
- Emotion from facial expression analysis
- Face embedding for identity verification

**Microphone (when enabled):**
- Speech rate (words per minute)
- Voice stress signal (pitch/rate variability)
- Voice embedding for speaker verification

**Keyboard (when enabled):**
- Typing speed (words per minute)
- Keystroke rhythm patterns

**What is NOT collected:**
- ❌ No raw video is stored
- ❌ No audio recordings are saved
- ❌ No keystroke content is logged
- ❌ No data is sent to external servers""")

    with st.expander("🔒 Where is my data stored?", expanded=False):
        st.markdown("""All data is stored **locally on your device**:
- Face/voice embeddings → `data/` folder
- Session history → `data/sessions.db` (SQLite)
- Reports → `reports/output/` folder

**No data leaves your device.** The only external call is to the
AI chat API (Anthropic Claude) which receives anonymised session
metrics — never raw biometric data.""")

    # ═══════════════════════════════════════════════════════════════════════
    #  AI TRANSPARENCY
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(section_label(C.SETTINGS_AI_TRANSPARENCY), unsafe_allow_html=True)
    st.markdown(
        f'<div class="aria-card" style="padding:20px">'
        f'<div style="font-weight:700;color:var(--text-primary);margin-bottom:12px;font-size:0.9rem;">'
        f'{C.AI_TRANSPARENCY_TITLE}</div>'
        f'<div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.6;">'
        f'{C.AI_TRANSPARENCY_MODELS.replace("- ", "• ")}</div>'
        f'<div style="margin:16px 0;height:1px;background:var(--border);"></div>'
        f'<div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.6;">'
        f'{C.AI_TRANSPARENCY_DATA.replace("- ", "• ")}</div>'
        f'<div style="margin:16px 0;height:1px;background:var(--border);"></div>'
        f'<div style="font-size:0.8rem;color:var(--text-secondary);line-height:1.6;">'
        f'{C.AI_TRANSPARENCY_LIMITS.replace("- ", "• ")}</div>'
        f'</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    #  APPEARANCE
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(section_label(C.SETTINGS_APPEARANCE), unsafe_allow_html=True)

    dark = st.toggle("🌙  Dark mode", key="dark_mode",
                     help="Switch between light and dark theme.")

    # ═══════════════════════════════════════════════════════════════════════
    #  TRUST & ABOUT
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(trust_banner(
        "Aria is designed with Human-Centred AI (HCAI) principles. "
        "You have full control over what is monitored, and you can delete "
        "your data at any time.",
        icon="🛡️"
    ), unsafe_allow_html=True)

    st.markdown(section_label(C.SETTINGS_ABOUT), unsafe_allow_html=True)
    st.markdown(
        f'<div class="aria-card-flat" style="text-align:center;padding:20px">'
        f'<div style="font-size:1.5rem;margin-bottom:8px">🧠</div>'
        f'<p style="font-weight:700;color:var(--text-primary);margin:0">{C.ABOUT_TITLE}</p>'
        f'<p style="font-size:0.75rem;color:var(--text-muted);margin:4px 0 0">'
        f'{C.ABOUT_SUBTITLE}</p>'
        f'<p style="font-size:0.65rem;color:var(--text-muted);margin:8px 0 0;line-height:1.5">'
        f'{C.ABOUT_DISCLAIMER}</p>'
        f'</div>', unsafe_allow_html=True)


# ── Private Helpers ───────────────────────────────────────────────────────────

def _logout():
    st.session_state.active_user = None
    st.session_state.user_bbox_cache = None
    st.session_state.page = "login"
    if st.session_state.running:
        st.session_state.running = False
        typing_monitor.stop_monitoring()
        voice_stress_mod.stop_monitoring()
    st.rerun()

def _go_to_registration():
    st.session_state.page = "registration"
    if st.session_state.running:
        st.session_state.running = False
        typing_monitor.stop_monitoring()
        voice_stress_mod.stop_monitoring()
    st.rerun()

def _delete_profile():
    _active = st.session_state.get("active_user")
    if not _active:
        return
    face_id.delete_user(_active)
    voice_id.delete_speaker(_active)
    st.session_state.active_user = None
    st.session_state.user_bbox_cache = None
    remaining = face_id.get_registered_users()
    st.session_state.page = "login" if remaining else "registration"
    if st.session_state.running:
        st.session_state.running = False
        typing_monitor.stop_monitoring()
        voice_stress_mod.stop_monitoring()
    st.rerun()
