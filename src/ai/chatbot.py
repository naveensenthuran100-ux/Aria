import os
os.environ.pop("ANTHROPIC_BASE_URL", None)
os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

from anthropic import Anthropic
from dotenv import load_dotenv
from src.ai.prompts import SYSTEM_PROMPT_TEMPLATE, REPORT_SUMMARY_TEMPLATE
from src.fusion.aggregator import get_session_summary

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Conversation history for multi-turn chat
conversation_history = []

def build_system_prompt():
    """Build dynamic system prompt from live session data."""
    summary = get_session_summary()
    return SYSTEM_PROMPT_TEMPLATE.format(**summary)

def chat(user_message: str) -> str:
    """Send message to Claude with full session context."""
    global conversation_history

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=build_system_prompt(),
            messages=conversation_history
        )

        reply = response.content[0].text

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
    """Generate AI written session summary for PDF report."""
    summary = get_session_summary()
    prompt = REPORT_SUMMARY_TEMPLATE.format(**summary)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except Exception as e:
        print(f"[chatbot] Report error: {e}")
        return "Unable to generate AI summary."

def reset_conversation():
    """Clear conversation history for new session."""
    global conversation_history
    conversation_history = []
