import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def posture_timeline_chart(posture_history: list, output_path: str):
    """Line chart of posture scores over session time, colour-coded green/amber/red."""
    if not posture_history:
        return None

    _ensure_dir(output_path)

    t0 = posture_history[0]["timestamp"]
    mins = [(h["timestamp"] - t0) / 60.0 for h in posture_history]
    scores = [h["score"] for h in posture_history]

    fig, ax = plt.subplots(figsize=(10, 4))

    for i in range(len(scores) - 1):
        color = "#2ecc71" if scores[i] >= 75 else "#f39c12" if scores[i] >= 50 else "#e74c3c"
        ax.plot(mins[i:i+2], scores[i:i+2], color=color, linewidth=2)

    ax.axhline(y=75, color="#2ecc71", linestyle="--", alpha=0.5, linewidth=1, label="Good (75+)")
    ax.axhline(y=50, color="#f39c12", linestyle="--", alpha=0.5, linewidth=1, label="Moderate (50+)")
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Posture Score")
    ax.set_title("Posture Score Timeline")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close("all")
    return output_path


def stress_timeline_chart(stress_history: list, output_path: str):
    """Line chart of cognitive stress index over session time."""
    if not stress_history:
        return None

    _ensure_dir(output_path)

    t0 = stress_history[0]["timestamp"]
    mins = [(h["timestamp"] - t0) / 60.0 for h in stress_history]
    scores = [h["score"] for h in stress_history]

    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Shade background to indicate severity (0-1.0 scale)
    ax.axhspan(0.75, 1.0, color="#e74c3c", alpha=0.1)
    ax.axhspan(0.35, 0.75, color="#f39c12", alpha=0.1)
    ax.axhspan(0.0, 0.35, color="#2ecc71", alpha=0.1)

    ax.plot(mins, scores, color="#34495e", linewidth=2, label="Stress Index")
    ax.axhline(y=0.75, color="#e74c3c", linestyle="--", alpha=0.5, linewidth=1.5, label="High Stress")
    
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Stress Index (0-1)")
    ax.set_title("Cognitive Stress Timeline")
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close("all")
    return output_path



def emotion_pie_chart(emotion_counts: dict, output_path: str):
    """Pie chart of emotion distribution across the session."""
    filtered = {k: v for k, v in emotion_counts.items() if v > 0}
    if not filtered:
        return None

    _ensure_dir(output_path)

    colors = {
        "happy": "#2ecc71", "neutral": "#95a5a6", "sad": "#3498db",
        "angry": "#e74c3c", "fear": "#9b59b6", "disgust": "#e67e22", "surprise": "#f1c40f"
    }
    labels = list(filtered.keys())
    sizes = list(filtered.values())
    chart_colors = [colors.get(label, "#95a5a6") for label in labels]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, colors=chart_colors,
           autopct="%1.1f%%", startangle=90, textprops={"fontsize": 10})
    ax.set_title("Emotion Distribution", fontsize=14, fontweight="bold")

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close("all")
    return output_path


def blink_rate_chart(blink_rate: float, baseline: float, threshold: float, output_path: str):
    """Bar chart comparing current blink rate against baseline and fatigue threshold."""
    _ensure_dir(output_path)

    fig, ax = plt.subplots(figsize=(6, 4))

    bars = ax.bar(
        ["Your Rate", "Baseline", "Fatigue Threshold"],
        [blink_rate, baseline, threshold],
        color=["#e74c3c" if blink_rate < threshold else "#2ecc71", "#3498db", "#e74c3c"],
        width=0.5
    )

    for bar, val in zip(bars, [blink_rate, baseline, threshold]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1f}/min", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.axhline(y=threshold, color="#e74c3c", linestyle="--", alpha=0.6, linewidth=1.5)
    ax.set_ylabel("Blinks per minute")
    ax.set_title("Blink Rate Analysis")
    ax.set_ylim(0, max(25, baseline * 2, blink_rate * 1.3))
    ax.grid(True, axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close("all")
    return output_path
