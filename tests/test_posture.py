import numpy as np
from src.vision.posture import get_current_reading

def test_no_frame():
    result = get_current_reading(frame=None)
    assert result["posture_score"] == 0
    assert result["status"] == "no_frame"

def test_black_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = get_current_reading(frame=frame)
    assert "posture_score" in result
    assert 0 <= result["posture_score"] <= 100

def test_score_range():
    result = get_current_reading(frame=None)
    assert 0 <= result["posture_score"] <= 100
