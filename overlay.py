"""Schwebende Statusleiste am unteren Bildschirmrand (Wispr-Flow-Stil).

Die Leiste ist ein randloses, immer-oben, nicht fokussierbares Tk-Fenster.
Gezeichnet wird eine abgerundete "Pille" auf transparentem Hintergrund:
- Leerlauf:       gruener Punkt + Hotkey-Hinweis
- Aufnahme:       roter Puls-Punkt + Live-Wellenform + Timer
- Transkribieren: gelber Punkt + animierte Punkte
- Modell laden:   blauer Punkt + Modellname
"""
import collections
import ctypes
import math
import time
import tkinter as tk
import tkinter.font as tkfont

TRANSPARENT = "#010203"  # Farbschluessel fuer Fenstertransparenz

# Farbschemata, umschaltbar in den Einstellungen ("Design der Leiste")
THEMES = {
    "light": dict(bg="#fbfbfd", border="#c9c9d6", text="#1b1b24",
                  dim="#82828f", wave="#1b1b24"),
    "dark": dict(bg="#16161f", border="#3c3c50", text="#e8e8f0",
                 dim="#9a9aac", wave="#e8e8f0"),
}
RED = "#ff5252"
GREEN = "#3ad36b"
AMBER = "#ffb02e"
BLUE = "#4da3ff"
VIOLET = "#a86bff"

W, H = 460, 72
PILL_H = 46

GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080


def pretty_hotkey(combo: str) -> str:
    names = {
        "ctrl": "Strg", "strg": "Strg", "alt": "Alt", "alt gr": "AltGr",
        "shift": "Umschalt", "umschalt": "Umschalt",
        "windows": "Win", "linke windows": "Win", "rechte windows": "Win",
        "left windows": "Win", "right windows": "Win",
        "space": "Leertaste", "leertaste": "Leertaste",
        "enter": "Enter", "esc": "Esc", "tab": "Tab",
    }
    parts = []
    for key in combo.split("+"):
        key = key.strip()
        parts.append(names.get(
            key.lower(), key.upper() if len(key) <= 3 else key.capitalize()))
    return "+".join(parts)


class OverlayBar:
    def __init__(self, root: tk.Tk, app):
        self.root = root
        self.app = app
        self.levels = collections.deque([0.0] * 30, maxlen=30)

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", TRANSPARENT)
        root.configure(bg=TRANSPARENT)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{W}x{H}+{(sw - W) // 2}+{sh - H - 76}")

        self.canvas = tk.Canvas(root, width=W, height=H, bg=TRANSPARENT,
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        self.font = tkfont.Font(family="Segoe UI", size=10)
        self.font_bold = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        root.update_idletasks()
        self._make_unfocusable()
        self._tick()

    def _make_unfocusable(self):
        """Klicks auf die Leiste duerfen der Ziel-App nicht den Fokus stehlen."""
        try:
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = int(self.root.wm_frame(), 16)
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def _on_click(self, _event):
        if self.app.state in ("idle", "recording"):
            self.app.toggle_recording()

    # ------------------------------------------------------------- Zeichnen

    def _rounded_pill(self, x0, y0, x1, y1, fill, outline):
        r = (y1 - y0) / 2
        self.canvas.create_arc(x0, y0, x0 + 2 * r, y1, start=90, extent=180,
                               fill=fill, outline=fill)
        self.canvas.create_arc(x1 - 2 * r, y0, x1, y1, start=270, extent=180,
                               fill=fill, outline=fill)
        self.canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=fill, outline=fill)
        # duenner Rand nur oben/unten (Vollrand um Boegen sieht in Tk unsauber aus)
        self.canvas.create_line(x0 + r, y0, x1 - r, y0, fill=outline)
        self.canvas.create_line(x0 + r, y1, x1 - r, y1, fill=outline)

    def _draw(self):
        c = self.canvas
        c.delete("all")
        state = self.app.state
        now = time.time()
        th = THEMES.get(self.app.cfg.get("theme", "light"), THEMES["light"])

        if state == "recording":
            self.levels.append(self.app.recorder.level)
        else:
            self.levels.append(0.0)

        if state == "hidden":
            return

        # Inhalt bestimmen
        if state == "recording":
            dot, dot_pulse = RED, True
            elapsed = int(now - self.app.record_started)
            label = f"{elapsed // 60}:{elapsed % 60:02d}"
            hint = "Aufnahme läuft"
            show_wave = True
        elif state == "transcribing":
            dots = "." * (int(now * 3) % 4)
            dot, dot_pulse = AMBER, False
            label, hint, show_wave = "", f"Transkribiere{dots}", False
        elif state == "polishing":
            dots = "." * (int(now * 3) % 4)
            dot, dot_pulse = VIOLET, False
            label, hint, show_wave = "", f"Formuliere{dots}", False
        elif state == "translating":
            dots = "." * (int(now * 3) % 4)
            dot, dot_pulse = BLUE, False
            label, hint, show_wave = "", f"Übersetze{dots}", False
        elif state == "loading":
            dot, dot_pulse = BLUE, False
            label, hint, show_wave = "", self.app.status_message or "Lade Modell…", False
        else:  # idle
            dot, dot_pulse = GREEN, False
            label = ""
            hint = f"Bereit — {pretty_hotkey(self.app.cfg['hotkey'])}"
            if self.app.cfg.get("cleanup_enabled") and self.app.cfg.get("cleanup_hotkey"):
                hint += f"  ·  KI: {pretty_hotkey(self.app.cfg['cleanup_hotkey'])}"
            show_wave = False

        # Breite berechnen
        pad = 18
        wave_w = 30 * 5 if show_wave else 0
        text_w = self.font.measure(hint) + (self.font_bold.measure(label) + 12 if label else 0)
        pill_w = pad + 16 + 10 + wave_w + (12 if show_wave else 0) + text_w + pad
        pill_w = max(pill_w, 170)
        x0 = (W - pill_w) / 2
        y0 = (H - PILL_H) / 2
        x1, y1 = x0 + pill_w, y0 + PILL_H
        cy = (y0 + y1) / 2

        self._rounded_pill(x0, y0, x1, y1, th["bg"], th["border"])

        # Status-Punkt
        r = 5
        if dot_pulse:
            r = 5 + 1.6 * (0.5 + 0.5 * math.sin(now * 5))
        cx = x0 + pad + 8
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=dot, outline=dot)
        x = cx + 8 + 10

        # Wellenform
        if show_wave:
            for i, lvl in enumerate(self.levels):
                bh = 3 + lvl * 24
                bx = x + i * 5
                c.create_rectangle(bx, cy - bh / 2, bx + 3, cy + bh / 2,
                                   fill=th["wave"], outline=th["wave"])
            x += wave_w + 12

        # Text
        if hint:
            color = th["text"] if state != "idle" else th["dim"]
            c.create_text(x, cy, text=hint, anchor="w", font=self.font, fill=color)
            x += self.font.measure(hint) + 12
        if label:
            c.create_text(x, cy, text=label, anchor="w", font=self.font_bold,
                          fill=th["text"])

    # ---------------------------------------------------------- Poll-Schleife

    def _tick(self):
        # Anfragen aus anderen Threads (Tray, Hotkey) im Tk-Thread ausfuehren
        self.app.process_ui_requests()

        state = self.app.state
        if state == "idle" and not self.app.cfg.get("show_idle_bar", True):
            self.root.withdraw()
        elif state == "hidden":
            self.root.withdraw()
        else:
            if self.root.state() == "withdrawn":
                self.root.deiconify()
                self.root.attributes("-topmost", True)
            self._draw()
        self.root.after(50, self._tick)
