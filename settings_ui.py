"""Einstellungsfenster im modernen Karten-Design (customtkinter).

Alle Aenderungen wirken SOFORT: Jedes Steuerelement ruft _apply() auf, das
die Konfiguration speichert und in der laufenden App anwendet (Hotkeys,
Theme der Leiste, Modellwechsel ...). Einen Speichern-Knopf gibt es nicht.
"""
import threading
import tkinter as tk

import customtkinter as ctk
import keyboard

import audio
import polish
import transcriber
from overlay import pretty_hotkey

WINBG = ("#ececef", "#17171d")
CARD = ("#ffffff", "#23232c")
TXT = ("#1b1b22", "#ececf2")
SUB = ("#8a8a96", "#9a9aa8")
FIELD = ("#f3f3f6", "#2d2d38")
FIELD_HOVER = ("#e7e7ec", "#383844")
PRIMARY = ("#1a1a1f", "#e8e8f0")
PRIMARY_HOVER = ("#31313a", "#cfcfd8")
PRIMARY_TXT = ("#ffffff", "#17171d")
BORDER = ("#e2e2e9", "#3a3a46")

MODEL_LABELS = {
    "large-v3-turbo": "Large v3 Turbo · empfohlen (1,6 GB)",
    "large-v3": "Large v3 · max. Genauigkeit (3,1 GB)",
    "medium": "Medium · gut (1,5 GB)",
    "small": "Small · schnell & einfach (0,5 GB)",
    "base": "Base · minimal (0,15 GB)",
    "tiny": "Tiny · winzig (0,08 GB)",
}
LANG_LABELS = {"de": "Deutsch", "auto": "Automatisch", "en": "Englisch"}
MODE_LABELS = {"toggle": "Umschalten", "hold": "Halten (PTT)"}
THEME_LABELS = {"light": "Hell", "dark": "Dunkel"}

DWMWA_USE_IMMERSIVE_DARK_MODE = 20


class SettingsWindow:
    def __init__(self, root: tk.Tk, app):
        self.app = app
        cfg = app.cfg
        self._building = True  # unterdrueckt _apply waehrend des Aufbaus
        ctk.set_appearance_mode("dark" if cfg.get("theme") == "dark" else "light")

        self.win = ctk.CTkToplevel(root)
        self.win.title("WisperMe – Einstellungen")
        self.win.geometry("640x760")
        self.win.minsize(560, 420)
        self.win.resizable(True, True)
        self.win.configure(fg_color=WINBG)
        self.win.attributes("-topmost", True)

        self.f_title = ctk.CTkFont("Segoe UI", 22, "bold")
        self.f_card = ctk.CTkFont("Segoe UI", 14, "bold")
        self.f_label = ctk.CTkFont("Segoe UI", 13)
        self.f_small = ctk.CTkFont("Segoe UI", 11)

        outer = ctk.CTkScrollableFrame(self.win, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=18, pady=(14, 0))

        # ---------------------------------------------------------- Kopfzeile
        head = ctk.CTkFrame(outer, fg_color="transparent")
        head.pack(fill="x", pady=(2, 12))
        ctk.CTkLabel(head, text="✦  WisperMe", font=self.f_title,
                     text_color=TXT).pack(side="left")
        ctk.CTkLabel(head, text="lokales Diktat · Änderungen wirken sofort",
                     font=self.f_small, text_color=SUB
                     ).pack(side="left", padx=(10, 0), pady=(8, 0))

        # ------------------------------------------------------ Karte Aufnahme
        card = self._card(outer, "Aufnahme")
        row = self._row(card, "Shortcut")
        self.hotkey_var = tk.StringVar(value=cfg["hotkey"])
        self.hotkey_chip = ctk.CTkLabel(
            row, text=pretty_hotkey(cfg["hotkey"]), font=self.f_label,
            text_color=TXT, fg_color=FIELD, corner_radius=8, padx=14, pady=5)
        self.hotkey_chip.pack(side="left", padx=(14, 0))
        self.capture_btn = ctk.CTkButton(
            row, text="Ändern…", width=92, height=30, corner_radius=15,
            font=self.f_label, fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            text_color=PRIMARY_TXT,
            command=lambda: self._capture(self.hotkey_chip, self.capture_btn,
                                          self.hotkey_var))
        self.capture_btn.pack(side="right")

        row = self._row(card, "Modus")
        self.mode_seg = self._segment(row, list(MODE_LABELS.values()),
                                      MODE_LABELS.get(cfg["hotkey_mode"], "Umschalten"))
        self.mode_seg.pack(side="right")

        # ---------------------------------------------------- Karte Erkennung
        card = self._card(outer, "Erkennung")
        row = self._row(card, "Modell")
        values = []
        for name, label in MODEL_LABELS.items():
            if not transcriber.is_model_downloaded(name):
                label += "  ↓"
            values.append(label)
        current = values[list(MODEL_LABELS).index(cfg["model"])] \
            if cfg["model"] in MODEL_LABELS else values[0]
        self.model_menu = self._dropdown(row, values, current, width=330)
        self.model_menu.pack(side="right")
        ctk.CTkLabel(card, text="↓ = wird beim ersten Einsatz automatisch heruntergeladen",
                     font=self.f_small, text_color=SUB).pack(anchor="e", padx=18)

        row = self._row(card, "Sprache")
        self.lang_seg = self._segment(row, list(LANG_LABELS.values()),
                                      LANG_LABELS.get(cfg["language"], "Deutsch"))
        self.lang_seg.pack(side="right")

        row = self._row(card, "Mikrofon")
        self.devices = audio.list_input_devices()
        dev_values = [name for _, name in self.devices]
        current_dev = dev_values[0]
        for idx, name in self.devices:
            if idx == cfg.get("device_index"):
                current_dev = name
        self.device_menu = self._dropdown(row, dev_values, current_dev, width=330)
        self.device_menu.pack(side="right")

        row = self._row(card, "Eigene Begriffe")
        self.prompt_entry = ctk.CTkEntry(
            row, width=330, height=30, corner_radius=8, font=self.f_label,
            fg_color=FIELD, border_color=BORDER, border_width=1, text_color=TXT,
            placeholder_text="Namen, Fachwörter … (kommagetrennt)")
        self.prompt_entry.insert(0, cfg.get("initial_prompt", ""))
        self.prompt_entry.pack(side="right")
        # Freitext: uebernehmen beim Verlassen des Felds oder mit Enter
        self.prompt_entry.bind("<FocusOut>", lambda e: self._apply())
        self.prompt_entry.bind("<Return>", lambda e: self._apply())

        # -------------------------------------------- Karte KI-Nachbearbeitung
        card = self._card(outer, "KI-Nachbearbeitung")
        ctk.CTkLabel(card, text="Zweiter Shortcut: Diktat wird nach der Transkription lokal\n"
                     "geglättet — Selbstkorrekturen, Füllwörter, Grammatik (via Ollama).",
                     font=self.f_small, text_color=SUB, justify="left"
                     ).pack(anchor="w", padx=18)
        row = self._row(card, "Aktiv")
        self.cleanup_switch = self._switch(row, cfg.get("cleanup_enabled", False))

        row = self._row(card, "Shortcut KI-Diktat")
        self.cleanup_hotkey_var = tk.StringVar(value=cfg.get("cleanup_hotkey", ""))
        self.cleanup_chip = ctk.CTkLabel(
            row, text=pretty_hotkey(cfg.get("cleanup_hotkey", "")) or "—",
            font=self.f_label, text_color=TXT, fg_color=FIELD,
            corner_radius=8, padx=14, pady=5)
        self.cleanup_chip.pack(side="left", padx=(14, 0))
        self.cleanup_capture_btn = ctk.CTkButton(
            row, text="Ändern…", width=92, height=30, corner_radius=15,
            font=self.f_label, fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
            text_color=PRIMARY_TXT,
            command=lambda: self._capture(self.cleanup_chip,
                                          self.cleanup_capture_btn,
                                          self.cleanup_hotkey_var))
        self.cleanup_capture_btn.pack(side="right")

        row = self._row(card, "Sprachmodell")
        ollama_models = polish.list_models(cfg.get("ollama_url", "http://127.0.0.1:11434"))
        current_llm = cfg.get("cleanup_model", "qwen3:8b")
        if current_llm not in ollama_models:
            ollama_models = [current_llm] + ollama_models
        self.cleanup_model_menu = self._dropdown(row, ollama_models, current_llm,
                                                 width=330)
        self.cleanup_model_menu.pack(side="right")

        # ------------------------------------------------------- Karte System
        card = self._card(outer, "Darstellung & System")
        row = self._row(card, "Design")
        self.theme_seg = self._segment(row, list(THEME_LABELS.values()),
                                       THEME_LABELS.get(cfg.get("theme", "light"), "Hell"))
        self.theme_seg.pack(side="right")

        row = self._row(card, "Leiste im Leerlauf anzeigen")
        self.idle_switch = self._switch(row, cfg.get("show_idle_bar", True))
        row = self._row(card, "Mit Windows starten")
        self.autostart_switch = self._switch(row, cfg.get("autostart", False))

        # ------------------------------------------------------------- Footer
        footer = ctk.CTkFrame(self.win, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=12)
        ctk.CTkButton(footer, text="Schließen", width=120, height=34,
                      corner_radius=17, font=self.f_label, fg_color=PRIMARY,
                      hover_color=PRIMARY_HOVER, text_color=PRIMARY_TXT,
                      command=self.win.destroy).pack(side="right")

        self._building = False
        self._set_titlebar_dark(cfg.get("theme") == "dark")
        self.win.lift()
        self.win.focus_force()

    # ------------------------------------------------------------ UI-Bausteine

    def _card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=16)
        card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(card, text=title, font=self.f_card, text_color=TXT
                     ).pack(anchor="w", padx=18, pady=(14, 2))
        return card

    def _row(self, card, label):
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=7)
        ctk.CTkLabel(row, text=label, font=self.f_label, text_color=TXT
                     ).pack(side="left")
        return row

    def _segment(self, row, values, current):
        seg = ctk.CTkSegmentedButton(
            row, values=values, height=30, corner_radius=15,
            font=self.f_small, fg_color=FIELD,
            selected_color=("#ffffff", "#4a4a58"),
            selected_hover_color=("#f2f2f7", "#565664"),
            unselected_color=FIELD, unselected_hover_color=FIELD_HOVER,
            text_color=TXT, text_color_disabled=SUB,
            command=lambda _value: self._apply())
        seg.set(current)
        return seg

    def _dropdown(self, row, values, current, width=300):
        menu = ctk.CTkOptionMenu(
            row, values=values, width=width, height=30, corner_radius=8,
            font=self.f_label, dropdown_font=self.f_label,
            fg_color=FIELD, button_color=FIELD, button_hover_color=FIELD_HOVER,
            text_color=TXT, dropdown_fg_color=CARD, dropdown_text_color=TXT,
            dropdown_hover_color=FIELD,
            command=lambda _value: self._apply())
        menu.set(current)
        return menu

    def _switch(self, row, value):
        sw = ctk.CTkSwitch(row, text="", width=46, progress_color=PRIMARY,
                           fg_color=FIELD_HOVER, button_color=("#ffffff", "#17171d"),
                           command=self._apply)
        if value:
            sw.select()
        sw.pack(side="right")
        return sw

    def _set_titlebar_dark(self, dark: bool):
        """Windows-11-Titelleiste dem Theme anpassen."""
        try:
            import ctypes
            self.win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.win.winfo_id())
            value = ctypes.c_int(1 if dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

    # --------------------------------------------------------------- Aktionen

    def _capture(self, chip, btn, var):
        btn.configure(state="disabled")
        chip.configure(text="Tasten drücken…")
        self.app.pause_hotkey()

        def worker():
            try:
                combo = keyboard.read_hotkey(suppress=False)
            except Exception:
                combo = var.get()

            def apply():
                var.set(combo)
                chip.configure(text=pretty_hotkey(combo))
                btn.configure(state="normal")
                self.app.resume_hotkey()
                self._apply()  # neuer Shortcut gilt sofort
            self.win.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self):
        """Sammelt alle Werte ein und wendet sie sofort auf die App an."""
        if self._building:
            return
        new = dict(self.app.cfg)
        new["hotkey"] = self.hotkey_var.get()
        new["hotkey_mode"] = self._rev(MODE_LABELS, self.mode_seg.get(), "toggle")
        model_label = self.model_menu.get().replace("  ↓", "")
        new["model"] = self._rev(MODEL_LABELS, model_label, new["model"])
        new["language"] = self._rev(LANG_LABELS, self.lang_seg.get(), "de")
        new["theme"] = self._rev(THEME_LABELS, self.theme_seg.get(), "light")
        for idx, name in self.devices:
            if name == self.device_menu.get():
                new["device_index"] = idx
        new["initial_prompt"] = self.prompt_entry.get()
        new["show_idle_bar"] = bool(self.idle_switch.get())
        new["autostart"] = bool(self.autostart_switch.get())
        new["cleanup_enabled"] = bool(self.cleanup_switch.get())
        new["cleanup_hotkey"] = self.cleanup_hotkey_var.get()
        new["cleanup_model"] = self.cleanup_model_menu.get()

        theme_changed = new["theme"] != self.app.cfg.get("theme")
        self.app.apply_settings(new)

        if theme_changed:
            self._switch_theme(new["theme"])

    def _switch_theme(self, theme: str):
        """Wechselt Hell/Dunkel ohne sichtbares Element-fuer-Element-Geflacker.

        customtkinter faerbt beim Moduswechsel jedes Widget einzeln um.
        Eine deckende Flaeche in der Zielfarbe verdeckt diesen Umbau und
        blendet danach in wenigen Schritten weich aus.
        """
        dark = theme == "dark"
        target_bg = WINBG[1] if dark else WINBG[0]

        cover = tk.Frame(self.win, bg=target_bg)
        cover.place(x=0, y=0, relwidth=1, relheight=1)
        cover.lift()
        self.win.update_idletasks()

        ctk.set_appearance_mode("dark" if dark else "light")
        self._set_titlebar_dark(dark)

        # kurz warten bis alle Widgets umgefaerbt sind, dann weich aufdecken
        def reveal(step=0):
            if step >= 4:
                cover.destroy()
                return
            # Ausblenden ueber schrumpfende Hoehe (Tk kann keine Teiltransparenz)
            cover.place_configure(relheight=1 - step * 0.25)
            self.win.after(30, lambda: reveal(step + 1))

        self.win.after(160, reveal)

    @staticmethod
    def _rev(mapping, label, default):
        for key, val in mapping.items():
            if val == label:
                return key
        return default
