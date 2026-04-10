import os
from groq import Groq
from dotenv import load_dotenv
from src.ai.prompts import SYSTEM_PROMPT_TEMPLATE, REPORT_SUMMARY_TEMPLATE
from src.fusion.aggregator import get_session_summary

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Conversation history for multi-turn chat
conversation_history = []

def build_system_prompt():
    """Build dynamic system prompt from live session data."""
    summary = get_session_summary()
    return SYSTEM_PROMPT_TEMPLATE.format(**summary)

def chat(user_message: str) -> str:
    """Send message to Groq with full session context."""
    global conversation_history

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    if not os.getenv("GROQ_API_KEY"):
        reply = "I'm your PosturePal Wellness AI. You don't have a Groq API key installed in your .env file, so I'm running in offline mock mode!"
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

    try:
        # Prepend dynamic system message
        messages = [{"role": "system", "content": build_system_prompt()}] + conversation_history
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=300
        )

        reply = response.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": reply
        })

        # Keep last 20 messages to manage token usage
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        return reply

    except Exception as e:
        print(f"[chatbot] Error: {e}")
        return "I'm having trouble connecting right now. Please check your API key."

def generate_report_summary() -> str:
    """Generate AI written session summary for PDF report using Groq."""
    if not os.getenv("GROQ_API_KEY"):
        return "Session report AI generation requires a valid Groq API key."
        
    summary = get_session_summary()
    prompt = REPORT_SUMMARY_TEMPLATE.format(**summary)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[chatbot] Report error: {e}")
        return "Unable to generate AI summary."

def reset_conversation():
    """Clear conversation history for new session."""
    global conversation_history
    conversation_history = []
