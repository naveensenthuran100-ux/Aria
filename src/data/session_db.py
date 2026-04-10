import sqlite3
import json
import os
import time

DB_PATH = "data/sessions.db"


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp     REAL,
            user_name     TEXT,
            duration_mins REAL,
            posture_score INTEGER,
            blink_rate    REAL,
            dominant_emotion TEXT,
            stress_index  REAL,
            alerts_count  INTEGER,
            ai_summary    TEXT,
            session_data  TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_session(summary: dict, ai_summary: str = "") -> int:
    """Persist a completed session. Returns the new row id."""
    init_db()
    conn = _get_conn()
    cursor = conn.execute("""
        INSERT INTO sessions (
            timestamp, user_name, duration_mins, posture_score,
            blink_rate, dominant_emotion, stress_index,
            alerts_count, ai_summary, session_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        time.time(),
        summary.get("user_name", "User"),
        summary.get("seated_mins", 0),
        summary.get("posture_score", 0),
        summary.get("blink_rate", 0.0),
        summary.get("dominant_emotion", "neutral"),
        summary.get("stress_index", 0.0),
        summary.get("alerts_triggered", 0),
        ai_summary,
        json.dumps(summary)
    ))
    conn.commit()
    row_id = cursor.lastrowid
    conn.close()
    return row_id


def get_recent_sessions(limit: int = 10) -> list:
    """Return the most recent sessions as a list of dicts."""
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
