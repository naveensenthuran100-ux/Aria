# Aria: AI-Powered Wellness Companion 🧘‍♂️✨

**Aria** is a real-time AI wellness monitoring system designed to enhance your physical and mental health during work. By leveraging computer vision, audio analysis, and multimodal signal fusion, Aria detects patterns associated with fatigue, stress, and poor posture, offering interactive tools and detailed wellness reports.

---

## ✨ Key Features

*   **Posture Monitoring**: Real-time scoring and trend analysis to prevent slouching.
*   **Blink Detection**: Monitors eye fatigue risk using live facial landmarks.
*   **Emotion Tracking**: AI-driven facial sentiment analysis to gauge stress and mood.
*   **Stress Relief Tools**: Interactive grounding exercises and a guided box-breathing counter.
*   **Physical Resets**: Minimalist guided routines for shoulder and neck mobility.
*   **Smart Reports**: AI-generated PDF summaries of your wellness trends with visual charts.

---

## 🏗 System Architecture

Aria is built using a modern, decoupled architecture:

*   **Backend (Python/FastAPI)**: High-performance ML serving layer handling real-time Computer Vision (MediaPipe/OpenCV), Audio Processing (Librosa), and AI Summarization (Groq Llama 3.3).
*   **Frontend (Next.js/React)**: A premium, minimalist dashboard designed with Inter typography, Framer Motion animations, and real-time WebSocket connectivity.
*   **AI Engine**: Powered by Groq for lightning-fast wellness insights and personalized feedback.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Groq API Key** (Required for AI features)

### 2. Installation
Clone the repository and install all dependencies:

```bash
# Clone the repo
git clone https://github.com/your-username/Aria.git
cd Aria

# 1. Setup Backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# 2. Setup Frontend
cd frontend
npm install
```

### 3. Running the App
You will need two terminal windows:

**Terminal 1: Backend Server**
```bash
python -m uvicorn backend.server:app --port 8000
```

**Terminal 2: Frontend Dashboard**
```bash
cd frontend
npm run dev
```

Visit **http://localhost:3000** to start your session!

---

## 🔒 Configuration & Environment

Make sure your `.env` file at the root contains your API key:
```env
GROQ_API_KEY=your_key_here
```

Thresholds for alerts and posture scores can be tuned in `config.yaml`.

---

## 📂 Project Structure

*   `backend/`: FastAPI server logic and model endpoints.
*   `frontend/`: Next.js application, UI components, and styles.
*   `src/`: Core Python modules for Signal Fusion, Vision, and Audio analysis.
*   `public/`: Shared assets including guided physical routine images.

---
*Created with ❤️ for a healthier work-life balance.*
