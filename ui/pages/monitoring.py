"""
Monitoring Page — Live Session Tracking
=======================================
Replaces the old "Live" mode. Shows WebRTC camera feed side-by-side
with live posture analysis (including shoulder misalignment data) and alerts.
"""

import time
import streamlit as st

from streamlit_webrtc import webrtc_streamer
from streamlit_autorefresh import st_autorefresh

from src.webrtc_bridge import (
    video_frame_callback, audio_frame_callback,
    get_results, set_control, reset_bridge,
)
from src.vision.blink import reset_session as reset_blink
from src.vision.emotion import (
    reset_session as reset_emotion,
    load_user_calibration, save_user_calibration,
)
from src.fusion.aggregator import (
    update_typing, get_session_summary, session_state as agg_state,
    reset_session as reset_aggregator,
)
from src.alerts.notifier import (
    process_alerts, get_notification_log, reset_notifier,
)
from src.io import typing_monitor
from ui import copy as C
from ui.components import (
    section_label, metrics_grid, alerts_html, session_timer,
    empty_state, disclaimer_bar, signal_strip
)

import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

BLINK_THR = config["alerts"]["blink_rate_low"]
SEATED_MAX = config["alerts"]["sitting_duration_mins"]


def render(rtc_config):
    """Render the live monitoring page."""
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    
    st.markdown(
        f'<div style="margin-bottom:20px;">'
        f'<h1 style="font-size:1.6rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.03em;margin:0;">Live Monitoring</h1>'
        f'<p style="font-size:0.85rem;color:var(--text-muted);font-weight:500;margin:4px 0 0;">Real-time posture and wellness tracking.</p>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # ── Initialise Session if not running ─────────────────────────────────
    if not st.session_state.running:
        st.markdown(
            f'<div class="aria-card" style="text-align:center;padding:40px;">'
            f'<div style="font-size:3rem;margin-bottom:12px;">📷</div>'
            f'<h3 style="font-size:1.2rem;font-weight:700;color:var(--text-primary);margin:0 0 8px;">Ready to Monitor</h3>'
            f'<p style="font-size:0.85rem;color:var(--text-muted);margin:0 0 24px;">Start a session to enable the camera and track your posture.</p>'
            f'<div class="start-btn">'
            f'</div>'
            f'</div>', unsafe_allow_html=True
        )
        if st.button("Start Monitoring", use_container_width=True):
            _start_session()
            st.rerun()
        return

    # Timer
    timer_placeholder = st.empty()

    # Layout: Camera on Left, Analysis on Right
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown(section_label("Camera Feed"), unsafe_allow_html=True)
        frame_placeholder = st.empty()
        
        # Toggles row
        _tc1, _tc2, _tc3 = st.columns(3)
        with _tc1:
            st.toggle("🦴 Skeleton overlay", key="show_skeleton")
        with _tc2:
            _mic_status = st.session_state.get("_mic_active", False)
            _mic_label = "🎙️ Mic Active" if _mic_status else "🎙️ Mic Off"
            _mic_color = "var(--success)" if _mic_status else "var(--text-muted)"
            st.markdown(
                f'<div style="padding-top:10px;"><span style="font-size:0.82rem;color:{_mic_color};font-weight:600;">'
                f'{_mic_label}</span></div>', unsafe_allow_html=True)
        with _tc3:
            st.markdown('<div class="ghost-btn" style="text-align:right;">', unsafe_allow_html=True)
            if st.button("⏹ Stop", key="stop_btn"):
                _on_stop_click()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:20px;"></div>', unsafe_allow_html=True)
        st.markdown(section_label("System Signals"), unsafe_allow_html=True)
        metrics_placeholder = st.empty()

    with col2:
        st.markdown(section_label("Posture Analysis"), unsafe_allow_html=True)
        shoulder_placeholder = st.empty()
        
        st.markdown(section_label("Aria Chat"), unsafe_allow_html=True)
        # We will embed the chat here
        chat_placeholder = st.empty()
        chat_input_placeholder = st.empty()

    st.markdown(disclaimer_bar(), unsafe_allow_html=True)

    # ── WebRTC Stream ─────────────────────────────────────────────────────
    _run_webrtc(col1, frame_placeholder, timer_placeholder,
                metrics_placeholder, shoulder_placeholder,
                alert_placeholder, rtc_config)


def _start_session():
    """Initialize a new monitoring session."""
    st.session_state.running = True
    st.session_state.paused = False
    st.session_state.session_started = True
    st.session_state.session_start_ts = time.time()
    st.session_state.user_bbox_cache = None

    reset_blink()
    reset_emotion()
    reset_aggregator()
    reset_notifier()

    if st.session_state.get("active_user"):
        agg_state["user_name"] = st.session_state.active_user
        load_user_calibration(st.session_state.active_user)

    if st.session_state.get("typing_enabled", True):
        typing_monitor.reset_session()
        typing_monitor.start_monitoring()

    reset_bridge()
    st.session_state.webrtc_key += 1

    if st.session_state.get("_mic_active"):
        set_control("mic_active", True)


def _on_stop_click():
    """Callback for the stop button."""
    _final_summary = get_session_summary()
    st.session_state["_final_summary"] = _final_summary
    st.session_state["_final_alerts"] = get_notification_log()
    if st.session_state.session_start_ts:
        st.session_state["_final_elapsed"] = int(time.time() - st.session_state.session_start_ts)
        
    st.session_state.running = False
    st.session_state.paused = False
    typing_monitor.stop_monitoring()
    if st.session_state.get("active_user"):
        save_user_calibration(st.session_state.active_user)

    reset_bridge()
    
    # Save the session via backend loop logic
    from ui.pages.home import _on_stop_click as home_stop_fallback
    # To keep code clean, jump directly to summary after saving
    try:
        from src.data.session_db import save_session
        save_session(_final_summary, "")
    except Exception: pass
    
    # Reroute to History or Dashboard to see the summary
    st.session_state.page = "dashboard"
    st.rerun()


def _run_webrtc(col1, frame_placeholder, timer_placeholder,
                metrics_placeholder, shoulder_placeholder,
                alert_placeholder, rtc_config):
    """Render WebRTC stream and update live metrics."""

    set_control("paused", st.session_state.paused)
    set_control("active_user", st.session_state.get("active_user"))
    set_control("show_skeleton", st.session_state.get("show_skeleton", False))
    _mic_is_on = st.session_state.get("_mic_active", False)
    set_control("mic_active", _mic_is_on)

    with frame_placeholder.container():
        ctx = webrtc_streamer(
            key=f"wellness-monitor-{st.session_state.webrtc_key}",
            video_frame_callback=video_frame_callback,
            audio_frame_callback=audio_frame_callback,
            media_stream_constraints={
                "video": {"width": {"ideal": 640}, "height": {"ideal": 480}},
                "audio": True,
            },
            rtc_configuration=rtc_config,
            async_processing=True,
        )

    if ctx.state.playing:
        st_autorefresh(interval=2000, key="metrics_refresh")

        _r = get_results()
        posture_data = _r["posture_data"]
        blink_data = _r["blink_data"]
        emotion_data = _r["emotion_data"]
        voice_data = _r["voice_data"]

        # Process alerts
        pending = _r.get("pending_alerts", [])
        if pending:
            for _a in pending:
                process_alerts([_a], use_streamlit=True)
            set_control("pending_alerts", [])

        # Timer
        if st.session_state.session_start_ts:
            _elapsed_s = int(time.time() - st.session_state.session_start_ts)
            timer_placeholder.markdown(session_timer(_elapsed_s, "live"), unsafe_allow_html=True)

        summary = get_session_summary()
        p_score = posture_data.get("posture_score") or summary.get("posture_score", 0)
        
        # ── Shoulder Misalignment UI ──────────────────────────────────────
        details = posture_data.get("details", {})
        shoulder_slope = details.get("shoulder_slope_raw", 0.0)
        
        if shoulder_slope > 0.03:
            sh_class = "shoulder-alert" if shoulder_slope > 0.08 else "shoulder-warn"
            sh_title = C.ALERT_SHOULDER_TITLE
            sh_body = C.ALERT_SHOULDER_ACTION
            icon = "⚠️"
        else:
            sh_class = "shoulder-normal"
            sh_title = "Shoulders Aligned"
            sh_body = "Good lateral posture maintained."
            icon = "✅"
            
        shoulder_placeholder.markdown(
            f'<div class="shoulder-card {sh_class}">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;">'
            f'<span style="font-weight:700;font-size:0.85rem;color:var(--text-primary);">{sh_title}</span>'
            f'<span>{icon}</span>'
            f'</div>'
            f'<div style="font-size:0.75rem;color:var(--text-secondary);">{sh_body}</div>'
            f'<div style="margin-top:12px;font-size:0.65rem;color:var(--text-muted);display:flex;align-items:center;gap:4px;">'
            f'<span>ℹ️</span> {C.EXPLAIN_SHOULDER}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Get live typing data
        typing_reading = typing_monitor.get_current_reading()
        live_typing_wpm = typing_reading.get("wpm", 0.0)
        live_typing_stress = typing_reading.get("stress_signal", 0.0)
        
        # Get voice data from bridge
        voice_data = _r.get("voice_data", {})
        live_voice_rate = voice_data.get("speech_rate", 0.0)
        live_voice_stress = voice_data.get("stress_signal", 0.0)
        live_voice_speaking = voice_data.get("is_speaking", False)
        live_voice_status = voice_data.get("status", "stopped")

        metrics_placeholder.markdown(
            metrics_grid(
                p_score, posture_data.get("category", "unknown"), blink_data.get("blink_rate", 0.0),
                emotion_data.get("current_emotion", "neutral"), emotion_data.get("emotion_confidence", 0.0), summary["seated_mins"],
                BLINK_THR, SEATED_MAX,
                typing_wpm=live_typing_wpm, typing_stress=live_typing_stress, stress_index=summary.get("stress_index", 0.0),
                voice_rate=live_voice_rate, voice_stress_val=live_voice_stress, voice_speaking=live_voice_speaking, voice_status=live_voice_status
            ), unsafe_allow_html=True
        )
        
        # Chat UI
        from src.ai.chatbot import chat as aria_chat
        
        with chat_placeholder.container():
            chat_box = st.container(height=280)
            if not st.session_state.messages:
                with chat_box:
                    st.markdown(
                        f'<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.8rem;">'
                        f'Aria is monitoring and ready to chat.'
                        f'</div>', unsafe_allow_html=True)
            else:
                with chat_box:
                    for msg in st.session_state.messages:
                        with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])
        
        with chat_input_placeholder.container():
            user_input = st.chat_input("Ask Aria about your wellness...")
            if user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})
                try:
                    reply = aria_chat(user_input)
                except Exception:
                    reply = "I'm having trouble connecting to AI services."
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()

    else:
        chat_placeholder.markdown("")
        chat_input_placeholder.markdown("")
