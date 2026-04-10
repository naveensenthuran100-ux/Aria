import os
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

import cv2
import time
import logging
import numpy as np
import yaml
import streamlit as st

logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv()

from streamlit_webrtc import webrtc_streamer, RTCConfiguration
from streamlit_autorefresh import st_autorefresh
from src.webrtc_bridge import (
    video_frame_callback, audio_frame_callback,
    get_results, set_control, reset_bridge,
)

# TURN/STUN config for remote WebRTC connectivity
_ice_servers = [
    {"urls": ["stun:stun.l.google.com:19302"]},
    {"urls": ["stun:stun1.l.google.com:19302"]},
]
_turn_user = os.getenv("TURN_USERNAME", "")
_turn_cred = os.getenv("TURN_CREDENTIAL", "")
if _turn_user and _turn_cred:
    # Metered TURN servers (all standard ports/transports)
    _turn_urls = [
        "turn:a.relay.metered.ca:80",
        "turn:a.relay.metered.ca:80?transport=tcp",
        "turn:a.relay.metered.ca:443",
        "turn:a.relay.metered.ca:443?transport=tcp",
        "turns:a.relay.metered.ca:443",
    ]
    for _u in _turn_urls:
        _ice_servers.append({
            "urls": _u,
            "username": _turn_user,
            "credential": _turn_cred,
        })
    print(f"[TURN] Configured {len(_turn_urls)} TURN servers with user={_turn_user[:4]}...")
else:
    print("[TURN] WARNING: No TURN_USERNAME/TURN_CREDENTIAL set — remote video may not work")
RTC_CONFIG = RTCConfiguration({"iceServers": _ice_servers})

from src.vision.posture import get_current_reading as get_posture
from src.vision.blink import get_current_reading as get_blink, reset_session as reset_blink
from src.vision.emotion import (
    get_current_reading as get_emotion, reset_session as reset_emotion,
    load_user_calibration, save_user_calibration
)
from src.fusion.aggregator import (
    update_posture, update_blink, update_emotion, update_typing, update_voice,
    get_session_summary, check_alerts, reset_session as reset_aggregator,
    session_state
)
from src.ai.chatbot import chat, reset_conversation, generate_report_summary
from src.alerts.notifier import process_alerts, get_notification_log, reset_notifier
from src.reports.generator import generate_pdf_report
from src.data.session_db import save_session
from src.vision import face_id
from src.io import typing_monitor
from src.audio import voice_stress
from src.audio import voice_id

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# ── Display helpers ───────────────────────────────────────────────────────────
EMOTION_EMOJI = {
    "happy": "😊", "neutral": "😐", "sad": "😢",
    "angry": "😠", "fear": "😨", "disgust": "🤢", "surprise": "😮"
}
EMOTION_COLOR = {
    "happy": "#16a34a", "neutral": "#64748b", "sad": "#3b82f6",
    "angry": "#ef4444", "fear": "#a855f7", "disgust": "#f97316", "surprise": "#eab308"
}

def _posture_color(s):
    return "#16a34a" if s >= 75 else "#f59e0b" if s >= 50 else "#ef4444"

def _blink_color(r, thr):
    return "#16a34a" if r >= thr else "#f59e0b" if r >= thr * 0.7 else "#ef4444"

def _seated_color(m, mx):
    return "#16a34a" if m < mx * 0.5 else "#f59e0b" if m < mx else "#ef4444"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Aria — Wellness Monitor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS — Light theme ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Base */
*{font-family:'Inter',system-ui,-apple-system,sans-serif}
.main .block-container{padding-top:.8rem;padding-bottom:2rem;max-width:1480px}
[data-testid="stAppViewContainer"]>.main{background:#ffffff}
[data-testid="stSidebar"]{background:#f7f8fc;border-right:1px solid #e2e8f0;
  min-width:21rem!important;width:21rem!important;
  position:fixed!important;top:0!important;left:0!important;height:100vh!important;
  z-index:999990!important;box-shadow:4px 0 24px rgba(0,0,0,.08)}
[data-testid="stSidebar"] > div:first-child{width:21rem!important;min-width:21rem!important}
#MainMenu,footer,header{visibility:hidden}
/* Center main content — sidebar is now overlay, not push */
[data-testid="stAppViewContainer"]{margin-left:0!important}
.main .block-container{margin:0 auto!important}


/* Header bar */
.wm-header{
  background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:16px 24px;
  margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 1px 3px rgba(0,0,0,.04)}
.wm-left{display:flex;align-items:center;gap:14px}
.wm-logo{width:38px;height:38px;border-radius:10px;
  background:linear-gradient(135deg,#6B86F6,#8da2f8);
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;color:#fff;flex-shrink:0}
.wm-title{font-size:1.25rem;font-weight:700;color:#0f172a;margin:0;letter-spacing:-.02em}
.wm-sub{font-size:.78rem;color:#94a3b8;margin:2px 0 0;font-weight:500}
.wm-dot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:5px;vertical-align:middle}
.dot-live{background:#22c55e;box-shadow:0 0 6px #22c55e88}
.dot-idle{background:#cbd5e1}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.dot-live{animation:pulse 2s infinite}
.wm-status{display:flex;align-items:center;gap:10px}
.wm-chip{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;
  border-radius:20px;font-size:.72rem;font-weight:600;letter-spacing:.02em}
.chip-live{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0}
.chip-idle{background:#f1f5f9;color:#64748b;border:1px solid #e2e8f0}
.chip-user{background:#eef2ff;color:#6366f1;border:1px solid #c7d2fe}

/* Section labels */
.sec-label{font-size:.68rem;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.1em;font-weight:600;margin:12px 0 8px;
  display:flex;align-items:center;gap:8px}
.sec-label::after{content:'';flex:1;height:1px;background:#e2e8f0}

/* Cards */
.card{background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
  padding:16px 18px;box-shadow:0 1px 2px rgba(0,0,0,.03);transition:box-shadow .2s}
.card:hover{box-shadow:0 4px 12px rgba(0,0,0,.06)}

/* Metric grid */
.metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0}
.mc{background:#f7f8fc;border:1px solid #e2e8f0;border-radius:12px;
  padding:14px 16px;min-height:82px;transition:box-shadow .2s;
  box-shadow:0 1px 2px rgba(0,0,0,.03)}
.mc:hover{box-shadow:0 4px 12px rgba(0,0,0,.06)}
.mc-label{font-size:.65rem;color:#94a3b8;text-transform:uppercase;
  letter-spacing:.08em;font-weight:600;margin-bottom:6px}
.mc-value{font-size:1.4rem;font-weight:700;color:#0f172a;line-height:1.2}
.mc-sub{font-size:.72rem;color:#94a3b8;margin-top:5px;font-weight:500}
.prog-track{background:#e2e8f0;border-radius:6px;height:4px;margin-top:8px;overflow:hidden}
.prog-fill{height:100%;border-radius:6px;transition:width .4s ease}

/* Emotion badge */
.emo-badge{display:inline-flex;align-items:center;gap:4px;
  padding:3px 10px;border-radius:16px;font-size:.78rem;font-weight:600}

/* Alert cards */
.alert-card{border-left:3px solid;border-radius:0 10px 10px 0;
  padding:10px 14px;margin:6px 0;font-size:.82rem;color:#334155;
  background:#ffffff}
.al-posture{border-color:#ef4444;background:#fef2f2}
.al-blink{border-color:#f59e0b;background:#fffbeb}
.al-seated{border-color:#3b82f6;background:#eff6ff}
.al-combined{border-color:#a855f7;background:#faf5ff}

/* Buttons — #6B86F6 blue */
.stButton>button{border-radius:10px!important;font-weight:600!important;
  border:none!important;background:#6B86F6!important;
  color:#fff!important;transition:all .15s!important;
  box-shadow:0 2px 6px rgba(107,134,246,.3)!important}
.stButton>button:hover{background:#5a75e4!important;
  color:#fff!important;
  box-shadow:0 4px 12px rgba(107,134,246,.4)!important}

/* Start/stop session buttons */
.start-btn button{background:linear-gradient(135deg,#6B86F6,#8da2f8)!important;
  color:#fff!important;border:none!important;
  box-shadow:0 2px 10px rgba(107,134,246,.35)!important;font-size:1rem!important}
.start-btn button:hover{box-shadow:0 4px 16px rgba(107,134,246,.45)!important;
  background:linear-gradient(135deg,#5a75e4,#7b96f7)!important;color:#fff!important}
.stop-btn button{background:#fef2f2!important;color:#dc2626!important;
  border:1px solid #fca5a5!important;box-shadow:none!important}
.stop-btn button:hover{background:#fee2e2!important;border-color:#dc2626!important}
.pause-btn button{background:#fffbeb!important;color:#d97706!important;
  border:1px solid #fcd34d!important;box-shadow:none!important}
.pause-btn button:hover{background:#fef3c7!important;border-color:#d97706!important}
.resume-btn button{background:#f0fdf4!important;color:#16a34a!important;
  border:1px solid #86efac!important;box-shadow:none!important}
.resume-btn button:hover{background:#dcfce7!important;border-color:#16a34a!important}

/* Chat */
[data-testid="stChatMessage"]{background:#f7f8fc!important;
  border:1px solid #e2e8f0!important;border-radius:12px!important}
[data-testid="stChatInput"]{border:1px solid #e2e8f0!important;
  border-radius:12px!important;background:#f7f8fc!important}
[data-testid="stChatInput"]:focus-within{border-color:#6B86F6!important;
  box-shadow:0 0 0 3px rgba(107,134,246,.12)!important}

/* Divider */
hr{border-color:#e2e8f0!important}

/* Metrics widget */
[data-testid="stMetric"]{background:#6B86F6;border:none;
  border-radius:12px;padding:14px 16px;box-shadow:0 2px 8px rgba(107,134,246,.25)}
[data-testid="stMetricLabel"]{font-size:.65rem!important;color:rgba(255,255,255,.75)!important;
  text-transform:uppercase;letter-spacing:.08em;font-weight:600!important}
[data-testid="stMetricValue"]{color:#fff!important;font-weight:700!important}
[data-testid="stMetricDelta"]{color:rgba(255,255,255,.8)!important}

/* Toggle */
[data-testid="stCheckbox"] label span{color:#334155!important;font-weight:500!important}

/* No-alerts placeholder */
.no-alerts{color:#94a3b8;font-size:.82rem;padding:12px 0;font-style:italic}

/* Video frame container */
.video-wrap{border-radius:12px;overflow:hidden;border:1px solid #e2e8f0;
  box-shadow:0 1px 3px rgba(0,0,0,.04)}
[data-testid="stImage"]{border-radius:12px;overflow:hidden}

/* Scrollbar */
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:#f1f5f9;border-radius:3px}
::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#94a3b8}

/* Container heights */
.chat-wrap [data-testid="stVerticalBlock"]{gap:.5rem}
</style>
""", unsafe_allow_html=True)

# Sidebar toggle button — inject into parent DOM via iframe
import streamlit.components.v1 as _stc
_stc.html("""
<script>
(function(){
  var pdoc = window.parent.document;
  if(pdoc.getElementById('aria-sb-btn')) return;

  var btn = pdoc.createElement('div');
  btn.id = 'aria-sb-btn';
  btn.innerHTML = '&#9776;';
  btn.title = 'Toggle sidebar';
  btn.style.cssText = 'position:fixed;top:14px;left:14px;z-index:999999;'+
    'width:38px;height:38px;border-radius:10px;border:1px solid #e2e8f0;'+
    'background:#fff;box-shadow:0 2px 8px rgba(0,0,0,.08);cursor:pointer;'+
    'display:flex;align-items:center;justify-content:center;font-size:1.2rem;'+
    'color:#64748b;user-select:none;transition:all .15s ease';
  pdoc.body.appendChild(btn);

  btn.onmouseenter = function(){ btn.style.background='#f1f5f9'; btn.style.color='#0f172a'; };
  btn.onmouseleave = function(){ btn.style.background='#fff'; btn.style.color='#64748b'; };

  var isOpen = true;
  btn.onclick = function(){
    var sb = pdoc.querySelector('section[data-testid="stSidebar"]');
    if(!sb) return;
    if(isOpen){
      sb.style.setProperty('transform','translateX(-100%)','important');
      sb.style.setProperty('visibility','hidden','important');
      sb.style.setProperty('transition','transform .3s ease, visibility .3s ease','important');
    } else {
      sb.style.setProperty('transform','none','important');
      sb.style.setProperty('visibility','visible','important');
      sb.style.setProperty('transition','transform .3s ease, visibility .3s ease','important');
    }
    isOpen = !isOpen;
  };
})();
</script>
""", height=0)

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("running", False), ("paused", False), ("messages", []),
    ("session_started", False), ("report_path", None),
    ("session_start_ts", None), ("user_bbox_cache", None),
    ("active_user", None), ("page", None), ("webrtc_key", 0),
    ("show_skeleton", False), ("_mic_active", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default



# Auto-detect page on first load
if st.session_state.page is None:
    _existing = face_id.get_registered_users()
    if _existing and len(_existing) == 1:
        st.session_state.page = "dashboard"
        st.session_state.active_user = _existing[0]
    elif _existing:
        st.session_state.page = "login"
    else:
        st.session_state.page = "registration"


# ── Registration Page ────────────────────────────────────────────────────────
def render_registration_page():
    import io
    import scipy.io.wavfile

    for key, default in [
        ("reg_step", 1), ("reg_name", ""),
        ("reg_face_done", False), ("reg_voice_done", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    step = st.session_state.reg_step

    # Header
    st.markdown("""
    <div style="max-width:580px;margin:30px auto 0;text-align:center">
      <div style="width:56px;height:56px;border-radius:14px;
        background:linear-gradient(135deg,#6B86F6,#8da2f8);
        display:inline-flex;align-items:center;justify-content:center;
        font-size:1.6rem;color:#fff;margin-bottom:12px">🧠</div>
      <h2 style="color:#0f172a;margin:0;font-weight:700;font-size:1.6rem;
        letter-spacing:-.02em">Welcome to Aria</h2>
      <p style="color:#94a3b8;font-size:.9rem;margin:6px 0 0">
        Let's set up your profile so Aria tracks only you.</p>
    </div>
    """, unsafe_allow_html=True)

    # Step indicator
    steps = ["Name", "Face", "Voice", "Done"]
    cols = st.columns([1, 3, 1])
    with cols[1]:
        step_html = '<div style="display:flex;justify-content:center;gap:8px;margin:24px 0 28px">'
        for i, label in enumerate(steps, 1):
            if i < step:
                bg, col, border = "#6B86F6", "#fff", "#6B86F6"
            elif i == step:
                bg, col, border = "#6B86F6", "#fff", "#6B86F6"
            else:
                bg, col, border = "#fff", "#94a3b8", "#e2e8f0"
            step_html += (
                f'<div style="display:flex;flex-direction:column;align-items:center;gap:4px">'
                f'<div style="width:32px;height:32px;border-radius:50%;background:{bg};'
                f'border:2px solid {border};color:{col};font-size:.78rem;font-weight:700;'
                f'display:flex;align-items:center;justify-content:center">{i}</div>'
                f'<span style="font-size:.65rem;color:{col if i==step else "#94a3b8"};'
                f'font-weight:600;text-transform:uppercase;letter-spacing:.05em">{label}</span>'
                f'</div>'
            )
            if i < len(steps):
                line_col = "#6B86F6" if i < step else "#e2e8f0"
                step_html += f'<div style="flex:1;height:2px;background:{line_col};align-self:center;margin:0 4px;margin-bottom:18px"></div>'
        step_html += '</div>'
        st.markdown(step_html, unsafe_allow_html=True)

    # Card wrapper
    card_cols = st.columns([1, 2.5, 1])
    with card_cols[1]:
        if step == 1:
            st.markdown('<p style="font-weight:600;color:#0f172a;font-size:1.05rem;margin-bottom:4px">'
                        'What\'s your name?</p>', unsafe_allow_html=True)
            st.caption("This is how Aria will address you.")
            name = st.text_input("Name", placeholder="e.g. Alex", label_visibility="collapsed", key="reg_name_input")
            if st.button("Continue", width="stretch", key="reg_next_1",
                         disabled=not name):
                st.session_state.reg_name = name.strip()
                st.session_state.reg_step = 2
                st.rerun()

        elif step == 2:
            st.markdown(f'<p style="font-weight:600;color:#0f172a;font-size:1.05rem;margin-bottom:4px">'
                        f'Face Enrollment</p>', unsafe_allow_html=True)
            st.caption("Take a clear photo looking directly at the camera.")
            cam_img = st.camera_input("Look at the camera", key="reg_cam", label_visibility="collapsed")
            c1, c2 = st.columns(2)
            with c1:
                if c1.button("Back", width="stretch", key="reg_back_2"):
                    st.session_state.reg_step = 1
                    st.rerun()
            with c2:
                if c2.button("Register Face", width="stretch", key="reg_face_btn",
                             disabled=cam_img is None):
                    with st.spinner("Extracting face embedding..."):
                        arr = np.frombuffer(cam_img.read(), np.uint8)
                        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        ok, msg = face_id.register_user(st.session_state.reg_name, [frame])
                    if ok:
                        st.session_state.reg_face_done = True
                        st.session_state.reg_step = 3
                        st.rerun()
                    else:
                        st.error(msg)

        elif step == 3:
            st.markdown('<p style="font-weight:600;color:#0f172a;font-size:1.05rem;margin-bottom:4px">'
                        'Voice Enrollment</p>', unsafe_allow_html=True)
            st.caption("Record yourself reading the sentence below (5–10 seconds).")
            st.info('"The quick brown fox jumps over the lazy dog near the quiet riverbank on a warm afternoon."')
            audio_file = st.audio_input("Record your voice", key="reg_voice_rec", label_visibility="collapsed")
            c1, c2 = st.columns(2)
            with c1:
                if c1.button("Skip", width="stretch", key="reg_skip_voice"):
                    st.session_state.reg_step = 4
                    st.rerun()
            with c2:
                if c2.button("Enroll Voice", width="stretch", key="reg_voice_btn",
                             disabled=audio_file is None):
                    with st.spinner("Processing voice..."):
                        sr, audio_data = scipy.io.wavfile.read(io.BytesIO(audio_file.read()))
                        audio_float = audio_data.astype(np.float32) / 32768.0
                        ok, msg = voice_id.enroll_speaker(st.session_state.reg_name, audio_float, sr)
                    if ok:
                        st.session_state.reg_voice_done = True
                        st.session_state.reg_step = 4
                        st.rerun()
                    else:
                        st.error(msg)

        elif step == 4:
            st.markdown(f'<div style="text-align:center;padding:16px 0">'
                        f'<div style="font-size:2.5rem;margin-bottom:8px">✅</div>'
                        f'<p style="font-weight:700;color:#0f172a;font-size:1.2rem;margin:0">'
                        f'All set, {st.session_state.reg_name}!</p>'
                        f'<p style="color:#94a3b8;font-size:.85rem;margin:6px 0 0">'
                        f'Your profile is ready. Aria will only track you.</p></div>',
                        unsafe_allow_html=True)

            checks = [("Face enrolled", st.session_state.reg_face_done),
                      ("Voice enrolled", st.session_state.reg_voice_done)]
            for label, done in checks:
                icon = "✓" if done else "—"
                color = "#16a34a" if done else "#94a3b8"
                st.markdown(f'<p style="color:{color};font-size:.85rem;font-weight:500;margin:4px 0">'
                            f'{icon} {label}</p>', unsafe_allow_html=True)

            if st.button("Start Monitoring", width="stretch", key="reg_finish"):
                st.session_state.page = "dashboard"
                st.session_state.active_user = st.session_state.reg_name
                for k in ["reg_step", "reg_name", "reg_face_done", "reg_voice_done"]:
                    st.session_state.pop(k, None)
                st.rerun()


# ── Login Page ────────────────────────────────────────────────────────────────
def render_login_page():
    _users = face_id.get_registered_users()
    if not _users:
        st.session_state.page = "registration"
        st.rerun()

    st.markdown("""
    <div style="max-width:580px;margin:30px auto 0;text-align:center">
      <div style="width:56px;height:56px;border-radius:14px;
        background:linear-gradient(135deg,#6B86F6,#8da2f8);
        display:inline-flex;align-items:center;justify-content:center;
        font-size:1.6rem;color:#fff;margin-bottom:12px">🧠</div>
      <h2 style="color:#0f172a;margin:0;font-weight:700;font-size:1.6rem;
        letter-spacing:-.02em">Welcome back</h2>
      <p style="color:#94a3b8;font-size:.9rem;margin:6px 0 24px">
        Select your profile to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    card_cols = st.columns([1, 2.5, 1])
    with card_cols[1]:
        for user in _users:
            _voice = user in voice_id.get_enrolled_speakers()
            _v_text = "Face + Voice" if _voice else "Face only"
            st.markdown(
                f'<div style="background:#f7f8fc;border:1px solid #e2e8f0;border-radius:12px;'
                f'padding:16px 18px;margin-bottom:8px;display:flex;align-items:center;'
                f'justify-content:space-between">'
                f'<div><span style="font-weight:700;color:#0f172a;font-size:1rem">👤 {user}</span>'
                f'<br><span style="color:#94a3b8;font-size:.75rem;font-weight:500">{_v_text}</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if st.button(f"Log in as {user}", width="stretch", key=f"login_{user}"):
                st.session_state.active_user = user
                st.session_state.page = "dashboard"
                st.session_state.user_bbox_cache = None
                load_user_calibration(user)
                st.rerun()

        st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
        if st.button("+ Register new user", width="stretch", key="login_new_user"):
            st.session_state.page = "registration"
            st.rerun()


# ── Page routing ─────────────────────────────────────────────────────────────
if st.session_state.page == "registration":
    render_registration_page()
    st.stop()

if st.session_state.page == "login":
    render_login_page()
    st.stop()

# ── Sidebar: Profile & Features ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec-label">User Profile</div>', unsafe_allow_html=True)

    _users = face_id.get_registered_users()

    if not _users:
        st.session_state.page = "registration"
        st.rerun()

    # Set active user if not set or if current active was deleted
    if st.session_state.active_user not in _users:
        st.session_state.active_user = _users[0]
    _active = st.session_state.active_user

    # Active user card
    _voice_enrolled = _active in voice_id.get_enrolled_speakers()
    _voice_icon = "✓" if _voice_enrolled else "✗"
    _voice_color = "#16a34a" if _voice_enrolled else "#94a3b8"
    st.markdown(
        f'<div style="background:#eef2ff;border:1px solid #c7d2fe;border-radius:12px;'
        f'padding:14px 16px;margin-bottom:10px">'
        f'<span style="color:#4f46e5;font-weight:700;font-size:.95rem">👤 {_active}</span>'
        f'<br><span style="color:#6366f1;font-size:.72rem;font-weight:500">Active user</span>'
        f'<br><span style="color:{_voice_color};font-size:.7rem;font-weight:500">'
        f'🎙️ Voice {_voice_icon}</span></div>',
        unsafe_allow_html=True
    )

    # Voice enrollment (if face is registered but voice isn't, or user requested it)
    _show_voice_enroll = not _voice_enrolled or st.session_state.get("_show_voice_enroll", False)
    if not _voice_enrolled and _show_voice_enroll:
        st.markdown('<div class="sec-label">Voice Enrollment</div>', unsafe_allow_html=True)
        st.caption("Record yourself reading the sentence below (5–10 sec).")
        st.info('"The quick brown fox jumps over the lazy dog near the quiet riverbank on a warm afternoon."')
        _voice_audio = st.audio_input("Record your voice", key="sidebar_voice_rec",
                                       label_visibility="collapsed")
        if st.button("Enroll Voice", width="stretch", key="sidebar_voice_enroll_btn",
                     disabled=_voice_audio is None):
            import io, scipy.io.wavfile
            with st.spinner("Processing voice..."):
                sr_rate, audio_data = scipy.io.wavfile.read(io.BytesIO(_voice_audio.read()))
                audio_float = audio_data.astype(np.float32) / 32768.0
                ok, msg = voice_id.enroll_speaker(_active, audio_float, sr_rate)
            if ok:
                st.success(msg)
                st.session_state.pop("_show_voice_enroll", None)
                st.rerun()
            else:
                st.error(msg)

    # Switch user (if multiple registered)
    if len(_users) > 1:
        _other_users = [u for u in _users if u != _active]
        selected = st.selectbox("Switch user", _other_users, key="switch_user_select",
                                label_visibility="collapsed",
                                index=None, placeholder="Switch to another user...")
        if selected:
            st.session_state.active_user = selected
            st.session_state.user_bbox_cache = None
            st.rerun()

    # Action buttons
    sb1, sb2 = st.columns(2)
    with sb1:
        if st.button("Log out", width="stretch", key="logout_btn"):
            st.session_state.active_user = None
            st.session_state.user_bbox_cache = None
            st.session_state.page = "login"
            if st.session_state.running:
                st.session_state.running = False
                typing_monitor.stop_monitoring()
                voice_stress.stop_monitoring()
            st.rerun()
    with sb2:
        if st.button("Delete", width="stretch", key="del_profile"):
            face_id.delete_user(_active)
            voice_id.delete_speaker(_active)
            st.session_state.active_user = None
            st.session_state.user_bbox_cache = None
            remaining = face_id.get_registered_users()
            if remaining:
                st.session_state.page = "login"
            else:
                st.session_state.page = "registration"
            if st.session_state.running:
                st.session_state.running = False
                typing_monitor.stop_monitoring()
                voice_stress.stop_monitoring()
            st.rerun()

    # Add new user button
    if st.button("+ Add new user", width="stretch", key="add_user_btn"):
        st.session_state.page = "registration"
        if st.session_state.running:
            st.session_state.running = False
            typing_monitor.stop_monitoring()
            voice_stress.stop_monitoring()
        st.rerun()

    st.markdown('<div class="sec-label" style="margin-top:16px">Features</div>',
                unsafe_allow_html=True)
    if "typing_enabled" not in st.session_state:
        st.session_state["typing_enabled"] = True
    st.toggle("Typing speed monitor", key="typing_enabled")
    _voice_toggle = st.toggle("Voice stress (mic)", key="_mic_active")
    if _voice_toggle:
        # Turning on — check enrollment
        if _active not in voice_id.get_enrolled_speakers():
            st.warning("Please enroll your voice below before enabling the mic.")
            st.session_state["_show_voice_enroll"] = True
            st.session_state["_mic_active"] = False
        else:
            set_control("mic_active", True)
    else:
        set_control("mic_active", False)

    if st.session_state.get("_mic_active"):
        # Use WebRTC bridge voice data when session is running
        if st.session_state.running:
            _vr = get_results().get("voice_data", {})
        else:
            _vr = voice_stress.get_current_reading()
        _v_wpm = _vr.get("speech_rate", 0.0)
        _v_str = _vr.get("stress_signal", 0.0)
        _v_spk = _vr.get("is_speaking", False)
        _v_st = _vr.get("status", "stopped")
        if _v_st in ("listening", "ok"):
            _vc = "#16a34a" if _v_str < 0.3 else "#f59e0b" if _v_str < 0.65 else "#ef4444"
            _spk_label = "Speaking" if _v_spk else "Listening..."
            _bar_w = int(min(100, _v_str * 100))
            st.markdown(
                f'<div style="background:#f7f8fc;border:1px solid #e2e8f0;border-radius:10px;'
                f'padding:10px 14px;margin-top:6px">'
                f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-size:.72rem;color:#64748b;font-weight:600">🎙️ {_spk_label}</span>'
                f'<span style="font-size:.85rem;font-weight:700;color:{_vc}">'
                f'{_v_wpm:.0f} <span style="font-size:.65rem;color:#94a3b8">WPM</span></span></div>'
                f'<div style="background:#e2e8f0;border-radius:4px;height:4px;margin-top:6px;overflow:hidden">'
                f'<div style="width:{_bar_w}%;height:100%;border-radius:4px;background:{_vc};'
                f'transition:width .3s"></div></div>'
                f'<div style="font-size:.62rem;color:#94a3b8;margin-top:3px;text-align:right">'
                f'stress {_bar_w}%</div></div>',
                unsafe_allow_html=True
            )

# ── Header ────────────────────────────────────────────────────────────────────
if st.session_state.running:
    dot, status_txt, chip_cls = "dot-live", "Live", "chip-live"
elif st.session_state.session_started:
    dot, status_txt, chip_cls = "dot-idle", "Stopped", "chip-idle"
else:
    dot, status_txt, chip_cls = "dot-idle", "Ready", "chip-idle"

user_chip = ""
if st.session_state.get("active_user"):
    user_chip = f'<span class="wm-chip chip-user">👤 {st.session_state.active_user}</span>'

st.markdown(f"""
<div class="wm-header">
  <div class="wm-left">
    <div class="wm-logo">🧠</div>
    <div>
      <p class="wm-title">Aria</p>
      <p class="wm-sub">AI Wellness Coach</p>
    </div>
  </div>
  <div class="wm-status">
    <span class="wm-chip {chip_cls}"><span class="wm-dot {dot}"></span>{status_txt}</span>
    {user_chip}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Layout: 2 columns — Feed+Metrics | Chat ──────────────────────────────────
col1, col2 = st.columns([1.25, 1])

# ── Left column: Feed + Metrics + Alerts ──────────────────────────────────────
with col1:
    st.markdown('<div class="sec-label">Live Feed</div>', unsafe_allow_html=True)
    timer_placeholder = st.empty()
    frame_placeholder = st.empty()
    # Toggles below the feed (only during active session)
    if st.session_state.running:
        _tc1, _tc2 = st.columns(2)
        with _tc1:
            st.toggle("Show posture skeleton", key="show_skeleton")
        with _tc2:
            _mic_status = st.session_state.get("_mic_active", False)
            _mic_label = "🎙️ Mic ON" if _mic_status else "🎙️ Mic OFF"
            st.markdown(f'<span style="font-size:0.85rem;color:{"#16a34a" if _mic_status else "#94a3b8"}">{_mic_label}</span>',
                        unsafe_allow_html=True)
    metrics_placeholder = st.empty()

    if not st.session_state.running:
        st.markdown('<div class="start-btn">', unsafe_allow_html=True)
        if st.button("Start Session", width="stretch", key="start_btn"):
            st.session_state.running = True
            st.session_state.paused = False
            st.session_state.session_started = True
            st.session_state.report_path = None
            st.session_state.session_start_ts = time.time()
            st.session_state.user_bbox_cache = None
            st.session_state.pop("_final_summary", None)
            st.session_state.pop("_final_alerts", None)
            st.session_state.pop("_final_elapsed", None)
            reset_blink(); reset_emotion(); reset_aggregator()
            reset_notifier(); reset_conversation()
            if st.session_state.get("active_user"):
                session_state["user_name"] = st.session_state.active_user
                load_user_calibration(st.session_state.active_user)
            if st.session_state.get("typing_enabled"):
                typing_monitor.reset_session(); typing_monitor.start_monitoring()
            reset_bridge()
            st.session_state.webrtc_key += 1  # fresh WebRTC connection
            if st.session_state.get("_mic_active"):
                set_control("mic_active", True)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        _btn1, _btn2 = st.columns(2)
        with _btn1:
            # Pause / Resume
            if st.session_state.paused:
                st.markdown('<div class="resume-btn">', unsafe_allow_html=True)
                if st.button("▶ Resume", width="stretch", key="resume_btn"):
                    st.session_state.paused = False
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="pause-btn">', unsafe_allow_html=True)
                if st.button("⏸ Pause", width="stretch", key="pause_btn"):
                    st.session_state.paused = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        with _btn2:
            # Stop — use on_click so webcam releases BEFORE rerun
            def _on_stop_click():
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

            st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
            st.button("⏹ Stop", width="stretch", key="stop_btn", on_click=_on_stop_click)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec-label">Alerts</div>', unsafe_allow_html=True)
    alert_placeholder = st.empty()

# ── Right column: Chat + Snapshot ─────────────────────────────────────────────
with col2:
    st.markdown('<div class="sec-label">Chat with Aria</div>', unsafe_allow_html=True)
    chat_container = st.container(height=340)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    user_input = st.chat_input("Ask Aria about your wellness...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
        with st.spinner("Thinking..."):
            reply = chat(user_input)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(reply)

    st.markdown('<div class="sec-label">Session Snapshot</div>', unsafe_allow_html=True)
    summary = get_session_summary()
    s1, s2 = st.columns(2)
    s1.metric("Posture", f"{summary['posture_score']}/100", summary['posture_trend'])
    s2.metric("Blinks/min", f"{summary['blink_rate']}")
    s3, s4 = st.columns(2)
    s3.metric("Emotion", f"{EMOTION_EMOJI.get(summary['dominant_emotion'],'😐')} {summary['dominant_emotion'].title()}")
    s4.metric("Seated", f"{summary['seated_mins']} min")

# ── Helpers for in-loop rendering ─────────────────────────────────────────────
BLINK_THR = config["alerts"]["blink_rate_low"]
SEATED_MAX = config["alerts"]["sitting_duration_mins"]

def _metrics_html(p_score, p_cat, blink_rate, emotion, emotion_conf, seated_mins,
                  typing_wpm=0.0, typing_stress=0.0, stress_index=0.0,
                  voice_rate=0.0, voice_stress=0.0, voice_speaking=False, voice_status="stopped"):
    pc = _posture_color(p_score)
    bc = _blink_color(blink_rate, BLINK_THR)
    sc = _seated_color(seated_mins, SEATED_MAX)
    ec = EMOTION_COLOR.get(emotion, "#64748b")
    ee = EMOTION_EMOJI.get(emotion, "😐")
    pbar = min(100, p_score)
    tc = "#16a34a" if typing_stress < 0.3 else "#f59e0b" if typing_stress < 0.65 else "#ef4444"
    wlabel = f"{typing_wpm:.0f}" if typing_wpm > 0 else "–"
    tstatus = ("normal" if typing_stress < 0.3 else
               "irregular" if typing_stress < 0.65 else "stressed") if typing_wpm > 0 else "calibrating..."
    stc = "#16a34a" if stress_index < 0.35 else "#f59e0b" if stress_index < 0.65 else "#ef4444"
    sbar = int(min(100, stress_index * 100))
    # Voice
    vc = "#16a34a" if voice_stress < 0.3 else "#f59e0b" if voice_stress < 0.65 else "#ef4444"
    v_rate_label = f"{voice_rate:.0f}" if voice_rate > 0 else "–"
    if voice_status == "stopped":
        v_status = "mic off"
        vc = "#94a3b8"
    elif voice_speaking:
        v_status = "speaking" if voice_stress < 0.3 else "rushed" if voice_stress < 0.65 else "stressed"
    else:
        v_status = "listening..."
        vc = "#64748b"
    vbar = int(min(100, voice_stress * 100))
    return f"""
<div class="metric-grid">
  <div class="mc">
    <div class="mc-label">Posture</div>
    <div class="mc-value" style="color:{pc}">{p_score}<span style="font-size:.8rem;color:#94a3b8">/100</span></div>
    <div class="prog-track"><div class="prog-fill" style="width:{pbar}%;background:{pc}"></div></div>
    <div class="mc-sub" style="color:{pc}">{p_cat.upper()}</div>
  </div>
  <div class="mc">
    <div class="mc-label">Blink Rate</div>
    <div class="mc-value" style="color:{bc}">{blink_rate:.1f}<span style="font-size:.8rem;color:#94a3b8"> /min</span></div>
    <div class="mc-sub">threshold {BLINK_THR}/min</div>
  </div>
  <div class="mc">
    <div class="mc-label">Emotion</div>
    <div class="mc-value">
      <span class="emo-badge" style="background:{ec}15;color:{ec};border:1px solid {ec}30">
        {ee} {emotion.title()}
      </span>
    </div>
    <div class="mc-sub">{emotion_conf:.0f}% confidence</div>
  </div>
</div>
<div class="metric-grid" style="margin-top:8px">
  <div class="mc">
    <div class="mc-label">Time Seated</div>
    <div class="mc-value" style="color:{sc}">{seated_mins:.0f}<span style="font-size:.8rem;color:#94a3b8"> min</span></div>
    <div class="mc-sub">break after {SEATED_MAX} min</div>
  </div>
  <div class="mc">
    <div class="mc-label">Typing</div>
    <div class="mc-value" style="color:{tc}">{wlabel}<span style="font-size:.8rem;color:#94a3b8"> WPM</span></div>
    <div class="mc-sub" style="color:{tc}">{tstatus}</div>
  </div>
  <div class="mc">
    <div class="mc-label">Voice</div>
    <div class="mc-value" style="color:{vc}">{v_rate_label}<span style="font-size:.8rem;color:#94a3b8"> WPM</span></div>
    <div class="prog-track"><div class="prog-fill" style="width:{vbar}%;background:{vc}"></div></div>
    <div class="mc-sub" style="color:{vc}">{v_status}</div>
  </div>
  <div class="mc">
    <div class="mc-label">Stress</div>
    <div class="mc-value" style="color:{stc}">{sbar}<span style="font-size:.8rem;color:#94a3b8">%</span></div>
    <div class="prog-track"><div class="prog-fill" style="width:{sbar}%;background:{stc}"></div></div>
    <div class="mc-sub">combined risk</div>
  </div>
</div>"""

ALERT_CLASS = {"posture": "al-posture", "blink": "al-blink",
               "seated": "al-seated", "combined": "al-combined"}

def _alerts_html(log):
    if not log:
        return '<p class="no-alerts">No alerts yet — looking good!</p>'
    html = ""
    for a in reversed(log[-5:]):
        cls = ALERT_CLASS.get(a["type"], "al-combined")
        t = time.strftime("%H:%M", time.localtime(a["timestamp"]))
        html += (f'<div class="alert-card {cls}">'
                 f'<strong>{a["title"]}</strong> &middot; {t}'
                 f'<br><span style="color:#64748b">{a["message"]}</span></div>')
    return html


# ── WebRTC video stream ───────────────────────────────────────────────────────
if st.session_state.running:
    # Sync control flags to the bridge (callback thread reads these)
    set_control("paused", st.session_state.paused)
    set_control("active_user", st.session_state.get("active_user"))
    set_control("show_skeleton", st.session_state.get("show_skeleton", False))
    _mic_is_on = st.session_state.get("_mic_active", False)
    set_control("mic_active", _mic_is_on)
    # Set voice status so the UI shows "listening" right away when mic is on
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
                rtc_configuration=RTC_CONFIG,
                async_processing=True,
            )

    # Auto-refresh every 2s so metrics/timer update while stream plays
    if ctx.state.playing:
        st_autorefresh(interval=2000, key="metrics_refresh")

        # Poll results from bridge
        _r = get_results()
        posture_data = _r["posture_data"]
        blink_data = _r["blink_data"]
        emotion_data = _r["emotion_data"]
        voice_data = _r["voice_data"]

        # Typing monitor (still local — only works on same machine)
        typing_data = {"wpm": 0.0, "stress_signal": 0.0, "status": "stopped"}
        if st.session_state.get("typing_enabled"):
            typing_data = typing_monitor.get_current_reading()
            update_typing(typing_data)

        # Process pending alerts from callback thread
        pending = _r.get("pending_alerts", [])
        if pending:
            for _a in pending:
                process_alerts([_a], use_streamlit=True)
            set_control("pending_alerts", [])

        # Update timer
        if st.session_state.session_start_ts:
            _elapsed_s = int(time.time() - st.session_state.session_start_ts)
            if st.session_state.paused:
                timer_placeholder.markdown(
                    f'<div style="text-align:right;font-size:.82rem;font-weight:600;'
                    f'color:#d97706;font-variant-numeric:tabular-nums;margin-bottom:4px">'
                    f'⏸ Paused &middot; {_elapsed_s//60:02d}:{_elapsed_s%60:02d}</div>',
                    unsafe_allow_html=True
                )
            else:
                timer_placeholder.markdown(
                    f'<div style="text-align:right;font-size:.82rem;font-weight:600;'
                    f'color:#64748b;font-variant-numeric:tabular-nums;margin-bottom:4px">'
                    f'⏱ {_elapsed_s//60:02d}:{_elapsed_s%60:02d}</div>',
                    unsafe_allow_html=True
                )

        # Metric cards
        summary = get_session_summary()
        p_score = posture_data.get("posture_score") or summary.get("posture_score", 0)
        p_cat = posture_data.get("category", "unknown")
        e_conf = emotion_data.get("emotion_confidence", 0.0)
        cur_emo = emotion_data.get("current_emotion", summary.get("dominant_emotion", "neutral"))

        metrics_placeholder.markdown(
            _metrics_html(p_score, p_cat, blink_data.get("blink_rate", 0.0),
                          cur_emo, e_conf, summary["seated_mins"],
                          typing_data.get("wpm", 0.0),
                          typing_data.get("stress_signal", 0.0),
                          summary.get("stress_index", 0.0),
                          voice_rate=voice_data.get("speech_rate", 0.0),
                          voice_stress=voice_data.get("stress_signal", 0.0),
                          voice_speaking=voice_data.get("is_speaking", False),
                          voice_status=voice_data.get("status", "stopped")),
            unsafe_allow_html=True
        )

        alert_placeholder.markdown(
            _alerts_html(get_notification_log()),
            unsafe_allow_html=True
        )

elif not st.session_state.running and st.session_state.get("session_started"):
    # Show saved results from the completed session
    _fs = st.session_state.get("_final_summary")
    if _fs:
        # Clear the video feed — session is over
        frame_placeholder.empty()

        # Show elapsed time
        _fe = st.session_state.get("_final_elapsed", 0)
        if _fe:
            timer_placeholder.markdown(
                f'<div style="text-align:right;font-size:.82rem;font-weight:600;'
                f'color:#64748b;font-variant-numeric:tabular-nums;margin-bottom:4px">'
                f'Session ended &middot; {_fe//60:02d}:{_fe%60:02d}</div>',
                unsafe_allow_html=True
            )

        # Show final metrics
        metrics_placeholder.markdown(
            _metrics_html(
                _fs.get("posture_score", 0),
                _fs.get("posture_trend", "unknown"),
                _fs.get("blink_rate", 0.0),
                _fs.get("dominant_emotion", "neutral"),
                _fs.get("emotion_pct", 0.0),
                _fs.get("seated_mins", 0),
                typing_wpm=_fs.get("typing_wpm", 0.0),
                typing_stress=_fs.get("typing_stress", 0.0),
                stress_index=_fs.get("stress_index", 0.0),
                voice_stress=_fs.get("voice_stress", 0.0)),
            unsafe_allow_html=True
        )

    # Show final alerts
    _fa = st.session_state.get("_final_alerts")
    if _fa:
        alert_placeholder.markdown(_alerts_html(_fa), unsafe_allow_html=True)
    else:
        alert_placeholder.markdown('<p class="no-alerts">No alerts — good session!</p>',
                                   unsafe_allow_html=True)
elif not st.session_state.running:
    alert_placeholder.markdown('<p class="no-alerts">No alerts yet — looking good!</p>',
                               unsafe_allow_html=True)

# ── Report section ────────────────────────────────────────────────────────────
if st.session_state.session_started and not st.session_state.running:
    st.divider()
    st.markdown('<div class="sec-label">Session Report</div>', unsafe_allow_html=True)
    rc1, rc2, _ = st.columns([1, 1, 2])

    with rc1:
        if st.button("Generate PDF Report", width="stretch"):
            with st.spinner("Generating AI report..."):
                try:
                    summary = get_session_summary()
                    ai_text = generate_report_summary()
                    save_session(summary, ai_text)
                    pdf_path = generate_pdf_report(
                        session_summary=summary,
                        ai_summary=ai_text,
                        posture_history=session_state.get("posture_history", []),
                        emotion_counts=session_state.get("emotion_counts", {})
                    )
                    st.session_state.report_path = pdf_path
                    st.success("Report ready!")
                except Exception as e:
                    st.error(f"Report failed: {e}")

    with rc2:
        if st.session_state.report_path:
            try:
                with open(st.session_state.report_path, "rb") as f:
                    st.download_button(
                        label="Download PDF",
                        data=f,
                        file_name="wellness_report.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
            except FileNotFoundError:
                st.session_state.report_path = None
