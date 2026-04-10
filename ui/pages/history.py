"""
Session History Page
=====================
Browse past sessions with trend summary and better empty state.
"""

import streamlit as st

from src.data.session_db import get_recent_sessions
from ui import copy as C
from ui.charts import render_trend_graph
from ui.components import (
    section_label, session_card, empty_state, trust_banner, wellness_color_hex,
    EMOTION_EMOJI,
)


def render():
    """Render the session history page."""

    # Title
    st.markdown(
        f'<div style="margin-bottom:16px">'
        f'<h1 style="font-size:1.6rem;font-weight:800;color:var(--text-primary);margin:0;letter-spacing:-0.03em">'
        f'Session History</h1>'
        f'<p style="font-size:0.85rem;color:var(--text-muted);margin:4px 0 0">'
        f'{C.HISTORY_SUBTITLE}</p>'
        f'</div>', unsafe_allow_html=True)

    # Fetch sessions
    try:
        sessions = get_recent_sessions(limit=30)
    except Exception:
        sessions = []

    if not sessions:
        st.markdown(empty_state("📊", C.HISTORY_EMPTY_TITLE, C.HISTORY_EMPTY_DESC),
                    unsafe_allow_html=True)

        # CTA to go home
        st.markdown('<div style="text-align:center;margin-top:12px">', unsafe_allow_html=True)
        if st.button(C.HISTORY_EMPTY_CTA, key="history_go_home", use_container_width=False):
            st.session_state.page = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # ── Trend Summary Card ────────────────────────────────────────────
        total = len(sessions)
        avg_posture = sum(s.get("posture_score", 0) for s in sessions) / total
        avg_stress = sum(s.get("stress_index", 0.0) for s in sessions) / total
        avg_wellness = int((1 - avg_stress) * 100)
        total_mins = sum(s.get("duration_mins", 0) for s in sessions)

        wc = wellness_color_hex(avg_wellness)

        # Trend card
        st.markdown(
            f'<div class="aria-card" style="padding:20px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
            f'<div>'
            f'<div style="font-size:0.75rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">'
            f'📈 Log Overview</div>'
            f'<div style="font-size:0.9rem;color:var(--text-primary);font-weight:600;">'
            f'{total} sessions · {total_mins:.0f} total minutes</div>'
            f'</div>'
            f'<div style="text-align:right">'
            f'<div style="font-size:0.75rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">'
            f'Average Wellness</div>'
            f'<div style="font-size:2.2rem;font-weight:800;color:{wc};letter-spacing:-0.03em;line-height:1;">{avg_wellness}%</div>'
            f'</div>'
            f'</div>'
            f'</div>', unsafe_allow_html=True)

        # Trend Graph
        st.markdown(
            f'<div class="aria-card-flat" style="padding:20px;margin-bottom:16px;">'
            f'<div style="margin-bottom:20px;">'
            f'<div style="font-size:1rem;font-weight:700;color:var(--text-primary);display:flex;align-items:center;gap:8px;">'
            f'<span>📉</span> Longitudinal Posture Trend</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        is_dark = st.session_state.get("dark_mode", False)
        render_trend_graph(sessions, is_dark_mode=is_dark)
        st.markdown('</div>', unsafe_allow_html=True)

        # Session list
        st.markdown(section_label("Recent Sessions"), unsafe_allow_html=True)

        for sess in sessions:
            st.markdown(session_card(sess), unsafe_allow_html=True)

            # Expandable AI summary
            ai_summary = sess.get("ai_summary", "")
            if ai_summary:
                with st.expander("View AI Summary", expanded=False):
                    st.markdown(ai_summary)
                    st.markdown(trust_banner(C.COACHING_TRUST, icon="ℹ️"),
                                unsafe_allow_html=True)

    # Trust banner
    st.markdown(trust_banner(C.HISTORY_TRUST, icon="🔒"), unsafe_allow_html=True)
