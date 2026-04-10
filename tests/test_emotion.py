import numpy as np
from src.vision.emotion import get_current_reading, reset_session

def test_no_frame():
    result = get_current_reading(frame=None)
    assert result["status"] == "no_frame"
    assert result["current_emotion"] == "neutral"

def test_black_frame():
    reset_session()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = get_current_reading(frame=frame)
    assert "current_emotion" in result
    assert "dominant_emotion" in result

def test_reset():
    reset_session()
    result = get_current_reading(frame=None)
    assert result["emotion_confidence"] == 0.0
