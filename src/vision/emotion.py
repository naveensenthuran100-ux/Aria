import cv2
import numpy as np
import os
import pickle
import time
import collections
import logging

logger = logging.getLogger(__name__)

# --- Constants ---
BUFFER_SIZE    = 8      # rolling window for stable output
MIN_FACE_PX    = 48     # minimum face detection size
MIN_CONFIDENCE = 0.20   # minimum probability threshold (0-1 scale)
FACE_INPUT_SIZE = 260   # enet_b2 uses 260×260
PROFILES_DIR   = "data/profiles"

# --- HSEmotion (enet_b2_8 — larger, more accurate, trained on AffectNet) ---
_hse_model = None
_HSE_MODEL_NAME = "enet_b2_8"

# Map HSEmotion labels → our unified label set
_HSE_MAP = {
    "Anger": "angry", "Contempt": "angry",   # merge contempt into angry
    "Disgust": "disgust", "Fear": "fear",
    "Happiness": "happy", "Neutral": "neutral",
    "Sadness": "sad", "Surprise": "surprise"
}

def _get_hse():
    global _hse_model
    if _hse_model is None:
        try:
            from hsemotion_onnx.facial_emotions import HSEmotionRecognizer
            _hse_model = HSEmotionRecognizer(model_name=_HSE_MODEL_NAME)
            logger.info(f"[emotion] Loaded HSEmotion {_HSE_MODEL_NAME}")
        except Exception as e:
            print(f"[emotion] HSEmotion unavailable: {e}")
            _hse_model = "unavailable"
    return _hse_model


# --- MediaPipe face detection ---
_mp_face = None

def _get_mp_face():
    global _mp_face
    if _mp_face is None:
        try:
            import mediapipe as mp
            _mp_face = mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )
        except ImportError:
            _mp_face = "unavailable"
    return _mp_face


# --- Haar cascade fallback ---
_face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# --- Per-user calibration ---
_calibration = {
    "user": None,
    "samples": 0,
    "emotion_stats": {},   # {emotion: {"total_conf": float, "count": int}}
    "total_readings": 0,
}

def load_user_calibration(name: str):
    """Load saved emotion calibration for a user, or start fresh."""
    _calibration["user"] = name
    path = os.path.join(PROFILES_DIR, f"{name}_emotion.pkl")
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                saved = pickle.load(f)
            _calibration["samples"] = saved.get("samples", 0)
            _calibration["emotion_stats"] = saved.get("emotion_stats", {})
            _calibration["total_readings"] = saved.get("total_readings", 0)
            logger.info(f"[emotion] Loaded calibration for {name} "
                        f"({_calibration['total_readings']} readings)")
        except Exception as e:
            logger.warning(f"[emotion] Could not load calibration for {name}: {e}")
            _reset_calibration(name)
    else:
        _reset_calibration(name)


def save_user_calibration(name: str):
    """Persist current calibration data to disk."""
    if _calibration["total_readings"] < 10:
        return
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f"{name}_emotion.pkl")
    data = {
        "samples": _calibration["samples"],
        "emotion_stats": _calibration["emotion_stats"],
        "total_readings": _calibration["total_readings"],
    }
    try:
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"[emotion] Saved calibration for {name} "
                    f"({_calibration['total_readings']} readings)")
    except Exception as e:
        logger.warning(f"[emotion] Could not save calibration for {name}: {e}")


def _reset_calibration(name: str):
    _calibration["user"] = name
    _calibration["samples"] = 0
    _calibration["emotion_stats"] = {}
    _calibration["total_readings"] = 0


def _update_calibration(emotion: str, confidence: float):
    """Track per-emotion statistics for personalization."""
    _calibration["total_readings"] += 1
    _calibration["samples"] += 1
    stats = _calibration["emotion_stats"]
    if emotion not in stats:
        stats[emotion] = {"total_conf": 0.0, "count": 0}
    stats[emotion]["total_conf"] += confidence
    stats[emotion]["count"] += 1


def _apply_calibration(dominant: str, confidence: float, all_probs: dict):
    """Apply personal bias correction once enough data is collected.

    If the user's resting face is frequently misread as a certain emotion
    with low confidence, reclassify it based on their personal baseline.
    """
    total = _calibration["total_readings"]
    if total < 50:
        return dominant, confidence  # cold start — use raw predictions

    stats = _calibration["emotion_stats"]

    # Compute user's personal frequency distribution
    frequencies = {}
    for emo, s in stats.items():
        frequencies[emo] = s["count"] / total

    # Get user's mean confidence for the predicted emotion
    if dominant in stats and stats[dominant]["count"] > 0:
        mean_conf = stats[dominant]["total_conf"] / stats[dominant]["count"]
    else:
        return dominant, confidence

    # Bias correction: if a non-neutral emotion fires frequently (>25%) with
    # low confidence relative to baseline, it's likely a resting-face artifact
    if dominant != "neutral" and dominant in ("sad", "angry", "fear", "disgust"):
        freq = frequencies.get(dominant, 0.0)
        neutral_freq = frequencies.get("neutral", 0.0)

        # If this "negative" emotion fires more than neutral and has weak
        # confidence, it's probably the user's resting face
        if (freq > 0.25 and confidence < mean_conf * 0.8 and
                confidence < 0.40):
            # Demote to next-best emotion (usually neutral)
            sorted_emos = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)
            for emo, conf in sorted_emos:
                if emo != dominant:
                    return emo, conf
            return "neutral", confidence

    return dominant, confidence


# --- Module state ---
emotion_state = {
    "current_emotion": "neutral",
    "dominant_emotion": "neutral",
    "emotion_confidence": 0.0,
    "emotion_pct": 0.0,
    "emotion_history": [],
    "session_start": time.time(),
    "emotion_counts": {
        "happy": 0, "neutral": 0, "sad": 0,
        "angry": 0, "fear": 0, "disgust": 0, "surprise": 0
    }
}
_emotion_buffer: collections.deque = collections.deque(maxlen=BUFFER_SIZE)
_confidence_buffer: collections.deque = collections.deque(maxlen=BUFFER_SIZE)


def _detect_face_mediapipe(frame):
    mp_face = _get_mp_face()
    if mp_face == "unavailable":
        return None
    h, w = frame.shape[:2]
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_face.process(rgb)
    if not results.detections:
        return None
    best = max(results.detections, key=lambda d: d.score[0])
    bbox = best.location_data.relative_bounding_box
    x1 = max(0, int(bbox.xmin * w))
    y1 = max(0, int(bbox.ymin * h))
    bw = int(bbox.width * w)
    bh = int(bbox.height * h)
    if bw < MIN_FACE_PX or bh < MIN_FACE_PX:
        return None
    pad = int(0.25 * max(bw, bh))
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x1 + bw + 2 * pad)
    y2 = min(h, y1 + bh + 2 * pad)
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def _detect_face_haar(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_eq = cv2.equalizeHist(gray)
    faces = _face_cascade.detectMultiScale(
        gray_eq, scaleFactor=1.1, minNeighbors=5,
        minSize=(MIN_FACE_PX, MIN_FACE_PX)
    )
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    pad = int(0.25 * max(w, h))
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(frame.shape[1], x + w + pad)
    y2 = min(frame.shape[0], y + h + pad)
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def _detect_face_crop(frame):
    crop = _detect_face_mediapipe(frame)
    if crop is not None:
        return crop
    return _detect_face_haar(frame)


def _hse_predict(face_bgr):
    """HSEmotion prediction — returns (unified_emotion, confidence_0to1, all_probs)."""
    hse = _get_hse()
    if hse == "unavailable":
        return None, 0.0, {}
    try:
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        emo_label, raw_scores = hse.predict_emotions(face_rgb, logits=False)
        probs = raw_scores[:8]
        idx_to_class = hse.idx_to_class
        # Build unified probability dict
        unified = collections.defaultdict(float)
        for i, p in enumerate(probs):
            cls = idx_to_class.get(i, "neutral")
            mapped = _HSE_MAP.get(cls, "neutral")
            unified[mapped] += float(p)
        dominant = max(unified, key=unified.get)
        return dominant, unified[dominant], dict(unified)
    except Exception as e:
        print(f"[emotion] HSE error: {e}")
        return None, 0.0, {}


def get_dominant_emotion(session_mins=5):
    cutoff = time.time() - (session_mins * 60)
    recent = [
        e["emotion"] for e in emotion_state["emotion_history"]
        if e["timestamp"] > cutoff
    ]
    if not recent:
        return "neutral", 0.0
    dominant = max(set(recent), key=recent.count)
    pct = round((recent.count(dominant) / len(recent)) * 100, 1)
    return dominant, pct


def _stale_return(status="no_face"):
    dom, pct = get_dominant_emotion()
    return {
        "current_emotion":   emotion_state["current_emotion"],
        "emotion_confidence": emotion_state["emotion_confidence"],
        "dominant_emotion":  dom,
        "emotion_pct":       pct,
        "emotion_counts":    emotion_state["emotion_counts"],
        "status":            status
    }


def _weighted_smooth():
    if not _emotion_buffer:
        return "neutral", 0.0
    weighted = collections.defaultdict(float)
    for emo, conf in zip(_emotion_buffer, _confidence_buffer):
        weighted[emo] += conf
    best = max(weighted, key=weighted.get)
    avg_conf = weighted[best] / max(1, list(_emotion_buffer).count(best))
    return best, avg_conf


def get_current_reading(frame=None, face_crop=None):
    global emotion_state, _emotion_buffer, _confidence_buffer

    if frame is None and face_crop is None:
        return {
            "current_emotion": "neutral", "emotion_confidence": 0.0,
            "dominant_emotion": "neutral", "emotion_pct": 0.0,
            "emotion_counts": emotion_state["emotion_counts"],
            "status": "no_frame"
        }

    try:
        # 1. Get face crop
        if face_crop is None:
            face_crop = _detect_face_crop(frame)
        if face_crop is None:
            return _stale_return("no_face")

        # 2. Resize for enet_b2 (260×260)
        face_resized = cv2.resize(face_crop, (FACE_INPUT_SIZE, FACE_INPUT_SIZE))

        # 3. HSEmotion prediction (single model, no ensemble)
        dominant, confidence, all_probs = _hse_predict(face_resized)

        if dominant is None:
            return _stale_return("no_result")

        # 4. Reject very low confidence
        if confidence < MIN_CONFIDENCE:
            return _stale_return("low_confidence")

        # 5. Suppress noisy emotions — disgust/fear need higher confidence
        if dominant in ("disgust", "fear") and confidence < 0.35:
            sorted_emos = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_emos) > 1:
                dominant = sorted_emos[1][0]
                confidence = sorted_emos[1][1]

        # 6. Apply personal calibration bias correction
        dominant, confidence = _apply_calibration(dominant, confidence, all_probs)

        # 7. Update calibration stats (before smoothing, so we track raw predictions)
        _update_calibration(dominant, confidence)

        # 8. Rolling buffer smoothing
        _emotion_buffer.append(dominant)
        _confidence_buffer.append(confidence)
        smoothed, avg_conf = _weighted_smooth()

        # 9. Update session state
        emotion_state["current_emotion"] = smoothed
        emotion_state["emotion_confidence"] = round(avg_conf * 100, 1)  # store as 0-100
        emotion_state["emotion_counts"][smoothed] = (
            emotion_state["emotion_counts"].get(smoothed, 0) + 1
        )
        emotion_state["emotion_history"].append({
            "emotion": smoothed, "confidence": avg_conf,
            "timestamp": time.time()
        })
        if len(emotion_state["emotion_history"]) > 1000:
            emotion_state["emotion_history"] = emotion_state["emotion_history"][-1000:]

        dom_session, pct = get_dominant_emotion()
        emotion_state["dominant_emotion"] = dom_session
        emotion_state["emotion_pct"] = pct

        return {
            "current_emotion":   smoothed,
            "emotion_confidence": round(avg_conf * 100, 1),
            "all_emotions":      all_probs,
            "dominant_emotion":  dom_session,
            "emotion_pct":       pct,
            "emotion_counts":    emotion_state["emotion_counts"],
            "status":            "ok"
        }

    except Exception as e:
        print(f"[emotion] Error: {e}")
        return _stale_return("error")


def reset_session():
    global emotion_state
    _emotion_buffer.clear()
    _confidence_buffer.clear()
    emotion_state = {
        "current_emotion":    "neutral",
        "dominant_emotion":   "neutral",
        "emotion_confidence": 0.0,
        "emotion_pct":        0.0,
        "emotion_history":    [],
        "session_start":      time.time(),
        "emotion_counts": {
            "happy": 0, "neutral": 0, "sad": 0,
            "angry": 0, "fear": 0, "disgust": 0, "surprise": 0
        }
    }
