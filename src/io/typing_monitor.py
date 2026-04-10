"""
Typing speed monitor — measures WPM and detects stress from keystroke patterns.

Runs a pynput keyboard listener in a daemon thread.
WPM is computed over a rolling 30-second window; stress is derived from how
much the current rate deviates from the user's personal typing baseline.

API
---
start_monitoring()
stop_monitoring()
get_current_reading() → dict
reset_session()
"""

import threading
import time
import collections
import logging
import numpy as np

logger = logging.getLogger(__name__)

_WINDOW      = 30.0   # seconds for rolling WPM window
_CHARS_PER_WORD = 5   # standard for WPM calculation

_state = {
    "wpm":           0.0,
    "baseline_wpm":  None,   # established after ~8 samples
    "stress_signal": 0.0,    # 0–1 deviation from baseline
    "total_keys":    0,
    "status":        "stopped",
}

_timestamps: collections.deque = collections.deque()
_baseline_samples: collections.deque = collections.deque(maxlen=20)
_listener = None
_lock = threading.Lock()


def _on_press(key):
    now = time.time()
    with _lock:
        _timestamps.append(now)
        _state["total_keys"] += 1

        # Drop timestamps outside the rolling window
        cutoff = now - _WINDOW
        while _timestamps and _timestamps[0] < cutoff:
            _timestamps.popleft()

        count = len(_timestamps)
        wpm   = round((count / _CHARS_PER_WORD) / (_WINDOW / 60.0), 1)
        _state["wpm"] = wpm

        # Accumulate for baseline (only count non-zero bursts)
        if wpm > 5:
            _baseline_samples.append(wpm)

        # Establish baseline after enough samples; then slowly adapt it
        if _state["baseline_wpm"] is None:
            if len(_baseline_samples) >= 8:
                _state["baseline_wpm"] = float(np.median(list(_baseline_samples)))
        else:
            _state["baseline_wpm"] = 0.97 * _state["baseline_wpm"] + 0.03 * wpm
            baseline = _state["baseline_wpm"]
            if baseline > 0:
                deviation = abs(wpm - baseline) / baseline
                # Squash: 50% deviation → 1.0 stress
                _state["stress_signal"] = round(min(1.0, deviation * 2.0), 3)


def start_monitoring():
    global _listener
    try:
        from pynput import keyboard
        if _listener is not None and _listener.running:
            return
        _listener = keyboard.Listener(on_press=_on_press)
        _listener.start()
        with _lock:
            _state["status"] = "running"
        logger.info("[typing] Keyboard monitor started")
    except ImportError:
        with _lock:
            _state["status"] = "no_library"
        logger.warning("[typing] pynput not installed — run: pip install pynput")
    except Exception as e:
        with _lock:
            _state["status"] = "error"
        logger.warning(f"[typing] Cannot start listener: {e} "
                       "(macOS: grant Accessibility access in System Settings)")


def stop_monitoring():
    global _listener
    if _listener:
        _listener.stop()
        _listener = None
    with _lock:
        _state["status"] = "stopped"


def get_current_reading() -> dict:
    with _lock:
        return dict(_state)


def reset_session():
    with _lock:
        _timestamps.clear()
        _baseline_samples.clear()
        _state.update({
            "wpm":           0.0,
            "baseline_wpm":  None,
            "stress_signal": 0.0,
            "total_keys":    0,
        })
