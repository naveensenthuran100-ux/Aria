"""
Chat Page — Full-Page AI Chatbot
=================================
Dedicated chat with session context, suggested prompts,
HCAI disclaimers, and graceful API error handling.
"""

import streamlit as st

from src.ai.chatbot import chat, reset_conversation
from src.fusion.aggregator import get_session_summary
from ui import copy as C
from ui.components import (
    disclaimer_bar, trust_banner, EMOTION_EMOJI,
)


def render():
    """Render the full-page chatbot experience."""

    # Determine status
    if st.session_state.running and st.session_state.paused:
        status = "paused"
    elif st.session_state.running:
        status = "live"
    else:
        status = "idle"

    # Header
    st.markdown(
        f'<div style="margin-bottom:20px;">'
        f'<h1 style="font-size:1.6rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.03em;margin:0;">Al Wellness Chat</h1>'
        f'<p style="font-size:0.85rem;color:var(--text-muted);font-weight:500;margin:4px 0 0;">Talk to Aria about your posture and wellness.</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Session context header
    summary = get_session_summary()
    ee = EMOTION_EMOJI.get(summary["dominant_emotion"], "😐")
    st.markdown(
        f'<div class="chat-header">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">'
        f'<span style="font-weight:700;color:var(--text-primary);font-size:0.92rem">💬 {C.CHAT_TITLE}</span>'
        f'<span style="font-size:0.68rem;color:var(--text-muted);font-weight:500">{C.CHAT_SUBTITLE}</span>'
        f'</div>'
        f'<div class="chat-context">'
        f'<span class="chat-stat">Posture: <span class="chat-stat-val">{summary["posture_score"]}/100</span></span>'
        f'<span class="chat-stat">Blinks: <span class="chat-stat-val">{summary["blink_rate"]}/min</span></span>'
        f'<span class="chat-stat">Emotion: <span class="chat-stat-val">{ee} {summary["dominant_emotion"].title()}</span></span>'
        f'<span class="chat-stat">Seated: <span class="chat-stat-val">{summary["seated_mins"]} min</span></span>'
        f'</div>'
        f'</div>', unsafe_allow_html=True)

    # Trust banner
    st.markdown(trust_banner(C.CHAT_TRUST, icon="ℹ️"), unsafe_allow_html=True)

    # Chat history
    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.messages:
            user_name = summary.get("user_name", "there")
            st.markdown(
                f'<div style="text-align:center;padding:36px 20px;color:var(--text-muted)">'
                f'<div style="font-size:2rem;margin-bottom:12px">💬</div>'
                f'<p style="font-weight:600;color:var(--text-secondary);margin:0 0 4px;font-size:0.88rem">'
                f'{C.CHAT_EMPTY_HI.format(name=user_name)}</p>'
                f'<p style="font-size:0.78rem;margin:0;line-height:1.5">'
                f'{C.CHAT_EMPTY_DESC}</p>'
                f'</div>', unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # Suggested prompts (when no messages yet)
    if not st.session_state.messages:
        st.markdown(section_label("Suggestions"), unsafe_allow_html=True)
        sugg_cols = st.columns(len(C.CHAT_PROMPTS))
        for i, sugg in enumerate(C.CHAT_PROMPTS):
            with sugg_cols[i]:
                if st.button(sugg, key=f"sugg_{i}", use_container_width=True):
                    _send_message(sugg, chat_container)

    # Chat input
    user_input = st.chat_input(C.CHAT_INPUT_PLACEHOLDER)
    if user_input:
        _send_message(user_input, chat_container)

    # Clear chat button
    if st.session_state.messages:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        if st.button(C.CHAT_CLEAR, key="clear_chat", use_container_width=True):
            reset_conversation()
            st.session_state.messages = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Disclaimer
    st.markdown(disclaimer_bar(), unsafe_allow_html=True)


def _send_message(text, chat_container):
    """Send a message to Aria and display the response."""
    st.session_state.messages.append({"role": "user", "content": text})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(text)
    with st.spinner("Thinking…"):
        try:
            reply = chat(text)
        except Exception:
            reply = C.CHAT_API_ERROR
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(reply)
