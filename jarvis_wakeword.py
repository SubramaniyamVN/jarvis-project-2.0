"""
jarvis_wakeword.py — Phase 2: Always-On Wake Word
Listens 24/7 for "Hey Jarvis" without pressing any button.
Uses pvporcupine (free tier available) or a fallback keyword spotter.
"""

import threading
import time
import struct
from jarvis_engine import speak

# ── PORCUPINE WAKE WORD ───────────────────────────────────────────────────────
# Free API key from: https://console.picovoice.ai/
PORCUPINE_KEY = "YOUR_PICOVOICE_ACCESS_KEY"

# Wake word: use built-in "jarvis" keyword or custom .ppn file
WAKE_WORD = "jarvis"

# Global flag
_wake_callback = None
_listening = False
_thread = None


def set_wake_callback(fn):
    """Set function to call when wake word is detected."""
    global _wake_callback
    _wake_callback = fn


# ── METHOD 1: pvporcupine (Recommended) ─────────────────────────────────────
def _porcupine_loop():
    global _listening
    try:
        import pvporcupine
        import pyaudio

        porcupine = pvporcupine.create(
            access_key=PORCUPINE_KEY,
            keywords=[WAKE_WORD]
        )
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print(f"[WAKE] Listening for '{WAKE_WORD}'... (pvporcupine)")
        speak(f"Wake word engine active. Say Hey Jarvis to activate me.")

        while _listening:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                print(f"\n[WAKE] Wake word detected!")
                speak("Yes sir, I am listening.")
                if _wake_callback:
                    _wake_callback()

        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

    except ImportError:
        print("[WAKE] pvporcupine not installed. Falling back to keyword method.")
        _keyword_loop()
    except Exception as e:
        print(f"[WAKE] Porcupine error: {e}. Falling back.")
        _keyword_loop()


# ── METHOD 2: Keyword Fallback (No API key needed) ───────────────────────────
def _keyword_loop():
    """
    Fallback: use SpeechRecognition to check for wake word.
    Less efficient than porcupine but works without API key.
    """
    import speech_recognition as sr
    global _listening

    r = sr.Recognizer()
    r.pause_threshold = 0.5
    r.energy_threshold = 300

    print("[WAKE] Listening for 'jarvis'... (fallback keyword spotter)")

    while _listening:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=3, phrase_time_limit=3)
            text = r.recognize_google(audio, language='en-in').lower()
            print(f"[WAKE] Heard: {text}")
            if "jarvis" in text:
                print("[WAKE] Wake word detected!")
                speak("Yes sir, I am listening.")
                if _wake_callback:
                    _wake_callback()
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except sr.RequestError:
            time.sleep(2)
        except Exception as e:
            print(f"[WAKE] Error: {e}")
            time.sleep(1)


# ── PUBLIC API ────────────────────────────────────────────────────────────────
def start_wake_word(callback=None):
    """Start wake word listener in background thread."""
    global _listening, _thread, _wake_callback
    if callback:
        _wake_callback = callback
    _listening = True
    _thread = threading.Thread(target=_porcupine_loop, daemon=True)
    _thread.start()
    print("[WAKE] Wake word engine started in background.")


def stop_wake_word():
    """Stop the wake word listener."""
    global _listening
    _listening = False
    print("[WAKE] Wake word engine stopped.")


# ── STANDALONE TEST ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    def on_wake():
        from jarvis_engine import take_command
        from jarvis_ai_brain import brain
        query = take_command()
        brain(query)

    start_wake_word(callback=on_wake)
    print("Wake word engine running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_wake_word()
        print("Stopped.")