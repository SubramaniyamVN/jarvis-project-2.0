"""
jarvis_ai_brain.py — Phase 1: AI Brain
Uses Claude API (or OpenAI) for natural language understanding.
Any sentence, any command — no more fixed if/elif.
"""

import os
import json
import datetime
from jarvis_engine import speak

# ── API CONFIG ────────────────────────────────────────────────────────────────
# Set your API key in environment variables:
#   Windows: setx ANTHROPIC_API_KEY "your-key-here"
#   Or put it directly below (not recommended for sharing)

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY    = os.environ.get("OPENAI_API_KEY", "")

# Which AI to use: "claude" or "openai"
AI_PROVIDER = "claude"

# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are J.A.R.V.I.S (Just A Rather Very Intelligent System), an advanced AI
assistant running on the user's laptop. You are helpful, concise, and slightly
formal like the Iron Man movie Jarvis.

You can control the laptop, search the web, manage files, and answer questions.
When the user asks you to DO something on the laptop (open app, shutdown, volume,
etc.), respond with a JSON action block like this:

{"action": "open_app", "value": "chrome"}
{"action": "shutdown"}
{"action": "volume_up"}
{"action": "volume_down"}
{"action": "mute"}
{"action": "screenshot"}
{"action": "open_website", "value": "https://youtube.com"}
{"action": "speak_only", "text": "Your spoken reply here"}
{"action": "search_wikipedia", "query": "topic"}
{"action": "get_weather", "city": "city name"}
{"action": "tell_joke"}
{"action": "get_time"}
{"action": "get_date"}
{"action": "create_file", "filename": "name.txt"}
{"action": "lock_screen"}
{"action": "sleep"}
{"action": "restart"}

For conversational replies (no action needed), just reply normally in text.
Keep all replies under 3 sentences unless explaining something complex.
Always stay in character as Jarvis.
"""

# ── CONVERSATION HISTORY (memory within session) ──────────────────────────────
conversation_history = []

def add_to_history(role, content):
    conversation_history.append({"role": role, "content": content})
    # Keep only last 20 messages to save tokens
    if len(conversation_history) > 20:
        conversation_history.pop(0)

# ── CLAUDE API ────────────────────────────────────────────────────────────────
def ask_claude(user_input):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        add_to_history("user", user_input)
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=conversation_history
        )
        reply = response.content[0].text
        add_to_history("assistant", reply)
        return reply
    except ImportError:
        return '{"action": "speak_only", "text": "Anthropic library not installed. Run: pip install anthropic"}'
    except Exception as e:
        return f'{{"action": "speak_only", "text": "Claude API error: {str(e)}"}}'

# ── OPENAI API ────────────────────────────────────────────────────────────────
def ask_openai(user_input):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        add_to_history("user", user_input)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            max_tokens=512
        )
        reply = response.choices[0].message.content
        add_to_history("assistant", reply)
        return reply
    except ImportError:
        return '{"action": "speak_only", "text": "OpenAI library not installed. Run: pip install openai"}'
    except Exception as e:
        return f'{{"action": "speak_only", "text": "OpenAI API error: {str(e)}"}}'

# ── MAIN AI QUERY ─────────────────────────────────────────────────────────────
def ask_ai(user_input):
    """Send user input to AI and get response."""
    print(f"\n[AI] Thinking...")
    if AI_PROVIDER == "claude":
        return ask_claude(user_input)
    else:
        return ask_openai(user_input)

# ── PARSE AI RESPONSE ─────────────────────────────────────────────────────────
def parse_response(response_text):
    """
    Parse AI response — either a JSON action or plain text reply.
    Returns (action_dict or None, spoken_text or None)
    """
    response_text = response_text.strip()

    # Try to find a JSON block in the response
    import re
    json_match = re.search(r'\{[^}]+\}', response_text)
    if json_match:
        try:
            action = json.loads(json_match.group())
            # Get any text outside the JSON as additional context
            text_part = response_text.replace(json_match.group(), '').strip()
            return action, text_part
        except json.JSONDecodeError:
            pass

    # Plain text response
    return None, response_text

# ── EXECUTE AI ACTION ─────────────────────────────────────────────────────────
def execute_action(action, extra_text=""):
    """Execute the action returned by the AI."""
    from jarvis_apps   import open_app, open_website
    from jarvis_system import (volume_up, volume_down, mute_volume,
                               shutdown, restart, sleep_pc, lock_screen)
    from jarvis_media  import take_screenshot
    from jarvis_info   import (tell_joke, tell_time, tell_date,
                               search_wikipedia, get_weather)
    from jarvis_files  import create_file

    act = action.get("action", "")

    if act == "speak_only":
        text = action.get("text", extra_text)
        speak(text)

    elif act == "open_app":
        val = action.get("value", "")
        speak(f"Opening {val}.")
        open_app(val)

    elif act == "open_website":
        url = action.get("value", "")
        speak(f"Opening website.")
        import webbrowser
        webbrowser.open(url)

    elif act == "volume_up":
        volume_up()
    elif act == "volume_down":
        volume_down()
    elif act == "mute":
        mute_volume()
    elif act == "screenshot":
        take_screenshot()
    elif act == "shutdown":
        shutdown()
    elif act == "restart":
        restart()
    elif act == "sleep":
        sleep_pc()
    elif act == "lock_screen":
        lock_screen()
    elif act == "tell_joke":
        tell_joke()
    elif act == "get_time":
        tell_time()
    elif act == "get_date":
        tell_date()
    elif act == "search_wikipedia":
        q = action.get("query", "")
        search_wikipedia(q)
    elif act == "get_weather":
        city = action.get("city", "Chennai")
        get_weather(city)
    elif act == "create_file":
        fname = action.get("filename", "new_file.txt")
        create_file(fname)
    else:
        # Just speak the response
        if extra_text:
            speak(extra_text)

    # Speak any extra text after action
    if extra_text and act != "speak_only":
        speak(extra_text)

# ── MAIN BRAIN HANDLER ────────────────────────────────────────────────────────
def brain(user_input):
    """
    Main entry: take user input → ask AI → parse → execute.
    Returns True to keep running, False to exit.
    """
    if not user_input:
        return True

    # Check for exit without calling API
    if any(w in user_input.lower() for w in ["exit jarvis","quit jarvis","goodbye jarvis"]):
        speak("Goodbye sir. J.A.R.V.I.S shutting down.")
        return False

    response = ask_ai(user_input)
    print(f"[AI Response] {response}")

    action, text = parse_response(response)

    if action:
        execute_action(action, text)
    elif text:
        speak(text)

    return True


if __name__ == "__main__":
    from jarvis_engine import take_command, wish_me
    speak("Phase 1 AI Brain test. Ask me anything.")
    while True:
        query = take_command()
        if not brain(query):
            break