"""
Aria v2 — Reusable Component Library
=====================================
HTML builder functions for all UI components.
Each function returns an HTML string for st.markdown(..., unsafe_allow_html=True).

RULES:
  • No leading whitespace (4+ spaces → Streamlit code blocks)
  • Use textwrap.dedent or single-line f-strings
  • All colours reference CSS custom properties where possible
"""

import time
import textwrap
import streamlit as st
from datetime import datetime

from ui import copy as C


# ── Display Constants ─────────────────────────────────────────────────────────

EMOTION_EMOJI = {
    "happy": "😊", "neutral": "😐", "sad": "😢",
    "angry": "😠", "fear": "😨", "disgust": "🤢", "surprise": "😮"
}

EMOTION_COLOR = {
    "happy": "#10B981", "neutral": "#64748B", "sad": "#3B82F6",
    "angry": "#EF4444", "fear": "#8B5CF6", "disgust": "#F97316", "surprise": "#EAB308"
}

ALERT_CLASS = {
    "posture": "al-posture", "blink": "al-blink",
    "seated": "al-seated", "combined": "al-combined"
}

ALERT_ACTIONS = {
    "posture": C.ALERT_POSTURE_ACTION,
    "blink": C.ALERT_BLINK_ACTION,
    "seated": C.ALERT_SEATED_ACTION,
    "combined": C.ALERT_COMBINED_ACTION,
}

SIGNAL_EXPLANATIONS = {
    "posture": C.EXPLAIN_POSTURE,
    "blink": C.EXPLAIN_BLINK,
    "emotion": C.EXPLAIN_EMOTION,
    "seated": C.EXPLAIN_SEATED,
    "typing": C.EXPLAIN_TYPING,
    "voice": C.EXPLAIN_VOICE,
    "wellness": C.EXPLAIN_WELLNESS,
}


# ── Colour Helpers ────────────────────────────────────────────────────────────

def posture_color(score):
    if score >= 75: return "var(--success)"
    if score >= 50: return "var(--warning)"
    return "var(--danger)"

def posture_color_hex(score):
    if score >= 75: return "#10B981"
    if score >= 50: return "#F59E0B"
    return "#EF4444"

def blink_color(rate, threshold):
    if rate >= threshold: return "var(--success)"
    if rate >= threshold * 0.7: return "var(--warning)"
    return "var(--danger)"

def seated_color(mins, max_mins):
    if mins < max_mins * 0.5: return "var(--success)"
    if mins < max_mins: return "var(--warning)"
    return "var(--danger)"

def stress_color(val):
    if val < 0.35: return "var(--success)"
    if val < 0.65: return "var(--warning)"
    return "var(--danger)"

def stress_color_hex(val):
    if val < 0.35: return "#10B981"
    if val < 0.65: return "#F59E0B"
    return "#EF4444"

def wellness_color(pct):
    if pct >= 70: return "var(--success)"
    if pct >= 40: return "var(--warning)"
    return "var(--danger)"

def wellness_color_hex(pct):
    if pct >= 70: return "#10B981"
    if pct >= 40: return "#F59E0B"
    return "#EF4444"

def voice_color(stress):
    if stress < 0.3: return "var(--success)"
    if stress < 0.65: return "var(--warning)"
    return "var(--danger)"

def confidence_level(pct):
    if pct >= 70: return "High", "conf-high"
    if pct >= 40: return "Medium", "conf-med"
    return "Low", "conf-low"


def _h(html_str):
    """Strip leading whitespace to prevent Streamlit code-block rendering."""
    return textwrap.dedent(html_str).strip()


# ── Top App Bar ───────────────────────────────────────────────────────────────

def app_header(status="idle", user_name=None):
    if status == "live":
        dot_cls, chip_cls, status_txt = "dot-live", "chip-live", "Monitoring"
    elif status == "paused":
        dot_cls, chip_cls, status_txt = "dot-paused", "chip-paused", "Paused"
    else:
        dot_cls, chip_cls, status_txt = "dot-idle", "chip-idle", "Ready"

    user_chip = ""
    if user_name:
        user_chip = f'<span class="aria-chip chip-user">👤 {user_name}</span>'

    return _h(f"""
    <div class="aria-topbar">
    <div class="aria-topbar-left">
    <div class="aria-logo">🧠</div>
    <div>
    <p class="aria-topbar-title">Aria</p>
    <p class="aria-topbar-sub">AI Wellness Companion</p>
    </div>
    </div>
    <div class="aria-topbar-right">
    <span class="aria-chip {chip_cls}">
    <span class="status-dot {dot_cls}"></span>{status_txt}
    </span>
    {user_chip}
    </div>
    </div>
    """)


# ── Navigation ────────────────────────────────────────────────────────────────

def render_nav_buttons(active_tab):
    """Render functional navigation as styled Streamlit buttons."""
    tabs = ["home", "chat", "history", "settings"]
    labels = ["🏠 Home", "💬 Chat", "📊 History", "⚙️ Settings"]

    st.markdown('<div style="background:var(--nav-bg);border-radius:14px;padding:4px;margin-bottom:16px">', unsafe_allow_html=True)
    cols = st.columns(len(tabs))
    for i, (key, label) in enumerate(zip(tabs, labels)):
        with cols[i]:
            if key == active_tab:
                st.markdown(
                    f'<div style="text-align:center;padding:9px 4px;border-radius:11px;'
                    f'background:var(--nav-active-bg);color:var(--primary);font-weight:600;'
                    f'font-size:0.78rem;box-shadow:var(--shadow-sm);letter-spacing:-0.01em">'
                    f'{label}</div>', unsafe_allow_html=True)
            else:
                if st.button(label, key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Greeting ──────────────────────────────────────────────────────────────────

def greeting_card(user_name, subtitle=""):
    hour = datetime.now().hour
    if hour < 12:
        greet = C.HOME_GREETING_MORNING.format(name=user_name)
    elif hour < 18:
        greet = C.HOME_GREETING_AFTERNOON.format(name=user_name)
    else:
        greet = C.HOME_GREETING_EVENING.format(name=user_name)

    sub_html = f'<p class="greeting-sub">{subtitle}</p>' if subtitle else ''

    return (
        f'<div class="greeting">'
        f'<h1 class="greeting-title">{greet}</h1>'
        f'{sub_html}'
        f'</div>'
    )


# ── Wellness Dial ─────────────────────────────────────────────────────────────

def wellness_dial(score, label="Wellness Score", sub="AI estimate · based on all active signals"):
    """Render a large radial wellness score display."""
    pct = max(0, min(100, int(score)))
    color = wellness_color_hex(pct)

    # SVG ring
    r = 65
    circ = 2 * 3.14159 * r
    offset = circ - (pct / 100) * circ

    svg = (
        f'<svg width="160" height="160" viewBox="0 0 160 160">'
        f'<circle cx="80" cy="80" r="{r}" fill="none" stroke="var(--border)" stroke-width="8" />'
        f'<circle cx="80" cy="80" r="{r}" fill="none" stroke="{color}" stroke-width="8" '
        f'stroke-dasharray="{circ}" stroke-dashoffset="{offset}" '
        f'stroke-linecap="round" transform="rotate(-90 80 80)" '
        f'style="transition: stroke-dashoffset 1s ease" />'
        f'<text x="80" y="72" text-anchor="middle" '
        f'style="font-size:2.5rem;font-weight:800;fill:{color};font-family:Inter,sans-serif;letter-spacing:-0.03em">'
        f'{pct}</text>'
        f'<text x="80" y="96" text-anchor="middle" '
        f'style="font-size:0.7rem;fill:var(--text-muted);font-family:Inter,sans-serif;font-weight:600;letter-spacing:0.06em;text-transform:uppercase">'
        f'{label}</text>'
        f'</svg>'
    )

    return (
        f'<div class="wellness-dial">'
        f'{svg}'
        f'<p class="wellness-dial-sub">{sub}</p>'
        f'</div>'
    )


# ── Signal / Metric Card ─────────────────────────────────────────────────────

def signal_card(label, value, unit="", sub="", color="var(--text-primary)",
                progress=None, icon="", conf_pct=None, signal_key=None):
    """Individual signal metric card with optional confidence badge and explanation button."""

    # Confidence badge
    conf_html = ""
    if conf_pct is not None:
        cl, cc = confidence_level(conf_pct)
        conf_html = f'<span class="conf-badge {cc}">{cl} · {conf_pct:.0f}%</span>'

    # Progress bar
    prog_html = ""
    if progress is not None:
        pct = min(100, max(0, int(progress)))
        prog_html = (
            f'<div class="prog-track">'
            f'<div class="prog-fill" style="width:{pct}%;background:{color}"></div>'
            f'</div>'
        )

    # Explain button hint
    explain_html = ""
    if signal_key:
        expl = C.EXPLAIN_POSTURE if signal_key == "posture" else (
               C.EXPLAIN_BLINK     if signal_key == "blink" else (
               C.EXPLAIN_SEATED    if signal_key == "seated" else (
               C.EXPLAIN_TYPING    if signal_key == "typing" else (
               C.EXPLAIN_VOICE     if signal_key == "voice" else "Information about this metric."))))
        explain_html = f'<div class="mc-explain-btn" title="{expl}">ⓘ</div>'

    # Unit
    unit_html = f'<span class="mc-value-unit"> {unit}</span>' if unit else ""

    # Icon
    icon_prefix = f'{icon} ' if icon else ""

    return (
        f'<div class="mc">'
        f'<div class="mc-header">'
        f'<div class="mc-label">{icon_prefix}{label}</div>'
        f'{explain_html}'
        f'</div>'
        f'<div class="mc-value" style="color:{color}">{value}{unit_html}</div>'
        f'{prog_html}'
        f'<div class="mc-sub">{sub} {conf_html}</div>'
        f'</div>'
    )


# ── Full Metrics Grid ────────────────────────────────────────────────────────

def metrics_grid(p_score, p_cat, blink_rate, emotion, emotion_conf,
                 seated_mins, blink_thr, seated_max,
                 typing_wpm=0.0, typing_stress=0.0, stress_index=0.0,
                 voice_rate=0.0, voice_stress_val=0.0,
                 voice_speaking=False, voice_status="stopped"):
    """Render the complete metric grid for the monitoring dashboard."""

    pc = posture_color(p_score)
    bc = blink_color(blink_rate, blink_thr)
    sc = seated_color(seated_mins, seated_max)
    ec = EMOTION_COLOR.get(emotion, "#64748B")
    ee = EMOTION_EMOJI.get(emotion, "😐")
    pbar = min(100, p_score)

    # Confidence badge for emotion
    conf_label, conf_cls = confidence_level(emotion_conf)

    # Typing
    tc = stress_color(typing_stress) if typing_wpm > 0 else "var(--text-muted)"
    wlabel = f"{typing_wpm:.0f}" if typing_wpm > 0 else "–"
    tstatus = ("normal" if typing_stress < 0.3 else
               "irregular" if typing_stress < 0.65 else "stressed") if typing_wpm > 0 else "calibrating…"

    # Voice
    vc = voice_color(voice_stress_val) if voice_status != "stopped" else "var(--text-muted)"
    v_rate_label = f"{voice_rate:.0f}" if voice_rate > 0 else "–"
    if voice_status == "stopped":
        v_status = "mic off"
    elif voice_speaking:
        v_status = "speaking" if voice_stress_val < 0.3 else "rushed" if voice_stress_val < 0.65 else "stressed"
    else:
        v_status = "listening…"
    vbar = int(min(100, voice_stress_val * 100))

    # Wellness
    wellness_pct = max(0, min(100, int((1 - stress_index) * 100)))
    wc = wellness_color(wellness_pct)

    return _h(f"""
    <div class="metric-grid">
    {signal_card("Posture", p_score, "/100", p_cat.upper(), pc, pbar, "🦴", signal_key="posture")}
    {signal_card("Blink Rate", f"{blink_rate:.1f}", "/min", f"threshold {blink_thr}/min", bc, icon="👁️", signal_key="blink")}
    </div>
    <div class="metric-grid" style="margin-top:8px">
    <div class="mc">
    <div class="mc-header">
    <div class="mc-label">😊 Emotion</div>
    <div class="mc-explain-btn" title="{C.EXPLAIN_EMOTION}">ⓘ</div>
    </div>
    <div class="mc-value">
    <span class="emo-badge" style="background:{ec}15;color:{ec};border:1px solid {ec}30">{ee} {emotion.title()}</span>
    </div>
    <div class="mc-sub"><span class="conf-badge {conf_cls}">{conf_label} · {emotion_conf:.0f}%</span></div>
    </div>
    {signal_card("Time Seated", f"{seated_mins:.0f}", "min", f"break after {seated_max} min", sc, icon="⏱️", signal_key="seated")}
    </div>
    <div class="metric-grid" style="margin-top:8px">
    {signal_card("Typing", wlabel, "WPM", tstatus, tc, icon="⌨️", signal_key="typing")}
    {signal_card("Voice", v_rate_label, "WPM", v_status, vc, vbar if voice_status != "stopped" else None, "🎙️", signal_key="voice")}
    </div>
    """)


# ── Wellness Summary Bar ─────────────────────────────────────────────────────

def wellness_bar(stress_index):
    """Compact wellness bar for inline display."""
    pct = max(0, min(100, int((1 - stress_index) * 100)))
    color = wellness_color_hex(pct)

    return (
        f'<div class="mc" style="grid-column:span 2">'
        f'<div class="mc-header">'
        f'<div class="mc-label">🧠 Combined Wellness</div>'
        f'<div class="mc-explain-btn" title="AI-estimated wellness based on all active signals.">ⓘ</div>'
        f'</div>'
        f'<div class="mc-value" style="color:{color}">{pct}<span class="mc-value-unit">%</span></div>'
        f'<div class="prog-track"><div class="prog-fill" style="width:{pct}%;background:{color}"></div></div>'
        f'<div class="mc-sub">higher is better · AI-estimated from all signals</div>'
        f'</div>'
    )


# ── Signal Status Strip ──────────────────────────────────────────────────────

def signal_strip(cam=True, mic=False, kb=True):
    """Render a compact signal status strip showing what's active."""
    cam_cls = "signal-on" if cam else "signal-off"
    mic_cls = "signal-on" if mic else "signal-off"
    kb_cls = "signal-on" if kb else "signal-off"
    cam_icon = "✓" if cam else "✗"
    mic_icon = "✓" if mic else "✗"
    kb_icon = "✓" if kb else "✗"

    return (
        f'<div class="signal-strip">'
        f'<span class="{cam_cls}">📷 Camera {cam_icon}</span>'
        f'<span class="{mic_cls}">🎙️ Mic {mic_icon}</span>'
        f'<span class="{kb_cls}">⌨️ Keyboard {kb_icon}</span>'
        f'</div>'
    )


# ── Alert Cards ───────────────────────────────────────────────────────────────

def alerts_html(log):
    """Render alert cards with recovery actions, or empty state."""
    if not log:
        return empty_state("🔔", "No alerts", "Looking good — no concerns detected so far.")

    html = ""
    for a in reversed(log[-5:]):
        cls = ALERT_CLASS.get(a["type"], "al-combined")
        t = time.strftime("%H:%M", time.localtime(a["timestamp"]))
        action = ALERT_ACTIONS.get(a["type"], "")
        action_html = f'<div class="alert-action">💡 {action}</div>' if action else ""

        html += (
            f'<div class="alert-card {cls}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<span class="alert-title">{a.get("title", "Alert")}</span>'
            f'<span class="alert-time">{t}</span>'
            f'</div>'
            f'<div class="alert-msg">{a["message"]}</div>'
            f'{action_html}'
            f'</div>'
        )
    return html


# ── Coaching Summary Card ─────────────────────────────────────────────────────

def coaching_card(bullets):
    """AI coaching summary after session — list of actionable insight strings."""
    if not bullets:
        return ""

    items_html = ""
    for b in bullets:
        items_html += f'<div class="coaching-item">{b}</div>'

    return (
        f'<div class="coaching-card">'
        f'<div class="coaching-title">🧠 {C.COACHING_TITLE}</div>'
        f'{items_html}'
        f'<div class="coaching-trust">{C.COACHING_TRUST}</div>'
        f'</div>'
    )


# ── Reflection Prompt ─────────────────────────────────────────────────────────

def reflection_prompt():
    """Post-session emoji reflection selector. Returns selected index via Streamlit buttons."""
    st.markdown(
        f'<div class="reflection-bar">'
        f'<div class="reflection-title">{C.REFLECTION_TITLE}</div>'
        f'</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    emojis = ["😊", "🙂", "😐", "😔", "😢"]
    labels = ["Great", "Good", "Okay", "Not great", "Difficult"]
    for i, (emoji, label) in enumerate(zip(emojis, labels)):
        with cols[i]:
            if st.button(f"{emoji}\n{label}", key=f"reflect_{i}", use_container_width=True):
                st.session_state["reflection_response"] = i
                st.rerun()


# ── Explanation Drawer ────────────────────────────────────────────────────────

def explanation_drawer(signal_key, title="Why am I seeing this?"):
    """Render an expandable explanation for a signal."""
    explanation = SIGNAL_EXPLANATIONS.get(signal_key, "")
    if not explanation:
        return

    with st.expander(f"ⓘ {title}", expanded=False):
        st.markdown(
            f'<div class="explain-drawer">'
            f'<div class="explain-drawer-title">How this works</div>'
            f'{explanation}'
            f'</div>', unsafe_allow_html=True)


# ── Empty State ───────────────────────────────────────────────────────────────

def empty_state(icon, title, description):
    return (
        f'<div class="empty-state">'
        f'<div class="empty-icon">{icon}</div>'
        f'<p class="empty-title">{title}</p>'
        f'<p class="empty-desc">{description}</p>'
        f'</div>'
    )


# ── Error / Recovery Card ────────────────────────────────────────────────────

def error_card(title, description, icon="⚠️", action=""):
    action_html = f'<div class="error-action">💡 {action}</div>' if action else ""
    return (
        f'<div class="error-card">'
        f'<div class="error-icon">{icon}</div>'
        f'<div>'
        f'<div class="error-title">{title}</div>'
        f'<div class="error-desc">{description}</div>'
        f'{action_html}'
        f'</div>'
        f'</div>'
    )


# ── Trust Banner ──────────────────────────────────────────────────────────────

def trust_banner(text, icon="🔒"):
    return (
        f'<div class="trust-banner">'
        f'<span class="trust-banner-icon">{icon}</span>'
        f'<span>{text}</span>'
        f'</div>'
    )


def disclaimer_bar():
    return f'<div class="disclaimer-bar">ℹ️ {C.DISCLAIMER}</div>'


# ── Confidence Badge ──────────────────────────────────────────────────────────

def confidence_badge(pct):
    label, cls = confidence_level(pct)
    return f'<span class="conf-badge {cls}">{label} · {pct:.0f}%</span>'


# ── Feature Cards (Welcome) ──────────────────────────────────────────────────

def feature_card(icon, name, description):
    return (
        f'<div class="feature-card">'
        f'<span class="feature-icon">{icon}</span>'
        f'<p class="feature-name">{name}</p>'
        f'<p class="feature-desc">{description}</p>'
        f'</div>'
    )


def feature_grid(features):
    html = '<div class="feature-grid">'
    for icon, name, desc in features:
        html += feature_card(icon, name, desc)
    html += '</div>'
    return html


# ── Permission Card (Privacy Disclosure) ──────────────────────────────────────

def permission_card(icon, title, desc, not_collected):
    return (
        f'<div class="perm-card">'
        f'<div class="perm-icon">{icon}</div>'
        f'<div class="perm-content">'
        f'<div class="perm-title">{title}</div>'
        f'<div class="perm-desc">{desc}</div>'
        f'<div class="perm-not">✓ {not_collected}</div>'
        f'</div>'
        f'</div>'
    )


# ── Onboarding Hero ──────────────────────────────────────────────────────────

def onboarding_hero(title, subtitle):
    return _h(f"""
    <div class="onboard-hero">
    <div class="onboard-logo">🧠</div>
    <h1 class="onboard-title">{title}</h1>
    <p class="onboard-subtitle">{subtitle}</p>
    </div>
    """)


# ── Step Indicator ────────────────────────────────────────────────────────────

def step_indicator(steps, current):
    html = '<div class="step-bar">'
    for i, label in enumerate(steps, 1):
        if i < current:
            dot_cls, icon = "step-done", "✓"
        elif i == current:
            dot_cls, icon = "step-active", str(i)
        else:
            dot_cls, icon = "step-pending", str(i)

        lbl_color = 'var(--primary)' if i <= current else 'var(--text-muted)'
        html += (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px">'
            f'<div class="step-dot {dot_cls}">{icon}</div>'
            f'<span class="step-label" style="color:{lbl_color}">{label}</span>'
            f'</div>'
        )
        if i < len(steps):
            line_cls = "step-line-done" if i < current else "step-line-pending"
            html += f'<div class="step-line {line_cls}"></div>'

    html += '</div>'
    return html


# ── Session History Card ─────────────────────────────────────────────────────

def session_card(session):
    ts = session.get("timestamp", 0)
    date_str = time.strftime("%b %d, %Y · %H:%M", time.localtime(ts)) if ts else "Unknown"
    duration = session.get("duration_mins", 0)
    posture = session.get("posture_score", 0)
    emotion = session.get("dominant_emotion", "neutral")
    stress = session.get("stress_index", 0.0)
    ee = EMOTION_EMOJI.get(emotion, "😐")
    wellness_pct = int((1 - stress) * 100)
    wc = wellness_color_hex(wellness_pct)
    pc = posture_color_hex(posture)

    return (
        f'<div class="session-card">'
        f'<div class="session-top">'
        f'<span class="session-date">{date_str}</span>'
        f'<span class="session-duration">{duration:.0f} min</span>'
        f'</div>'
        f'<div class="session-metrics">'
        f'<span class="session-metric">Posture: <span class="session-metric-val" style="color:{pc}">{posture}/100</span></span>'
        f'<span class="session-metric">Emotion: <span class="session-metric-val">{ee} {emotion.title()}</span></span>'
        f'<span class="session-metric">Wellness: <span class="session-metric-val" style="color:{wc}">{wellness_pct}%</span></span>'
        f'</div>'
        f'</div>'
    )


# ── Last Session Summary Card ─────────────────────────────────────────────────

def last_session_card(session):
    """Compact card showing last session stats for the home idle view."""
    if not session:
        return ""
    ts = session.get("timestamp", 0)
    date_str = time.strftime("%b %d · %H:%M", time.localtime(ts)) if ts else ""
    posture = session.get("posture_score", 0)
    wellness = int((1 - session.get("stress_index", 0.0)) * 100)
    wc = wellness_color_hex(wellness)

    return (
        f'<div class="aria-card" style="padding:14px 18px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<div>'
        f'<div style="font-size:0.65rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px">'
        f'📊 {C.HOME_LAST_SESSION}</div>'
        f'<div style="font-size:0.78rem;color:var(--text-secondary)">{date_str} · Posture {posture}/100</div>'
        f'</div>'
        f'<div style="text-align:right">'
        f'<div style="font-size:1.3rem;font-weight:800;color:{wc};letter-spacing:-0.03em">{wellness}%</div>'
        f'<div style="font-size:0.62rem;color:var(--text-muted);font-weight:500">wellness</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


# ── Readiness Indicator ───────────────────────────────────────────────────────

def readiness_item(label, status_text, passed=True):
    """Single readiness check item."""
    dot_cls = "readiness-pass" if passed else "readiness-fail"
    return (
        f'<div class="readiness-item">'
        f'<div class="readiness-dot {dot_cls}"></div>'
        f'<div>'
        f'<div class="readiness-label">{label}</div>'
        f'<div class="readiness-status">{status_text}</div>'
        f'</div>'
        f'</div>'
    )


# ── Section Label ─────────────────────────────────────────────────────────────

def section_label(text):
    return f'<div class="aria-section">{text}</div>'


# ── Timer Display ─────────────────────────────────────────────────────────────

def session_timer(elapsed_seconds, status="live"):
    mins = elapsed_seconds // 60
    secs = elapsed_seconds % 60

    if status == "paused":
        return f'<div class="session-timer timer-paused">⏸ Paused · {mins:02d}:{secs:02d}</div>'
    elif status == "ended":
        return f'<div class="session-timer timer-ended">Session ended · {mins:02d}:{secs:02d}</div>'
    else:
        return f'<div class="session-timer timer-live">⏱ {mins:02d}:{secs:02d}</div>'
