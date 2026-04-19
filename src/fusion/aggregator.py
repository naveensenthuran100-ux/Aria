import time
import yaml
from pathlib import Path

# Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Master session state — shared across all modules
session_state = {
    "user_name": config["user"]["name"],
    "baseline_blink": config["user"]["baseline_blink"],
    "usual_duration": config["user"]["usual_duration"],
    "session_start": time.time(),
    "seated_mins": 0,

    # Signal readings
    "posture_score": 0,
    "posture_trend": "stable",
    "posture_details": {},
    "posture_history": [],
    "stress_history": [],

    "blink_rate": 0.0,
    "blink_count": 0,
    "ear": 0.0,

    "dominant_emotion": "neutral",
    "current_emotion": "neutral",
    "emotion_pct": 0.0,
    "emotion_counts": {},

    "stress_index": 0.0,
    "typing_wpm": 0.0,
    "typing_stress": 0.0,
    "voice_stress": 0.0,

    # Alerts
    "alerts_triggered": [],
    "last_alert_time": 0,

    # Status
    "window_mins": 5,
    "is_running": False
}

# Thresholds from config
POSTURE_LOW = config["alerts"]["posture_score_low"]
BLINK_LOW = config["alerts"]["blink_rate_low"]
SEATED_MAX = config["alerts"]["sitting_duration_mins"]
STRESS_MAX = config["alerts"]["stress_dominant_mins"]
COOLDOWN = config["alerts"]["cooldown_mins"] * 60
COMBINED_THRESHOLD = config["alerts"]["combined_score_threshold"]

def update_posture(reading: dict):
    """Update posture signals in session state."""
    # Only accept successful readings — posture.py now sets status:"ok" on detection
    if reading.get("status") != "ok":
        return
    curr = reading.get("posture_score")
    if curr is None:
        return
    prev = session_state["posture_score"]
    session_state["posture_score"] = curr
    session_state["posture_details"] = reading.get("details", {})
    session_state["posture_history"].append({
        "score": curr,
        "timestamp": time.time()
    })
    # Keep last 500 readings
    if len(session_state["posture_history"]) > 500:
        session_state["posture_history"] = session_state["posture_history"][-500:]
    # Trend
    if curr > prev + 5:
        session_state["posture_trend"] = "improving"
    elif curr < prev - 5:
        session_state["posture_trend"] = "declining"
    else:
        session_state["posture_trend"] = "stable"

def update_blink(reading: dict):
    """Update blink signals in session state."""
    if reading.get("status") not in ("ok", "no_face"):
        return
    session_state["blink_rate"] = reading.get("blink_rate", 0.0)
    session_state["blink_count"] = reading.get("blink_count", 0)
    session_state["ear"] = reading.get("ear", 0.0)

def update_emotion(reading: dict):
    """Update emotion signals in session state."""
    if reading.get("status") not in ("ok", "no_frame"):
        return
    session_state["current_emotion"] = reading.get("current_emotion", "neutral")
    session_state["dominant_emotion"] = reading.get("dominant_emotion", "neutral")
    session_state["emotion_pct"] = reading.get("emotion_pct", 0.0)
    session_state["emotion_counts"] = reading.get("emotion_counts", {})

def update_audio(reading: dict):
    """Update audio stress signals in session state."""
    if reading.get("status") != "ok":
        return
    session_state["stress_index"] = reading.get("stress_index", 0.0)


def update_typing(reading: dict):
    """Update typing speed / stress signals in session state."""
    if reading.get("status") not in ("running", "ok"):
        return
    session_state["typing_wpm"]    = reading.get("wpm", 0.0)
    session_state["typing_stress"] = reading.get("stress_signal", 0.0)


def update_voice(reading: dict):
    """Update voice stress signals in session state."""
    if reading.get("status") not in ("listening", "ok"):
        return
    session_state["voice_stress"] = reading.get("stress_signal", 0.0)

def update_seated_time():
    """Update how long user has been seated."""
    elapsed = (time.time() - session_state["session_start"]) / 60.0
    session_state["seated_mins"] = round(elapsed, 1)
    session_state["window_mins"] = min(round(elapsed, 1), 5)

def calculate_combined_score():
    """
    Weighted fusion score 0-1.
    Higher = more at risk / needs attention.
    """
    posture_risk = max(0, (100 - session_state["posture_score"]) / 100)
    blink_risk = 1.0 if session_state["blink_rate"] < BLINK_LOW and session_state["blink_rate"] > 0 else 0.0
    seated_risk = min(1.0, session_state["seated_mins"] / SEATED_MAX)
    stress_risk = session_state["stress_index"]
    emotion_risk = 1.0 if session_state["dominant_emotion"] in ("angry", "fear", "sad") else 0.0

    typing_risk = session_state["typing_stress"]
    voice_risk  = session_state["voice_stress"]
    combined = (
        posture_risk * 0.30 +
        blink_risk   * 0.18 +
        seated_risk  * 0.18 +
        stress_risk  * 0.12 +
        emotion_risk * 0.10 +
        typing_risk  * 0.07 +
        voice_risk   * 0.05
    )
    return round(combined, 3)

def check_alerts():
    """Check all thresholds and return list of triggered alerts."""
    now = time.time()
    cooldown_ok = (now - session_state["last_alert_time"]) > COOLDOWN
    alerts = []

    if not cooldown_ok:
        return alerts

    if session_state["posture_score"] < POSTURE_LOW and session_state["posture_score"] > 0:
        alerts.append({
            "type": "posture",
            "message": f"Poor posture detected! Score: {session_state['posture_score']}/100",
            "timestamp": now
        })

    if session_state["blink_rate"] < BLINK_LOW and session_state["blink_rate"] > 0:
        alerts.append({
            "type": "blink",
            "message": f"Eye fatigue risk! Blink rate: {session_state['blink_rate']}/min",
            "timestamp": now
        })

    if session_state["seated_mins"] > SEATED_MAX:
        alerts.append({
            "type": "seated",
            "message": f"You've been seated for {session_state['seated_mins']} mins. Take a break!",
            "timestamp": now
        })

    combined = calculate_combined_score()
    session_state["stress_history"].append({
        "score": combined,
        "timestamp": now
    })
    if len(session_state["stress_history"]) > 500:
        session_state["stress_history"] = session_state["stress_history"][-500:]

    if combined > COMBINED_THRESHOLD:
        alerts.append({
            "type": "combined",
            "message": f"Overall wellness score low ({combined}). Consider a break.",
            "timestamp": now
        })

    if alerts:
        session_state["last_alert_time"] = now
        session_state["alerts_triggered"].extend(alerts)

    return alerts

def get_session_summary():
    """Return full session state for Claude chatbot context."""
    update_seated_time()
    return {
        "user_name":        session_state["user_name"],
        "baseline_blink":   session_state["baseline_blink"],
        "usual_duration":   session_state["usual_duration"],
        "window":           session_state["window_mins"],
        "posture_score":    session_state.get("posture_score", 0),
        "posture_details":  session_state.get("posture_details", {}),
        "posture_trend":    session_state["posture_trend"],
        "blink_rate":       session_state["blink_rate"],
        "dominant_emotion": session_state["dominant_emotion"],
        "emotion_pct":      session_state["emotion_pct"],
        "seated_mins":      session_state["seated_mins"],
        "stress_index":     calculate_combined_score(),
        "typing_wpm":       session_state["typing_wpm"],
        "typing_stress":    session_state["typing_stress"],
        "voice_stress":     session_state["voice_stress"],
        "alerts_triggered": len(session_state["alerts_triggered"])
    }

def reset_session():
    """Reset full session state."""
    global session_state
    session_state.update({
        "session_start":   time.time(),
        "seated_mins":     0,
        "posture_score":   0,
        "posture_trend":   "stable",
        "posture_history": [],
        "stress_history":  [],
        "blink_rate":      0.0,
        "blink_count":     0,
        "dominant_emotion": "neutral",
        "current_emotion":  "neutral",
        "emotion_pct":      0.0,
        "stress_index":     0.0,
        "typing_wpm":       0.0,
        "typing_stress":    0.0,
        "voice_stress":     0.0,
        "alerts_triggered": [],
        "last_alert_time":  0,
    })
