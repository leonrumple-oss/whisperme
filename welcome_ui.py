"""Erste-Schritte-Assistent beim allerersten Start (Mikrofon-Test + Hotkeys)."""
import tkinter as tk

import customtkinter as ctk

import config
from audio import Recorder
from overlay import pretty_hotkey
# ui_theme ist leichtgewichtig — zieht keine schwere Importkette mit
from ui_theme import (CARD, FIELD, GREEN, PRIMARY, PRIMARY_HOVER,
                      PRIMARY_TXT, SUB, TXT, WINBG)


class WelcomeWindow:
    def __init__(self, root: tk.Tk, app):
        self.app = app
        ctk.set_appearance_mode(
            "dark" if app.cfg.get("theme") == "dark" else "light")

        self.win = ctk.CTkToplevel(root)
        self.win.title("Willkommen bei WisperMe")
        self.win.geometry("520x560")
        self.win.resizable(False, False)
        self.win.configure(fg_color=WINBG)
        self.win.attributes("-topmost", True)

        f_title = ctk.CTkFont("Segoe UI", 24, "bold")
        f_head = ctk.CTkFont("Segoe UI", 14, "bold")
        f_label = ctk.CTkFont("Segoe UI", 13)
        f_small = ctk.CTkFont("Segoe UI", 11)

        ctk.CTkLabel(self.win, text="✦  Willkommen bei WisperMe",
                     font=f_title, text_color=TXT).pack(pady=(24, 4))
        ctk.CTkLabel(self.win, text="Lokales Diktat — kein Audio verlässt deinen Rechner.",
                     font=f_small, text_color=SUB).pack()

        card = ctk.CTkFrame(self.win, fg_color=CARD, corner_radius=16)
        card.pack(fill="x", padx=24, pady=(18, 10))
        ctk.CTkLabel(card, text="So funktioniert's", font=f_head,
                     text_color=TXT).pack(anchor="w", padx=18, pady=(12, 4))
        cfg = app.cfg
        steps = (
            f"1.  {pretty_hotkey(cfg['hotkey'])} drücken und sprechen\n"
            f"2.  nochmal drücken — der Text landet im aktiven Fenster\n"
            f"3.  {pretty_hotkey(cfg.get('cleanup_hotkey', '')) or '—'} nutzt zusätzlich die KI-Glättung\n"
            f"     (Grammatik, Füllwörter, Selbstkorrekturen)"
        )
        ctk.CTkLabel(card, text=steps, font=f_label, text_color=TXT,
                     justify="left").pack(anchor="w", padx=18, pady=(0, 12))

        card = ctk.CTkFrame(self.win, fg_color=CARD, corner_radius=16)
        card.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card, text="Mikrofon-Test", font=f_head,
                     text_color=TXT).pack(anchor="w", padx=18, pady=(12, 2))
        self.level_label = ctk.CTkLabel(card, text="Sprich etwas — der Balken sollte ausschlagen:",
                                        font=f_small, text_color=SUB)
        self.level_label.pack(anchor="w", padx=18)
        self.meter = ctk.CTkProgressBar(card, height=14, corner_radius=7,
                                        fg_color=FIELD, progress_color=GREEN)
        self.meter.set(0)
        self.meter.pack(fill="x", padx=18, pady=(6, 14))

        ctk.CTkLabel(self.win,
                     text="Alle Einstellungen (Shortcut, Modell, Design …) findest du\n"
                          "per Rechtsklick auf das Mikrofon-Icon im System-Tray.",
                     font=f_small, text_color=SUB, justify="center").pack(pady=(4, 0))

        ctk.CTkButton(self.win, text="Los geht's!", width=160, height=40,
                      corner_radius=20, font=f_head, fg_color=PRIMARY,
                      hover_color=PRIMARY_HOVER, text_color=PRIMARY_TXT,
                      command=self._close).pack(pady=16)

        # eigener Mini-Recorder nur fuer die Pegelanzeige
        self.meter_rec = Recorder(cfg.get("device_index"))
        try:
            self.meter_rec.start()
        except Exception:
            self.level_label.configure(text="Mikrofon nicht verfügbar — bitte in den Einstellungen prüfen.")
            self.meter_rec = None
        self._tick()

        self.win.protocol("WM_DELETE_WINDOW", self._close)
        self.win.lift()
        self.win.focus_force()

    def _tick(self):
        if not self.win.winfo_exists():
            return
        if self.meter_rec is not None:
            self.meter.set(min(1.0, self.meter_rec.level * 1.4))
        self.win.after(60, self._tick)

    def _close(self):
        if self.meter_rec is not None:
            try:
                self.meter_rec.stop()
            except Exception:
                pass
            self.meter_rec = None
        self.app.cfg["first_run_done"] = True
        config.save(self.app.cfg)
        self.win.destroy()
