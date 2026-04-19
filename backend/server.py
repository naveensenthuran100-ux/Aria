"""
Aria API Backend
----------------
FastAPI server wrapping existing Aria ML models and DB.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import base64
import cv2
import numpy as np
import os

# Import existing Aria logic
from src.fusion.aggregator import (
    session_state,
    update_posture,
    update_blink,
    update_emotion,
    get_session_summary,
    check_alerts,
)
from src.vision.posture import get_current_reading as capture_posture
from src.vision.blink import get_current_reading as capture_blink
from src.vision.emotion import get_current_reading as capture_emotion
from src.ai.chatbot import chat, reset_conversation, generate_report_summary
from src.data.session_db import save_session, get_recent_sessions

app = FastAPI(title="PosturePal Wellness Backend")

# Relax CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import FileResponse
from src.reports.generator import generate_pdf_report

@app.get("/api/report")
def get_ai_report():
    try:
        # Generate the LLM summary
        summary_text = generate_report_summary()
        
        # Generate the physical PDF file
        pdf_path = generate_pdf_report(
            session_summary=session_state,
            ai_summary=summary_text,
            posture_history=session_state.get("posture_history", []),
            emotion_counts=session_state.get("emotion_counts", {})
        )
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF generation failed to produce a file.")

        return FileResponse(
            pdf_path, 
            media_type='application/pdf', 
            filename="posture_wellness_report.pdf"
        )
    except Exception as e:
        print(f"Report Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
def read_sessions(limit: int = 10):
    sessions = get_recent_sessions(limit)
    
    # Ensure live dashboard connectivity by providing current state
    current = get_session_summary()
    current["timestamp"] = session_state.get("session_start", time.time())
    current["is_live"] = session_state.get("is_running", False)
    
    # If no live session is active, provide some mock live data for the breakdown demo
    if not current["is_live"] and not sessions:
        current["posture_score"] = 85
        current["posture_details"] = {"hn_penalty": 8.5, "slouch_penalty": 6.5}
        current["is_live"] = True
        
    return [current] + sessions


class SessionPayload(BaseModel):
    user_name: str
    seated_mins: int
    posture_score: float
    blink_rate: float
    dominant_emotion: str
    stress_index: float
    alerts_triggered: int


@app.post("/api/sessions")
def create_session(payload: SessionPayload):
    row_id = save_session(payload.dict())
    return {"id": row_id}


class ChatMessage(BaseModel):
    text: str


@app.post("/api/chat")
def process_chat(msg: ChatMessage):
    reply = chat(msg.text)
    return {"reply": reply}


@app.post("/api/session/start")
def start_session():
    session_state["is_running"] = True
    session_state["session_start"] = time.time()
    reset_conversation()
    return {"status": "started"}


@app.post("/api/session/stop")
def stop_session():
    if not session_state["is_running"]:
        return {"status": "not_running"}
    session_state["is_running"] = False
    
    summary = get_session_summary()
    save_session(summary)
    
    return {"status": "stopped", "summary": summary}


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Internal timer simulation
    last_posture = 0.0
    last_blink = 0.0
    last_emotion = 0.0

    try:
        while True:
            data = await websocket.receive_text()
            # expecting base64 jpeg data from frontend
            # format "data:image/jpeg;base64,xxxx..."
            if not data.startswith("data:image"):
                continue

            # Parse frame
            b64_str = data.split(",")[1]
            img_data = base64.b64decode(b64_str)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            now = time.time()
            metrics = {}

            # Execute vision tasks on interval
            if now - last_posture > 1.0:
                posture_res = capture_posture(frame)
                update_posture(posture_res)
                metrics["posture"] = posture_res.get("posture_score", 0)
                metrics["posture_cat"] = posture_res.get("category", "unknown")
                metrics["posture_details"] = posture_res.get("details", {})
                metrics["keypoints"] = posture_res.get("keypoints", [])
                last_posture = now

            if now - last_blink > 0.5:
                blink_res = capture_blink(frame)
                update_blink(blink_res)
                metrics["blink_rate"] = blink_res.get("blink_rate", 0.0)
                last_blink = now

            if now - last_emotion > 1.5:
                # Need face crop logic or just pass whole frame
                emotion_res = capture_emotion(frame)
                update_emotion(emotion_res)
                metrics["emotion"] = emotion_res.get("current_emotion", "neutral")
                last_emotion = now

            # Check alerts
            alerts = check_alerts()
            if alerts:
                metrics["alerts"] = alerts
                try:
                    from src.alerts.notifier import process_alerts
                    process_alerts(alerts, use_streamlit=False)
                except Exception as e:
                    print(f"Failed to trigger local desktop notification: {e}")

            # Return updated master state
            await websocket.send_json({
                "status": "ok",
                "metrics": metrics,
                "aggregator": {
                    "posture_score": session_state["posture_score"],
                    "blink_rate": session_state["blink_rate"],
                    "dominant_emotion": session_state["dominant_emotion"],
                }
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WS Error: {e}")
