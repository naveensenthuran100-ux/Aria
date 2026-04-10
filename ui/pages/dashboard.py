"""
Dashboard Page — High-level Overview
====================================
The landing view for the main application shell. Shows today's metrics,
trend graphs, and tips, matching the premium desktop utility layout.
"""

import streamlit as st
import datetime

from src.data.session_db import get_recent_sessions
from ui import copy as C
from ui.charts import render_trend_graph
from ui.components import wellness_color_hex, empty_state


def render():
    """Render the dashboard overview."""
    st.markdown(
        f'<div style="margin-bottom:20px;">'
        f'<h1 style="font-size:1.6rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.03em;margin:0;">Dashboard</h1>'
        f'<p style="font-size:0.85rem;color:var(--text-muted);font-weight:500;margin:4px 0 0;">Overview of your recent wellness and posture data.</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    try:
        sessions = get_recent_sessions(limit=20)
    except Exception:
        sessions = []

    if not sessions:
        _render_empty_dashboard()
        return

    # Calculate metrics
    total_sessions = len(sessions)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    today_sessions = []
    for s in sessions:
        ts = s.get("timestamp")
        if isinstance(ts, (int, float)):
            # convert posix to str
            dt_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            if dt_str == today_str:
                today_sessions.append(s)
        elif isinstance(ts, str) and ts.startswith(today_str):
            today_sessions.append(s)
            
    total_usage_mins = sum(s.get("duration_mins", 0) for s in sessions)
    today_usage_mins = sum(s.get("duration_mins", 0) for s in today_sessions)
    
    avg_posture = int(sum(s.get("posture_score", 0) for s in sessions) / max(1, total_sessions))
    today_posture = int(sum(s.get("posture_score", 0) for s in today_sessions) / max(1, len(today_sessions))) if today_sessions else avg_posture

    c_posture = wellness_color_hex(today_posture)

    # ── Top Row: Hero Metrics ────────────────────────────────────────────────
    col1, col2, col3 = st.columns([1.5, 1, 1])

    with col1:
        st.markdown(
            f'<div class="aria-card" style="display:flex;flex-direction:column;align-items:center;text-align:center;padding:24px;">'
            f'<div style="font-size:0.75rem;font-weight:700;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">'
            f'Today\'s Avg Posture Score</div>'
            f'<div style="position:relative;width:120px;height:120px;border-radius:50%;display:flex;align-items:center;justify-content:center;'
            f'border:8px solid var(--surface-raised);border-left-color:{c_posture};border-top-color:{c_posture};transform:rotate(-45deg);margin-bottom:12px;">'
            f'<div style="transform:rotate(45deg);"><span style="font-size:2.5rem;font-weight:800;color:var(--text-primary);">{today_posture}</span>'
            f'<span style="font-size:0.8rem;color:var(--text-muted);">/100</span></div>'
            f'</div>'
            f'<div style="font-size:0.85rem;color:var(--text-secondary);font-weight:500;">'
            f'{C.ACTIVE_KEEP_UP if today_posture > 75 else "Needs some improvement"}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f'<div class="aria-card" style="padding:20px;height:100%;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:16px;">'
            f'<span style="font-size:0.8rem;font-weight:700;color:var(--text-primary);">Total Sessions</span>'
            f'<span style="font-size:1.1rem;">📈</span>'
            f'</div>'
            f'<div style="font-size:2.5rem;font-weight:800;color:var(--text-primary);line-height:1;margin-bottom:4px;">{total_sessions}</div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);line-height:1.4;">Cumulative sessions tracked so far</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f'<div class="aria-card" style="padding:20px;height:100%;">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:16px;">'
            f'<span style="font-size:0.8rem;font-weight:700;color:var(--text-primary);">Usage Time</span>'
            f'<span style="font-size:1.1rem;">⏱️</span>'
            f'</div>'
            f'<div style="font-size:2.5rem;font-weight:800;color:var(--text-primary);line-height:1;margin-bottom:4px;">{today_usage_mins} <span style="font-size:1rem;color:var(--text-muted);">min</span></div>'
            f'<div style="font-size:0.7rem;color:var(--text-muted);line-height:1.4;">Total session time for today</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Middle Row: Trend Graph ──────────────────────────────────────────────
    st.markdown(
        f'<div class="aria-card-flat" style="padding:20px;margin-bottom:16px;">'
        f'<div style="margin-bottom:20px;">'
        f'<div style="font-size:1rem;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px;">'
        f'<span>📉</span> Posture Score Trend</div>'
        f'<div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">{C.EXPLAIN_TREND}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    is_dark = st.session_state.get("dark_mode", False)
    render_trend_graph(sessions, is_dark_mode=is_dark)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Bottom Row: Tips & Breakdown ─────────────────────────────────────────
    bcol1, bcol2 = st.columns([1, 1.5])
    
    with bcol1:
        st.markdown(
            f'<div class="aria-card" style="padding:20px;height:100%;">'
            f'<div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px;margin-bottom:16px;">'
            f'<span>✨</span> Posture Improvement Tips</div>'
            f'<ul style="padding-left:20px;margin:0;color:var(--text-secondary);font-size:0.8rem;line-height:1.8;">'
            f'<li>Keep your neck straight and pull your shoulders back.</li>'
            f'<li>Adjust your monitor to eye level.</li>'
            f'<li>Stretch every 30 minutes.</li>'
            f'<li>Sit with your back fully against the chair.</li>'
            f'<li>Keep your feet flat on the floor.</li>'
            f'</ul>'
            f'</div>',
            unsafe_allow_html=True
        )
        
    with bcol2:
        good_mins = int(today_usage_mins * (today_posture / 100))
        bad_mins = today_usage_mins - good_mins
        
        st.markdown(
            f'<div class="aria-card" style="padding:20px;height:100%;">'
            f'<div style="font-size:0.9rem;font-weight:700;color:var(--text-primary);margin-bottom:12px;">Today\'s Posture Breakdown</div>',
            unsafe_allow_html=True
        )
        from ui.charts import render_pie_chart
        is_dark = st.session_state.get("dark_mode", False)
        render_pie_chart(good_mins, bad_mins, is_dark_mode=is_dark)
        st.markdown('</div>', unsafe_allow_html=True)
        
    _render_guided_stretches()


def _render_guided_stretches():
    """Render a full width guided stretches panel."""
    st.markdown(
        f'<div style="margin-top:24px;"></div>'
        f'<div class="aria-card" style="padding:24px;">'
        f'<div style="font-size:1.1rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.02em;margin-bottom:6px;">'
        f'🧘 Guided Stretches</div>'
        f'<div style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:20px;">'
        f'Follow this simple 3-step neck mobility routine to relieve tension.</div>',
        unsafe_allow_html=True
    )
    
    # 3-column photo layout for Neck
    st.markdown('<div style="font-size:0.95rem;font-weight:700;color:var(--primary);margin:16px 0 12px;">Neck Mobility Routine</div>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    
    with g1:
        st.image("ui/assets/media__1775835179563.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">1. Neutral Position</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Sit up straight.</div>', unsafe_allow_html=True)
        
    with g2:
        st.image("ui/assets/media__1775835180446.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">2. Deep Breath</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Inhale deeply and hold.</div>', unsafe_allow_html=True)
        
    with g3:
        st.image("ui/assets/media__1775835183996.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">3. Lateral Stretch</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Gently tilt neck for 15s.</div>', unsafe_allow_html=True)

    # 3-column photo layout for Shoulders
    st.markdown('<div style="font-size:0.95rem;font-weight:700;color:var(--primary);margin:32px 0 12px;">Shoulder Tension Relief</div>', unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    
    with s1:
        st.image("ui/assets/media__1775836424987.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">1. Shoulder Drop</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Actively lower shoulders down.</div>', unsafe_allow_html=True)
        
    with s2:
        st.image("ui/assets/media__1775836425012.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">2. Rest & Reset</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Hold the lowered stance.</div>', unsafe_allow_html=True)
        
    with s3:
        st.image("ui/assets/media__1775836473328.png", use_container_width=True)
        st.markdown('<div style="text-align:center;font-weight:600;font-size:0.85rem;color:var(--text-primary);margin-top:8px;">3. Breathe Out</div><div style="text-align:center;font-size:0.75rem;color:var(--text-muted);">Exhale fully, retracting scapula.</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)


def _render_empty_dashboard():
    """Empty state when no sessions are found."""
    st.markdown(empty_state("✨", "Dashboard Empty", "Start a monitoring session to begin populating your wellness trends."), unsafe_allow_html=True)
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="start-btn" style="text-align:center;">', unsafe_allow_html=True)
    if st.button("Start First Session", key="dash_start", use_container_width=False):
        st.session_state.page = "monitoring"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

