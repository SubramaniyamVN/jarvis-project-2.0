"""
jarvis_advanced.py — Phases 6–14: All Advanced Modules
Phase 6:  Smart Home (Home Assistant / Tuya)
Phase 7:  Memory System (SQLite)
Phase 8:  Code Assistant (AI + subprocess)
Phase 9:  Web Automation (Selenium)
Phase 10: News & Reminders (feedparser + Google Calendar)
Phase 11: Custom Voice (ElevenLabs)
Phase 12: PC Monitoring (psutil + GPUtil)
Phase 13: Image Generation (DALL-E / Stable Diffusion)
Phase 14: Offline Mode (Whisper + Ollama)
"""

import os, re, json, time, sqlite3, datetime, subprocess, threading, webbrowser
from pathlib import Path
from jarvis_engine import speak

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 6 — SMART HOME
# ══════════════════════════════════════════════════════════════════════════════

HA_URL   = "http://homeassistant.local:8123"   # change to your HA IP
HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"      # HA → Profile → Long-lived tokens

TUYA_DEVICES = {
    "bedroom light": {"device_id": "DEVICE_ID_HERE", "key": "LOCAL_KEY_HERE", "ip": "192.168.1.100"},
}

def ha_call(domain, service, entity_id):
    """Call Home Assistant REST API."""
    try:
        import requests
        url  = f"{HA_URL}/api/services/{domain}/{service}"
        headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
        payload = {"entity_id": entity_id}
        r = requests.post(url, json=payload, headers=headers, timeout=5)
        return r.status_code == 200
    except ImportError:
        speak("requests not installed. Run: pip install requests")
        return False
    except Exception as e:
        speak(f"Smart home error: {str(e)[:60]}")
        return False

def smart_home_control(action, device):
    device_map = {
        "bedroom light":   "light.bedroom",
        "living room light":"light.living_room",
        "kitchen light":   "light.kitchen",
        "fan":             "switch.fan",
        "ac":              "climate.ac",
        "door lock":       "lock.front_door",
        "tv":              "media_player.tv",
    }
    entity = device_map.get(device.lower(), f"light.{device.replace(' ','_')}")
    svc = "turn_on" if action == "on" else "turn_off"
    domain = entity.split(".")[0]
    ok = ha_call(domain, svc, entity)
    speak(f"{'Turned on' if action=='on' else 'Turned off'} {device}." if ok else f"Could not control {device}.")

def handle_smarthome(query):
    q = query.lower()
    action = "on" if any(w in q for w in ["turn on","switch on","on"]) else "off"
    devices = ["bedroom light","living room light","kitchen light","fan","ac","tv","door lock"]
    for d in devices:
        if d in q:
            smart_home_control(action, d)
            return
    speak("Which device should I control?")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 7 — MEMORY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

DB_PATH = str(Path.home() / "jarvis_memory.db")

def _init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT, role TEXT, content TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE, value TEXT, updated TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime TEXT, message TEXT, done INTEGER DEFAULT 0)""")
    con.commit()
    con.close()

_init_db()

def memory_save(role, content):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO conversations (timestamp,role,content) VALUES (?,?,?)",
                (datetime.datetime.now().isoformat(), role, content))
    con.commit(); con.close()

def memory_search(keyword, limit=5):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT timestamp,role,content FROM conversations WHERE content LIKE ? ORDER BY id DESC LIMIT ?",
        (f"%{keyword}%", limit)).fetchall()
    con.close()
    return rows

def fact_save(key, value):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT OR REPLACE INTO facts (key,value,updated) VALUES (?,?,?)",
                (key.lower(), value, datetime.datetime.now().isoformat()))
    con.commit(); con.close()
    speak(f"Got it. I'll remember that {key} is {value}.")

def fact_recall(key):
    con = sqlite3.connect(DB_PATH)
    row = con.execute("SELECT value FROM facts WHERE key=?", (key.lower(),)).fetchone()
    con.close()
    if row:
        speak(f"You told me that {key} is {row[0]}.")
    else:
        speak(f"I don't have anything saved for {key}.")

def reminder_add(dt_str, message):
    con = sqlite3.connect(DB_PATH)
    con.execute("INSERT INTO reminders (datetime,message) VALUES (?,?)", (dt_str, message))
    con.commit(); con.close()
    speak(f"Reminder set: {message} at {dt_str}.")

def reminder_check_loop():
    """Background thread: check and trigger reminders."""
    def _loop():
        while True:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            con = sqlite3.connect(DB_PATH)
            rows = con.execute(
                "SELECT id,message FROM reminders WHERE datetime=? AND done=0", (now,)).fetchall()
            for rid, msg in rows:
                speak(f"Reminder: {msg}")
                con.execute("UPDATE reminders SET done=1 WHERE id=?", (rid,))
                con.commit()
            con.close()
            time.sleep(30)
    threading.Thread(target=_loop, daemon=True).start()

def handle_memory(query):
    q = query.lower()
    if "remember that" in q:
        # "remember that my password is 1234"
        rest = q.replace("remember that","").strip()
        if " is " in rest:
            k, v = rest.split(" is ", 1)
            fact_save(k.strip(), v.strip())
        else:
            speak("Please say: remember that [thing] is [value]")
    elif "what is my" in q or "what's my" in q:
        key = re.sub(r"what(?:'s| is) my", "", q).strip().rstrip("?")
        fact_recall(key)
    elif "search memory" in q:
        kw = q.replace("search memory","").strip()
        rows = memory_search(kw)
        if rows:
            speak(f"Found {len(rows)} memories about {kw}.")
            for ts, role, content in rows[:3]:
                speak(f"{role}: {content[:100]}")
        else:
            speak(f"No memories found about {kw}.")
    elif "set reminder" in q or "remind me" in q:
        speak("What should I remind you about?")
        from jarvis_engine import take_command
        msg = take_command()
        speak("At what time? Say it like: 14 30 for 2:30 PM")
        t = take_command()
        nums = re.findall(r'\d+', t)
        if len(nums) >= 2:
            dt = datetime.datetime.now().replace(
                hour=int(nums[0]), minute=int(nums[1]), second=0)
            reminder_add(dt.strftime("%Y-%m-%d %H:%M"), msg)
        else:
            speak("Could not parse time. Please try again.")
    else:
        speak("Memory command not recognized.")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 8 — CODE ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════

CODE_DIR = str(Path.home() / "Desktop" / "jarvis_code")

def write_and_run_code(description):
    """Ask AI to write code, save it, and run it."""
    from jarvis_ai_brain import ask_ai
    os.makedirs(CODE_DIR, exist_ok=True)

    speak(f"Writing code for: {description}")
    prompt = f"""Write a complete, working Python script that: {description}
Return ONLY the Python code, no explanation, no markdown, no backticks."""

    code = ask_ai(prompt)
    # Strip markdown if AI added it
    code = re.sub(r'```python|```', '', code).strip()

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = os.path.join(CODE_DIR, f"jarvis_script_{timestamp}.py")

    with open(filename, 'w') as f:
        f.write(code)
    speak(f"Script saved. Running it now.")
    print(f"\n[CODE] Script:\n{code}\n")

    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            speak(f"Script ran successfully. Output: {result.stdout[:200]}")
        else:
            speak(f"Script had an error: {result.stderr[:150]}")
            print(f"[CODE] Error:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        speak("Script timed out after 30 seconds.")
    except Exception as e:
        speak(f"Could not run script: {str(e)[:60]}")

def handle_code(query):
    q = query.lower()
    if "write code" in q or "write a script" in q or "create script" in q:
        desc = re.sub(r'(write code|write a script|create script|for|to)', '', q).strip()
        write_and_run_code(desc or "print Hello World")
    elif "run script" in q or "run code" in q:
        # Find latest script
        import glob
        scripts = glob.glob(os.path.join(CODE_DIR, "*.py"))
        if scripts:
            latest = max(scripts, key=os.path.getmtime)
            speak(f"Running latest script: {os.path.basename(latest)}")
            subprocess.Popen(["python", latest])
        else:
            speak("No scripts found in the code directory.")
    else:
        desc = re.sub(r'(code|script|python)', '', q).strip()
        write_and_run_code(desc)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 9 — WEB AUTOMATION
# ══════════════════════════════════════════════════════════════════════════════

def web_search_automated(query):
    """Open browser and search Google automatically."""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.chrome.options import Options

        speak(f"Automating browser search for: {query}")
        opts = Options()
        opts.add_argument("--start-maximized")
        driver = webdriver.Chrome(options=opts)
        driver.get("https://www.google.com")
        time.sleep(1)
        box = driver.find_element(By.NAME, "q")
        box.send_keys(query)
        box.send_keys(Keys.RETURN)
        speak("Search complete. Browser is showing results.")
        return driver

    except ImportError:
        speak("Selenium not installed. Run: pip install selenium")
        webbrowser.open(f"https://google.com/search?q={query}")
        return None
    except Exception as e:
        speak(f"Browser automation error: {str(e)[:60]}")
        return None

def fill_form_automated(url, fields):
    """Automatically fill a web form. fields = {field_id: value}"""
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options

        opts = Options()
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        time.sleep(2)
        for field_id, value in fields.items():
            try:
                el = driver.find_element(By.ID, field_id)
                el.clear()
                el.send_keys(value)
            except Exception:
                pass
        speak("Form filled successfully.")
        return driver
    except ImportError:
        speak("Selenium not installed.")
        return None

def handle_webauto(query):
    q = query.lower()
    if "search" in q:
        term = re.sub(r'(search|google|browse|find)', '', q).strip()
        web_search_automated(term or "python tutorial")
    elif "open website" in q or "go to" in q:
        url = re.sub(r'(open website|go to|open)', '', q).strip()
        if not url.startswith("http"):
            url = "https://" + url
        speak(f"Opening {url}")
        webbrowser.open(url)
    else:
        speak("Web automation command not recognized.")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 10 — NEWS & REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://techcrunch.com/feed/",
]

def get_news(count=5):
    try:
        import feedparser
        all_items = []
        for feed_url in NEWS_FEEDS:
            feed = feedparser.parse(feed_url)
            all_items.extend(feed.entries[:3])
        items = all_items[:count]
        speak(f"Here are your top {len(items)} headlines.")
        for i, item in enumerate(items, 1):
            speak(f"Headline {i}: {item.get('title','No title')}")
            time.sleep(0.3)
    except ImportError:
        speak("feedparser not installed. Run: pip install feedparser")
    except Exception as e:
        speak(f"News error: {str(e)[:60]}")

def weather_report(city="Chennai"):
    try:
        import requests
        # Use wttr.in — no API key needed
        r = requests.get(f"https://wttr.in/{city}?format=3", timeout=5)
        if r.status_code == 200:
            speak(f"Weather update: {r.text.strip()}")
        else:
            webbrowser.open(f"https://google.com/search?q=weather+{city}")
    except ImportError:
        webbrowser.open(f"https://google.com/search?q=weather+{city}")
    except Exception:
        webbrowser.open(f"https://google.com/search?q=weather+{city}")

def handle_news(query):
    q = query.lower()
    if "news" in q or "headline" in q:
        count = int(re.findall(r'\d+', q)[0]) if re.findall(r'\d+', q) else 5
        get_news(count)
    elif "weather" in q:
        city = re.sub(r'(weather|in|at|for)', '', q).strip() or "Chennai"
        weather_report(city)
    else:
        get_news(3)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 11 — CUSTOM VOICE (ElevenLabs)
# ══════════════════════════════════════════════════════════════════════════════

ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVEN_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # "Adam" voice — deep male

def speak_elevenlabs(text):
    """Speak using ElevenLabs AI voice instead of pyttsx3."""
    if not ELEVEN_API_KEY:
        speak(text)
        return

    try:
        from elevenlabs import generate, play, set_api_key
        set_api_key(ELEVEN_API_KEY)
        print(f"[VOICE] ElevenLabs: {text}")
        audio = generate(
            text=text,
            voice=ELEVEN_VOICE_ID,
            model="eleven_monolingual_v1"
        )
        play(audio)
    except ImportError:
        speak(text)  # fallback to pyttsx3
    except Exception as e:
        print(f"[VOICE] ElevenLabs error: {e}")
        speak(text)

def list_eleven_voices():
    try:
        from elevenlabs import voices, set_api_key
        set_api_key(ELEVEN_API_KEY)
        vs = voices()
        speak(f"Available voices: {', '.join(v.name for v in vs)}")
    except Exception:
        speak("Could not fetch ElevenLabs voices.")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 12 — PC MONITORING
# ══════════════════════════════════════════════════════════════════════════════

ALERT_CPU_THRESHOLD  = 90   # %
ALERT_RAM_THRESHOLD  = 90   # %
ALERT_TEMP_THRESHOLD = 85   # °C
ALERT_DISK_THRESHOLD = 90   # %

def full_system_report():
    import psutil
    cpu   = psutil.cpu_percent(interval=1)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage('/')
    bat   = psutil.sensors_battery()

    report = (
        f"CPU: {cpu}% | "
        f"RAM: {ram.percent}% ({round(ram.used/1e9,1)}GB of {round(ram.total/1e9,1)}GB) | "
        f"Disk: {disk.percent}% used | "
        f"Battery: {int(bat.percent) if bat else 'N/A'}%"
    )
    speak(report)

    # GPU (optional)
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        for g in gpus:
            speak(f"GPU {g.name}: Load {g.load*100:.0f}%, Temp {g.temperature}°C, VRAM {g.memoryUsed:.0f}MB/{g.memoryTotal:.0f}MB")
    except ImportError:
        pass

def list_top_processes(n=5):
    import psutil
    procs = sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']),
                   key=lambda p: p.info['cpu_percent'] or 0, reverse=True)
    speak(f"Top {n} processes by CPU usage:")
    for p in procs[:n]:
        speak(f"{p.info['name']}: CPU {p.info['cpu_percent']:.1f}%, RAM {p.info['memory_percent']:.1f}%")

def kill_process(name):
    import psutil
    killed = []
    for p in psutil.process_iter(['name']):
        if name.lower() in p.info['name'].lower():
            p.kill()
            killed.append(p.info['name'])
    if killed:
        speak(f"Killed: {', '.join(killed)}")
    else:
        speak(f"No process named {name} found.")

def monitor_alerts_loop():
    """Background monitoring — alert on high usage."""
    import psutil

    def _loop():
        while True:
            try:
                cpu = psutil.cpu_percent(interval=2)
                ram = psutil.virtual_memory().percent
                disk = psutil.disk_usage('/').percent

                if cpu > ALERT_CPU_THRESHOLD:
                    speak(f"Warning! CPU usage is critically high at {cpu} percent.")
                if ram > ALERT_RAM_THRESHOLD:
                    speak(f"Warning! RAM usage is at {ram} percent. Consider closing some applications.")
                if disk > ALERT_DISK_THRESHOLD:
                    speak(f"Warning! Disk is {disk} percent full. Please free up space.")
            except Exception:
                pass
            time.sleep(60)

    threading.Thread(target=_loop, daemon=True).start()
    print("[MON] Background monitoring started.")

def handle_monitor(query):
    q = query.lower()
    if "system info" in q or "system status" in q:
        full_system_report()
    elif "top process" in q or "what's using" in q:
        list_top_processes()
    elif "kill" in q:
        name = re.sub(r'(kill|process|app)', '', q).strip()
        kill_process(name)
    elif "cpu" in q:
        import psutil
        speak(f"CPU usage is {psutil.cpu_percent(interval=1)} percent.")
    elif "ram" in q or "memory" in q:
        import psutil
        r = psutil.virtual_memory()
        speak(f"RAM: {r.percent}% used, {round(r.available/1e9,1)} GB available.")
    elif "disk" in q or "storage" in q:
        import psutil
        d = psutil.disk_usage('/')
        speak(f"Disk: {d.percent}% used, {round(d.free/1e9,1)} GB free.")
    elif "battery" in q:
        import psutil
        b = psutil.sensors_battery()
        if b:
            speak(f"Battery at {int(b.percent)}%, {'charging' if b.power_plugged else 'on battery'}.")
        else:
            speak("No battery detected.")
    else:
        full_system_report()


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 13 — IMAGE GENERATION
# ══════════════════════════════════════════════════════════════════════════════

IMAGE_SAVE_DIR = str(Path.home() / "Desktop" / "jarvis_images")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")

def generate_image_dalle(prompt):
    """Generate image using DALL-E 3 (needs OpenAI API key)."""
    try:
        from openai import OpenAI
        import requests as req

        os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
        client = OpenAI(api_key=OPENAI_KEY)
        speak(f"Generating image: {prompt}. Please wait.")

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url

        # Download and save
        img_data = req.get(image_url).content
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = os.path.join(IMAGE_SAVE_DIR, f"jarvis_img_{timestamp}.png")
        with open(filename, 'wb') as f:
            f.write(img_data)

        speak(f"Image generated and saved to Desktop jarvis images folder.")
        os.startfile(filename) if os.name == 'nt' else subprocess.Popen(['xdg-open', filename])

    except ImportError:
        speak("OpenAI library not installed. Run: pip install openai")
    except Exception as e:
        speak(f"Image generation failed: {str(e)[:80]}")

def generate_image_local(prompt):
    """Generate image locally using Stable Diffusion (no API key, needs GPU)."""
    try:
        from diffusers import StableDiffusionPipeline
        import torch

        os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)
        speak("Loading Stable Diffusion locally. This may take a minute on first run.")

        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")

        speak(f"Generating: {prompt}")
        image = pipe(prompt).images[0]

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = os.path.join(IMAGE_SAVE_DIR, f"sd_img_{timestamp}.png")
        image.save(filename)
        speak(f"Image saved to Desktop jarvis images folder.")
        os.startfile(filename) if os.name == 'nt' else subprocess.Popen(['xdg-open', filename])

    except ImportError:
        speak("diffusers or torch not installed. Run: pip install diffusers transformers torch")
    except Exception as e:
        speak(f"Local image generation error: {str(e)[:80]}")

def handle_imagegen(query):
    q = query.lower()
    prompt = re.sub(r'(generate|create|make|draw|image|picture|photo|of)', '', q).strip()
    if not prompt:
        speak("What should I generate an image of?")
        from jarvis_engine import take_command
        prompt = take_command()

    if OPENAI_KEY:
        generate_image_dalle(prompt)
    else:
        speak("No OpenAI key found. Trying local Stable Diffusion.")
        generate_image_local(prompt)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 14 — OFFLINE MODE (Whisper + Ollama)
# ══════════════════════════════════════════════════════════════════════════════

_offline_mode = False

def set_offline_mode(enabled=True):
    global _offline_mode
    _offline_mode = enabled
    if enabled:
        speak("Offline mode activated. Using Whisper for speech recognition and Ollama for AI.")
    else:
        speak("Online mode restored.")

def transcribe_offline(audio_data):
    """Use OpenAI Whisper locally for speech-to-text (no internet needed)."""
    try:
        import whisper
        import tempfile, soundfile as sf

        model = whisper.load_model("base")  # tiny/base/small/medium/large
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio_data, 16000)
            result = model.transcribe(tmp.name, language="en")
        return result["text"].strip()
    except ImportError:
        speak("Whisper not installed. Run: pip install openai-whisper soundfile")
        return ""
    except Exception as e:
        print(f"[OFFLINE] Whisper error: {e}")
        return ""

def ask_ollama(prompt, model="llama3"):
    """Send prompt to local Ollama LLM (no internet needed)."""
    try:
        import requests
        r = requests.post("http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}, timeout=60)
        if r.status_code == 200:
            return r.json().get("response", "")
        return "Ollama returned an error."
    except ImportError:
        return "requests not installed."
    except Exception as e:
        return f"Ollama error: {str(e)[:80]}. Is Ollama running? Start with: ollama serve"

def offline_take_command():
    """Record audio and transcribe offline using Whisper."""
    import speech_recognition as sr
    import numpy as np

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("[OFFLINE] Listening (Whisper)...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=8, phrase_time_limit=12)
        raw = np.frombuffer(audio.get_raw_data(convert_rate=16000, convert_width=2),
                             dtype=np.int16).astype(np.float32) / 32768.0
        text = transcribe_offline(raw)
        print(f"[OFFLINE] You said: {text}")
        return text.lower()
    except Exception as e:
        print(f"[OFFLINE] Listen error: {e}")
        return ""

def offline_brain(user_input):
    """Full offline pipeline: user input → Ollama → response."""
    from jarvis_engine import speak as jarvis_speak
    print("[OFFLINE] Asking Ollama...")
    system = """You are Jarvis, an AI assistant. Be concise and helpful.
If the user wants to control the laptop, reply with a JSON action.
Otherwise reply normally in 1-2 sentences."""
    response = ask_ollama(f"{system}\n\nUser: {user_input}\nJarvis:")
    print(f"[OFFLINE] Ollama: {response}")
    jarvis_speak(response[:300])
    return response

def handle_offline(query):
    q = query.lower()
    if "offline mode" in q or "go offline" in q:
        set_offline_mode(True)
    elif "online mode" in q or "go online" in q:
        set_offline_mode(False)
    elif "ollama" in q:
        from jarvis_engine import take_command
        speak("What do you want to ask Ollama?")
        prompt = take_command()
        result = ask_ollama(prompt)
        speak(result[:300])
    else:
        speak("Offline command not recognized. Say 'offline mode' or 'online mode'.")