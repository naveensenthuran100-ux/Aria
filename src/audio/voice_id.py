"""
Speaker identity module -- enroll and verify the active user's voice.

Uses resemblyzer (d-vector) for speaker embeddings; saved as .pkl
alongside face profiles in data/profiles/.

API
---
enroll_speaker(name, audio, sample_rate) -> (bool, str)
verify_speaker(audio, sample_rate, target_name) -> {"status","name","confidence"}
get_enrolled_speakers() -> list[str]
delete_speaker(name)
"""

import numpy as np
import os
import pickle
import time
import logging

logger = logging.getLogger(__name__)

PROFILES_DIR = "data/profiles"
SIMILARITY_THRESHOLD = 0.75

_voice_profiles: dict = {}
_loaded = False
_encoder = None


def _ensure_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def _get_encoder():
    global _encoder
    if _encoder is None:
        from resemblyzer import VoiceEncoder
        _encoder = VoiceEncoder()
    return _encoder


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def _load_profiles():
    global _loaded
    if _loaded:
        return
    _loaded = True
    _ensure_dir()
    for fname in os.listdir(PROFILES_DIR):
        if fname.endswith("_voice.pkl"):
            name = fname[:-10]  # strip _voice.pkl
            try:
                with open(os.path.join(PROFILES_DIR, fname), "rb") as f:
                    _voice_profiles[name] = pickle.load(f)
                logger.info(f"[voice_id] Loaded voice profile: {name}")
            except Exception as e:
                logger.warning(f"[voice_id] Could not load {fname}: {e}")


def get_enrolled_speakers() -> list:
    _load_profiles()
    return list(_voice_profiles.keys())


def enroll_speaker(name: str, audio: np.ndarray, sample_rate: int = 16000) -> tuple:
    """
    Enroll a speaker from a numpy audio array (float32 or int16).
    Returns (success: bool, message: str).
    """
    from resemblyzer import preprocess_wav

    encoder = _get_encoder()

    # Normalize int16 to float32 if needed
    if audio.dtype == np.int16:
        audio = audio.astype(np.float32) / 32768.0
    elif audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    wav = preprocess_wav(audio, source_sr=sample_rate)

    if len(wav) < sample_rate * 2:
        return False, "Audio too short. Please speak for at least 5 seconds."

    embedding = encoder.embed_utterance(wav)

    profile = {
        "embedding": embedding,
        "num_samples": 1,
        "enrolled_at": time.time(),
    }

    _ensure_dir()
    path = os.path.join(PROFILES_DIR, f"{name}_voice.pkl")
    with open(path, "wb") as f:
        pickle.dump(profile, f)

    _voice_profiles[name] = profile
    logger.info(f"[voice_id] Enrolled speaker: {name}")
    return True, "Voice profile saved."


def verify_speaker(audio: np.ndarray, sample_rate: int, target_name: str) -> dict:
    """
    Verify if the audio matches the enrolled speaker.
    Returns dict with status, name, confidence.
    """
    _load_profiles()

    if target_name not in _voice_profiles:
        return {"status": "no_enrollment", "name": None, "confidence": 0.0}

    try:
        from resemblyzer import preprocess_wav

        encoder = _get_encoder()

        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        elif audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        wav = preprocess_wav(audio, source_sr=sample_rate)

        if len(wav) < sample_rate * 0.5:  # need at least 0.5s
            return {"status": "too_short", "name": None, "confidence": 0.0}

        embedding = encoder.embed_utterance(wav)
        enrolled = _voice_profiles[target_name]["embedding"]
        similarity = _cosine_sim(embedding, enrolled)

        if similarity >= SIMILARITY_THRESHOLD:
            return {"status": "ok", "name": target_name, "confidence": round(similarity, 3)}
        else:
            return {"status": "no_match", "name": None, "confidence": round(similarity, 3)}

    except Exception as e:
        logger.error(f"[voice_id] Verification error: {e}")
        return {"status": "error", "name": None, "confidence": 0.0}


def delete_speaker(name: str):
    _voice_profiles.pop(name, None)
    path = os.path.join(PROFILES_DIR, f"{name}_voice.pkl")
    if os.path.exists(path):
        os.remove(path)
    logger.info(f"[voice_id] Deleted voice profile: {name}")
