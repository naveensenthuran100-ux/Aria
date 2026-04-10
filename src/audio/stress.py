import numpy as np
import time
import threading
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

audio_state = {
    "stress_index": 0.0,
    "last_update": 0.0,
    "is_recording": False,
    "status": "idle"
}

_recording_thread = None


def _extract_stress_features(audio_data, sample_rate=22050):
    """Extract stress index 0-1 from raw audio using MFCC, pitch, and energy."""
    try:
        import librosa

        mfcc = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=13)
        mfcc_std = float(np.mean(np.std(mfcc, axis=1)))

        f0, _, _ = librosa.pyin(audio_data, fmin=50, fmax=500, sr=sample_rate)
        f0_clean = f0[~np.isnan(f0)] if f0 is not None else np.array([])
        pitch_std = float(np.std(f0_clean)) if len(f0_clean) > 1 else 0.0

        rms = librosa.feature.rms(y=audio_data)[0]
        energy_mean = float(np.mean(rms))

        sc = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)[0]
        sc_mean = float(np.mean(sc))

        pitch_stress = min(1.0, pitch_std / 50.0)
        energy_stress = min(1.0, energy_mean / 0.05)
        spectral_stress = min(1.0, sc_mean / 3000.0)
        mfcc_stress = min(1.0, mfcc_std / 20.0)

        stress = (
            pitch_stress * 0.35 +
            energy_stress * 0.30 +
            spectral_stress * 0.20 +
            mfcc_stress * 0.15
        )
        return round(float(np.clip(stress, 0.0, 1.0)), 3)

    except Exception as e:
        print(f"[audio] Feature extraction error: {e}")
        return 0.0


def _record_chunk(duration=3.0, sample_rate=22050):
    """Record a short audio chunk from the microphone."""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=1024
        )
        frames = []
        num_chunks = int(sample_rate / 1024 * duration)
        for _ in range(num_chunks):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.float32))
        stream.stop_stream()
        stream.close()
        p.terminate()
        return np.concatenate(frames)
    except Exception as e:
        print(f"[audio] Recording error: {e}")
        return None


def _background_record():
    """Background thread that periodically samples audio and updates stress_index."""
    global audio_state
    while audio_state["is_recording"]:
        audio_data = _record_chunk(duration=3.0)
        if audio_data is not None and len(audio_data) > 0:
            stress = _extract_stress_features(audio_data)
            # Exponential moving average smoothing
            alpha = 0.3
            audio_state["stress_index"] = round(
                alpha * stress + (1 - alpha) * audio_state["stress_index"], 3
            )
            audio_state["last_update"] = time.time()
            audio_state["status"] = "ok"
        time.sleep(2.0)


def start_recording():
    """Start background audio capture thread."""
    global _recording_thread, audio_state
    if audio_state["is_recording"]:
        return
    audio_state["is_recording"] = True
    audio_state["status"] = "recording"
    _recording_thread = threading.Thread(target=_background_record, daemon=True)
    _recording_thread.start()


def stop_recording():
    """Stop background audio capture."""
    global audio_state
    audio_state["is_recording"] = False
    audio_state["status"] = "idle"


def get_current_reading() -> dict:
    """Required interface: returns dict with stress_index."""
    return {
        "stress_index": audio_state["stress_index"],
        "status": audio_state["status"],
        "last_update": audio_state["last_update"]
    }


def reset_session():
    """Reset audio stress state for new session."""
    global audio_state
    audio_state["stress_index"] = 0.0
    audio_state["last_update"] = 0.0
    audio_state["status"] = "idle"
