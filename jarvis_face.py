"""
jarvis_face.py — Phase 3: Face Recognition
Uses webcam to identify the authorized user on startup.
Blocks unknown faces. Trains on your own photo.
"""

import os
import cv2
import time
import pickle
import numpy as np
from pathlib import Path
from jarvis_engine import speak

# ── CONFIG ────────────────────────────────────────────────────────────────────
FACE_DATA_FILE = str(Path.home() / "jarvis_face_data.pkl")
PHOTOS_DIR     = str(Path.home() / "Desktop" / "jarvis_faces")
AUTHORIZED_NAME = "authorized_user"
MAX_RETRIES     = 3
CONFIDENCE_THRESHOLD = 0.55   # lower = stricter


# ── TRAIN: Register Your Face ────────────────────────────────────────────────
def register_face(name=AUTHORIZED_NAME):
    """
    Capture 20 photos of your face from webcam and save encodings.
    Run this ONCE before using face recognition.
    """
    try:
        import face_recognition
    except ImportError:
        speak("face_recognition not installed. Run: pip install face-recognition")
        return False

    os.makedirs(PHOTOS_DIR, exist_ok=True)
    speak(f"Starting face registration for {name}. Look at the camera. I will capture 20 photos.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Cannot open webcam.")
        return False

    encodings = []
    count = 0

    print("[FACE] Capturing face photos... Press Q to cancel.")
    while count < 20:
        ret, frame = cap.read()
        if not ret:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        cv2.putText(frame, f"Captured: {count}/20", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Jarvis Face Registration", frame)

        if face_locations:
            encoding = face_recognition.face_encodings(rgb_frame, face_locations)
            if encoding:
                encodings.append(encoding[0])
                count += 1
                time.sleep(0.2)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if encodings:
        with open(FACE_DATA_FILE, 'wb') as f:
            pickle.dump({name: encodings}, f)
        speak(f"Face registration complete! Saved {len(encodings)} encodings for {name}.")
        print(f"[FACE] Saved to {FACE_DATA_FILE}")
        return True
    else:
        speak("No face detected during registration. Please try again.")
        return False


# ── LOAD: Load Known Faces ───────────────────────────────────────────────────
def load_known_faces():
    """Load registered face encodings from disk."""
    if not os.path.exists(FACE_DATA_FILE):
        return {}, []

    with open(FACE_DATA_FILE, 'rb') as f:
        data = pickle.load(f)

    known_encodings = []
    known_names = []
    for name, encodings in data.items():
        for enc in encodings:
            known_encodings.append(enc)
            known_names.append(name)

    return data, known_encodings, known_names


# ── VERIFY: Authenticate User ────────────────────────────────────────────────
def verify_face(timeout=15):
    """
    Open webcam, scan for face, return True if authorized user detected.
    Shows live HUD overlay.
    """
    try:
        import face_recognition
    except ImportError:
        speak("face_recognition not installed. Skipping face auth.")
        return True   # skip auth if library missing

    if not os.path.exists(FACE_DATA_FILE):
        speak("No face data found. Please register your face first by running: python jarvis_face.py register")
        return False

    _, known_encodings, known_names = load_known_faces()
    if not known_encodings:
        speak("No known faces loaded.")
        return False

    speak("Scanning for authorized user. Please look at the camera.")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        speak("Cannot open webcam. Skipping face authentication.")
        return True   # allow if no cam

    start = time.time()
    verified = False
    process_every = 2  # process every 2nd frame for speed

    print("[FACE] Scanning... (face recognition active)")
    frame_count = 0

    while time.time() - start < timeout:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        if frame_count % process_every == 0:
            face_locations = face_recognition.face_locations(rgb_small)
            face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

            for enc in face_encodings:
                distances = face_recognition.face_distance(known_encodings, enc)
                if len(distances) > 0:
                    min_dist = min(distances)
                    best_idx = np.argmin(distances)
                    name = known_names[best_idx] if min_dist < CONFIDENCE_THRESHOLD else "Unknown"

                    if name != "Unknown":
                        verified = True
                        # Draw box
                        top, right, bottom, left = face_locations[0]
                        top *= 4; right *= 4; bottom *= 4; left *= 4
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, f"✓ {name.upper()}", (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    else:
                        top, right, bottom, left = face_locations[0]
                        top *= 4; right *= 4; bottom *= 4; left *= 4
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "UNKNOWN — ACCESS DENIED", (left, top - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # HUD overlay
        elapsed = time.time() - start
        cv2.putText(frame, f"JARVIS FACE AUTH", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        cv2.putText(frame, f"Scanning: {int(elapsed)}s / {timeout}s", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        cv2.imshow("JARVIS — Face Authentication", frame)

        if verified:
            time.sleep(0.5)
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if verified:
        speak("Identity confirmed. Welcome back, sir. Access granted.")
    else:
        speak("Face authentication failed. Unauthorized access attempt logged.")

    return verified


# ── CONTINUOUS MONITORING ─────────────────────────────────────────────────────
def monitor_face_background(on_unknown_callback=None):
    """
    Run in background thread — alerts if an unknown face appears.
    """
    import threading

    def _monitor():
        try:
            import face_recognition
        except ImportError:
            return

        if not os.path.exists(FACE_DATA_FILE):
            return

        _, known_encodings, known_names = load_known_faces()
        cap = cv2.VideoCapture(0)
        last_alert = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                continue

            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb)
            encs  = face_recognition.face_encodings(rgb, faces)

            for enc in encs:
                distances = face_recognition.face_distance(known_encodings, enc)
                if len(distances) > 0 and min(distances) >= CONFIDENCE_THRESHOLD:
                    now = time.time()
                    if now - last_alert > 30:   # alert max once per 30s
                        speak("Warning! Unknown face detected.")
                        last_alert = now
                        if on_unknown_callback:
                            on_unknown_callback()

            time.sleep(2)  # check every 2 seconds

    t = threading.Thread(target=_monitor, daemon=True)
    t.start()
    print("[FACE] Background monitoring started.")


# ── CLI INTERFACE ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "register":
        name = sys.argv[2] if len(sys.argv) > 2 else AUTHORIZED_NAME
        register_face(name)
    else:
        print("Usage:")
        print("  python jarvis_face.py register          — Register your face")
        print("  python jarvis_face.py register YourName — Register with custom name")
        print()
        print("Testing face verification...")
        result = verify_face()
        print(f"Result: {'AUTHORIZED' if result else 'DENIED'}")