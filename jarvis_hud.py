"""
jarvis_hud.py — Phase 4: Iron Man HUD Interface
A live floating overlay that shows Jarvis status, speech, and system info.
Built with Tkinter (no extra install needed).
"""

import tkinter as tk
import threading
import datetime
import time
import psutil
import queue

# ── CONFIG ────────────────────────────────────────────────────────────────────
HUD_WIDTH  = 420
HUD_HEIGHT = 320
HUD_X      = 20      # screen position (top-left corner)
HUD_Y      = 20
OPACITY    = 0.88    # 0.0 = invisible, 1.0 = solid
UPDATE_MS  = 1000    # stats refresh rate

# Colors (Iron Man palette)
C_BG     = "#020a12"
C_BORDER = "#00d4ff"
C_ARC    = "#00d4ff"
C_GREEN  = "#00ffcc"
C_WARN   = "#ff6b35"
C_TEXT   = "#a8e6f5"
C_DIM    = "#4a7a8a"
C_FONT   = "Courier"

# Message queue for thread-safe updates
_msg_queue = queue.Queue()
_hud_instance = None


class JarvisHUD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.geometry(f"{HUD_WIDTH}x{HUD_HEIGHT}+{HUD_X}+{HUD_Y}")
        self.root.configure(bg=C_BG)
        self.root.overrideredirect(True)       # no window borders
        self.root.wm_attributes("-topmost", True)  # always on top
        self.root.wm_attributes("-alpha", OPACITY)

        # Allow dragging the HUD
        self.root.bind("<ButtonPress-1>",  self._drag_start)
        self.root.bind("<B1-Motion>",      self._drag_motion)
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._start_stats_loop()
        self._process_queue()

    def _build_ui(self):
        """Build the HUD layout."""
        # ── Outer border frame ───────────────────────────────────────────────
        outer = tk.Frame(self.root, bg=C_BORDER, padx=1, pady=1)
        outer.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        inner = tk.Frame(outer, bg=C_BG, padx=10, pady=8)
        inner.pack(fill=tk.BOTH, expand=True)

        # ── Header row ───────────────────────────────────────────────────────
        hdr = tk.Frame(inner, bg=C_BG)
        hdr.pack(fill=tk.X)

        tk.Label(hdr, text="J.A.R.V.I.S", bg=C_BG, fg=C_ARC,
                 font=(C_FONT, 14, "bold")).pack(side=tk.LEFT)

        self.lbl_time = tk.Label(hdr, text="--:--:--", bg=C_BG, fg=C_ARC,
                                  font=(C_FONT, 11))
        self.lbl_time.pack(side=tk.RIGHT)

        self.lbl_status = tk.Label(hdr, text="● STANDBY", bg=C_BG, fg=C_DIM,
                                    font=(C_FONT, 9))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # ── Separator ────────────────────────────────────────────────────────
        tk.Frame(inner, bg=C_BORDER, height=1).pack(fill=tk.X, pady=5)

        # ── Speech display ───────────────────────────────────────────────────
        sp_frame = tk.Frame(inner, bg=C_BG)
        sp_frame.pack(fill=tk.X, pady=2)

        tk.Label(sp_frame, text="YOU:", bg=C_BG, fg=C_DIM,
                 font=(C_FONT, 8)).pack(anchor=tk.W)
        self.lbl_user = tk.Label(sp_frame, text="...", bg=C_BG, fg=C_WARN,
                                  font=(C_FONT, 10), wraplength=380, justify=tk.LEFT)
        self.lbl_user.pack(anchor=tk.W, padx=10)

        tk.Label(sp_frame, text="JARVIS:", bg=C_BG, fg=C_DIM,
                 font=(C_FONT, 8)).pack(anchor=tk.W, pady=(4,0))
        self.lbl_jarvis = tk.Label(sp_frame, text="Awaiting command...",
                                    bg=C_BG, fg=C_TEXT,
                                    font=(C_FONT, 10), wraplength=380, justify=tk.LEFT)
        self.lbl_jarvis.pack(anchor=tk.W, padx=10)

        # ── Separator ────────────────────────────────────────────────────────
        tk.Frame(inner, bg=C_BORDER, height=1).pack(fill=tk.X, pady=5)

        # ── System stats row ─────────────────────────────────────────────────
        stats = tk.Frame(inner, bg=C_BG)
        stats.pack(fill=tk.X)

        self.lbl_cpu  = self._stat_label(stats, "CPU",  "0%")
        self.lbl_ram  = self._stat_label(stats, "RAM",  "0%")
        self.lbl_bat  = self._stat_label(stats, "BAT",  "0%")

        # ── Bottom bar ───────────────────────────────────────────────────────
        tk.Frame(inner, bg=C_BORDER, height=1).pack(fill=tk.X, pady=(6,2))

        bottom = tk.Frame(inner, bg=C_BG)
        bottom.pack(fill=tk.X)

        tk.Label(bottom, text="PHASE ACTIVE:", bg=C_BG, fg=C_DIM,
                 font=(C_FONT, 8)).pack(side=tk.LEFT)
        self.lbl_phase = tk.Label(bottom, text="—", bg=C_BG, fg=C_GREEN,
                                   font=(C_FONT, 8))
        self.lbl_phase.pack(side=tk.LEFT, padx=6)

        # Close button
        tk.Button(bottom, text="✕", bg=C_BG, fg=C_DIM,
                  font=(C_FONT, 10), bd=0, cursor="hand2",
                  command=self.hide).pack(side=tk.RIGHT)

    def _stat_label(self, parent, label, value):
        frame = tk.Frame(parent, bg=C_BG, padx=8)
        frame.pack(side=tk.LEFT, expand=True)
        tk.Label(frame, text=label, bg=C_BG, fg=C_DIM,
                 font=(C_FONT, 7)).pack()
        lbl = tk.Label(frame, text=value, bg=C_BG, fg=C_ARC,
                       font=(C_FONT, 12, "bold"))
        lbl.pack()
        return lbl

    # ── Drag support ──────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag_motion(self, e):
        x = self.root.winfo_x() + (e.x - self._drag_x)
        y = self.root.winfo_y() + (e.y - self._drag_y)
        self.root.geometry(f"+{x}+{y}")

    # ── Stats loop ────────────────────────────────────────────────────────────
    def _start_stats_loop(self):
        def update():
            try:
                cpu  = psutil.cpu_percent()
                ram  = psutil.virtual_memory().percent
                bat  = psutil.sensors_battery()
                bat_pct = f"{int(bat.percent)}%" if bat else "N/A"
                now  = datetime.datetime.now().strftime("%H:%M:%S")

                self.lbl_cpu.config(text=f"{cpu:.0f}%",
                    fg="#ff4444" if cpu > 80 else C_ARC)
                self.lbl_ram.config(text=f"{ram:.0f}%",
                    fg="#ff4444" if ram > 85 else C_ARC)
                self.lbl_bat.config(text=bat_pct)
                self.lbl_time.config(text=now)
            except Exception:
                pass
            self.root.after(UPDATE_MS, update)

        self.root.after(100, update)

    # ── Thread-safe queue ─────────────────────────────────────────────────────
    def _process_queue(self):
        try:
            while True:
                fn = _msg_queue.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(50, self._process_queue)

    # ── Public update methods ─────────────────────────────────────────────────
    def set_user_text(self, text):
        def _do():
            self.lbl_user.config(text=text[:80])
        _msg_queue.put(_do)

    def set_jarvis_text(self, text):
        def _do():
            self.lbl_jarvis.config(text=text[:120])
        _msg_queue.put(_do)

    def set_status(self, status, color=None):
        status_map = {
            "listening":  ("● LISTENING",  C_GREEN),
            "speaking":   ("● SPEAKING",   C_ARC),
            "thinking":   ("● THINKING",   C_WARN),
            "standby":    ("● STANDBY",    C_DIM),
            "error":      ("● ERROR",      "#ff2244"),
        }
        if status in status_map:
            text, col = status_map[status]
        else:
            text, col = status, (color or C_TEXT)

        def _do():
            self.lbl_status.config(text=text, fg=col)
        _msg_queue.put(_do)

    def set_phase(self, n, name):
        def _do():
            self.lbl_phase.config(text=f"PHASE {n:02d} — {name.upper()}")
        _msg_queue.put(_do)

    def show(self):
        def _do():
            self.root.deiconify()
        _msg_queue.put(_do)

    def hide(self):
        def _do():
            self.root.withdraw()
        _msg_queue.put(_do)

    def run(self):
        self.root.mainloop()


# ── Singleton interface ───────────────────────────────────────────────────────
def start_hud():
    """Start HUD in its own thread. Returns controller object."""
    global _hud_instance

    ready_event = threading.Event()

    def _run():
        global _hud_instance
        _hud_instance = JarvisHUD()
        ready_event.set()
        _hud_instance.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    ready_event.wait(timeout=3)
    print("[HUD] Overlay started.")
    return _hud_instance


def hud_update(user_text=None, jarvis_text=None, status=None, phase=None):
    """Update HUD from anywhere in the code."""
    global _hud_instance
    if _hud_instance is None:
        return
    if user_text   is not None: _hud_instance.set_user_text(user_text)
    if jarvis_text is not None: _hud_instance.set_jarvis_text(jarvis_text)
    if status      is not None: _hud_instance.set_status(status)
    if phase       is not None: _hud_instance.set_phase(*phase)


if __name__ == "__main__":
    hud = start_hud()
    time.sleep(1)
    hud_update(status="listening", phase=(1, "AI Brain"))
    hud_update(user_text="open spotify")
    time.sleep(1)
    hud_update(status="thinking")
    time.sleep(1)
    hud_update(status="speaking", jarvis_text="Opening Spotify for you, sir.")
    time.sleep(5)