"""
Dashboard Page — Core Monitoring Experience
=============================================
The main screen. Handles:
- Idle state (ready to start)
- Live monitoring (WebRTC + metrics + alerts)
- Paused state
- Session ended (summary + report access)
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
from src.ai.chatbot import reset_conversation, generate_report_summary
from src.alerts.notifier import (
    process_alerts, get_notification_log, reset_notifier,
)
from src.reports.generator import generate_pdf_report
from src.data.session_db import save_session
from src.io import typing_monitor
from src.audio import voice_stress

from ui.components import (
    app_header, render_nav_buttons, section_label,
    metrics_grid, alerts_html, session_timer,
    empty_state, trust_banner, disclaimer_bar,
    EMOTION_EMOJI,
)

import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

BLINK_THR = config["alerts"]["blink_rate_low"]
SEATED_MAX = config["alerts"]["sitting_duration_mins"]


def render(rtc_config):
    """Render the main dashboard page."""

    # ── Determine status ──────────────────────────────────────────────────
    if st.session_state.running and st.session_state.paused:
        status = "paused"
    elif st.session_state.running:
        status = "live"
    else:
        status = "idle"

    # ── Header + Nav ──────────────────────────────────────────────────────
    st.markdown(app_header(status, st.session_state.get("active_user")),
                unsafe_allow_html=True)

    # Navigation tabs
    st.markdown('<div style="background:#F1F5F9;border-radius:14px;padding:4px;margin-bottom:20px">',
                unsafe_allow_html=True)
    render_nav_buttons("dashboard")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Layout: Two columns — Feed+Metrics | Chat Snapshot ────────────────
    col1, col2 = st.columns([1.3, 1])

    with col1:
        # Timer
        timer_placeholder = st.empty()

        # Live Feed section
        st.markdown(section_label("Live Feed"), unsafe_allow_html=True)
        frame_placeholder = st.empty()

        # Toggles during active session
        if st.session_state.running:
            _tc1, _tc2 = st.columns(2)
            with _tc1:
                st.toggle("Show posture skeleton", key="show_skeleton")
            with _tc2:
                _mic_status = st.session_state.get("_mic_active", False)
                _mic_label = "🎙️ Mic ON" if _mic_status else "🎙️ Mic OFF"
                st.markdown(
                    f'<span style="font-size:0.85rem;color:{"#10B981" if _mic_status else "#94A3B8"}">'
                    f'{_mic_label}</span>', unsafe_allow_html=True)

        # Metrics placeholder
        metrics_placeholder = st.empty()

        # ── Session Controls ──────────────────────────────────────────────
        if not st.session_state.running:
            # Show idle state or session results
            if not st.session_state.get("session_started"):
                # Fresh idle — show empty state + Start button
                frame_placeholder.markdown(empty_state(
                    "🎯", "Ready to monitor",
                    "Start a session to begin tracking your posture, eye health, and stress signals."
                ), unsafe_allow_html=True)

            st.markdown('<div class="start-btn">', unsafe_allow_html=True)
            if st.button("Start Session", key="start_btn", use_container_width=True):
                _start_session()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            _btn1, _btn2 = st.columns(2)
            with _btn1:
                if st.session_state.paused:
                    st.markdown('<div class="resume-btn">', unsafe_allow_html=True)
                    if st.button("▶ Resume", key="resume_btn", use_container_width=True):
                        st.session_state.paused = False
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="pause-btn">', unsafe_allow_html=True)
                    if st.button("⏸ Pause", key="pause_btn", use_container_width=True):
                        st.session_state.paused = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            with _btn2:
                st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
                st.button("⏹ Stop", key="stop_btn", use_container_width=True,
                          on_click=_on_stop_click)
                st.markdown('</div>', unsafe_allow_html=True)

        # Alerts section
        st.markdown(section_label("Alerts"), unsafe_allow_html=True)
        alert_placeholder = st.empty()

    # ── Right column: Quick Chat + Session Snapshot ───────────────────────
    with col2:
        st.markdown(section_label("Chat with Aria"), unsafe_allow_html=True)
        chat_container = st.container(height=320)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_input = st.chat_input("Ask Aria about your wellness…")
        if user_input:
            _handle_chat(user_input, chat_container)

        # Session snapshot
        st.markdown(section_label("Session Snapshot"), unsafe_allow_html=True)
        summary = get_session_summary()
        s1, s2 = st.columns(2)
        s1.metric("Posture", f"{summary['posture_score']}/100", summary['posture_trend'])
        s2.metric("Blinks/min", f"{summary['blink_rate']}")
        s3, s4 = st.columns(2)
        ee = EMOTION_EMOJI.get(summary['dominant_emotion'], '😐')
        s3.metric("Emotion", f"{ee} {summary['dominant_emotion'].title()}")
        s4.metric("Seated", f"{summary['seated_mins']} min")

        # HCAI disclaimer
        st.markdown(disclaimer_bar(), unsafe_allow_html=True)

    # ── WebRTC Stream (when running) ──────────────────────────────────────
    if st.session_state.running:
        _render_live_stream(col1, frame_placeholder, timer_placeholder,
                            metrics_placeholder, alert_placeholder, rtc_config)
    elif st.session_state.get("session_started") and not st.session_state.running:
        _render_session_ended(frame_placeholder, timer_placeholder,
                              metrics_placeholder, alert_placeholder)
    elif not st.session_state.running:
        alert_placeholder.markdown(
            empty_state("🔔", "No alerts", "Start a session to see alerts here."),
            unsafe_allow_html=True)

    # ── Report section (after session ends) ───────────────────────────────
    if st.session_state.get("session_started") and not st.session_state.running:
        st.divider()
        st.markdown(section_label("Session Report"), unsafe_allow_html=True)

        st.markdown(trust_banner(
            "Reports include AI-generated wellness insights based on your session data. "
            "These are suggestions, not medical assessments.",
            icon="ℹ️"
        ), unsafe_allow_html=True)

        rc1, rc2, _ = st.columns([1, 1, 2])
        with rc1:
            if st.button("Generate PDF Report", key="gen_report_btn",
                         use_container_width=True):
                _generate_report()
        with rc2:
            if st.session_state.report_path:
                try:
                    with open(st.session_state.report_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f,
                            file_name="wellness_report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                except FileNotFoundError:
                    st.session_state.report_path = None


# ── Private helpers ───────────────────────────────────────────────────────────

def _start_session():
    """Initialize a new monitoring session."""
    st.session_state.running = True
    st.session_state.paused = False
    st.session_state.session_started = True
    st.session_state.report_path = None
    st.session_state.session_start_ts = time.time()
    st.session_state.user_bbox_cache = None
    st.session_state.pop("_final_summary", None)
    st.session_state.pop("_final_alerts", None)
    st.session_state.pop("_final_elapsed", None)

    reset_blink()
    reset_emotion()
    reset_aggregator()
    reset_notifier()
    reset_conversation()

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
    """Callback for the stop button — saves final state before rerun."""
    _final_summary = get_session_summary()
    st.session_state["_final_summary"] = _final_summary
    st.session_state["_final_alerts"] = get_notification_log()
    if st.session_state.session_start_ts:
        st.session_state["_final_elapsed"] = int(
            time.time() - st.session_state.session_start_ts)
    st.session_state.running = False
    st.session_state.paused = False
    typing_monitor.stop_monitoring()
    if st.session_state.get("active_user"):
        save_user_calibration(st.session_state.active_user)
    reset_bridge()


def _handle_chat(user_input, chat_container):
    """Process a chat message."""
    from src.ai.chatbot import chat

    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    with st.spinner("Thinking…"):
        reply = chat(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(reply)


def _generate_report():
    """Generate PDF wellness report."""
    with st.spinner("Generating AI wellness report…"):
        try:
            summary = get_session_summary()
            ai_text = generate_report_summary()
            save_session(summary, ai_text)
            pdf_path = generate_pdf_report(
                session_summary=summary,
                ai_summary=ai_text,
                posture_history=agg_state.get("posture_history", []),
                emotion_counts=agg_state.get("emotion_counts", {}),
            )
            st.session_state.report_path = pdf_path
            st.success("✅ Report ready!")
        except Exception as e:
            st.error(f"Report generation failed: {e}")


def _render_live_stream(col1, frame_placeholder, timer_placeholder,
                        metrics_placeholder, alert_placeholder, rtc_config):
    """Render WebRTC stream and update live metrics."""

    # Sync controls to bridge
    set_control("paused", st.session_state.paused)
    set_control("active_user", st.session_state.get("active_user"))
    set_control("show_skeleton", st.session_state.get("show_skeleton", False))
    _mic_is_on = st.session_state.get("_mic_active", False)
    set_control("mic_active", _mic_is_on)

    if _mic_is_on:
        _cur_voice = get_results().get("voice_data", {})
        if _cur_voice.get("status") == "stopped":
            set_control("voice_data", {
                "stress_signal": 0.0, "is_speaking": False,
                "status": "listening", "speech_rate": 0.0,
            })

    with col1:
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

        # Typing monitor
        typing_data = {"wpm": 0.0, "stress_signal": 0.0, "status": "stopped"}
        if st.session_state.get("typing_enabled", True):
            typing_data = typing_monitor.get_current_reading()
            update_typing(typing_data)

        # Process pending alerts
        pending = _r.get("pending_alerts", [])
        if pending:
            for _a in pending:
                process_alerts([_a], use_streamlit=True)
            set_control("pending_alerts", [])

        # Timer
        if st.session_state.session_start_ts:
            _elapsed_s = int(time.time() - st.session_state.session_start_ts)
            if st.session_state.paused:
                timer_placeholder.markdown(
                    session_timer(_elapsed_s, "paused"), unsafe_allow_html=True)
            else:
                timer_placeholder.markdown(
                    session_timer(_elapsed_s, "live"), unsafe_allow_html=True)

        # Metrics
        summary = get_session_summary()
        p_score = posture_data.get("posture_score") or summary.get("posture_score", 0)
        p_cat = posture_data.get("category", "unknown")
        e_conf = emotion_data.get("emotion_confidence", 0.0)
        cur_emo = emotion_data.get("current_emotion",
                                   summary.get("dominant_emotion", "neutral"))

        metrics_placeholder.markdown(
            metrics_grid(
                p_score, p_cat, blink_data.get("blink_rate", 0.0),
                cur_emo, e_conf, summary["seated_mins"],
                BLINK_THR, SEATED_MAX,
                typing_wpm=typing_data.get("wpm", 0.0),
                typing_stress=typing_data.get("stress_signal", 0.0),
                stress_index=summary.get("stress_index", 0.0),
                voice_rate=voice_data.get("speech_rate", 0.0),
                voice_stress_val=voice_data.get("stress_signal", 0.0),
                voice_speaking=voice_data.get("is_speaking", False),
                voice_status=voice_data.get("status", "stopped"),
            ),
            unsafe_allow_html=True,
        )

        alert_placeholder.markdown(
            alerts_html(get_notification_log()), unsafe_allow_html=True)


def _render_session_ended(frame_placeholder, timer_placeholder,
                          metrics_placeholder, alert_placeholder):
    """Render the post-session view with frozen metrics."""

    _fs = st.session_state.get("_final_summary")
    if _fs:
        frame_placeholder.empty()

        # Elapsed
        _fe = st.session_state.get("_final_elapsed", 0)
        if _fe:
            timer_placeholder.markdown(
                session_timer(_fe, "ended"), unsafe_allow_html=True)

        # Final metrics
        metrics_placeholder.markdown(
            metrics_grid(
                _fs.get("posture_score", 0),
                _fs.get("posture_trend", "unknown"),
                _fs.get("blink_rate", 0.0),
                _fs.get("dominant_emotion", "neutral"),
                _fs.get("emotion_pct", 0.0),
                _fs.get("seated_mins", 0),
                BLINK_THR, SEATED_MAX,
                typing_wpm=_fs.get("typing_wpm", 0.0),
                typing_stress=_fs.get("typing_stress", 0.0),
                stress_index=_fs.get("stress_index", 0.0),
                voice_stress_val=_fs.get("voice_stress", 0.0),
            ),
            unsafe_allow_html=True,
        )

    # Final alerts
    _fa = st.session_state.get("_final_alerts")
    if _fa:
        alert_placeholder.markdown(alerts_html(_fa), unsafe_allow_html=True)
    else:
        alert_placeholder.markdown(
            empty_state("🎉", "No alerts!", "Great session — no concerns detected."),
            unsafe_allow_html=True)
