import cv2, numpy as np, pickle, os, logging, yaml
from ultralytics import YOLO
logger = logging.getLogger(__name__)
YOLO_PATH="models/yolov8s-pose.pt"; ML_PATH="models/posture_classifier.pkl"
_yolo=None; _ml=None; _ml_loaded=False; _scores=[]; _history=[]
_smoothed_score = None   # EMA state
_baseline = None         # personal baseline (calibrated from first N good frames)
_baseline_samples = []

with open("config.yaml", "r") as _f:
    _config = yaml.safe_load(_f)
_DEVICE = _config.get("models", {}).get("device", "cpu")
_EMA_ALPHA = 0.4    # responsive to posture changes

def _yolo_model():
    global _yolo
    if _yolo is None: _yolo=YOLO(YOLO_PATH)
    return _yolo

def _ml_model():
    global _ml,_ml_loaded
    if _ml_loaded: return _ml
    _ml_loaded=True
    if os.path.exists(ML_PATH):
        try: _ml=pickle.load(open(ML_PATH,"rb")); logger.info(f"[posture] ML loaded acc={_ml.get('classifier_acc',0):.1%}")
        except Exception as e: logger.warning(f"[posture] ML failed:{e}")
    return _ml

def _features(kp_data, fw, fh):
    if kp_data is None or len(kp_data)==0: return None
    kp=kp_data[0]
    for i in [0,5,6]:
        if kp[i][2]<0.35: return None
    def pt(i): return np.array([kp[i][0]/fw, kp[i][1]/fh])
    def c(i): return float(kp[i][2])
    nose=pt(0); ls=pt(5); rs=pt(6); le=pt(7); re=pt(8); ms=(ls+rs)/2
    def av(t,b):
        v=t-b; return np.degrees(np.arccos(np.clip(np.dot(v,np.array([0,-1]))/(np.linalg.norm(v)+1e-9),-1,1)))
    ec=(c(7)+c(8))/2
    nv=nose-ms; nah=float(np.degrees(np.arctan2(abs(nv[0]),abs(nv[1])+1e-9)))
    f=np.array([[av(nose,ms),float(ls[1]-rs[1]),abs(float(ls[1]-rs[1])),
        np.linalg.norm(ls-rs),float(nose[0]-ms[0]),float(ms[1]-nose[1]),
        float(nose[1]),float(ms[1]),ec,
        float((le[1]+re[1])/2) if ec>0.1 else float(ms[1]),
        nah,c(0),c(5),c(6)]],dtype=np.float32)
    return f if np.all(np.isfinite(f)) else None

def _rule(kp_data, fw, fh):
    """Enhanced rule-based scoring with shoulder/back/torso awareness."""
    f = _features(kp_data, fw, fh)
    if f is None:
        return None, "unknown", {}
    kp = kp_data[0]

    def pt(i): return np.array([kp[i][0] / fw, kp[i][1] / fh])
    def c(i): return float(kp[i][2])

    hn_angle = float(f[0, 0])      # head-neck angle from vertical
    head_fwd = abs(float(f[0, 4])) # horizontal head offset
    shoulder_slope = float(f[0, 2]) # abs shoulder tilt
    shoulder_w = float(f[0, 3])     # shoulder width (normalised)
    head_height = float(f[0, 5])    # vertical head-shoulder distance

    score = 100.0
    details = {"head_neck_angle": round(hn_angle, 1), "model": "rule-v3"}

    # 1. Head-neck lean (primary signal — triggers earlier and harder)
    if hn_angle > 4:
        score -= min(45.0, (hn_angle - 4) * 3.0)
    details["hn_penalty"] = round(max(0, min(45.0, (hn_angle - 4) * 3.0)) if hn_angle > 4 else 0, 1)

    # 2. Head forward offset (stricter — catches forward lean)
    if head_fwd > 0.02:
        penalty = min(25.0, head_fwd * 150)
        score -= penalty
        details["head_fwd_penalty"] = round(penalty, 1)

    # 3. Shoulder slope / asymmetry
    details["shoulder_slope_raw"] = round(shoulder_slope, 3)
    if shoulder_slope > 0.03:
        penalty = min(15.0, (shoulder_slope - 0.03) * 180)
        score -= penalty
        details["slope_penalty"] = round(penalty, 1)

    # 4. Shoulder rounding via shoulder-to-ear width ratio
    shoulder_penalty = 0
    if c(3) > 0.2 and c(4) > 0.2:
        ear_w = float(np.linalg.norm(pt(3) - pt(4)))
        if ear_w > 0.01 and shoulder_w > 0.01:
            ratio = shoulder_w / ear_w
            details["shoulder_ear_ratio"] = round(ratio, 2)
            if ratio < 2.0:
                shoulder_penalty += min(25.0, (2.0 - ratio) * 70)

    # 5. Slouching — head drops closer to shoulders when hunching
    if head_height < 0.12:
        slouch_penalty = min(30.0, (0.12 - head_height) * 350)
        shoulder_penalty += slouch_penalty
        details["slouch_penalty"] = round(slouch_penalty, 1)

    # 6. Elbow tension
    if c(7) > 0.3 and c(8) > 0.3:
        ls_p, rs_p = pt(5), pt(6)
        le_p, re_p = pt(7), pt(8)
        elbow_above = max(0, float(ls_p[1] - le_p[1]), float(rs_p[1] - re_p[1]))
        if elbow_above > 0.02:
            ep = min(10.0, elbow_above * 150)
            shoulder_penalty += ep
            details["elbow_penalty"] = round(ep, 1)

    score -= min(35.0, shoulder_penalty)
    if shoulder_penalty > 0:
        details["shoulder_penalty"] = round(min(35.0, shoulder_penalty), 1)

    # ── 7. BACK / TORSO analysis (uses hip keypoints 11, 12) ──
    back_penalty = 0.0
    has_hips = c(11) > 0.25 and c(12) > 0.25
    has_one_hip = c(11) > 0.25 or c(12) > 0.25

    if has_hips:
        ms = (pt(5) + pt(6)) / 2    # shoulder midpoint
        mh = (pt(11) + pt(12)) / 2  # hip midpoint

        # 7a. Torso lean angle — angle of shoulder→hip line from vertical
        torso_vec = ms - mh  # points upward (y inverted in image)
        torso_angle = float(np.degrees(np.arctan2(
            abs(torso_vec[0]), abs(torso_vec[1]) + 1e-9
        )))
        details["torso_lean_angle"] = round(torso_angle, 1)
        if torso_angle > 5:
            tp = min(20.0, (torso_angle - 5) * 3.0)
            back_penalty += tp
            details["torso_lean_penalty"] = round(tp, 1)

        # 7b. Torso compression — short shoulder-to-hip distance = slouching
        torso_len = float(np.linalg.norm(ms - mh))
        details["torso_length"] = round(torso_len, 3)

        # Compare to baseline torso length if available
        global _baseline
        if _baseline is not None and "torso_len" in _baseline:
            bl_torso = _baseline["torso_len"]
            compression = (bl_torso - torso_len) / (bl_torso + 1e-9)
            if compression > 0.05:  # torso shortened by >5%
                cp = min(30.0, compression * 250)
                back_penalty += cp
                details["torso_compression"] = round(compression * 100, 1)
                details["torso_compress_penalty"] = round(cp, 1)

        # 7c. Forward lean — shoulder midpoint shifts forward (in image: x offset)
        #     relative to hip midpoint. When hunching, shoulders move forward.
        fwd_shift = abs(float(ms[0] - mh[0]))
        if fwd_shift > 0.03:
            fp = min(15.0, (fwd_shift - 0.03) * 200)
            back_penalty += fp
            details["back_fwd_shift"] = round(fwd_shift, 3)
            details["back_fwd_penalty"] = round(fp, 1)

        # 7d. Hip asymmetry — one hip higher than the other (uneven sitting)
        hip_slope = abs(float(pt(11)[1] - pt(12)[1]))
        if hip_slope > 0.03:
            hp = min(10.0, (hip_slope - 0.03) * 150)
            back_penalty += hp
            details["hip_slope_penalty"] = round(hp, 1)

    elif has_one_hip:
        # Partial hip visibility — can still detect side lean
        hip_idx = 11 if c(11) > 0.25 else 12
        shoulder_idx = 5 if hip_idx == 11 else 6
        hip_p = pt(hip_idx)
        shoulder_p = pt(shoulder_idx)
        side_vec = shoulder_p - hip_p
        side_angle = float(np.degrees(np.arctan2(
            abs(side_vec[0]), abs(side_vec[1]) + 1e-9
        )))
        if side_angle > 8:
            sp = min(15.0, (side_angle - 8) * 2.5)
            back_penalty += sp
            details["side_lean_penalty"] = round(sp, 1)

    score -= min(40.0, back_penalty)
    if back_penalty > 0:
        details["back_penalty"] = round(min(40.0, back_penalty), 1)

    # ── 8. Personal baseline comparison ──
    if _baseline is not None:
        bl_angle = _baseline.get("hn_angle", 0)
        deviation = hn_angle - bl_angle
        if deviation > 5:
            baseline_penalty = min(15.0, (deviation - 5) * 2.0)
            score -= baseline_penalty
            details["baseline_penalty"] = round(baseline_penalty, 1)

    score = max(0, min(100, score))
    cat = "good" if score >= 75 else "moderate" if score >= 50 else "poor"
    return int(score), cat, details


def _ml_score(kp_data, fw, fh, m):
    f = _features(kp_data, fw, fh)
    if f is None:
        return None, "unknown", {}
    xs = m["scaler"].transform(f)
    cat = m["label_encoder"].inverse_transform(m["classifier"].predict(xs))[0]
    raw = float(m["regressor"].predict(xs)[0])
    # Direct mapping — trust the regressor more after proper training
    score = int(np.clip(raw, 0, 100))
    details = {
        "head_neck_angle": round(float(f[0, 0]), 1),
        "model": f"ml({m.get('classifier_acc', 0):.0%})"
    }
    return score, cat, details


def _update_baseline(kp_data, fw, fh):
    """Calibrate personal baseline from first N good frames (includes torso length)."""
    global _baseline, _baseline_samples
    if _baseline is not None:
        return
    f = _features(kp_data, fw, fh)
    if f is None:
        return
    kp = kp_data[0]
    hn = float(f[0, 0])
    # Only use frames where person is likely sitting normally (low angle)
    if hn < 20:
        torso_len = None
        if kp[11][2] > 0.25 and kp[12][2] > 0.25:
            ms = (np.array([kp[5][0]/fw, kp[5][1]/fh]) + np.array([kp[6][0]/fw, kp[6][1]/fh])) / 2
            mh = (np.array([kp[11][0]/fw, kp[11][1]/fh]) + np.array([kp[12][0]/fw, kp[12][1]/fh])) / 2
            torso_len = float(np.linalg.norm(ms - mh))
        _baseline_samples.append({"hn": hn, "torso_len": torso_len})
    if len(_baseline_samples) >= 30:
        hn_vals = [s["hn"] for s in _baseline_samples]
        torso_vals = [s["torso_len"] for s in _baseline_samples if s["torso_len"] is not None]
        _baseline = {"hn_angle": float(np.median(hn_vals))}
        if torso_vals:
            _baseline["torso_len"] = float(np.median(torso_vals))
        logger.info(f"[posture] Baseline calibrated: {_baseline}")


def get_current_reading(frame=None):
    global _scores, _history, _smoothed_score
    if frame is None:
        return {"posture_score": 0, "category": "no_person", "details": {},
                "session_avg": None, "annotated_frame": None, "status": "no_frame"}
    yolo = _yolo_model(); ml = _ml_model(); h, w = frame.shape[:2]
    try:
        res = yolo(frame, verbose=False, device=_DEVICE)
        kps = res[0].keypoints
        if kps is None or kps.data.shape[0] == 0:
            return _none()
        all_kp = kps.data.cpu().numpy()

        # Select the person whose nose (kp 0) is closest to frame center
        if all_kp.shape[0] > 1:
            cx, cy = w / 2, h / 2
            best_idx, best_dist = 0, float('inf')
            for i in range(all_kp.shape[0]):
                nose = all_kp[i][0]
                if nose[2] > 0.3:  # nose confidence
                    dist = (nose[0] - cx) ** 2 + (nose[1] - cy) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
            kp = all_kp[best_idx:best_idx+1]
        else:
            kp = all_kp

        # Calibrate personal baseline
        _update_baseline(kp, w, h)

        # Always run rule-based scoring (catches slouch, lean, back issues)
        rule_score, rule_cat, rule_det = _rule(kp, w, h)

        if ml:
            ml_score_val, ml_cat, ml_det = _ml_score(kp, w, h, ml)
            if ml_score_val is not None and rule_score is not None:
                # Use the LOWER score — trust whichever says posture is worse
                score = min(ml_score_val, rule_score)
                det = rule_det  # always use rule details (has all penalty info)
                det["ml_score"] = ml_score_val
                cat = "good" if score >= 75 else "moderate" if score >= 50 else "poor"
            elif rule_score is not None:
                score, cat, det = rule_score, rule_cat, rule_det
            else:
                return _none()
        else:
            score, cat, det = rule_score, rule_cat, rule_det

        if score is None:
            return _none()

        # EMA smoothing
        if _smoothed_score is None:
            _smoothed_score = float(score)
        else:
            _smoothed_score = _EMA_ALPHA * score + (1.0 - _EMA_ALPHA) * _smoothed_score
        smoothed = int(round(_smoothed_score))
        smooth_cat = "good" if smoothed >= 75 else "moderate" if smoothed >= 50 else "poor"

        _scores.append(smoothed)
        _history.append({"score": smoothed, "category": smooth_cat})
        if len(_scores) > 500:
            _scores[:] = _scores[-500:]
            _history[:] = _history[-500:]

        ann = _annotate(frame.copy(), kp, smoothed, smooth_cat, det)
        return {"posture_score": smoothed, "category": smooth_cat, "details": det,
                "session_avg": int(np.mean(_scores[-30:])), "annotated_frame": ann,
                "keypoints": kp[0].tolist(), "status": "ok"}
    except Exception as e:
        logger.error(f"[posture] {e}")
        return _none()

def _none():
    return {"posture_score": 0, "category": "no_person", "details": {},
            "session_avg": None, "annotated_frame": None, "status": "no_person"}

def _annotate(frame, kp_data, score, cat, details=None):
    """Draw skeleton + score bar overlay with penalty indicators."""
    c = {"good": (0, 210, 90), "moderate": (0, 165, 255), "poor": (60, 60, 220)}.get(cat, (128, 128, 128))
    kp = kp_data[0]
    h, w = frame.shape[:2]

    # Skeleton connections (upper body + lower if visible)
    connections = [(5, 6), (0, 5), (0, 6), (5, 7), (6, 8), (7, 9), (8, 10),
                   (5, 11), (6, 12), (11, 12), (11, 13), (12, 14), (13, 15), (14, 16)]
    for a, b in connections:
        if a < len(kp) and b < len(kp) and kp[a][2] > 0.3 and kp[b][2] > 0.3:
            cv2.line(frame, (int(kp[a][0]), int(kp[a][1])),
                     (int(kp[b][0]), int(kp[b][1])), c, 2, cv2.LINE_AA)

    # Keypoint dots
    for i in range(min(17, len(kp))):
        if kp[i][2] > 0.3:
            cv2.circle(frame, (int(kp[i][0]), int(kp[i][1])), 5, c, -1, cv2.LINE_AA)
            cv2.circle(frame, (int(kp[i][0]), int(kp[i][1])), 5, (255, 255, 255), 1, cv2.LINE_AA)

    # Semi-transparent top bar
    bar_h = 54
    roi = frame[0:bar_h, 0:w]
    dark = np.zeros_like(roi); dark[:] = (13, 17, 23)
    frame[0:bar_h, 0:w] = cv2.addWeighted(dark, 0.82, roi, 0.18, 0)

    # Score progress bar
    tl, tr = 10, w - 130
    cv2.rectangle(frame, (tl, 36), (tr, 48), (40, 45, 55), -1)
    fill = max(0, int((score / 100.0) * (tr - tl)))
    cv2.rectangle(frame, (tl, 36), (tl + fill, 48), c, -1)

    # Score label
    cv2.putText(frame, f"Posture  {score}/100", (10, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.60, c, 2, cv2.LINE_AA)
    cat_str = cat.upper()
    (tw, _), _ = cv2.getTextSize(cat_str, cv2.FONT_HERSHEY_SIMPLEX, 0.60, 2)
    cv2.putText(frame, cat_str, (w - tw - 10, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.60, c, 2, cv2.LINE_AA)

    # Show penalty indicators
    warn_x = w - 120
    if details and details.get("back_penalty", 0) > 5:
        cv2.putText(frame, "BACK", (warn_x, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (60, 60, 220), 1, cv2.LINE_AA)
        warn_x -= 90
    if details and details.get("shoulder_penalty", 0) > 5:
        cv2.putText(frame, "SHOULDERS", (warn_x, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 165, 255), 1, cv2.LINE_AA)

    return frame

def reset_session():
    global _scores, _history, _smoothed_score, _baseline, _baseline_samples
    _scores = []; _history = []; _smoothed_score = None
    _baseline = None; _baseline_samples = []

def get_session_summary():
    if not _scores:
        return {"avg_score": None, "min_score": None, "total_frames": 0}
    return {"avg_score": int(np.mean(_scores)), "min_score": int(np.min(_scores)),
            "total_frames": len(_scores)}
