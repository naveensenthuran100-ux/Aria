"""
Home Page — Core Experience (3 modes)
======================================
Handles:
  1. Idle state — greeting + wellness dial + start session
  2. Live monitoring — WebRTC + metrics + alerts + chat
  3. Session ended — coaching summary + reflection + report
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
from src.data.session_db import save_session, get_recent_sessions
from src.io import typing_monitor
from src.audio import voice_stress

from ui import copy as C
from ui.components import (
    metrics_grid, wellness_bar, alerts_html, session_timer,
    empty_state, trust_banner, disclaimer_bar,
    greeting_card, wellness_dial, signal_strip,
    coaching_card, last_session_card,
    EMOTION_EMOJI,
)

import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

BLINK_THR = config["alerts"]["blink_rate_low"]
SEATED_MAX = config["alerts"]["sitting_duration_mins"]


def render(rtc_config):
    """Render the home page in the appropriate mode."""

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

    # ── Route to mode ─────────────────────────────────────────────────────
    if st.session_state.running:
        _render_live(rtc_config)
    elif st.session_state.get("session_started"):
        _render_summary()
    else:
        _render_idle()


# ══════════════════════════════════════════════════════════════════════════════
#  MODE 1: IDLE — Greeting + Wellness Dial + Start CTA
# ══════════════════════════════════════════════════════════════════════════════

def _render_idle():
    """Home screen when no session is active."""

    user = st.session_state.get("active_user", "there")

    # Greeting
    st.markdown(greeting_card(user, C.HOME_SUBTITLE_IDLE), unsafe_allow_html=True)

    # Wellness dial from last session (if exists)
    try:
        _sessions = get_recent_sessions(limit=1)
    except Exception:
        _sessions = []

    if _sessions:
        last = _sessions[0]
        last_wellness = max(0, min(100, int((1 - last.get("stress_index", 0.5)) * 100)))
        st.markdown(wellness_dial(last_wellness, "Wellness Score",
                                  "Based on your last session"), unsafe_allow_html=True)
        st.markdown(last_session_card(last), unsafe_allow_html=True)
    else:
        # No sessions yet — motivational empty state
        st.markdown(wellness_dial(0, "Wellness Score", C.HOME_NO_SESSIONS),
                    unsafe_allow_html=True)

    # Signal status strip
    cam_on = True  # Camera is always available
    mic_on = st.session_state.get("_mic_active", False)
    kb_on = st.session_state.get("typing_enabled", True)
    st.markdown(signal_strip(cam_on, mic_on, kb_on), unsafe_allow_html=True)

    # Trust banner
    st.markdown(trust_banner(C.LOCAL_PROCESSING, icon="🔒"), unsafe_allow_html=True)

    # Start Session CTA
    st.markdown('<div class="start-btn">', unsafe_allow_html=True)
    if st.button(C.HOME_START_CTA, key="start_btn", use_container_width=True):
        _start_session()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown(disclaimer_bar(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MODE 2: LIVE — Video + Metrics + Alerts + Chat
# ══════════════════════════════════════════════════════════════════════════════

def _render_live(rtc_config):
    """Live monitoring mode."""

    # Timer
    timer_placeholder = st.empty()

    # Signal strip
    mic_on = st.session_state.get("_mic_active", False)
    kb_on = st.session_state.get("typing_enabled", True)
    st.markdown(signal_strip(True, mic_on, kb_on), unsafe_allow_html=True)

    # Layout: Two columns
    col1, col2 = st.columns([1.3, 1])

    with col1:
        # Live Feed
        st.markdown(section_label("Live Feed"), unsafe_allow_html=True)
        frame_placeholder = st.empty()

        # Toggles
        _tc1, _tc2 = st.columns(2)
        with _tc1:
            st.toggle("Show posture skeleton", key="show_skeleton")
        with _tc2:
            _mic_status = st.session_state.get("_mic_active", False)
            _mic_label = "🎙️ Mic ON" if _mic_status else "🎙️ Mic OFF"
            _mic_color = "var(--success)" if _mic_status else "var(--text-muted)"
            st.markdown(
                f'<span style="font-size:0.82rem;color:{_mic_color};font-weight:500">'
                f'{_mic_label}</span>', unsafe_allow_html=True)

        # Metrics placeholder
        metrics_placeholder = st.empty()

        # Wellness bar placeholder
        wellness_placeholder = st.empty()

        # Session Controls
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

        # Alerts
        st.markdown(section_label("Alerts"), unsafe_allow_html=True)
        alert_placeholder = st.empty()

    # Right column: Chat + Snapshot
    with col2:
        st.markdown(section_label("Chat with Aria"), unsafe_allow_html=True)
        chat_container = st.container(height=300)
        with chat_container:
            if not st.session_state.messages:
                summary = get_session_summary()
                st.markdown(
                    f'<div style="text-align:center;padding:30px 16px;color:var(--text-muted)">'
                    f'<div style="font-size:1.8rem;margin-bottom:10px">💬</div>'
                    f'<p style="font-weight:600;color:var(--text-secondary);margin:0 0 4px;font-size:0.85rem">'
                    f'{C.CHAT_EMPTY_HI.format(name=summary.get("user_name", "there"))}</p>'
                    f'<p style="font-size:0.78rem;margin:0;line-height:1.5">'
                    f'{C.CHAT_EMPTY_DESC}</p>'
                    f'</div>', unsafe_allow_html=True)
            else:
                for msg in st.session_state.messages:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

        user_input = st.chat_input(C.CHAT_INPUT_PLACEHOLDER)
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

        st.markdown(disclaimer_bar(), unsafe_allow_html=True)

    # ── WebRTC Stream ─────────────────────────────────────────────────────
    _run_webrtc(col1, frame_placeholder, timer_placeholder,
                metrics_placeholder, wellness_placeholder,
                alert_placeholder, rtc_config)


# ══════════════════════════════════════════════════════════════════════════════
#  MODE 3: SESSION ENDED — Summary + Coaching + Reflection + Report
# ══════════════════════════════════════════════════════════════════════════════

def _render_summary():
    """Post-session summary with AI coaching and reflection."""

    _fs = st.session_state.get("_final_summary", {})
    _fe = st.session_state.get("_final_elapsed", 0)
    _fa = st.session_state.get("_final_alerts", [])

    # Title
    st.markdown(
        f'<div style="text-align:center;margin-bottom:8px">'
        f'<p style="font-size:1.3rem;font-weight:800;color:var(--text-primary);margin:0;letter-spacing:-0.02em">'
        f'{C.SUMMARY_TITLE}</p>'
        f'<p style="font-size:0.82rem;color:var(--text-muted);margin:4px 0 0">'
        f'{_fe // 60}m {_fe % 60}s monitored</p>'
        f'</div>', unsafe_allow_html=True)

    # Wellness dial
    wellness_pct = max(0, min(100, int((1 - _fs.get("stress_index", 0.5)) * 100)))
    st.markdown(wellness_dial(wellness_pct, "Session Wellness",
                              "AI estimate · based on this session's signals"),
                unsafe_allow_html=True)

    # Metrics snapshot
    if _fs:
        st.markdown(section_label("Session Metrics"), unsafe_allow_html=True)
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        s1.metric("Posture", f"{_fs.get('posture_score', 0)}/100")
        s2.metric("Blinks/min", f"{_fs.get('blink_rate', 0.0):.1f}")
        s3, s4 = st.columns(2)
        ee = EMOTION_EMOJI.get(_fs.get('dominant_emotion', 'neutral'), '😐')
        s3.metric("Emotion", f"{ee} {_fs.get('dominant_emotion', 'neutral').title()}")
        s4.metric("Seated", f"{_fs.get('seated_mins', 0)} min")
        st.markdown('</div>', unsafe_allow_html=True)

    # AI Coaching Summary
    st.markdown(section_label(C.COACHING_TITLE), unsafe_allow_html=True)

    if "coaching_bullets" not in st.session_state:
        with st.spinner("Generating wellness insights…"):
            try:
                ai_text = generate_report_summary()
                # Split into bullets
                bullets = [line.strip().lstrip("•-–").strip()
                           for line in ai_text.split("\n")
                           if line.strip() and len(line.strip()) > 10][:4]
                st.session_state["coaching_bullets"] = bullets
                st.session_state["coaching_raw"] = ai_text
            except Exception:
                st.session_state["coaching_bullets"] = [
                    "Your session data has been saved.",
                    "Check the chat for personalised suggestions.",
                    "Generate a full PDF report for detailed analysis."
                ]
                st.session_state["coaching_raw"] = ""

    st.markdown(coaching_card(st.session_state.get("coaching_bullets", [])),
                unsafe_allow_html=True)

    # Reflection prompt
    from ui.components import reflection_prompt
    reflection_prompt()

    if st.session_state.get("reflection_response") is not None:
        labels = ["great", "good", "okay", "not great", "difficult"]
        idx = st.session_state.reflection_response
        st.markdown(
            f'<div style="text-align:center;font-size:0.78rem;color:var(--primary);font-weight:600;margin:8px 0">'
            f'Thanks for sharing — you said you feel {labels[idx]}.</div>',
            unsafe_allow_html=True)

    # Alerts from session
    if _fa:
        st.markdown(section_label("Session Alerts"), unsafe_allow_html=True)
        st.markdown(alerts_html(_fa), unsafe_allow_html=True)

    # Report section
    st.divider()
    st.markdown(section_label("Session Report"), unsafe_allow_html=True)
    st.markdown(trust_banner(C.REPORT_TRUST, icon="ℹ️"), unsafe_allow_html=True)

    rc1, rc2, rc3 = st.columns([1, 1, 1])
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
    with rc3:
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button("New Session", key="new_session_btn", use_container_width=True):
            # Clear session state for new session
            st.session_state.session_started = False
            st.session_state.pop("_final_summary", None)
            st.session_state.pop("_final_alerts", None)
            st.session_state.pop("_final_elapsed", None)
            st.session_state.pop("coaching_bullets", None)
            st.session_state.pop("coaching_raw", None)
            st.session_state.pop("reflection_response", None)
            st.session_state.messages = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(disclaimer_bar(), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PRIVATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

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
    st.session_state.pop("coaching_bullets", None)
    st.session_state.pop("coaching_raw", None)
    st.session_state.pop("reflection_response", None)

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
    """Callback for the stop button."""
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

    # Save session to DB
    try:
        save_session(_final_summary, "")
    except Exception:
        pass

    reset_bridge()


def _handle_chat(user_input, chat_container):
    """Process a chat message."""
    from src.ai.chatbot import chat

    st.session_state.messages.append({"role": "user", "content": user_input})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(user_input)
    with st.spinner("Thinking…"):
        try:
            reply = chat(user_input)
        except Exception:
            reply = C.CHAT_API_ERROR
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(reply)


def _generate_report():
    """Generate PDF wellness report."""
    with st.spinner("Generating AI wellness report…"):
        try:
            summary = st.session_state.get("_final_summary") or get_session_summary()
            ai_text = st.session_state.get("coaching_raw", "") or generate_report_summary()
            save_session(summary, ai_text)
            pdf_path = generate_pdf_report(
                session_summary=summary,
                ai_summary=ai_text,
                posture_history=agg_state.get("posture_history", []),
                emotion_counts=agg_state.get("emotion_counts", {}),
            )
            st.session_state.report_path = pdf_path
            st.success(f"✅ {C.REPORT_READY}")
        except Exception as e:
            st.error(f"Report generation failed: {e}")


def _run_webrtc(col1, frame_placeholder, timer_placeholder,
                metrics_placeholder, wellness_placeholder,
                alert_placeholder, rtc_config):
    """Render WebRTC stream and update live metrics."""

    # Sync controls
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

        # Typing
        typing_data = {"wpm": 0.0, "stress_signal": 0.0, "status": "stopped"}
        if st.session_state.get("typing_enabled", True):
            typing_data = typing_monitor.get_current_reading()
            update_typing(typing_data)

        # Process alerts
        pending = _r.get("pending_alerts", [])
        if pending:
            for _a in pending:
                process_alerts([_a], use_streamlit=True)
            set_control("pending_alerts", [])

        # Timer
        if st.session_state.session_start_ts:
            _elapsed_s = int(time.time() - st.session_state.session_start_ts)
            _timer_status = "paused" if st.session_state.paused else "live"
            timer_placeholder.markdown(
                session_timer(_elapsed_s, _timer_status), unsafe_allow_html=True)

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

        # Wellness bar
        wellness_placeholder.markdown(
            wellness_bar(summary.get("stress_index", 0.0)),
            unsafe_allow_html=True,
        )

        # Alerts
        alert_placeholder.markdown(
            alerts_html(get_notification_log()), unsafe_allow_html=True)

    else:
        # WebRTC not playing yet
        alert_placeholder.markdown(
            empty_state("🔔", "No alerts", "Alerts will appear once monitoring begins."),
            unsafe_allow_html=True)
