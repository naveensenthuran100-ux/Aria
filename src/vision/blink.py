import cv2
import numpy as np
import time
import mediapipe as mp

# MediaPipe eye landmark indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# State
blink_state = {
    "blink_count": 0,
    "blink_rate": 0.0,
    "last_blink_time": time.time(),
    "session_start": time.time(),
    "was_closed": False
}

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

def get_current_reading(frame=None):
    """Required interface: returns dict with blink_rate."""
    global blink_state

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

        # Blink detection threshold
        EAR_THRESHOLD = 0.22
        is_closed = avg_ear < EAR_THRESHOLD

        if is_closed and not blink_state["was_closed"]:
            blink_state["blink_count"] += 1
            blink_state["last_blink_time"] = time.time()

        blink_state["was_closed"] = is_closed

        # Calculate blink rate per minute
        elapsed_mins = (time.time() - blink_state["session_start"]) / 60.0
        if elapsed_mins > 0:
            blink_state["blink_rate"] = round(
                blink_state["blink_count"] / elapsed_mins, 1
            )

        return {
            "blink_rate": blink_state["blink_rate"],
            "blink_count": blink_state["blink_count"],
            "ear": round(avg_ear, 3),
            "is_blinking": is_closed,
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
    global blink_state
    blink_state = {
        "blink_count": 0,
        "blink_rate": 0.0,
        "last_blink_time": time.time(),
        "session_start": time.time(),
        "ear_history": [],
        "was_closed": False
    }
