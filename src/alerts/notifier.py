import time
import yaml
from plyer import notification
import streamlit as st

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

COOLDOWN = config["alerts"]["cooldown_mins"] * 60

notifier_state = {
    "last_notify_time": 0,
    "notification_log": []
}

ALERT_MESSAGES = {
    "posture": {
        "title": "🪑 Posture Alert",
        "icon": "🪑"
    },
    "blink": {
        "title": "👁️ Eye Fatigue Alert",
        "icon": "👁️"
    },
    "seated": {
        "title": "⏰ Break Reminder",
        "icon": "⏰"
    },
    "combined": {
        "title": "🧠 Wellness Check",
        "icon": "🧠"
    }
}

def send_desktop_notification(title: str, message: str):
    """Send native desktop notification via plyer."""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Wellness Monitor",
            timeout=8
        )
    except Exception as e:
        print(f"[notifier] Desktop notification failed: {e}")

def send_streamlit_toast(message: str, icon: str = "⚠️"):
    """Send Streamlit toast notification."""
    try:
        st.toast(message, icon=icon)
    except Exception as e:
        print(f"[notifier] Streamlit toast failed: {e}")

def process_alerts(alerts: list, use_streamlit: bool = False):
    """
    Process list of alerts from aggregator.
    Sends desktop + optional streamlit notifications.
    """
    if not alerts:
        return

    now = time.time()
    cooldown_ok = (now - notifier_state["last_notify_time"]) > COOLDOWN

    if not cooldown_ok:
        return

    for alert in alerts:
        alert_type = alert.get("type", "combined")
        message = alert.get("message", "Wellness alert triggered.")
        meta = ALERT_MESSAGES.get(alert_type, ALERT_MESSAGES["combined"])

        # Desktop notification
        send_desktop_notification(meta["title"], message)

        # Streamlit toast if in UI context
        if use_streamlit:
            send_streamlit_toast(message, meta["icon"])

        # Log it
        notifier_state["notification_log"].append({
            "type": alert_type,
            "message": message,
            "timestamp": now,
            "title": meta["title"]
        })
        if len(notifier_state["notification_log"]) > 100:
            notifier_state["notification_log"] = notifier_state["notification_log"][-100:]

        print(f"[notifier] Alert sent: {meta['title']} — {message}")

    notifier_state["last_notify_time"] = now

def get_notification_log():
    """Return full notification history."""
    return notifier_state["notification_log"]

def reset_notifier():
    """Reset notification state for new session."""
    notifier_state["last_notify_time"] = 0
    notifier_state["notification_log"] = []
