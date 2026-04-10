"""
Posture ML Training Pipeline
=============================
Uses MPII Human Pose dataset (25K images, 40K+ annotated people) to train
a posture quality model.  Ground-truth joint positions → posture score
labels.  YOLOv8 keypoints → features.  Trains classifier + regressor.

Also processes UBFC-RPPG seated-desk videos as supplementary data with
self-supervised labels derived from YOLO keypoint angles.
"""

import os, sys, glob, time, pickle, warnings
import numpy as np
import cv2
from collections import Counter
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
HACKATHON  = "/Users/rishi/Claude stuff/hackathon datasets"
MPII_MAT   = os.path.join(HACKATHON, "mpii_human_pose_v1_u12_2", "mpii_human_pose_v1_u12_1.mat")
MPII_IMGS  = [os.path.join(HACKATHON, "images"), os.path.join(HACKATHON, "images 2")]
UBFC_BASE  = HACKATHON  # DATASET_2 * folders
OUT_DIR    = "models"
YOLO_PATH  = "models/yolov8s-pose.pt"

# ── MPII joint IDs ────────────────────────────────────────────────────────────
# 0-r ankle, 1-r knee, 2-r hip, 3-l hip, 4-l knee, 5-l ankle,
# 6-pelvis, 7-thorax, 8-upper neck, 9-head top,
# 10-r wrist, 11-r elbow, 12-r shoulder, 13-l shoulder, 14-l elbow, 15-l wrist
UPPER_BODY_IDS = {7, 8, 9, 12, 13}        # minimum needed
FULL_SPINE_IDS = {6, 7, 8, 9, 12, 13}     # pelvis adds spine info

# ── Feature extraction (14 features, same as inference) ───────────────────────
def yolo_features(kp_data, fw, fh):
    """Extract 14 upper-body posture features from YOLO keypoints."""
    if kp_data is None or len(kp_data) == 0:
        return None
    kp = kp_data[0]
    for i in [0, 5, 6]:
        if kp[i][2] < 0.3:
            return None
    def pt(i): return np.array([kp[i][0] / fw, kp[i][1] / fh])
    def c(i):  return float(kp[i][2])

    nose = pt(0); ls = pt(5); rs = pt(6)
    le = pt(7); re = pt(8); ms = (ls + rs) / 2

    def angle_from_vertical(t, b):
        v = t - b
        return np.degrees(np.arccos(np.clip(
            np.dot(v, np.array([0, -1])) / (np.linalg.norm(v) + 1e-9), -1, 1)))

    ec = (c(7) + c(8)) / 2
    nv = nose - ms
    nah = float(np.degrees(np.arctan2(abs(nv[0]), abs(nv[1]) + 1e-9)))

    f = np.array([[
        angle_from_vertical(nose, ms),                        # 0  head-neck angle
        float(ls[1] - rs[1]),                                # 1  shoulder slope (signed)
        abs(float(ls[1] - rs[1])),                           # 2  shoulder slope (abs)
        float(np.linalg.norm(ls - rs)),                      # 3  shoulder width
        float(nose[0] - ms[0]),                              # 4  head forward offset
        float(ms[1] - nose[1]),                              # 5  head height above shoulders
        float(nose[1]),                                      # 6  nose y
        float(ms[1]),                                        # 7  shoulder y
        ec,                                                  # 8  elbow confidence
        float((le[1] + re[1]) / 2) if ec > 0.1 else float(ms[1]),  # 9  elbow height
        nah,                                                 # 10 neck horizontal angle
        c(0),                                                # 11 nose confidence
        c(5), c(6),                                          # 12,13 shoulder confidences
    ]], dtype=np.float32)

    return f if np.all(np.isfinite(f)) else None


# ── Posture score from MPII ground-truth joints ──────────────────────────────
def mpii_posture_score(joints):
    """
    Compute a 0-100 posture score from MPII annotated joint positions.

    joints: dict  {joint_id: (x, y)}

    Scores based on:
      1. Head-neck-thorax alignment (vertical)
      2. Shoulder symmetry (height difference)
      3. Spine straightness (head-neck-thorax-pelvis alignment)
      4. Head forward offset from spine axis
    """
    needed = {7, 8, 9, 12, 13}
    if not needed.issubset(joints.keys()):
        return None, None

    head_top   = np.array(joints[9])
    upper_neck = np.array(joints[8])
    thorax     = np.array(joints[7])
    r_shoulder = np.array(joints[12])
    l_shoulder = np.array(joints[13])
    mid_shoulder = (r_shoulder + l_shoulder) / 2

    score = 100.0

    # 1. Head-neck angle (deviation from vertical) — main signal
    neck_vec = head_top - thorax
    vertical = np.array([0, -1])
    cos_a = np.dot(neck_vec, vertical) / (np.linalg.norm(neck_vec) + 1e-9)
    head_neck_angle = np.degrees(np.arccos(np.clip(cos_a, -1, 1)))
    # Penalise: >10° starts losing points, >30° is poor
    if head_neck_angle > 10:
        score -= min(40, (head_neck_angle - 10) * 2.0)

    # 2. Shoulder symmetry (height difference as fraction of shoulder width)
    shoulder_width = np.linalg.norm(r_shoulder - l_shoulder) + 1e-9
    shoulder_tilt = abs(r_shoulder[1] - l_shoulder[1]) / shoulder_width
    if shoulder_tilt > 0.05:
        score -= min(15, (shoulder_tilt - 0.05) * 100)

    # 3. Head forward offset (horizontal deviation of head from mid-shoulder)
    head_forward = abs(head_top[0] - mid_shoulder[0]) / shoulder_width
    if head_forward > 0.15:
        score -= min(20, (head_forward - 0.15) * 80)

    # 4. Spine alignment (if pelvis available)
    if 6 in joints:
        pelvis = np.array(joints[6])
        spine_vec = thorax - pelvis
        spine_cos = np.dot(spine_vec, vertical) / (np.linalg.norm(spine_vec) + 1e-9)
        spine_angle = np.degrees(np.arccos(np.clip(spine_cos, -1, 1)))
        if spine_angle > 12:
            score -= min(25, (spine_angle - 12) * 1.5)

    # 5. Shoulder rounding (shoulders forward relative to spine line)
    # Approximated by comparing shoulder midpoint to neck-thorax midpoint
    neck_mid = (upper_neck + thorax) / 2
    shoulder_fwd = abs(mid_shoulder[0] - neck_mid[0]) / shoulder_width
    if shoulder_fwd > 0.1:
        score -= min(15, (shoulder_fwd - 0.1) * 80)

    score = max(0, min(100, score))
    cat = "good" if score >= 75 else "moderate" if score >= 50 else "poor"
    return int(score), cat


# ── YOLO-based self-supervised score (for UBFC videos) ────────────────────────
def yolo_self_score(kp_data, fw, fh):
    """
    Compute posture score directly from YOLO keypoints.
    Used for self-supervised labelling of UBFC desk videos.
    """
    if kp_data is None or len(kp_data) == 0:
        return None, None
    kp = kp_data[0]
    for i in [0, 5, 6]:
        if kp[i][2] < 0.35:
            return None, None

    def pt(i): return np.array([kp[i][0] / fw, kp[i][1] / fh])

    nose = pt(0); ls = pt(5); rs = pt(6)
    ms = (ls + rs) / 2

    # Head-neck angle
    v = nose - ms
    cos_a = np.dot(v, np.array([0, -1])) / (np.linalg.norm(v) + 1e-9)
    hn_angle = np.degrees(np.arccos(np.clip(cos_a, -1, 1)))

    # Head forward
    head_fwd = abs(float(nose[0] - ms[0]))

    # Shoulder slope
    shoulder_w = float(np.linalg.norm(ls - rs))
    shoulder_tilt = abs(float(ls[1] - rs[1])) / (shoulder_w + 1e-9)

    score = 100.0
    if hn_angle > 8:
        score -= min(45, (hn_angle - 8) * 2.5)
    if head_fwd > 0.04:
        score -= min(25, head_fwd * 100)
    if shoulder_tilt > 0.05:
        score -= min(15, (shoulder_tilt - 0.05) * 100)

    # Shoulder rounding via ear-shoulder ratio
    if kp[3][2] > 0.25 and kp[4][2] > 0.25:
        ear_w = float(np.linalg.norm(pt(3) - pt(4)))
        if ear_w > 0.01 and shoulder_w > 0.01:
            ratio = shoulder_w / ear_w
            if ratio < 1.8:
                score -= min(20, (1.8 - ratio) * 50)

    score = max(0, min(100, score))
    cat = "good" if score >= 75 else "moderate" if score >= 50 else "poor"
    return int(score), cat


# ── Parse MPII annotations ───────────────────────────────────────────────────
def parse_mpii():
    """Parse MPII .mat annotations → list of (image_path, joints_dict, is_train)."""
    import scipy.io
    print("Loading MPII annotations...")
    mat = scipy.io.loadmat(MPII_MAT)
    r = mat["RELEASE"][0, 0]
    annolist = r["annolist"][0]
    img_train = r["img_train"][0]
    total = len(annolist)

    # Build image path lookup
    img_lookup = {}
    for d in MPII_IMGS:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.lower().endswith((".jpg", ".png", ".jpeg")):
                    img_lookup[f] = os.path.join(d, f)

    samples = []
    for i in range(total):
        try:
            entry = annolist[i]
            is_train = int(img_train[i])
            img_name = str(entry["image"]["name"][0, 0][0])
            img_path = img_lookup.get(img_name)
            if img_path is None:
                continue

            annorect = entry["annorect"]
            if annorect.size == 0:
                continue

            for j in range(annorect[0].shape[0]):
                rect = annorect[0, j]
                if "annopoints" not in rect.dtype.names or rect["annopoints"].size == 0:
                    continue

                points = rect["annopoints"][0, 0]["point"][0]
                joints = {}
                for p in points:
                    try:
                        pid = int(p["id"][0, 0])
                        px = float(p["x"][0, 0])
                        py = float(p["y"][0, 0])
                        joints[pid] = (px, py)
                    except:
                        pass

                if UPPER_BODY_IDS.issubset(joints.keys()):
                    samples.append((img_path, joints, is_train))
        except:
            pass

    print(f"  Parsed {len(samples)} annotated people from {total} images")
    return samples


# ── Find UBFC videos ─────────────────────────────────────────────────────────
def find_ubfc_videos():
    """Find all UBFC-RPPG subject videos."""
    vids = []
    for folder in sorted(glob.glob(os.path.join(UBFC_BASE, "DATASET_2*"))):
        if not os.path.isdir(folder) or folder.endswith(".zip"):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f == "vid.avi":
                    vids.append(os.path.join(root, f))
    return vids


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  Posture ML Training Pipeline v2")
    print("  MPII + UBFC datasets → Classifier + Regressor")
    print("=" * 65)

    from ultralytics import YOLO
    yolo = YOLO(YOLO_PATH)
    print(f"[ok] YOLOv8 loaded from {YOLO_PATH}")

    all_features = []
    all_scores   = []
    all_labels   = []

    # ── Phase 1: MPII dataset ────────────────────────────────────────────────
    print("\n─── Phase 1: MPII Human Pose (ground-truth joints) ───")
    mpii_samples = parse_mpii()

    t0 = time.time()
    mpii_ok = 0
    mpii_skip = 0
    batch_size = 500
    n_batches = (len(mpii_samples) + batch_size - 1) // batch_size

    for batch_i in range(n_batches):
        batch = mpii_samples[batch_i * batch_size : (batch_i + 1) * batch_size]
        for img_path, joints, is_train in batch:
            # 1. Compute ground-truth posture score from annotated joints
            gt_score, gt_cat = mpii_posture_score(joints)
            if gt_score is None:
                mpii_skip += 1
                continue

            # 2. Run YOLO on image to get predicted keypoints → features
            try:
                img = cv2.imread(img_path)
                if img is None:
                    mpii_skip += 1
                    continue

                res = yolo(img, verbose=False, device="mps")
                kps = res[0].keypoints
                if kps is None or kps.data.shape[0] == 0:
                    mpii_skip += 1
                    continue

                kp_np = kps.data.cpu().numpy()

                # If multiple people detected, find the one closest to annotated position
                if kp_np.shape[0] > 1:
                    gt_center = np.mean(list(joints.values()), axis=0)
                    best_idx = 0
                    best_dist = float("inf")
                    for ki in range(kp_np.shape[0]):
                        det_center = np.mean(kp_np[ki, :, :2], axis=0)
                        d = np.linalg.norm(det_center - gt_center)
                        if d < best_dist:
                            best_dist = d
                            best_idx = ki
                    kp_np = kp_np[best_idx:best_idx+1]

                feat = yolo_features(kp_np, img.shape[1], img.shape[0])
                if feat is not None:
                    all_features.append(feat)
                    all_scores.append(gt_score)
                    all_labels.append(gt_cat)
                    mpii_ok += 1
                else:
                    mpii_skip += 1
            except Exception as e:
                mpii_skip += 1

        elapsed = time.time() - t0
        done = (batch_i + 1) * batch_size
        rate = done / (elapsed + 1e-9)
        eta = (len(mpii_samples) - done) / (rate + 1e-9)
        print(f"  [{done:>6}/{len(mpii_samples)}] ok={mpii_ok} skip={mpii_skip} "
              f"| {elapsed:.0f}s | ~{eta:.0f}s left")

    print(f"  MPII total: {mpii_ok} samples extracted")

    # ── Phase 2: UBFC-RPPG videos (self-supervised) ──────────────────────────
    print("\n─── Phase 2: UBFC-RPPG seated desk videos ───")
    ubfc_vids = find_ubfc_videos()
    print(f"  Found {len(ubfc_vids)} videos")

    ubfc_ok = 0
    UBFC_SAMPLE_RATE = 15  # every 15th frame

    for vi, vid_path in enumerate(ubfc_vids):
        cap = cv2.VideoCapture(vid_path)
        fi = 0
        vid_ok = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if fi % UBFC_SAMPLE_RATE == 0:
                try:
                    res = yolo(frame, verbose=False, device="mps")
                    kps = res[0].keypoints
                    if kps is not None and kps.data.shape[0] > 0:
                        kp_np = kps.data.cpu().numpy()
                        feat = yolo_features(kp_np, frame.shape[1], frame.shape[0])
                        sc, cat = yolo_self_score(kp_np, frame.shape[1], frame.shape[0])
                        if feat is not None and sc is not None:
                            all_features.append(feat)
                            all_scores.append(sc)
                            all_labels.append(cat)
                            vid_ok += 1
                except:
                    pass
            fi += 1

        cap.release()
        ubfc_ok += vid_ok
        elapsed = time.time() - t0
        print(f"  [{vi+1:>2}/{len(ubfc_vids)}] {os.path.basename(os.path.dirname(vid_path))}: "
              f"{vid_ok} frames | total {ubfc_ok}")

    print(f"  UBFC total: {ubfc_ok} samples")

    # ── Phase 3: Train models ────────────────────────────────────────────────
    total = len(all_features)
    print(f"\n─── Phase 3: Training ({total} samples) ───")
    if total < 100:
        print("Too few samples!"); sys.exit(1)

    X  = np.array(all_features).reshape(total, -1)
    ys = np.array(all_scores, dtype=np.float32)
    yl = np.array(all_labels)
    print(f"  Class distribution: {dict(Counter(yl))}")
    print(f"  Score range: {ys.min():.0f} – {ys.max():.0f}, mean={ys.mean():.1f}")

    from sklearn.ensemble import (
        RandomForestClassifier, GradientBoostingRegressor,
        GradientBoostingClassifier
    )
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, mean_absolute_error

    le = LabelEncoder()
    ye = le.fit_transform(yl)
    sc = StandardScaler()
    Xs = sc.fit_transform(X)

    Xtr, Xte, yctr, ycte, yrtr, yrte = train_test_split(
        Xs, ye, ys, test_size=0.2, random_state=42, stratify=ye
    )

    # Classifier: GBT for better accuracy
    print("\n  Training GBT classifier...")
    clf = GradientBoostingClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.08,
        subsample=0.8, random_state=42
    )
    clf.fit(Xtr, yctr)
    acc = clf.score(Xte, ycte)
    print(f"  [ok] Classifier accuracy: {acc:.1%}")
    print(classification_report(ycte, clf.predict(Xte), target_names=le.classes_))

    # Regressor: GBT for score prediction
    print("  Training GBT regressor...")
    reg = GradientBoostingRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, random_state=42
    )
    reg.fit(Xtr, yrtr)
    mae = mean_absolute_error(yrte, reg.predict(Xte))
    print(f"  [ok] Regressor MAE: {mae:.1f} pts")

    # Cross-validation
    cv = cross_val_score(clf, Xs, ye, cv=5, scoring="accuracy")
    print(f"  [ok] 5-fold CV: {cv.mean():.1%} ± {cv.std():.1%}")

    # Feature importance
    feat_names = [
        "head_neck_angle", "shoulder_slope", "shoulder_slope_abs",
        "shoulder_width", "head_forward", "head_height",
        "nose_y", "shoulder_y", "elbow_conf", "elbow_height",
        "neck_angle_h", "nose_conf", "lshoulder_conf", "rshoulder_conf"
    ]
    importances = clf.feature_importances_
    top_idx = np.argsort(importances)[::-1]
    print("\n  Feature importance (top 8):")
    for i in top_idx[:8]:
        print(f"    {feat_names[i]:>22s}  {importances[i]:.3f}")

    # ── Save model ───────────────────────────────────────────────────────────
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "posture_classifier.pkl")
    model_data = {
        "classifier":       clf,
        "regressor":        reg,
        "scaler":           sc,
        "label_encoder":    le,
        "training_samples": total,
        "mpii_samples":     mpii_ok,
        "ubfc_samples":     ubfc_ok,
        "classifier_acc":   float(acc),
        "regressor_mae":    float(mae),
        "cv_accuracy":      float(cv.mean()),
        "feature_names":    feat_names,
    }
    with open(path, "wb") as f:
        pickle.dump(model_data, f)

    print(f"\n{'=' * 65}")
    print(f"  Model saved: {path}")
    print(f"  Samples: {total} (MPII={mpii_ok}, UBFC={ubfc_ok})")
    print(f"  Accuracy: {acc:.1%} | MAE: {mae:.1f} | CV: {cv.mean():.1%}")
    print(f"{'=' * 65}")


if __name__ == "__main__":
    main()
