import cv2
import numpy as np
import time
import mediapipe as mp
from collections import deque

# MediaPipe eye landmark indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# State
blink_state = {
    "blink_count": 0,
    "blink_rate": 0.0,
    "last_blink_time": time.time(),
    "session_start": time.time(),
    "was_closed": False,
    "close_start": None,       # timestamp when eyes first closed
}

# Sliding window: stores timestamps of confirmed blinks
_blink_timestamps: deque = deque(maxlen=500)
_WINDOW_SECS = 60.0  # compute rate over last 60 seconds

# Adaptive EAR calibration
_ear_history: deque = deque(maxlen=150)  # open-eye EAR samples for calibration
_calibrated_threshold = None
_CALIBRATION_FRAMES = 40  # frames to calibrate from
_THRESHOLD_RATIO = 0.75   # threshold = ratio * median open-eye EAR

# Blink duration constraints (seconds)
_MIN_BLINK_DURATION = 0.05   # faster than 50ms = noise
_MAX_BLINK_DURATION = 0.6    # longer than 600ms = eyes just closed, not a blink

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


def calculate_ear(landmarks, eye_indices, img_w, img_h):
    """Calculate Eye Aspect Ratio for blink detection."""
    pts = []
    for idx in eye_indices:
        lm = landmarks[idx]
        pts.append((lm.x * img_w, lm.y * img_h))

    # EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C + 1e-6)


def _get_threshold():
    """Return adaptive threshold if calibrated, else fixed default."""
    if _calibrated_threshold is not None:
        return _calibrated_threshold
    return 0.21


def _compute_sliding_rate():
    """Compute blink rate from sliding window of recent blink timestamps."""
    now = time.time()
    # Remove blinks older than window
    while _blink_timestamps and (now - _blink_timestamps[0]) > _WINDOW_SECS:
        _blink_timestamps.popleft()

    count = len(_blink_timestamps)
    if count == 0:
        return 0.0

    # If we have less than WINDOW_SECS of session time, use actual elapsed
    elapsed = min(_WINDOW_SECS, now - blink_state["session_start"])
    if elapsed < 5.0:
        # Too early to give meaningful rate — extrapolate from what we have
        elapsed = max(1.0, elapsed)

    return round(count * (60.0 / elapsed), 1)


def get_current_reading(frame=None):
    """Required interface: returns dict with blink_rate."""
    global blink_state, _calibrated_threshold

    if frame is None:
        return {
            "blink_rate": 0.0,
            "blink_count": 0,
            "ear": 0.0,
            "status": "no_frame"
        }

    try:
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return {
                "blink_rate": blink_state["blink_rate"],
                "blink_count": blink_state["blink_count"],
                "ear": 0.0,
                "status": "no_face"
            }

        landmarks = results.multi_face_landmarks[0].landmark

        left_ear = calculate_ear(landmarks, LEFT_EYE, w, h)
        right_ear = calculate_ear(landmarks, RIGHT_EYE, w, h)
        avg_ear = (left_ear + right_ear) / 2.0

        now = time.time()
        threshold = _get_threshold()
        is_closed = avg_ear < threshold

        # Adaptive calibration: collect open-eye EAR samples
        if _calibrated_threshold is None:
            if not is_closed or len(_ear_history) < 5:
                # Assume early frames are open-eye (filter out very low values)
                if avg_ear > 0.15:
                    _ear_history.append(avg_ear)
            if len(_ear_history) >= _CALIBRATION_FRAMES:
                median_ear = float(np.median(list(_ear_history)))
                _calibrated_threshold = median_ear * _THRESHOLD_RATIO
                # Re-check current frame with new threshold
                threshold = _calibrated_threshold
                is_closed = avg_ear < threshold

        # Blink detection with duration filtering
        if is_closed and not blink_state["was_closed"]:
            # Eyes just closed — record the start time
            blink_state["close_start"] = now
        elif not is_closed and blink_state["was_closed"]:
            # Eyes just opened — check if this was a valid blink duration
            close_start = blink_state.get("close_start")
            if close_start is not None:
                duration = now - close_start
                if _MIN_BLINK_DURATION <= duration <= _MAX_BLINK_DURATION:
                    blink_state["blink_count"] += 1
                    blink_state["last_blink_time"] = now
                    _blink_timestamps.append(now)
            blink_state["close_start"] = None

        blink_state["was_closed"] = is_closed

        # Compute rate from sliding window
        blink_state["blink_rate"] = _compute_sliding_rate()

        return {
            "blink_rate": blink_state["blink_rate"],
            "blink_count": blink_state["blink_count"],
            "ear": round(avg_ear, 3),
            "is_blinking": is_closed,
            "threshold": round(threshold, 3),
            "calibrated": _calibrated_threshold is not None,
            "status": "ok"
        }

    except Exception as e:
        print(f"[blink] Error: {e}")
        return {
            "blink_rate": 0.0,
            "blink_count": 0,
            "ear": 0.0,
            "status": "error"
        }


def reset_session():
    """Reset blink counters for new session."""
    global blink_state, _calibrated_threshold
    blink_state = {
        "blink_count": 0,
        "blink_rate": 0.0,
        "last_blink_time": time.time(),
        "session_start": time.time(),
        "was_closed": False,
        "close_start": None,
    }
    _blink_timestamps.clear()
    _ear_history.clear()
    _calibrated_threshold = None
