import numpy as np
from src.vision.blink import get_current_reading, reset_session

def test_no_frame():
    result = get_current_reading(frame=None)
    assert result["status"] == "no_frame"
    assert result["blink_rate"] == 0.0

def test_black_frame():
    reset_session()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = get_current_reading(frame=frame)
    assert "blink_rate" in result
    assert "ear" in result

def test_reset():
    reset_session()
    result = get_current_reading(frame=None)
    assert result["blink_count"] == 0
