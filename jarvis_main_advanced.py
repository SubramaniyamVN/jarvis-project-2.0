"""
╔══════════════════════════════════════════════════════════════════════╗
║         J.A.R.V.I.S  —  Advanced AI Laptop Assistant               ║
║         All 14 Phases — Full Source Code                            ║
╠══════════════════════════════════════════════════════════════════════╣
║  SETUP:                                                              ║
║  1. pip install -r requirements_advanced.txt                         ║
║  2. Set API keys in environment (see below)                         ║
║  3. python jarvis_face.py register   (first time only)              ║
║  4. python jarvis_main_advanced.py                                  ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import threading

# ── API KEY SETUP (edit these or set as environment variables) ─────────────
os.environ.setdefault("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY_HERE")
os.environ.setdefault("OPENAI_API_KEY",    "YOUR_OPENAI_KEY_HERE")
os.environ.setdefault("ELEVENLABS_API_KEY","YOUR_ELEVENLABS_KEY_HERE")

# ── FEATURE FLAGS (enable/disable phases) ──────────────────────────────────
ENABLE_FACE_AUTH   = False   # Phase 3  — set True after: python jarvis_face.py register
ENABLE_HUD         = True    # Phase 4  — floating HUD overlay
ENABLE_WAKE_WORD   = False   # Phase 2  — needs pvporcupine key
ENABLE_MONITORING  = True    # Phase 12 — background PC monitoring
ENABLE_REMINDERS   = True    # Phase 7  — background reminder checker
ENABLE_ELEVENLABS  = False   # Phase 11 — needs ElevenLabs API key
USE_AI_BRAIN       = True    # Phase 1  — use Claude/GPT-4 for all commands
OFFLINE_MODE       = False   # Phase 14 — use Whisper + Ollama


# ── IMPORTS ────────────────────────────────────────────────────────────────
from jarvis_engine  import speak, take_command, wish_me
from jarvis_system  import handle_system
from jarvis_apps    import handle_apps
from jarvis_files   import handle_files
from jarvis_media   import handle_media
from jarvis_info    import handle_info
from jarvis_mouse   import handle_mouse
from jarvis_messages import handle_messages
from jarvis_advanced import (
    handle_smarthome, handle_memory, handle_code,
    handle_webauto,   handle_news,   handle_monitor,
    handle_imagegen,  handle_offline,
    monitor_alerts_loop, reminder_check_loop,
    memory_save, speak_elevenlabs, set_offline_mode
)

# Override speak if ElevenLabs enabled
if ENABLE_ELEVENLABS:
    import jarvis_advanced
    jarvis_advanced.speak = speak_elevenlabs

# ── HUD ────────────────────────────────────────────────────────────────────
hud = None
if ENABLE_HUD:
    try:
        from jarvis_hud import start_hud, hud_update
        hud = start_hud()
        print("[HUD] Overlay started.")
    except Exception as e:
        print(f"[HUD] Could not start: {e}")
        ENABLE_HUD = False

def hud(u=None, j=None, s=None, p=None):
    if ENABLE_HUD:
        try:
            from jarvis_hud import hud_update
            hud_update(user_text=u, jarvis_text=j, status=s, phase=p)
        except Exception:
            pass


# ── COMMAND ROUTER ─────────────────────────────────────────────────────────
def route_command(query):
    """Route query to correct module. Returns False to exit."""
    if not query or not query.strip():
        return True

    q = query.lower().strip()

    # Save to memory
    memory_save("user", q)

    # Update HUD
    hud(u=query, s="thinking")

    # ── Exit ──────────────────────────────────────────────────────────────
    if any(w in q for w in ["exit jarvis","quit jarvis","goodbye jarvis","shutdown jarvis"]):
        speak("Goodbye sir. All systems powering down. Have a great day.")
        return False

    # ── Help ──────────────────────────────────────────────────────────────
    if "help" in q or "what can you do" in q:
        from jarvis_info import help_command
        help_command()

    # ── Phase 6: Smart Home ───────────────────────────────────────────────
    elif any(w in q for w in ["turn on","turn off","switch on","switch off",
                               "bedroom light","living room","kitchen light",
                               "fan","ac ","air condition","door lock","smart home"]):
        hud(s="speaking", p=(6,"Smart Home"))
        handle_smarthome(q)

    # ── Phase 13: Image Generation ────────────────────────────────────────
    elif any(w in q for w in ["generate image","create image","make image",
                               "draw image","generate picture","ai image"]):
        hud(s="thinking", p=(13,"Image Generation"))
        handle_imagegen(q)

    # ── Phase 9: Web Automation ───────────────────────────────────────────
    elif any(w in q for w in ["automate","selenium","web automation",
                               "fill form","auto search"]):
        hud(s="speaking", p=(9,"Web Automation"))
        handle_webauto(q)

    # ── Phase 8: Code Assistant ───────────────────────────────────────────
    elif any(w in q for w in ["write code","write a script","write python",
                               "create script","run script","code for"]):
        hud(s="thinking", p=(8,"Code Assistant"))
        handle_code(q)

    # ── Phase 7: Memory ───────────────────────────────────────────────────
    elif any(w in q for w in ["remember that","what is my","what's my",
                               "search memory","set reminder","remind me"]):
        hud(s="speaking", p=(7,"Memory System"))
        handle_memory(q)

    # ── Phase 5: Email & WhatsApp ─────────────────────────────────────────
    elif any(w in q for w in ["send email","compose email","read email",
                               "check email","check inbox","whatsapp",
                               "send message","send whatsapp"]):
        hud(s="speaking", p=(5,"Email & WhatsApp"))
        handle_messages(q)

    # ── Phase 10: News & Weather ──────────────────────────────────────────
    elif any(w in q for w in ["news","headlines","top stories",
                               "weather","temperature"]):
        hud(s="speaking", p=(10,"News & Alerts"))
        handle_news(q)

    # ── Phase 12: PC Monitoring ───────────────────────────────────────────
    elif any(w in q for w in ["system info","system status","cpu","ram",
                               "memory usage","disk","battery","top process",
                               "kill process","gpu","temperature"]):
        hud(s="speaking", p=(12,"PC Monitoring"))
        handle_monitor(q)

    # ── Phase 14: Offline ─────────────────────────────────────────────────
    elif any(w in q for w in ["offline mode","online mode","go offline",
                               "go online","use ollama","whisper"]):
        hud(s="speaking", p=(14,"Offline Mode"))
        handle_offline(q)

    # ── Phase 4: System Controls ──────────────────────────────────────────
    elif any(w in q for w in ["shutdown","restart","sleep","hibernate","lock",
                               "log off","volume","mute","brightness","wifi",
                               "bluetooth","task manager","clipboard",
                               "empty recycle","recycle bin"]):
        hud(s="speaking", p=(4,"System Controls"))
        handle_system(q)

    # ── Phase 4: Apps & Websites ──────────────────────────────────────────
    elif any(w in q for w in ["open","close","launch","start","google","youtube",
                               "gmail","facebook","whatsapp web","instagram",
                               "chrome","firefox","spotify","vlc","notepad",
                               "calculator","vs code","file explorer"]):
        hud(s="speaking", p=(4,"App Control"))
        handle_apps(q)

    # ── File operations ───────────────────────────────────────────────────
    elif any(w in q for w in ["create file","delete file","rename file",
                               "create folder","delete folder","list files",
                               "find file","open file","move file","copy file"]):
        hud(s="speaking", p=(7,"File System"))
        handle_files(q)

    # ── Media controls ────────────────────────────────────────────────────
    elif any(w in q for w in ["play","pause","next track","previous track",
                               "stop music","screenshot","screen record",
                               "scroll","zoom"]):
        hud(s="speaking", p=(4,"Media Control"))
        handle_media(q)

    # ── Mouse / keyboard ──────────────────────────────────────────────────
    elif any(w in q for w in ["click","right click","double click","move mouse",
                               "type ","press key","hotkey","select all",
                               "minimize","maximize","close window",
                               "switch window","snap left","snap right"]):
        hud(s="speaking", p=(4,"Mouse & Keyboard"))
        handle_mouse(q)

    # ── Info & Utilities ──────────────────────────────────────────────────
    elif any(w in q for w in ["time","date","day","joke","flip coin","roll dice",
                               "calculate","what is","who is","wikipedia",
                               "hello","hi","hey","how are you","your name"]):
        hud(s="speaking", p=(1,"AI Brain"))
        handle_info(q)

    # ── Phase 1: AI Brain (catch-all) ─────────────────────────────────────
    elif USE_AI_BRAIN:
        hud(s="thinking", p=(1,"AI Brain"))
        try:
            from jarvis_ai_brain import brain
            brain(q)
        except ImportError:
            speak(f"I heard: {query}. Please install the AI brain module.")

    else:
        speak(f"I'm not sure how to handle that, sir. Say 'help' for a list of commands.")

    # Save Jarvis response to memory
    memory_save("assistant", "response_logged")
    hud(s="standby")
    return True


# ── STARTUP SEQUENCE ───────────────────────────────────────────────────────
def startup():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              J.A.R.V.I.S  ADVANCED  v4.1                           ║
║              All 14 Phases Active                                   ║
╚══════════════════════════════════════════════════════════════════════╝""")

    # Phase 3: Face recognition
    if ENABLE_FACE_AUTH:
        hud(s="thinking", p=(3,"Face Auth"))
        from jarvis_face import verify_face
        if not verify_face():
            speak("Authentication failed. Shutting down.")
            sys.exit(1)

    # Phase 12: Background PC monitoring
    if ENABLE_MONITORING:
        monitor_alerts_loop()
        print("[PHASE 12] Background monitoring active.")

    # Phase 7: Reminder checker
    if ENABLE_REMINDERS:
        reminder_check_loop()
        print("[PHASE 7] Reminder engine active.")

    # Phase 2: Wake word
    if ENABLE_WAKE_WORD:
        from jarvis_wakeword import start_wake_word
        def on_wake():
            hud(s="listening", p=(2,"Wake Word"))
            speak("Yes sir.")
        start_wake_word(callback=on_wake)
        print("[PHASE 2] Wake word engine active.")

    # Phase 14: Offline mode
    if OFFLINE_MODE:
        set_offline_mode(True)

    # Greet
    wish_me()
    speak("All 14 modules loaded and operational. I am ready, sir.")
    hud(s="standby", p=(1,"AI Brain"))


# ── MAIN LOOP ──────────────────────────────────────────────────────────────
def main():
    startup()
    running = True
    while running:
        hud(s="listening")
        if OFFLINE_MODE:
            from jarvis_advanced import offline_take_command, offline_brain
            query = offline_take_command()
            if query:
                hud(u=query, s="thinking")
                offline_brain(query)
        else:
            query = take_command()
            running = route_command(query)


if __name__ == "__main__":
    main()