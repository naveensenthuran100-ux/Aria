"""
Face identity module — register and identify the active user in real-time.

Uses DeepFace (Facenet) for embedding extraction; embeddings are saved as
.pkl files under data/profiles/ so they persist across sessions.

API
---
register_user(name, frames)  → (bool, str)
identify_user(frame, target) → {"status","name","bbox","confidence"}
get_registered_users()       → list[str]
delete_user(name)
"""

import cv2
import numpy as np
import os
import pickle
import logging

logger = logging.getLogger(__name__)

PROFILES_DIR = "data/profiles"
MODEL_NAME   = "Facenet"   # fast + accurate; cached after first call
DETECTOR     = "opencv"    # reliable, no extra downloads needed

# In-memory profile store: {name: {"embeddings": [np.array,...], "avg": np.array}}
_profiles: dict = {}
_loaded = False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _ensure_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def _load_profiles():
    global _loaded
    if _loaded:
        return
    _loaded = True
    _ensure_dir()
    for fname in os.listdir(PROFILES_DIR):
        # Only load face-profile .pkl files (skip emotion/voice calibration files)
        if not fname.endswith(".pkl"):
            continue
        if "_emotion.pkl" in fname or "_voice.pkl" in fname:
            continue
        name = fname[:-4]
        try:
            with open(os.path.join(PROFILES_DIR, fname), "rb") as f:
                data = pickle.load(f)
            if "embeddings" not in data:
                logger.debug(f"[face_id] Skipping {fname}: not a face profile")
                continue
            _profiles[name] = data
            logger.info(f"[face_id] Loaded profile: {name}")
        except Exception as e:
            logger.warning(f"[face_id] Could not load {fname}: {e}")


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def _extract_embedding(bgr_frame: np.ndarray) -> np.ndarray | None:
    """Return a Facenet embedding for the most prominent face, or None."""
    try:
        from deepface import DeepFace
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = DeepFace.represent(
            rgb,
            model_name=MODEL_NAME,
            detector_backend=DETECTOR,
            enforce_detection=True,
            align=True,
        )
        if results:
            return np.array(results[0]["embedding"], dtype=np.float32)
    except Exception as e:
        logger.debug(f"[face_id] Embedding extraction failed: {e}")
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def get_registered_users() -> list:
    _load_profiles()
    return list(_profiles.keys())


def register_user(name: str, frames: list) -> tuple:
    """
    Extract face embeddings from a list of BGR frames and save the profile.
    Returns (success: bool, message: str).
    """
    embeddings = []
    for frame in frames:
        emb = _extract_embedding(frame)
        if emb is not None:
            embeddings.append(emb)
        # Augment with horizontal flip for robustness
        emb_flip = _extract_embedding(cv2.flip(frame, 1))
        if emb_flip is not None:
            embeddings.append(emb_flip)

    if not embeddings:
        return False, (
            "No face detected. Move closer to the camera, "
            "improve lighting, and look directly into the lens."
        )

    profile = {
        "embeddings": embeddings,
        "avg": np.mean(embeddings, axis=0),
    }
    _ensure_dir()
    path = os.path.join(PROFILES_DIR, f"{name}.pkl")
    with open(path, "wb") as f:
        pickle.dump(profile, f)
    _profiles[name] = profile
    logger.info(f"[face_id] Registered '{name}' ({len(embeddings)} embeddings)")
    return True, f"Profile saved — {len(embeddings)} face samples captured."


def delete_user(name: str):
    _profiles.pop(name, None)
    path = os.path.join(PROFILES_DIR, f"{name}.pkl")
    if os.path.exists(path):
        os.remove(path)
    logger.info(f"[face_id] Deleted profile: {name}")


def identify_user(frame: np.ndarray, target_name: str | None = None) -> dict:
    """
    Detect all faces in *frame* and return the best match against registered
    profiles (or *target_name* specifically if provided).

    Returns
    -------
    dict with keys:
        status      : "ok" | "no_profile" | "no_face" | "no_match" | "error"
        name        : matched name or None
        bbox        : (top, right, bottom, left) in pixel coords, or None
        confidence  : float 0-1
    """
    _load_profiles()
    if not _profiles:
        return {"status": "no_profile", "name": None, "bbox": None, "confidence": 0.0}

    try:
        from deepface import DeepFace
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        try:
            results = DeepFace.represent(
                rgb,
                model_name=MODEL_NAME,
                detector_backend=DETECTOR,
                enforce_detection=False,
                align=True,
            )
        except Exception:
            return {"status": "no_face", "name": None, "bbox": None, "confidence": 0.0}

        if not results:
            return {"status": "no_face", "name": None, "bbox": None, "confidence": 0.0}

        search_names = (
            [target_name] if target_name and target_name in _profiles
            else list(_profiles.keys())
        )

        best_name, best_bbox, best_conf = None, None, 0.0
        for r in results:
            emb = np.array(r["embedding"], dtype=np.float32)
            fa  = r.get("facial_area", {})
            x, y, w, h = fa.get("x", 0), fa.get("y", 0), fa.get("w", 0), fa.get("h", 0)
            bbox = (y, x + w, y + h, x)   # top, right, bottom, left

            for name in search_names:
                # Compare against both individual embeddings and average
                sims = [_cosine_sim(emb, e) for e in _profiles[name]["embeddings"]]
                avg_sim = _cosine_sim(emb, _profiles[name]["avg"])
                conf = max(float(np.max(sims)), avg_sim)
                if conf > 0.50 and conf > best_conf:
                    best_conf = conf
                    best_name = name
                    best_bbox = bbox

        if best_name:
            return {"status": "ok", "name": best_name,
                    "bbox": best_bbox, "confidence": round(best_conf, 3)}

        return {"status": "no_match", "name": None, "bbox": None, "confidence": 0.0}

    except Exception as e:
        logger.error(f"[face_id] identify_user error: {e}")
        return {"status": "error", "name": None, "bbox": None, "confidence": 0.0}


def crop_user_face(frame: np.ndarray, bbox: tuple, pad_frac: float = 0.25) -> np.ndarray | None:
    """
    Crop the user's face from *frame* given a cached *bbox* (top,right,bottom,left).
    Returns a BGR crop or None.
    """
    if bbox is None:
        return None
    top, right, bottom, left = bbox
    h, w = frame.shape[:2]
    pad = int(pad_frac * max(right - left, bottom - top))
    y1 = max(0, top - pad);  y2 = min(h, bottom + pad)
    x1 = max(0, left - pad); x2 = min(w, right + pad)
    crop = frame[y1:y2, x1:x2]
    return crop if crop.size > 0 else None
