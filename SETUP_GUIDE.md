# 🤖 J.A.R.V.I.S — Advanced AI Assistant (All 14 Phases)

---

## 📁 All Files — What Each Does

| File | Phase | Purpose |
|------|-------|---------|
| `jarvis_main_advanced.py` | ALL | ▶ **Run this** — master controller |
| `jarvis_engine.py` | Core | Voice input + text-to-speech |
| `jarvis_ai_brain.py` | 1 | Claude / GPT-4 AI brain |
| `jarvis_wakeword.py` | 2 | "Hey Jarvis" always listening |
| `jarvis_face.py` | 3 | Face recognition login |
| `jarvis_hud.py` | 4 | Iron Man HUD overlay |
| `jarvis_system.py` | 4 | Shutdown, volume, brightness |
| `jarvis_apps.py` | 4 | Open/close apps & websites |
| `jarvis_mouse.py` | 4 | Mouse + keyboard control |
| `jarvis_media.py` | 4 | Screenshots, media keys |
| `jarvis_files.py` | 4 | File & folder operations |
| `jarvis_info.py` | 4 | Time, date, jokes, Wikipedia |
| `jarvis_messages.py` | 5 | Email + WhatsApp |
| `jarvis_advanced.py` | 6–14 | Smart home, memory, code, web auto, news, voice, monitor, images, offline |
| `requirements_advanced.txt` | — | All libraries |

---

## ⚡ Quick Start (3 steps)

### Step 1 — Install libraries
```
pip install -r requirements_advanced.txt
```

> If pyaudio fails on Windows:
> ```
> pip install pipwin
> pipwin install pyaudio
> ```

> If face-recognition fails:
> ```
> pip install cmake
> pip install dlib
> pip install face-recognition
> ```

### Step 2 — Set your API keys
Open `jarvis_main_advanced.py` and set:
```python
os.environ.setdefault("ANTHROPIC_API_KEY", "your-key-here")
os.environ.setdefault("OPENAI_API_KEY",    "your-key-here")
os.environ.setdefault("ELEVENLABS_API_KEY","your-key-here")
```
Get keys from:
- Claude: https://console.anthropic.com
- OpenAI: https://platform.openai.com
- ElevenLabs: https://elevenlabs.io (free tier available)

### Step 3 — Run Jarvis
```
python jarvis_main_advanced.py
```

---

## 🔧 Phase-by-Phase Setup

### Phase 2 — Wake Word "Hey Jarvis"
1. Get free key: https://console.picovoice.ai
2. Open `jarvis_wakeword.py` → set `PORCUPINE_KEY`
3. In `jarvis_main_advanced.py` → set `ENABLE_WAKE_WORD = True`

### Phase 3 — Face Recognition
1. First, register your face (ONE TIME):
   ```
   python jarvis_face.py register
   ```
2. Look at camera for 20 photos
3. In `jarvis_main_advanced.py` → set `ENABLE_FACE_AUTH = True`

### Phase 5 — Email
1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Create app password for "Mail"
3. Open `jarvis_messages.py` → set `GMAIL_USER` and `GMAIL_PASSWORD`
4. Add your contacts to the `CONTACTS` dict

### Phase 6 — Smart Home
1. Install Home Assistant: https://www.home-assistant.io
2. Open HA → Profile → Long-Lived Access Tokens → Create Token
3. Open `jarvis_advanced.py` → set `HA_URL` and `HA_TOKEN`

### Phase 9 — Web Automation (Selenium)
1. Install Chrome browser
2. `pip install selenium webdriver-manager`
3. ChromeDriver is auto-downloaded by webdriver-manager

### Phase 11 — Custom AI Voice (ElevenLabs)
1. Sign up: https://elevenlabs.io (free: 10,000 chars/month)
2. Get API key from dashboard
3. Set `ELEVENLABS_API_KEY` env variable
4. In `jarvis_main_advanced.py` → set `ENABLE_ELEVENLABS = True`

### Phase 13 — Image Generation
Option A: DALL-E 3 (needs OpenAI key, costs ~$0.04/image)
- Just set `OPENAI_API_KEY` and it works automatically

Option B: Local Stable Diffusion (free, needs GPU with 4GB+ VRAM)
```
pip install diffusers transformers torch torchvision accelerate
```

### Phase 14 — Full Offline Mode
**Whisper (offline speech):**
```
pip install openai-whisper soundfile
```

**Ollama (offline AI):**
1. Download: https://ollama.ai
2. Install and run:
   ```
   ollama serve
   ollama pull llama3
   ```
3. In `jarvis_main_advanced.py` → set `OFFLINE_MODE = True`

---

## 🎤 Voice Commands Reference

### Power & System
```
shutdown / restart / sleep / hibernate / lock / log off
volume up / down / mute / set volume to 70
brightness up / down / set brightness to 50
battery status / wifi status / ip address
task manager / empty recycle bin
```

### Apps & Web
```
open chrome / open spotify / open vs code / open notepad
close chrome / close spotify
open youtube / open gmail / open github
search for [query]
search youtube for [song name]
```

### Smart Home (Phase 6)
```
turn on bedroom light / turn off fan
switch on AC / turn off kitchen light
smart home status
```

### Email & Messages (Phase 5)
```
send email to [name] [message]
check email / read inbox
whatsapp [name] [message]
```

### Memory (Phase 7)
```
remember that my birthday is January 5
what is my birthday?
search memory [topic]
remind me to call mom at 18 30
```

### Code Assistant (Phase 8)
```
write code to rename all files in downloads
write a python script to send an email
run script / run latest code
```

### News & Weather (Phase 10)
```
top headlines / latest news / 5 news
weather Chennai / weather in Mumbai
```

### Files & Folders
```
create file budget.xlsx / delete file notes.txt
create folder Projects / list files
find file report / open file resume.pdf
```

### PC Monitor (Phase 12)
```
system info / system status
cpu usage / ram usage / disk usage
top processes / battery
```

### Image Generation (Phase 13)
```
generate image of a futuristic city at night
create picture of a golden retriever puppy
make an image of Chennai skyline
```

### Offline Mode (Phase 14)
```
offline mode / go offline
online mode / go online
use ollama [question]
```

### Mouse & Keyboard
```
click / right click / double click
move mouse to 500 300 / type hello world
press enter / hotkey ctrl s
minimize / maximize / close window
switch window / show desktop / snap left
```

### Utilities
```
what time is it / today's date
tell me a joke / flip coin / roll dice
calculate 25 * 48 + 100
wikipedia artificial intelligence
how are you jarvis / your name
help / exit jarvis
```

---

## 🔄 Enable/Disable Features

Edit these flags in `jarvis_main_advanced.py`:
```python
ENABLE_FACE_AUTH   = False  # Phase 3
ENABLE_HUD         = True   # Phase 4 — floating overlay
ENABLE_WAKE_WORD   = False  # Phase 2 — needs pvporcupine
ENABLE_MONITORING  = True   # Phase 12 — background alerts
ENABLE_REMINDERS   = True   # Phase 7 — reminder checker
ENABLE_ELEVENLABS  = False  # Phase 11 — AI voice
USE_AI_BRAIN       = True   # Phase 1 — Claude/GPT
OFFLINE_MODE       = False  # Phase 14 — Whisper+Ollama
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| pyaudio install fails | `pip install pipwin` then `pipwin install pyaudio` |
| face-recognition fails | `pip install cmake dlib face-recognition` |
| No mic detected | Jarvis falls back to keyboard input automatically |
| Chrome not found by Selenium | Install Chrome browser, webdriver-manager handles driver |
| Ollama not responding | Run `ollama serve` in a separate terminal |
| ElevenLabs no sound | Check API key and internet connection |
| DALL-E fails | Check OpenAI API key and billing |

---

## 📂 Where Files Are Saved

| Type | Location |
|------|----------|
| Screenshots | `Desktop/Screenshots/` |
| AI Images | `Desktop/jarvis_images/` |
| Code scripts | `Desktop/jarvis_code/` |
| Memory database | `~/jarvis_memory.db` |
| Face data | `~/jarvis_face_data.pkl` |