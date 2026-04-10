"""
Aria Microcopy — Centralised User-Facing Text
===============================================
All user-facing strings in one place for easy review, consistency, and i18n readiness.
Tone: calm, precise, human, reassuring. Never robotic, overconfident, or childish.
"""

# ── Welcome & Onboarding ─────────────────────────────────────────────────────

WELCOME_TITLE = "Meet Aria"
WELCOME_SUBTITLE = (
    "Your personal AI wellness companion. Aria gently monitors your "
    "posture, eye health, and stress signals — so you can study and work at your best."
)
WELCOME_CTA = "Get Started"
WELCOME_LOGIN = "I already have a profile"
WELCOME_FOOTER = (
    "Built for NTU SC1304 · AI for Social Good\n"
    "Aria is not a medical device and does not diagnose conditions."
)

# ── Privacy Disclosure ────────────────────────────────────────────────────────

PRIVACY_TITLE = "Before We Begin"
PRIVACY_SUBTITLE = "Aria uses sensors to understand your wellness. You decide what's enabled."
PRIVACY_CAMERA_TITLE = "Camera"
PRIVACY_CAMERA_DESC = "Tracks posture, blink rate, and facial expression"
PRIVACY_CAMERA_NOT = "No photos or video are stored"
PRIVACY_MIC_TITLE = "Microphone"
PRIVACY_MIC_DESC = "Analyses speech rate and voice stress patterns"
PRIVACY_MIC_NOT = "No audio recordings are saved"
PRIVACY_KEYBOARD_TITLE = "Keyboard"
PRIVACY_KEYBOARD_DESC = "Monitors typing rhythm and speed for stress signals"
PRIVACY_KEYBOARD_NOT = "No keystroke content is logged"
PRIVACY_LOCAL = "All data is processed and stored locally on your device."
PRIVACY_CONTINUE = "Continue"
PRIVACY_CHANGE_LATER = "You can change these at any time in Settings."

# ── Registration ──────────────────────────────────────────────────────────────

REG_TITLE = "Set Up Your Profile"
REG_SUBTITLE = "Aria needs to recognise you so it tracks only your signals — not anyone else nearby."
REG_NAME_PROMPT = "What should Aria call you?"
REG_NAME_HELP = "This is how Aria will address you in conversations and reports."
REG_FACE_TITLE = "Face Enrollment"
REG_FACE_INSTRUCTION = "Position your face in the centre of the frame. Make sure you're in a well-lit area."
REG_FACE_TRUST = (
    "Your face data is stored locally as a compact mathematical embedding — not as an image. "
    "It's used only to identify you in the camera feed."
)
REG_FACE_FAIL = "No face detected. Try better lighting and face the camera directly."
REG_VOICE_TITLE = "Voice Enrollment"
REG_VOICE_INSTRUCTION = (
    "Read the sentence below clearly at your normal pace. "
    "This helps Aria verify who is speaking during monitoring."
)
REG_VOICE_SENTENCE = (
    "The quick brown fox jumps over the lazy dog near the quiet "
    "riverbank on a warm afternoon."
)
REG_VOICE_TRUST = (
    "Voice enrollment is optional. If you skip this, Aria will still work — "
    "it just won't verify your identity during voice analysis."
)
REG_VOICE_FAIL = "Voice enrollment issue. Try recording in a quieter environment and speak clearly for 5–10 seconds."
REG_VOICE_SKIP = "Skip for now"
REG_DONE_TITLE = "You're all set, {name}!"
REG_DONE_SUBTITLE = "Your profile is ready. Aria will only track your signals during monitoring."
REG_DONE_CTA = "Start Monitoring"

# ── Login ─────────────────────────────────────────────────────────────────────

LOGIN_TITLE = "Welcome Back"
LOGIN_SUBTITLE = "Select your profile to continue."
LOGIN_NEW_USER = "+ Register a new user"

# ── Home — Idle ───────────────────────────────────────────────────────────────

HOME_GREETING_MORNING = "Good morning, {name}"
HOME_GREETING_AFTERNOON = "Good afternoon, {name}"
HOME_GREETING_EVENING = "Good evening, {name}"
HOME_SUBTITLE_IDLE = "Ready when you are."
HOME_START_CTA = "Start Session"
HOME_LAST_SESSION = "Last Session"
HOME_NO_SESSIONS = "Start your first session to see your wellness insights here."
HOME_NO_SESSIONS_CTA = "Begin Monitoring"

# ── Readiness Check ───────────────────────────────────────────────────────────

READINESS_TITLE = "Quick Check"
READINESS_SUBTITLE = "Making sure everything is ready for accurate monitoring."
READINESS_CAMERA = "Camera"
READINESS_CAMERA_OK = "Face detected"
READINESS_CAMERA_FAIL = "No face detected — check lighting and position"
READINESS_MIC = "Microphone"
READINESS_MIC_OK = "Audio input detected"
READINESS_MIC_FAIL = "No audio input — check microphone permissions"
READINESS_LIGHTING = "Lighting"
READINESS_LIGHTING_OK = "Good lighting conditions"
READINESS_LIGHTING_WARN = "Low light — readings may be less accurate"
READINESS_SKIP = "Start anyway"
READINESS_READY = "All set — Start Session"

# ── Home — Live Session ───────────────────────────────────────────────────────

LIVE_MONITORING = "Monitoring"
LIVE_PAUSED = "Paused"
LIVE_SIGNALS_STRIP = "Monitoring: Camera {cam} · Mic {mic} · Keyboard {kb}"

# ── Signal Card Explanations ──────────────────────────────────────────────────

EXPLAIN_POSTURE = (
    "Aria estimates your posture by tracking key body points through the camera. "
    "A score of 75+ means you're sitting well. Below 50 means your posture has dipped — "
    "try sitting up straight or adjusting your chair."
)
EXPLAIN_BLINK = (
    "Aria counts your blinks by analysing your eye aspect ratio. "
    "A healthy rate is 15–20 blinks per minute. If your rate drops too low, "
    "your eyes may be straining. Try the 20-20-20 rule."
)
EXPLAIN_EMOTION = (
    "Aria estimates your emotional expression using facial analysis. "
    "This is a rough signal, not a mind-reader — it reflects what your face shows, "
    "not necessarily what you feel inside."
)
EXPLAIN_SEATED = (
    "Aria tracks how long you've been seated continuously. "
    "Prolonged sitting can affect your comfort and focus. "
    "A short break every 30–45 minutes is recommended."
)
EXPLAIN_TYPING = (
    "Aria monitors your typing rhythm and speed. "
    "Irregular patterns or sudden speed changes can indicate stress or fatigue. "
    "This is a behavioural signal, not a diagnosis."
)
EXPLAIN_VOICE = (
    "Aria analyses your speech rate and pitch variability when the mic is active. "
    "Rushed or irregular speech can indicate stress. "
    "This is an estimate and may not be accurate in noisy environments."
)
EXPLAIN_WELLNESS = (
    "Your wellness score is an AI-estimated composite of all active signals — "
    "posture, blink rate, emotion, seated time, typing, and voice. "
    "Higher is better. This is a suggestion, not a clinical measurement."
)
EXPLAIN_SHOULDER = (
    "Aria checks the vertical alignment of your left and right shoulders. "
    "Prolonged misalignment can cause neck and back strain."
)
EXPLAIN_TREND = (
    "Your average posture score across all sessions over the last 7 days."
)

# ── Confidence ────────────────────────────────────────────────────────────────

CONF_HIGH = "High confidence"
CONF_MEDIUM = "Medium confidence"
CONF_LOW = "Low confidence"
CONF_LOW_EXPLAIN = (
    "Aria isn't confident about this reading. "
    "Try adjusting your position or lighting for better accuracy."
)

# ── Alerts ────────────────────────────────────────────────────────────────────

ALERT_POSTURE_TITLE = "Posture Check"
ALERT_POSTURE_ACTION = "Try sitting up straight or standing for a quick stretch."
ALERT_BLINK_TITLE = "Eye Strain"
ALERT_BLINK_ACTION = "Try the 20-20-20 rule: look at something 20 feet away for 20 seconds."
ALERT_SEATED_TITLE = "Break Time"
ALERT_SEATED_ACTION = "A short walk or stretch break can help your focus and comfort."
ALERT_COMBINED_TITLE = "Wellness Check"
ALERT_COMBINED_ACTION = "Take a moment to check in with yourself. A brief pause can help."
ALERT_SHOULDER_TITLE = "Shoulder Misalignment"
ALERT_SHOULDER_ACTION = "Your shoulders appear uneven. Try to drop them and relax your upper body."

# ── Dashboard ─────────────────────────────────────────────────────────────────

ACTIVE_KEEP_UP = "Great posture! Keep it up."

# ── Session Summary & Coaching ────────────────────────────────────────────────

SUMMARY_TITLE = "Session Complete"
COACHING_TITLE = "Aria's Observations"
COACHING_TRUST = (
    "These suggestions were generated by AI based on your session data. "
    "They reflect patterns Aria observed — not medical assessments."
)
REFLECTION_TITLE = "How are you feeling?"
REFLECTION_OPTIONS = ["😊 Great", "🙂 Good", "😐 Okay", "😔 Not great", "😢 Difficult"]
REPORT_CTA = "View Report"
EXPORT_CTA = "Export PDF"
REPORT_READY = "Your wellness report is ready."
REPORT_TRUST = (
    "Reports include AI-generated wellness insights based on your session data. "
    "These are suggestions, not medical assessments."
)

# ── Chat ──────────────────────────────────────────────────────────────────────

CHAT_TITLE = "Chat with Aria"
CHAT_SUBTITLE = "Wellness AI Companion"
CHAT_TRUST = (
    "Aria uses your session data to give personalised suggestions. "
    "It's a wellness companion — not a medical professional."
)
CHAT_EMPTY_HI = "Hi {name}! I'm Aria."
CHAT_EMPTY_DESC = (
    "Ask me anything about your wellness session — I can see your "
    "posture, eye health, and stress signals in real time."
)
CHAT_PROMPTS = [
    "How's my posture?",
    "Am I stressed right now?",
    "What should I do differently?",
    "Explain my wellness score",
]
CHAT_INPUT_PLACEHOLDER = "Ask Aria about your wellness…"
CHAT_CLEAR = "Clear conversation"
CHAT_API_ERROR = (
    "Aria is having trouble connecting to the AI assistant. "
    "Your session data is safe — try again in a moment."
)

# ── History ───────────────────────────────────────────────────────────────────

HISTORY_TITLE = "Session History"
HISTORY_SUBTITLE = "Track your wellness journey over time."
HISTORY_EMPTY_TITLE = "No sessions yet"
HISTORY_EMPTY_DESC = (
    "Start your first monitoring session to begin building your wellness history."
)
HISTORY_EMPTY_CTA = "Go to Home"
HISTORY_TRUST = "Session data is stored locally on your device."

# ── Settings ──────────────────────────────────────────────────────────────────

SETTINGS_TITLE = "Settings"
SETTINGS_SUBTITLE = "Control what Aria monitors and manage your data."
SETTINGS_SIGNALS = "Signal Controls"
SETTINGS_SIGNALS_DESC = (
    "Toggle which signals Aria monitors. Changes take effect immediately."
)
SETTINGS_PROFILE = "Profile"
SETTINGS_PRIVACY = "Privacy & Data"
SETTINGS_AI_TRANSPARENCY = "AI Transparency"
SETTINGS_APPEARANCE = "Appearance"
SETTINGS_ABOUT = "About"

SETTINGS_LOGOUT = "Log out"
SETTINGS_NEW_USER = "New user"
SETTINGS_DELETE = "Delete profile"
SETTINGS_DELETE_CONFIRM = (
    "This will permanently delete your profile and all session history. "
    "This cannot be undone."
)
SETTINGS_CLEAR_HISTORY = "Clear all session history"

# ── AI Transparency Centre ────────────────────────────────────────────────────

AI_TRANSPARENCY_TITLE = "How Aria's AI Works"
AI_TRANSPARENCY_MODELS = (
    "Aria uses multiple AI models working together:\n"
    "• **MediaPipe** for body pose and face mesh detection\n"
    "• **DeepFace** for facial emotion analysis\n"
    "• **YOLOv8** for person detection\n"
    "• **Claude** (Anthropic) for conversational wellness coaching\n"
    "• **Custom fusion** algorithm combines all signals into a wellness score"
)
AI_TRANSPARENCY_DATA = (
    "What the AI sees:\n"
    "• Camera: body keypoints, eye aspect ratio, facial landmarks\n"
    "• Microphone: speech rate, pitch variability (not words)\n"
    "• Keyboard: typing speed, rhythm patterns (not content)\n\n"
    "What the AI does NOT see:\n"
    "• ❌ Raw images or video\n"
    "• ❌ Audio recordings or transcripts\n"
    "• ❌ What you type\n"
    "• ❌ Anything outside this app"
)
AI_TRANSPARENCY_LIMITS = (
    "**Limitations:**\n"
    "• Emotion detection reflects facial expression, not internal state\n"
    "• Posture scoring works best with a front-facing camera\n"
    "• Voice analysis is less accurate in noisy environments\n"
    "• The wellness score is an estimate, not a clinical measurement\n"
    "• AI coaching suggestions are not medical advice"
)

# ── Universal ─────────────────────────────────────────────────────────────────

DISCLAIMER = (
    "Aria is a wellness companion, not a medical device. "
    "It observes patterns and offers suggestions — it does not diagnose conditions."
)
LOCAL_PROCESSING = (
    "All data is processed and stored locally on your device. "
    "No video, audio, or biometric data is uploaded."
)
ABOUT_TITLE = "Aria"
ABOUT_SUBTITLE = "AI Wellness Companion · NTU SC1304"
ABOUT_DISCLAIMER = (
    "Aria is not a medical device and does not diagnose conditions. "
    "Always consult a healthcare professional for medical advice."
)
