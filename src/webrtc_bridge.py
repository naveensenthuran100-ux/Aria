"""
WebRTC bridge — video/audio frame callbacks for streamlit-webrtc.

Performance strategy:
- Video callback returns IMMEDIATELY with cached overlays (never blocks)
- Heavy ML runs in a separate background worker thread on sampled frames
- Worker thread picks up the latest frame and runs one ML task at a time
"""

import threading
import time
import collections
import logging
import numpy as np
import cv2
import av
import yaml

from src.vision.posture import get_current_reading as get_posture
from src.vision.blink import get_current_reading as get_blink
from src.vision.emotion import get_current_reading as get_emotion
from src.fusion.aggregator import (
    update_posture, update_blink, update_emotion,
    check_alerts,
)
from src.vision import face_id

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
with open("config.yaml", "r") as _f:
    _config = yaml.safe_load(_f)
BLINK_THR = _config.get("alerts", {}).get("blink_rate_low", 12.0)

# Time intervals (seconds) for each ML task in the worker thread
_INTERVAL_FACE_ID   = 3.0
_INTERVAL_FACE_SEEK = 1.0
_INTERVAL_POSTURE   = 0.8
_INTERVAL_BLINK     = 0.5
_INTERVAL_EMOTION   = 1.5
_INTERVAL_ALERTS    = 2.0

# ── Shared state ──────────────────────────────────────────────────────────────
_lock = threading.Lock()

_shared = {
    "posture_data": {"posture_score": 0, "category": "unknown"},
    "blink_data": {"blink_rate": 0.0, "status": "no_frame"},
    "emotion_data": {"current_emotion": "neutral", "emotion_confidence": 0.0},
    "voice_data": {"stress_signal": 0.0, "is_speaking": False, "status": "stopped"},
    "pending_alerts": [],
    "paused": False,
    "active_user": None,
    "show_skeleton": False,
    "mic_active": False,
}

# Per-thread cached ML results (written by worker, read by callback)
_ml_lock = threading.Lock()
_bbox_cache = None
_bbox_misses = 0
_posture_data = {"annotated_frame": None, "posture_score": 0, "category": "unknown"}
_blink_data = {"blink_rate": 0.0, "status": "no_frame"}
_emotion_data = {"current_emotion": "neutral", "emotion_confidence": 0.0}

# Latest frame for the worker thread to process
_latest_frame = None
_latest_frame_lock = threading.Lock()

# Frozen frame for pause (captured once when pause starts)
_paused_frame = None

# Worker thread control
_worker_thread = None
_worker_running = False

# Audio buffer
_audio_buffer: collections.deque = collections.deque(maxlen=400)
_last_audio_process = 0.0
_AUDIO_INTERVAL = 4.0


def get_results():
    with _lock:
        return {k: (v.copy() if isinstance(v, (dict, list)) else v) for k, v in _shared.items()}


def set_control(key, value):
    with _lock:
        _shared[key] = value


def reset_bridge():
    global _bbox_cache, _bbox_misses
    global _posture_data, _blink_data, _emotion_data
    global _last_audio_process, _latest_frame, _paused_frame

    _stop_worker()
    _paused_frame = None

    with _ml_lock:
        _bbox_cache = None
        _bbox_misses = 0
        _posture_data = {"annotated_frame": None, "posture_score": 0, "category": "unknown"}
        _blink_data = {"blink_rate": 0.0, "status": "no_frame"}
        _emotion_data = {"current_emotion": "neutral", "emotion_confidence": 0.0}

    with _latest_frame_lock:
        _latest_frame = None

    _last_audio_process = 0.0
    _audio_buffer.clear()

    with _lock:
        _shared["posture_data"] = {"posture_score": 0, "category": "unknown"}
        _shared["blink_data"] = {"blink_rate": 0.0, "status": "no_frame"}
        _shared["emotion_data"] = {"current_emotion": "neutral", "emotion_confidence": 0.0}
        _shared["voice_data"] = {"stress_signal": 0.0, "is_speaking": False, "status": "stopped"}
        _shared["pending_alerts"] = []


# ── Background ML worker ──────────────────────────────────────────────────────

def _start_worker():
    global _worker_thread, _worker_running
    if _worker_thread is not None and _worker_thread.is_alive():
        return
    _worker_running = True
    _worker_thread = threading.Thread(target=_ml_worker_loop, daemon=True)
    _worker_thread.start()


def _stop_worker():
    global _worker_running
    _worker_running = False


def _ml_worker_loop():
    """Runs in background thread. Grabs latest frame, runs ML tasks with time gating."""
    global _bbox_cache, _bbox_misses
    global _posture_data, _blink_data, _emotion_data

    last_face_id = 0.0
    last_posture = 0.0
    last_blink   = 0.0
    last_emotion = 0.0
    last_alerts  = 0.0

    while _worker_running:
      try:
        # Grab the latest frame
        with _latest_frame_lock:
            frame = _latest_frame
        if frame is None:
            time.sleep(0.05)
            continue

        with _lock:
            paused = _shared["paused"]
            active_user = _shared["active_user"]
        if paused:
            time.sleep(0.1)
            continue

        now = time.time()

        # ── Face ID ───────────────────────────────────────────────────
        with _ml_lock:
            has_bbox = _bbox_cache is not None
        face_interval = _INTERVAL_FACE_SEEK if (not has_bbox and active_user) else _INTERVAL_FACE_ID
        if active_user and (now - last_face_id) >= face_interval:
            last_face_id = now
            try:
                _id = face_id.identify_user(frame, active_user)
                with _ml_lock:
                    if _id["status"] == "ok":
                        new_bbox = _id["bbox"]
                        # Smooth bbox to reduce jitter
                        if _bbox_cache is not None:
                            _bbox_cache = tuple(
                                int(0.6 * new + 0.4 * old)
                                for new, old in zip(new_bbox, _bbox_cache)
                            )
                        else:
                            _bbox_cache = new_bbox
                        _bbox_misses = 0
                    else:
                        _bbox_misses += 1
                        if _bbox_misses >= 6:
                            _bbox_cache = None
            except Exception:
                pass

        # Get user body crop
        with _ml_lock:
            bbox = _bbox_cache
        user_frame = _get_user_frame(frame, bbox) if active_user else frame

        # ── Posture (YOLO) ────────────────────────────────────────────
        if (now - last_posture) >= _INTERVAL_POSTURE:
            last_posture = now
            try:
                result = get_posture(user_frame)
                with _ml_lock:
                    _posture_data = result
                update_posture(result)
            except Exception:
                pass
            # Share results immediately
            with _ml_lock:
                pd = {k: v for k, v in _posture_data.items() if k != "annotated_frame"}
            with _lock:
                _shared["posture_data"] = pd

        # ── Blink (MediaPipe) ─────────────────────────────────────────
        elif (now - last_blink) >= _INTERVAL_BLINK:
            last_blink = now
            try:
                result = get_blink(user_frame)
                with _ml_lock:
                    _blink_data = result
                update_blink(result)
            except Exception:
                pass
            with _ml_lock:
                bd = dict(_blink_data)
            with _lock:
                _shared["blink_data"] = bd

        # ── Emotion (HSEmotion) ───────────────────────────────────────
        elif (now - last_emotion) >= _INTERVAL_EMOTION:
            last_emotion = now
            try:
                with _ml_lock:
                    bbox_for_crop = _bbox_cache
                user_crop = (face_id.crop_user_face(frame, bbox_for_crop)
                             if active_user and bbox_for_crop else None)
                result = get_emotion(user_frame, face_crop=user_crop)
                with _ml_lock:
                    _emotion_data = result
                update_emotion(result)
            except Exception:
                pass
            with _ml_lock:
                ed = dict(_emotion_data)
            with _lock:
                _shared["emotion_data"] = ed

        # ── Alerts ────────────────────────────────────────────────────
        if (now - last_alerts) >= _INTERVAL_ALERTS:
            last_alerts = now
            try:
                alerts = check_alerts()
                if alerts:
                    with _lock:
                        _shared["pending_alerts"].extend(alerts)
            except Exception:
                pass

        # Small sleep to avoid busy-spinning when no tasks are due
        time.sleep(0.03)

      except Exception as e:
        # Never let the worker thread die — log and continue
        logger.error(f"[ml_worker] Unexpected error (recovering): {e}")
        time.sleep(0.1)


# ── Overlay helpers ───────────────────────────────────────────────────────────

def _add_info_overlay(frame, blink_rate, emotion):
    h, w = frame.shape[:2]
    strip_h = 36
    roi = frame[h - strip_h:h, 0:w]
    dark = np.zeros_like(roi)
    dark[:] = (30, 30, 35)
    frame[h - strip_h:h, 0:w] = cv2.addWeighted(dark, 0.75, roi, 0.25, 0)

    b_col = ((118, 230, 0) if blink_rate >= BLINK_THR
             else (0, 171, 255) if blink_rate >= BLINK_THR * 0.7
             else (68, 23, 255))
    cv2.putText(frame, f"Blink  {blink_rate:.1f}/min",
                (10, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.48, b_col, 1, cv2.LINE_AA)

    emo_str = emotion.title()
    (tw, _), _ = cv2.getTextSize(emo_str, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
    cv2.putText(frame, emo_str, (w - tw - 10, h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (210, 210, 215), 1, cv2.LINE_AA)


def _draw_posture_bar(display, p_score, p_cat):
    if p_score <= 0:
        return
    bar_c = ((0, 210, 90) if p_cat == "good"
             else (0, 165, 255) if p_cat == "moderate"
             else (60, 60, 220))
    h_f, w_f = display.shape[:2]
    cv2.rectangle(display, (0, 0), (w_f, 44), (30, 30, 35), -1)
    cv2.putText(display, f"Posture   {p_score}/100", (12, 28),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, bar_c, 1, cv2.LINE_AA)
    cv2.putText(display, p_cat.upper(), (w_f - 120, 28),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, bar_c, 1, cv2.LINE_AA)
    bar_w = int((w_f - 24) * min(p_score, 100) / 100)
    cv2.rectangle(display, (12, 34), (12 + bar_w, 40), bar_c, -1)


# Body crop multipliers — shared between posture crop and skeleton overlay
_BODY_W_MULT = 2.5   # face widths each side of center
_BODY_TOP_MULT = 0.5  # face heights above face
_BODY_BOT_MULT = 5.0  # face heights below face


def _body_region(bbox, img_h, img_w):
    """Return (top, bottom, left, right) of the body crop region."""
    top, right, bottom, left = bbox
    face_w = right - left
    face_h = bottom - top
    cx = (left + right) // 2
    b_l = max(0, cx - int(face_w * _BODY_W_MULT))
    b_r = min(img_w, cx + int(face_w * _BODY_W_MULT))
    b_t = max(0, top - int(face_h * _BODY_TOP_MULT))
    b_b = min(img_h, bottom + int(face_h * _BODY_BOT_MULT))
    return b_t, b_b, b_l, b_r


def _get_user_frame(img, bbox):
    """Crop wide enough for YOLO to see full upper body + hips for posture."""
    if bbox is None:
        return img
    h, w = img.shape[:2]
    b_t, b_b, b_l, b_r = _body_region(bbox, h, w)
    crop = img[b_t:b_b, b_l:b_r]
    return crop if crop.size > 0 else img


_SKEL_CONNECTIONS = [
    (5, 6), (0, 5), (0, 6), (5, 7), (6, 8), (7, 9), (8, 10),
    (5, 11), (6, 12), (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),
]

def _draw_skeleton_live(frame, kps, score, cat, crop_top, crop_left, crop_w, crop_h):
    """Draw skeleton on the live frame using cached keypoints (instant, no resize)."""
    color = {"good": (0, 210, 90), "moderate": (0, 165, 255), "poor": (60, 60, 220)}.get(cat, (128, 128, 128))

    # Keypoints are in crop-pixel coords from YOLO — offset to full-frame coords
    def kp_pt(i):
        return int(kps[i][0]) + crop_left, int(kps[i][1]) + crop_top

    def kp_conf(i):
        return kps[i][2] if len(kps[i]) > 2 else 0.0

    # Draw connections
    for a, b in _SKEL_CONNECTIONS:
        if a < len(kps) and b < len(kps) and kp_conf(a) > 0.3 and kp_conf(b) > 0.3:
            cv2.line(frame, kp_pt(a), kp_pt(b), color, 2, cv2.LINE_AA)

    # Draw keypoint dots
    for i in range(min(17, len(kps))):
        if kp_conf(i) > 0.3:
            p = kp_pt(i)
            cv2.circle(frame, p, 5, color, -1, cv2.LINE_AA)
            cv2.circle(frame, p, 5, (255, 255, 255), 1, cv2.LINE_AA)

    # Score bar at top
    h, w = frame.shape[:2]
    bar_h = 44
    roi = frame[0:bar_h, 0:w]
    dark = np.zeros_like(roi)
    dark[:] = (30, 30, 35)
    frame[0:bar_h, 0:w] = cv2.addWeighted(dark, 0.75, roi, 0.25, 0)
    cv2.putText(frame, f"Posture  {score}/100", (12, 28),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1, cv2.LINE_AA)
    cv2.putText(frame, cat.upper(), (w - 120, 28),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 1, cv2.LINE_AA)
    bar_w = int((w - 24) * min(score, 100) / 100)
    cv2.rectangle(frame, (12, 34), (12 + bar_w, 40), color, -1)


# ── Video callback (FAST — no ML, just overlays) ─────────────────────────────

def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    """MUST never raise — any exception kills the WebRTC feed."""
    global _latest_frame, _paused_frame

    try:
        img = frame.to_ndarray(format="bgr24")
    except Exception:
        return frame

    try:
        # Start worker if not running
        _start_worker()

        # Feed latest frame to worker thread (non-blocking)
        with _latest_frame_lock:
            _latest_frame = img

        with _lock:
            paused = _shared["paused"]
            active_user = _shared["active_user"]
            show_skeleton = _shared["show_skeleton"]

        if paused:
            # Capture the first frame when pause begins, then keep returning it
            if _paused_frame is None:
                overlay = img.copy()
                h, w = overlay.shape[:2]
                overlay = cv2.addWeighted(overlay, 0.4, np.zeros_like(overlay), 0.6, 0)
                text = "PAUSED"
                font = cv2.FONT_HERSHEY_DUPLEX
                scale = 1.5
                thickness = 3
                (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
                cx, cy = (w - tw) // 2, (h + th) // 2
                cv2.putText(overlay, text, (cx, cy), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
                _paused_frame = overlay
            return av.VideoFrame.from_ndarray(_paused_frame, format="bgr24")
        else:
            # Clear frozen frame when unpaused
            _paused_frame = None

        # Read cached ML results (fast — just reads, no computation)
        with _ml_lock:
            bbox = _bbox_cache
            p_data = dict(_posture_data)  # shallow copy to avoid mid-read mutation
            ann = _posture_data.get("annotated_frame")  # numpy ref is fine
            b_data = dict(_blink_data)
            e_data = dict(_emotion_data)

        # "Looking for user" overlay
        if active_user and bbox is None:
            cv2.putText(img, f"Looking for {active_user}...",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 255), 2, cv2.LINE_AA)
            return av.VideoFrame.from_ndarray(img, format="bgr24")

        # ── Compose display ───────────────────────────────────────────
        display = img  # reuse directly — no copy needed for non-skeleton path

        cached_kps = p_data.get("keypoints")
        if show_skeleton and cached_kps and active_user and bbox is not None:
            try:
                display = img.copy()
                h_f, w_f = img.shape[:2]
                b_t, b_b, b_l, b_r = _body_region(bbox, h_f, w_f)
                crop_w, crop_h = b_r - b_l, b_b - b_t
                if crop_w > 0 and crop_h > 0:
                    _draw_skeleton_live(display, cached_kps,
                                        p_data.get("posture_score", 0),
                                        p_data.get("category", "unknown"),
                                        b_t, b_l, crop_w, crop_h)
            except Exception:
                display = img
        elif show_skeleton and ann is not None and not active_user:
            display = ann.copy()
        else:
            display = img.copy()
            _draw_posture_bar(display,
                              p_data.get("posture_score", 0),
                              p_data.get("category", "unknown"))

        # User bounding box
        if active_user and bbox:
            try:
                top, right, bottom, left = bbox
                cv2.rectangle(display, (left, top), (right, bottom), (99, 102, 241), 2, cv2.LINE_AA)
                cv2.putText(display, active_user,
                            (left, max(0, top - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.46, (99, 102, 241), 1, cv2.LINE_AA)
            except Exception:
                pass

        _add_info_overlay(
            display,
            b_data.get("blink_rate", 0.0),
            e_data.get("current_emotion", "neutral")
        )

        return av.VideoFrame.from_ndarray(display, format="bgr24")

    except Exception as e:
        # Absolute last resort — return the raw frame, never crash
        logger.debug(f"[webrtc] callback error (feed preserved): {e}")
        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ── Audio callback ────────────────────────────────────────────────────────────

def _silent_frame(frame: av.AudioFrame) -> av.AudioFrame:
    """Return a silent audio frame with same format — prevents echo."""
    arr = frame.to_ndarray()
    silent = np.zeros_like(arr)
    out = av.AudioFrame.from_ndarray(silent, format=frame.format.name, layout=frame.layout.name)
    out.sample_rate = frame.sample_rate
    out.pts = frame.pts
    return out


def audio_frame_callback(frame: av.AudioFrame) -> av.AudioFrame:
    global _last_audio_process

    with _lock:
        mic_active = _shared["mic_active"]
        active_user = _shared["active_user"]

    if not mic_active:
        return _silent_frame(frame)

    sound = frame.to_ndarray()
    sample_rate = frame.sample_rate
    _audio_buffer.append((sound, sample_rate))

    now = time.time()
    if now - _last_audio_process < _AUDIO_INTERVAL:
        return _silent_frame(frame)
    _last_audio_process = now

    chunks = list(_audio_buffer)
    if len(chunks) < 10:
        return _silent_frame(frame)

    try:
        import speech_recognition as sr

        audio_np = np.concatenate([c[0].flatten() for c in chunks]).astype(np.float32)
        sr_rate = chunks[0][1]

        # Normalize float audio to [-1, 1] range if needed
        max_val = np.abs(audio_np).max()
        if max_val > 1.0:
            audio_np = audio_np / max_val

        logger.debug(f"[webrtc_audio] Processing {len(chunks)} chunks, "
                     f"{len(audio_np)} samples, sr={sr_rate}, "
                     f"range=[{audio_np.min():.3f}, {audio_np.max():.3f}]")

        # Voice identity verification (optional — don't block speech analysis)
        if active_user:
            try:
                from src.audio import voice_id
                result = voice_id.verify_speaker(audio_np, sr_rate, active_user)
                if result["status"] != "ok":
                    with _lock:
                        _shared["voice_data"]["is_speaking"] = False
                        _shared["voice_data"]["status"] = "listening"
                    _audio_buffer.clear()
                    return _silent_frame(frame)
            except Exception:
                pass  # Continue with speech analysis even if voice ID fails

        # Convert to int16 for speech_recognition
        audio_int16 = (audio_np * 32767).clip(-32768, 32767).astype(np.int16).tobytes()
        audio_data = sr.AudioData(audio_int16, sr_rate, 2)

        recognizer = sr.Recognizer()
        try:
            text = recognizer.recognize_google(audio_data)
            words = len(text.split())
            # Use actual buffer duration for accurate WPM
            duration_secs = max(1.0, len(chunks) * (sound.shape[-1] / sample_rate))
            rate = (words / duration_secs) * 60.0

            logger.info(f"[webrtc_audio] Recognized: '{text}' ({words} words, {rate:.0f} WPM)")

            with _lock:
                _shared["voice_data"] = {
                    "is_speaking": True,
                    "speech_rate": round(rate, 1),
                    "stress_signal": round(min(1.0, abs(rate - 140.0) / 140.0 * 1.5), 3),
                    "last_transcript": text,
                    "word_count": words,
                    "status": "listening",
                }
        except sr.UnknownValueError:
            with _lock:
                _shared["voice_data"]["is_speaking"] = False
                _shared["voice_data"]["status"] = "listening"
        except sr.RequestError as e:
            logger.warning(f"[webrtc_audio] Speech API error: {e}")

    except ImportError as e:
        logger.warning(f"[webrtc_audio] Missing module: {e}")
    except Exception as e:
        logger.warning(f"[webrtc_audio] Error: {e}")

    _audio_buffer.clear()
    return _silent_frame(frame)
