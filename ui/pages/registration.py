"""
Registration Page — Onboarding Wizard
======================================
4-step wizard: Name → Face Enrollment → Voice Enrollment → Done.
"""

import io
import cv2
import numpy as np
import scipy.io.wavfile
import streamlit as st

from src.vision import face_id
from src.audio import voice_id
from ui import copy as C
from ui.components import (
    onboarding_hero, step_indicator, trust_banner, error_card,
)


def render():
    """Render the registration wizard."""

    # Init registration state
    for key, default in [
        ("reg_step", 1), ("reg_name", ""),
        ("reg_face_done", False), ("reg_voice_done", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    step = st.session_state.reg_step

    st.markdown('<div class="onboard-container fade-in-up">', unsafe_allow_html=True)

    # Hero
    st.markdown(onboarding_hero(C.REG_TITLE, C.REG_SUBTITLE), unsafe_allow_html=True)

    # Step indicator
    steps_list = ["Name", "Face", "Voice", "Done"]
    st.markdown(step_indicator(steps_list, step), unsafe_allow_html=True)

    # ── Step 1: Name ──────────────────────────────────────────────────────
    if step == 1:
        st.markdown(
            f'<div class="aria-card">'
            f'<p style="font-weight:700;color:var(--text-primary);font-size:1rem;margin:0 0 4px">'
            f'{C.REG_NAME_PROMPT}</p>'
            f'<p style="color:var(--text-muted);font-size:0.78rem;margin:0 0 14px">'
            f'{C.REG_NAME_HELP}</p>'
            f'</div>', unsafe_allow_html=True)

        name = st.text_input("Your name", placeholder="e.g. Alex",
                             label_visibility="collapsed", key="reg_name_input")

        if st.button("Continue", key="reg_next_1", use_container_width=True,
                     disabled=not name):
            st.session_state.reg_name = name.strip()
            st.session_state.reg_step = 2
            st.rerun()

    # ── Step 2: Face Enrollment ───────────────────────────────────────────
    elif step == 2:
        st.markdown(
            f'<div class="aria-card">'
            f'<p style="font-weight:700;color:var(--text-primary);font-size:1rem;margin:0 0 4px">'
            f'📸 {C.REG_FACE_TITLE}</p>'
            f'<p style="color:var(--text-muted);font-size:0.78rem;margin:0 0 4px">'
            f'{C.REG_FACE_INSTRUCTION}</p>'
            f'</div>', unsafe_allow_html=True)

        st.markdown(trust_banner(C.REG_FACE_TRUST, icon="🔒"), unsafe_allow_html=True)

        cam_img = st.camera_input("Look at the camera", key="reg_cam",
                                  label_visibility="collapsed")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button("← Back", key="reg_back_2", use_container_width=True):
                st.session_state.reg_step = 1
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            if st.button("Register Face", key="reg_face_btn",
                         use_container_width=True, disabled=cam_img is None):
                with st.spinner("Extracting face embedding…"):
                    arr = np.frombuffer(cam_img.read(), np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    ok, msg = face_id.register_user(st.session_state.reg_name, [frame])
                if ok:
                    st.session_state.reg_face_done = True
                    st.session_state.reg_step = 3
                    st.rerun()
                else:
                    st.markdown(error_card(
                        "Face not detected",
                        C.REG_FACE_FAIL,
                        icon="📸",
                        action="Check your lighting and face the camera directly."
                    ), unsafe_allow_html=True)

    # ── Step 3: Voice Enrollment ──────────────────────────────────────────
    elif step == 3:
        st.markdown(
            f'<div class="aria-card">'
            f'<p style="font-weight:700;color:var(--text-primary);font-size:1rem;margin:0 0 4px">'
            f'🎙️ {C.REG_VOICE_TITLE}</p>'
            f'<p style="color:var(--text-muted);font-size:0.78rem;margin:0 0 4px">'
            f'{C.REG_VOICE_INSTRUCTION}</p>'
            f'</div>', unsafe_allow_html=True)

        st.markdown(trust_banner(C.REG_VOICE_TRUST, icon="ℹ️"), unsafe_allow_html=True)

        st.info(f'"{C.REG_VOICE_SENTENCE}"')

        audio_file = st.audio_input("Record your voice", key="reg_voice_rec",
                                    label_visibility="collapsed")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
            if st.button(C.REG_VOICE_SKIP, key="reg_skip_voice", use_container_width=True):
                st.session_state.reg_step = 4
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            if st.button("Enroll Voice", key="reg_voice_btn",
                         use_container_width=True, disabled=audio_file is None):
                with st.spinner("Processing voice…"):
                    sr, audio_data = scipy.io.wavfile.read(io.BytesIO(audio_file.read()))
                    audio_float = audio_data.astype(np.float32) / 32768.0
                    ok, msg = voice_id.enroll_speaker(st.session_state.reg_name, audio_float, sr)
                if ok:
                    st.session_state.reg_voice_done = True
                    st.session_state.reg_step = 4
                    st.rerun()
                else:
                    st.markdown(error_card(
                        "Voice enrollment issue",
                        C.REG_VOICE_FAIL,
                        icon="🎙️",
                        action="Try a quieter environment and speak clearly."
                    ), unsafe_allow_html=True)

    # ── Step 4: Done ──────────────────────────────────────────────────────
    elif step == 4:
        _name = st.session_state.reg_name
        st.markdown(
            f'<div class="aria-card" style="text-align:center;padding:28px 20px">'
            f'<div style="font-size:2.5rem;margin-bottom:12px">✅</div>'
            f'<p style="font-weight:800;color:var(--text-primary);font-size:1.2rem;margin:0;letter-spacing:-0.02em">'
            f'{C.REG_DONE_TITLE.format(name=_name)}</p>'
            f'<p style="color:var(--text-muted);font-size:0.85rem;margin:8px 0 0;line-height:1.5">'
            f'{C.REG_DONE_SUBTITLE}</p>'
            f'</div>', unsafe_allow_html=True)

        # Enrollment status
        checks = [
            ("Face enrolled", st.session_state.reg_face_done),
            ("Voice enrolled", st.session_state.reg_voice_done)
        ]
        for label, done in checks:
            icon_ch = "✓" if done else "—"
            color = "var(--success)" if done else "var(--text-muted)"
            st.markdown(
                f'<p style="color:{color};font-size:0.82rem;font-weight:600;margin:4px 0;text-align:center">'
                f'{icon_ch}  {label}</p>', unsafe_allow_html=True)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button(C.REG_DONE_CTA, key="reg_finish", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.active_user = st.session_state.reg_name
            for k in ["reg_step", "reg_name", "reg_face_done", "reg_voice_done"]:
                st.session_state.pop(k, None)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
