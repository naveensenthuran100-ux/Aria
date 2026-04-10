"""
Aria v2 Design System — Premium Wellness Theme
===============================================
Complete CSS with light + dark mode via CSS custom properties.
Dark mode: deep navy palette, not inverted.
"""

import streamlit as st


def inject_css(dark=False):
    """Inject the design system CSS. Set dark=True for dark mode."""
    mode_class = "dark" if dark else ""
    st.markdown(f'<div class="aria-root {mode_class}" id="aria-root">', unsafe_allow_html=True)
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


_GLOBAL_CSS = """
<style>
/* ══════════════════════════════════════════════════════════════════════════
   ARIA v2 DESIGN SYSTEM
   Light + Dark mode via CSS custom properties
   ══════════════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Light Mode (default) ───────────────────────────────────────────── */
:root {
  --bg: #F8FAFC;
  --surface: #FFFFFF;
  --surface-raised: #F1F5F9;
  --surface-overlay: rgba(248,250,252,0.92);
  --border: #E2E8F0;
  --border-subtle: #F1F5F9;

  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-muted: #94A3B8;
  --text-inverse: #FFFFFF;

  --primary: #6366F1;
  --primary-hover: #4F46E5;
  --primary-light: #818CF8;
  --primary-subtle: #EEF2FF;
  --primary-border: #C7D2FE;
  --primary-glow: rgba(99,102,241,0.25);

  --success: #10B981;
  --success-bg: #ECFDF5;
  --success-border: #A7F3D0;
  --warning: #F59E0B;
  --warning-bg: #FFFBEB;
  --warning-border: #FDE68A;
  --danger: #EF4444;
  --danger-bg: #FEF2F2;
  --danger-border: #FECACA;
  --info: #3B82F6;
  --info-bg: #EFF6FF;
  --info-border: #BFDBFE;

  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
  --shadow-md: 0 4px 16px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.03);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.08);
  --shadow-primary: 0 4px 16px rgba(99,102,241,0.25);

  --nav-bg: #F1F5F9;
  --nav-active-bg: #FFFFFF;
}

/* ── Dark Mode ──────────────────────────────────────────────────────── */
.dark {
  --bg: #0B0F1A;
  --surface: #141B2D;
  --surface-raised: #1A2332;
  --surface-overlay: rgba(11,15,26,0.92);
  --border: #1E293B;
  --border-subtle: #1E293B;

  --text-primary: #F1F5F9;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --text-inverse: #0F172A;

  --primary: #818CF8;
  --primary-hover: #6366F1;
  --primary-light: #A5B4FC;
  --primary-subtle: #1E1B4B;
  --primary-border: #312E81;
  --primary-glow: rgba(129,140,248,0.3);

  --success: #34D399;
  --success-bg: rgba(6,78,59,0.5);
  --success-border: rgba(6,95,70,0.5);
  --warning: #FBBF24;
  --warning-bg: rgba(120,53,15,0.5);
  --warning-border: rgba(146,64,14,0.5);
  --danger: #F87171;
  --danger-bg: rgba(127,29,29,0.5);
  --danger-border: rgba(153,27,27,0.5);
  --info: #60A5FA;
  --info-bg: rgba(30,58,95,0.5);
  --info-border: rgba(30,64,175,0.5);

  --shadow-sm: 0 4px 6px rgba(0,0,0,0.1);
  --shadow-md: 0 10px 24px rgba(0,0,0,0.25);
  --shadow-lg: 0 24px 48px rgba(0,0,0,0.5);
  --shadow-primary: 0 8px 24px rgba(129,140,248,0.25);

  --nav-bg: rgba(20,27,45,0.4);
  --nav-active-bg: rgba(30,41,59,0.6);
}

/* ── Base ────────────────────────────────────────────────────────────── */
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="collapsedControl"] { display: none !important; }

[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] > div:first-child {
  background: transparent !important;
}

[data-testid="stSidebarNav"] { display: none !important; }

/* ── Sidebar Navigation ──────────────────────────────────────────────── */
.sidebar-nav-item button {
  background: transparent !important;
  color: var(--text-muted) !important;
  box-shadow: none !important;
  border: none !important;
  justify-content: flex-start !important;
  padding: 10px 16px !important;
  margin-bottom: 6px !important;
  font-size: 0.9rem !important;
  font-weight: 500 !important;
}

.sidebar-nav-item button:hover {
  background: var(--surface-raised) !important;
  color: var(--text-primary) !important;
  transform: none !important;
}

.sidebar-nav-active button {
  background: var(--primary-subtle) !important;
  color: var(--primary) !important;
  box-shadow: none !important;
  border: none !important;
  justify-content: flex-start !important;
  padding: 10px 16px !important;
  margin-bottom: 6px !important;
  font-size: 0.9rem !important;
  font-weight: 700 !important;
}

.sidebar-nav-active button:hover {
  background: var(--primary-subtle) !important;
  color: var(--primary) !important;
  transform: none !important;
}

[data-testid="stAppViewContainer"] > .main {
  background: radial-gradient(ellipse at top left, #161D36 0%, #0B0F1A 80%) !important;
  background-attachment: fixed !important;
}

[data-testid="block-container"] {
  padding: 0 !important;
  max-width: 1280px !important;
  margin: 0 auto !important;
  padding-bottom: 80px !important;
}

/* ── Top Bar ─────────────────────────────────────────────────────────── */
.aria-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 4px;
  margin-bottom: 4px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--surface-overlay);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.aria-topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.aria-logo {
  width: 38px; height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, #6366F1 0%, #818CF8 50%, #A5B4FC 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem;
  box-shadow: var(--shadow-primary);
  flex-shrink: 0;
}

.aria-topbar-title {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.03em;
  margin: 0;
  line-height: 1;
}

.aria-topbar-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 500;
  margin: 2px 0 0;
}

.aria-topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── Status Chips ────────────────────────────────────────────────────── */
.aria-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.chip-live { background: var(--success-bg); color: var(--success); border: 1px solid var(--success-border); }
.chip-paused { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning-border); }
.chip-idle { background: var(--surface-raised); color: var(--text-muted); border: 1px solid var(--border); }
.chip-user { background: var(--primary-subtle); color: var(--primary); border: 1px solid var(--primary-border); }

.status-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot-live { background: var(--success); box-shadow: 0 0 8px rgba(16,185,129,0.6); animation: pulse-dot 2s ease-in-out infinite; }
.dot-paused { background: var(--warning); }
.dot-idle { background: var(--text-muted); }

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

/* ── Bottom Tab Bar ──────────────────────────────────────────────────── */
.aria-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1000px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  padding: 6px 8px 10px;
  z-index: 999;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.aria-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  border: none;
  background: transparent;
}

.aria-tab-icon { font-size: 1.2rem; }
.aria-tab-label {
  font-size: 0.62rem;
  font-weight: 600;
  color: var(--text-muted);
  letter-spacing: 0.02em;
}

.aria-tab--active .aria-tab-label { color: var(--primary); }
.aria-tab--active .aria-tab-icon { filter: none; }

/* ── Segmented Nav (fallback for Streamlit buttons) ──────────────────── */
.aria-nav {
  display: flex;
  background: var(--nav-bg);
  border-radius: 20px;
  padding: 4px;
  margin-bottom: 20px;
  gap: 2px;
}

.aria-nav-item {
  flex: 1;
  text-align: center;
  padding: 9px 4px;
  border-radius: 11px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.25s ease;
  background: transparent;
  letter-spacing: -0.01em;
}

.aria-nav-item:hover { color: var(--text-secondary); background: var(--surface); }
.aria-nav-active {
  background: var(--nav-active-bg) !important;
  color: var(--primary) !important;
  box-shadow: var(--shadow-sm);
}

/* ── Cards ───────────────────────────────────────────────────────────── */
.aria-card {
  background: rgba(30, 41, 59, 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255, 0.05);
  border-radius: 24px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border 0.3s ease;
}

.aria-card:hover {
  box-shadow: var(--shadow-md);
}

.aria-card-flat {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
}

/* ── Section Label ───────────────────────────────────────────────────── */
.aria-section {
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-weight: 700;
  margin: 20px 0 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.aria-section::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

/* ── Signal / Metric Cards ───────────────────────────────────────────── */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 8px 0;
}

@media (min-width: 768px) {
  .metric-grid-3 { grid-template-columns: repeat(3, 1fr); }
}

.mc {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px 16px;
  min-height: 85px;
  transition: all 0.25s ease;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}

.mc:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }

.mc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.mc-label {
  font-size: 0.62rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.mc-explain-btn {
  width: 18px; height: 18px;
  border-radius: 50%;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.mc-explain-btn:hover {
  background: var(--primary-subtle);
  color: var(--primary);
  border-color: var(--primary-border);
}

.mc-value {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
  letter-spacing: -0.03em;
}

.mc-value-unit {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}

.mc-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 4px;
  font-weight: 500;
}

/* Progress bar */
.prog-track {
  background: var(--surface-raised);
  border-radius: 6px;
  height: 4px;
  margin-top: 8px;
  overflow: hidden;
}

.prog-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s ease;
}

/* ── Confidence Badge ────────────────────────────────────────────────── */
.conf-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.58rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.conf-high { background: var(--success-bg); color: var(--success); }
.conf-med  { background: var(--warning-bg); color: var(--warning); }
.conf-low  { background: var(--danger-bg); color: var(--danger); }

/* ── Emotion Badge ───────────────────────────────────────────────────── */
.emo-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
}

/* ── Wellness Dial ───────────────────────────────────────────────────── */
.wellness-dial {
  text-align: center;
  padding: 24px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-sm);
}

.wellness-dial-value {
  font-size: 3.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
  margin: 8px 0;
}

.wellness-dial-label {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.wellness-dial-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.wellness-dial-ring {
  width: 160px;
  height: 160px;
  margin: 0 auto 12px;
  position: relative;
}

/* ── Shoulder Card ───────────────────────────────────────────────────── */
.shoulder-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 12px;
}
.shoulder-normal { border-left: 4px solid var(--success); }
.shoulder-warn { border-left: 4px solid var(--warning); }
.shoulder-alert { border-left: 4px solid var(--danger); }

/* ── Alert Cards ─────────────────────────────────────────────────────── */
.alert-card {
  border-left: 3px solid;
  border-radius: 0 14px 14px 0;
  padding: 14px 16px;
  margin: 8px 0;
  font-size: 0.82rem;
  background: var(--surface);
  transition: all 0.2s ease;
}

.al-posture { border-color: var(--danger); background: var(--danger-bg); }
.al-blink   { border-color: var(--warning); background: var(--warning-bg); }
.al-seated  { border-color: var(--info); background: var(--info-bg); }
.al-combined { border-color: #8B5CF6; background: #F5F3FF; }
.dark .al-combined { background: #2E1065; }

.alert-title { font-weight: 700; font-size: 0.82rem; color: var(--text-primary); }
.alert-time { font-size: 0.65rem; color: var(--text-muted); font-weight: 500; }
.alert-msg { color: var(--text-secondary); font-size: 0.75rem; margin-top: 2px; }
.alert-action {
  font-size: 0.72rem;
  color: var(--primary);
  font-weight: 600;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid var(--border-subtle);
}

/* ── Trust / HCAI Banners ────────────────────────────────────────────── */
.trust-banner {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.72rem;
  color: var(--text-secondary);
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 12px 0;
  line-height: 1.5;
}

.trust-banner-icon { font-size: 0.95rem; flex-shrink: 0; margin-top: 1px; }

.disclaimer-bar {
  text-align: center;
  font-size: 0.65rem;
  color: var(--text-muted);
  padding: 12px 0 4px;
  font-weight: 500;
}

/* ── Explanation Drawer ──────────────────────────────────────────────── */
.explain-drawer {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-top: 8px;
}

.explain-drawer-title {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.75rem;
  margin-bottom: 4px;
}

/* ── Coaching Card ───────────────────────────────────────────────────── */
.coaching-card {
  background: var(--primary-subtle);
  border: 1px solid var(--primary-border);
  border-radius: 16px;
  padding: 20px;
  margin: 12px 0;
}

.coaching-title {
  font-weight: 700;
  font-size: 0.92rem;
  color: var(--primary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.coaching-item {
  font-size: 0.82rem;
  color: var(--text-primary);
  line-height: 1.6;
  padding: 6px 0;
  padding-left: 20px;
  position: relative;
}

.coaching-item::before {
  content: '→';
  position: absolute;
  left: 0;
  color: var(--primary);
  font-weight: 700;
}

.coaching-trust {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

/* ── Reflection Prompt ───────────────────────────────────────────────── */
.reflection-bar {
  text-align: center;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  margin: 12px 0;
}

.reflection-title {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.reflection-options {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.reflection-opt {
  padding: 8px 14px;
  border-radius: 12px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--surface-raised);
  border: 1px solid var(--border);
}

.reflection-opt:hover {
  background: var(--primary-subtle);
  border-color: var(--primary-border);
  transform: scale(1.05);
}

.reflection-opt--selected {
  background: var(--primary-subtle) !important;
  border-color: var(--primary) !important;
}

/* ── Empty State ─────────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  margin: 12px 0;
}

.empty-icon { font-size: 2.5rem; margin-bottom: 12px; opacity: 0.8; }
.empty-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin: 0 0 6px; }
.empty-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  margin: 0 auto;
  max-width: 340px;
  line-height: 1.5;
}

/* ── Error / Recovery Card ───────────────────────────────────────────── */
.error-card {
  background: var(--danger-bg);
  border: 1px solid var(--danger-border);
  border-radius: 14px;
  padding: 14px 18px;
  margin: 8px 0;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.error-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 1px; }
.error-title { font-weight: 700; font-size: 0.85rem; color: var(--danger); margin-bottom: 2px; }
.error-desc { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4; }
.error-action {
  font-size: 0.72rem;
  color: var(--primary);
  font-weight: 600;
  margin-top: 6px;
  cursor: pointer;
}

/* ── Readiness Indicator ─────────────────────────────────────────────── */
.readiness-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 8px;
}

.readiness-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.readiness-pass { background: var(--success); box-shadow: 0 0 6px rgba(16,185,129,0.4); }
.readiness-fail { background: var(--danger); box-shadow: 0 0 6px rgba(239,68,68,0.4); }
.readiness-checking {
  background: var(--warning);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.readiness-label { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.readiness-status { font-size: 0.72rem; color: var(--text-muted); margin-top: 1px; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 0.85rem !important;
  border: none !important;
  background: var(--primary) !important;
  color: var(--text-inverse) !important;
  transition: all 0.2s ease !important;
  box-shadow: var(--shadow-primary) !important;
  letter-spacing: -0.01em !important;
  padding: 8px 20px !important;
}

.stButton > button:hover {
  background: var(--primary-hover) !important;
  color: var(--text-inverse) !important;
  box-shadow: var(--shadow-md) !important;
  transform: translateY(-1px) !important;
}

.start-btn button {
  background: linear-gradient(135deg, #6366F1, #818CF8) !important;
  color: #fff !important;
  box-shadow: var(--shadow-primary) !important;
  font-size: 0.95rem !important;
  padding: 12px 24px !important;
}
.start-btn button:hover {
  background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
  color: #fff !important;
}

.stop-btn button {
  background: var(--danger-bg) !important;
  color: var(--danger) !important;
  border: 1px solid var(--danger-border) !important;
  box-shadow: none !important;
}
.stop-btn button:hover { background: var(--danger-bg) !important; transform: none !important; }

.pause-btn button {
  background: var(--warning-bg) !important;
  color: var(--warning) !important;
  border: 1px solid var(--warning-border) !important;
  box-shadow: none !important;
}
.pause-btn button:hover { background: var(--warning-bg) !important; transform: none !important; }

.resume-btn button {
  background: var(--success-bg) !important;
  color: var(--success) !important;
  border: 1px solid var(--success-border) !important;
  box-shadow: none !important;
}
.resume-btn button:hover { background: var(--success-bg) !important; transform: none !important; }

.ghost-btn button {
  background: transparent !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  box-shadow: none !important;
}
.ghost-btn button:hover {
  background: var(--surface-raised) !important;
  transform: none !important;
}

.danger-btn button {
  background: transparent !important;
  color: var(--danger) !important;
  border: 1px solid var(--danger-border) !important;
  box-shadow: none !important;
}
.danger-btn button:hover { background: var(--danger-bg) !important; transform: none !important; }

/* ── Chat ────────────────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: var(--surface-raised) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  margin-bottom: 6px !important;
}

[data-testid="stChatInput"] {
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  background: var(--surface) !important;
}

[data-testid="stChatInput"]:focus-within {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
}

.chat-header {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 14px 18px;
  margin-bottom: 12px;
}

.chat-context { display: flex; gap: 14px; flex-wrap: wrap; }
.chat-stat { font-size: 0.68rem; color: var(--text-muted); }
.chat-stat-val { font-weight: 700; color: var(--text-primary); }

/* ── Streamlit Metric Override ───────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--primary);
  border: none;
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: var(--shadow-primary);
}

[data-testid="stMetricLabel"] {
  font-size: 0.62rem !important;
  color: rgba(255,255,255,0.7) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
  color: #FFFFFF !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em !important;
}

[data-testid="stMetricDelta"] { color: rgba(255,255,255,0.8) !important; }

/* ── Session History Card ────────────────────────────────────────────── */
.session-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 8px;
  transition: all 0.2s ease;
}

.session-card:hover { box-shadow: var(--shadow-md); }
.session-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.session-date { font-weight: 700; font-size: 0.85rem; color: var(--text-primary); }
.session-duration { font-size: 0.68rem; color: var(--text-muted); font-weight: 600; }
.session-metrics { display: flex; gap: 14px; flex-wrap: wrap; }
.session-metric { font-size: 0.72rem; color: var(--text-secondary); font-weight: 500; }
.session-metric-val { font-weight: 700; color: var(--text-primary); }

/* ── Onboarding ──────────────────────────────────────────────────────── */
.onboard-container { max-width: 520px; margin: 0 auto; padding: 32px 0 20px; }

.onboard-hero { text-align: center; margin-bottom: 28px; }

.onboard-logo {
  width: 68px; height: 68px;
  border-radius: 18px;
  background: linear-gradient(135deg, #6366F1 0%, #818CF8 50%, #A5B4FC 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  margin-bottom: 14px;
  box-shadow: var(--shadow-primary);
}

.onboard-title {
  font-size: 1.7rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.03em;
}

.onboard-subtitle {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin: 8px 0 0;
  line-height: 1.5;
}

/* Step indicator */
.step-bar { display: flex; justify-content: center; align-items: center; gap: 0; margin: 24px 0 28px; padding: 0 20px; }

.step-dot {
  width: 34px; height: 34px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.step-done { background: var(--primary); color: #fff; box-shadow: 0 2px 8px var(--primary-glow); }
.step-active { background: var(--primary); color: #fff; box-shadow: 0 2px 12px var(--primary-glow); transform: scale(1.1); }
.step-pending { background: var(--surface-raised); color: var(--text-muted); border: 2px solid var(--border); }

.step-line { flex: 1; height: 2px; margin: 0 4px; border-radius: 1px; }
.step-line-done { background: var(--primary); }
.step-line-pending { background: var(--border); }
.step-label { font-size: 0.58rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }

/* Feature cards */
.feature-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 16px 0; }

.feature-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 14px;
  text-align: center;
  transition: all 0.25s ease;
}

.feature-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.feature-icon { font-size: 1.4rem; margin-bottom: 6px; display: block; }
.feature-name { font-size: 0.78rem; font-weight: 700; color: var(--text-primary); margin: 0 0 3px; }
.feature-desc { font-size: 0.68rem; color: var(--text-muted); margin: 0; line-height: 1.4; }

/* ── Privacy Permission Card ─────────────────────────────────────────── */
.perm-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.perm-icon {
  width: 42px; height: 42px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem;
  flex-shrink: 0;
  background: var(--primary-subtle);
  border: 1px solid var(--primary-border);
}

.perm-content { flex: 1; }
.perm-title { font-weight: 700; font-size: 0.88rem; color: var(--text-primary); }
.perm-desc { font-size: 0.72rem; color: var(--text-secondary); margin-top: 1px; }
.perm-not { font-size: 0.65rem; color: var(--success); font-weight: 500; margin-top: 2px; }

/* ── Greeting ────────────────────────────────────────────────────────── */
.greeting {
  margin-bottom: 20px;
}

.greeting-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text-primary);
  letter-spacing: -0.03em;
  margin: 0;
}

.greeting-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 4px 0 0;
}

/* ── Timer ────────────────────────────────────────────────────────────── */
.session-timer {
  text-align: right;
  font-size: 0.82rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.timer-live { color: var(--text-secondary); }
.timer-paused { color: var(--warning); }
.timer-ended { color: var(--text-muted); }

/* ── Signal status strip ─────────────────────────────────────────────── */
.signal-strip {
  display: flex;
  gap: 12px;
  padding: 8px 14px;
  background: var(--surface-raised);
  border-radius: 10px;
  margin-bottom: 12px;
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 500;
}

.signal-on { color: var(--success); }
.signal-off { color: var(--text-muted); }

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Streamlit Overrides ─────────────────────────────────────────────── */
[data-testid="stCheckbox"] label span { color: var(--text-primary) !important; font-weight: 500 !important; }
[data-testid="stTextInput"] input { border-radius: 12px !important; border-color: var(--border) !important; background: var(--surface) !important; color: var(--text-primary) !important; }
[data-testid="stTextInput"] input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 3px var(--primary-glow) !important; }
[data-testid="stSelectbox"] > div > div { border-radius: 12px !important; border-color: var(--border) !important; }
[data-testid="stExpander"] { border: 1px solid var(--border) !important; border-radius: 14px !important; background: var(--surface) !important; }
[data-testid="stExpander"] summary { font-weight: 600 !important; color: var(--text-primary) !important; }
[data-testid="stToast"] { border-radius: 14px !important; }
[data-testid="stAlert"] { border-radius: 12px !important; }
[data-testid="stCameraInput"] { border-radius: 16px !important; overflow: hidden; }
[data-testid="stAudioInput"] { border-radius: 12px !important; }
hr { border-color: var(--border) !important; }

/* Toggle styling */
[data-testid="stToggle"] label { color: var(--text-primary) !important; }

/* ── Animations ──────────────────────────────────────────────────────── */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.fade-in { animation: fadeIn 0.4s ease forwards; }
.fade-in-up { animation: fadeInUp 0.5s ease forwards; }

</style>
"""
