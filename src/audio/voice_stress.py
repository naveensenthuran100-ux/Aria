"""
Voice stress monitor — optional feature that uses SpeechRecognition to capture
the user's speech and derive a stress signal from speech rate.

When enabled it occupies the microphone; start it instead of (not alongside)
the low-level audio stress module to avoid hardware conflicts.

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

_state = {
    "is_speaking":    False,
    "speech_rate":    0.0,    # words per minute (current phrase)
    "last_transcript": "",
    "stress_signal":  0.0,    # 0–1 deviation from personal speech baseline
    "word_count":     0,
    "status":         "stopped",
}

_rate_samples: collections.deque = collections.deque(maxlen=30)
_thread = None
_running = False
_lock = threading.Lock()
_target_user = None

# Average English conversational rate
_NORMAL_RATE = 140.0   # wpm


def _listen_loop():
    global _running
    try:
        import speech_recognition as sr
    except ImportError:
        with _lock:
            _state["status"] = "no_library"
        logger.warning("[voice] SpeechRecognition not installed — run: pip install SpeechRecognition")
        return

    recognizer = sr.Recognizer()
    recognizer.energy_threshold       = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold        = 0.8

    with _lock:
        _state["status"] = "listening"

    while _running:
        try:
            with sr.Microphone() as source:
                # Short ambient-noise calibration every loop iteration
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                try:
                    audio = recognizer.listen(source, timeout=4, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    with _lock:
                        _state["is_speaking"] = False
                    continue

            # Speaker verification gate
            if _target_user:
                try:
                    from src.audio import voice_id
                    raw = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
                    result = voice_id.verify_speaker(raw, audio.sample_rate, _target_user)
                    if result["status"] != "ok":
                        with _lock:
                            _state["is_speaking"] = False
                        continue
                except Exception as e:
                    logger.debug(f"[voice] Speaker verification skipped: {e}")

            try:
                text = recognizer.recognize_google(audio)
                words = len(text.split())
                # Estimate phrase duration: ~400ms per word at normal pace
                duration_secs = max(1.0, words * 0.4)
                rate = (words / duration_secs) * 60.0  # → wpm

                with _lock:
                    _state["is_speaking"]     = True
                    _state["last_transcript"] = text
                    _state["word_count"]      += words
                    _state["speech_rate"]     = round(rate, 1)
                    _rate_samples.append(rate)

                    # Personalised baseline: median of recent rates
                    if len(_rate_samples) >= 5:
                        baseline  = float(np.median(list(_rate_samples)))
                        deviation = abs(rate - baseline) / (baseline + 1e-9)
                        _state["stress_signal"] = round(min(1.0, deviation * 1.5), 3)
                    else:
                        # Cold start: use fixed normal rate
                        deviation = abs(rate - _NORMAL_RATE) / _NORMAL_RATE
                        _state["stress_signal"] = round(min(1.0, deviation * 1.5), 3)

                logger.debug(f"[voice] '{text}' | {rate:.0f} wpm | "
                             f"stress={_state['stress_signal']:.2f}")

            except sr.UnknownValueError:
                with _lock:
                    _state["is_speaking"] = False
            except sr.RequestError as e:
                logger.warning(f"[voice] Google Speech API error: {e}")
                time.sleep(3)

        except Exception as e:
            logger.error(f"[voice] Loop error: {e}")
            time.sleep(2)


def start_monitoring(target_user=None):
    global _thread, _running, _target_user
    if _running:
        return
    _target_user = target_user
    _running = True
    _thread = threading.Thread(target=_listen_loop, daemon=True, name="voice_stress")
    _thread.start()
    logger.info("[voice] Voice stress monitor started")


def stop_monitoring():
    global _running
    _running = False
    with _lock:
        _state["status"] = "stopped"
        _state["is_speaking"] = False


def get_current_reading() -> dict:
    with _lock:
        return dict(_state)


def reset_session():
    with _lock:
        _rate_samples.clear()
        _state.update({
            "is_speaking":    False,
            "speech_rate":    0.0,
            "last_transcript": "",
            "stress_signal":  0.0,
            "word_count":     0,
        })
