# Aria Wellness Monitor

Real-time AI wellness monitoring system built with Streamlit, WebRTC, computer vision, and audio analysis.

Aria uses live webcam, microphone, and activity-derived inputs to monitor posture, blink behavior, emotion-related facial cues, typing activity, and voice-based stress signals. These signals are fused into wellness-oriented feedback, alerts, charts, and reports through an interactive dashboard.

---

## Overview

Aria Wellness Monitor is a proof-of-concept system designed for lightweight, non-clinical wellness monitoring during laptop use. The project combines multimodal sensing and modular analysis pipelines to detect patterns associated with fatigue, stress, poor posture, and extended unhealthy work behavior.

The codebase is organized by function, with separate modules for:

- vision
- audio
- alerts
- AI assistant logic
- data/session storage
- signal fusion
- reporting
- interaction monitoring

---

## Core Features

- Real-time posture detection
- Blink monitoring using eye landmarks
- Emotion / facial-state inference
- Voice stress analysis
- Voice identity matching
- Typing activity monitoring
- Multi-signal wellness aggregation
- Rule-based alerting
- Session tracking and storage
- Charts and report generation
- Streamlit dashboard with WebRTC live input

---

## Tech Stack

### Application Layer
- Streamlit
- streamlit-webrtc

### Computer Vision
- OpenCV
- MediaPipe FaceMesh
- YOLOv8 Pose
- DeepFace

### Audio / Speech
- librosa
- SpeechRecognition
- Resemblyzer

### Data / Backend
- Python
- SQLAlchemy
- YAML

### Reporting / Visualization
- matplotlib
- reportlab

### Deployment
- Docker
- Hugging Face Spaces

---

## Repository Structure

```bash
aria_wellness_monitor/
├── .streamlit/
│   └── config.toml                  # Streamlit theme and UI settings
│
├── src/
│   ├── __init__.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── chatbot.py               # Chatbot / AI assistant logic
│   │   └── prompts.py               # Prompt templates and assistant instructions
│   │
│   ├── alerts/
│   │   ├── __init__.py
│   │   └── notifier.py              # Alert triggering and notification logic
│   │
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── stress.py                # Audio stress-related feature logic
│   │   ├── voice_id.py              # Speaker / voice identity processing
│   │   └── voice_stress.py          # Voice-based stress analysis
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── session_db.py            # Session storage and database access
│   │
│   ├── fusion/
│   │   ├── __init__.py
│   │   └── aggregator.py            # Combines signals from different modules
│   │
│   ├── io/
│   │   ├── __init__.py
│   │   └── typing_monitor.py        # Typing activity and keyboard behavior tracking
│   │
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── charts.py                # Chart generation
│   │   └── generator.py             # Report generation logic
│   │
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── blink.py                 # Blink detection
│   │   ├── emotion.py               # Emotion / facial-state analysis
│   │   ├── face_id.py               # Face identity handling
│   │   └── posture.py               # Posture detection and scoring
│   │
│   └── webrtc_bridge.py             # WebRTC stream integration layer
│
├── tests/
│   ├── test_blink.py                # Tests for blink analysis
│   ├── test_emotion.py              # Tests for emotion analysis
│   └── test_posture.py              # Tests for posture analysis
│
├── config.yaml                      # Runtime thresholds, model paths, app settings
├── main.py                          # Main Streamlit application entry point
├── train_posture_model.py           # Training script for posture model
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container setup for deployment
└── README.md                        # Project documentation
