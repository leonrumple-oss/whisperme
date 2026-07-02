"""WisperMe – lokales Diktat im Wispr-Flow-Stil (Windows).

Globaler Hotkey -> Mikrofonaufnahme -> Whisper auf der GPU -> Text landet
im aktiven Fenster. Statusleiste am unteren Bildschirmrand, Tray-Icon,
Einstellungsfenster.
"""
import ctypes
import logging
import logging.handlers
import os
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import APP_DIR, FROZEN  # noqa: E402

try:
    os.chdir(APP_DIR)
except OSError:
    pass

# scharfe Darstellung und korrekte Koordinaten bei Windows-Skalierung
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

import tkinter as tk

import keyboard

import config
import injector
from audio import Recorder

log = logging.getLogger("wisperme")


def setup_logging():
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.handlers.RotatingFileHandler(
        APP_DIR / "wisperme.log", maxBytes=512_000, backupCount=1, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    log.addHandler(sh)


def ensure_single_instance() -> bool:
    ctypes.windll.kernel32.CreateMutexW(None, False, "WisperMe_SingleInstance")
    return ctypes.windll.kernel32.GetLastError() != 183  # ERROR_ALREADY_EXISTS


STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / \
    "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def set_autostart(enabled: bool):
    link = STARTUP_DIR / "WisperMe.vbs"
    try:
        if enabled:
            if FROZEN:
                cmd = f'WshShell.Run """{sys.executable}""", 0, False\n'
            else:
                pythonw = APP_DIR / ".venv" / "Scripts" / "pythonw.exe"
                cmd = f'WshShell.Run """{pythonw}"" ""{APP_DIR / "app.py"}""", 0, False\n'
            link.write_text(
                'Set WshShell = CreateObject("WScript.Shell")\n' + cmd,
                encoding="utf-8")
        elif link.is_file():
            link.unlink()
    except Exception:
        log.exception("Autostart-Eintrag konnte nicht geschrieben werden")


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = config.load()
        self.state = "loading"
        self.status_message = "Starte…"
        self.record_started = 0.0
        self._last_toggle = 0.0
        self._hotkey_handles = []
        self._rec_mode = "raw"  # "raw" = nur Diktat, "polish" = mit KI-Glaettung
        self._requests = queue.Queue()

        self.recorder = Recorder(self.cfg.get("device_index"))
        self.transcriber = None  # wird im Hintergrund initialisiert (Import ist teuer)
        self.tray = None

        self.bind_hotkey()
        threading.Thread(target=self._init_transcriber, daemon=True).start()
        if not self.cfg.get("first_run_done"):
            self.request("welcome")

    # ------------------------------------------------------------ Startphase

    def _init_transcriber(self):
        self.status_message = f"Lade Modell {self.cfg['model']}…"
        try:
            import hardware
            log.info("Hardware: %s", hardware.summary())
        except Exception:
            pass
        try:
            import transcriber as tr_mod
            self._tr_mod = tr_mod
            self.transcriber = tr_mod.Transcriber(self.cfg["model"])
            self.transcriber.ensure_loaded()
            if self.transcriber.device == "cpu":
                log.warning("Keine CUDA-GPU gefunden – laufe auf CPU (int8), langsamer!")
            if self.state == "loading":
                self.state = "idle"
            self.status_message = ""
        except Exception:
            log.exception("Modell konnte nicht geladen werden")
            self.status_message = "Fehler beim Laden – siehe wisperme.log"
        # Korrektur-Modell parallel in den VRAM holen, damit das erste
        # KI-Diktat nicht auf den Modellstart wartet
        if self.cfg.get("cleanup_enabled"):
            import polish
            threading.Thread(
                target=polish.warmup,
                args=(self.cfg.get("cleanup_model", "qwen3:8b"),
                      self.cfg.get("ollama_url", "http://127.0.0.1:11434")),
                daemon=True).start()

    # ---------------------------------------------------------------- Hotkey

    def bind_hotkey(self):
        self.unbind_hotkey()
        combos = [(self.cfg["hotkey"], "raw")]
        cleanup_combo = self.cfg.get("cleanup_hotkey", "")
        if self.cfg.get("cleanup_enabled") and cleanup_combo \
                and cleanup_combo != self.cfg["hotkey"]:
            combos.append((cleanup_combo, "polish"))
        translate_combo = self.cfg.get("translate_hotkey", "")
        if translate_combo and translate_combo not in [c for c, _ in combos]:
            combos.append((translate_combo, "translate"))
        for combo, mode in combos:
            try:
                handle = keyboard.add_hotkey(
                    combo, lambda m=mode, c=combo: self._on_hotkey(m, c))
                self._hotkey_handles.append(handle)
                log.info("Hotkey aktiv: %s (%s, %s)", combo,
                         self.cfg["hotkey_mode"], mode)
            except Exception:
                log.exception("Hotkey %r konnte nicht registriert werden", combo)

    def unbind_hotkey(self):
        for handle in self._hotkey_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._hotkey_handles = []

    def pause_hotkey(self):
        self.unbind_hotkey()

    def resume_hotkey(self):
        self.bind_hotkey()

    def _on_hotkey(self, mode="raw", combo=None):
        if self.cfg["hotkey_mode"] == "hold":
            if self.state == "idle":
                self.start_recording(mode)
                threading.Thread(target=self._hold_monitor,
                                 args=(combo or self.cfg["hotkey"],),
                                 daemon=True).start()
        else:
            # Tasten-Autorepeat feuert den Hotkey mehrfach -> entprellen
            now = time.time()
            if now - self._last_toggle < 0.8:
                return
            self._last_toggle = now
            self.toggle_recording(mode)

    def _hold_monitor(self, combo):
        try:
            while keyboard.is_pressed(combo):
                time.sleep(0.03)
        except Exception:
            time.sleep(0.5)
        if self.state == "recording":
            self.stop_recording()

    # ------------------------------------------------------------- Aufnahme

    def toggle_recording(self, mode="raw"):
        if self.state == "idle":
            self.start_recording(mode)
        elif self.state == "recording":
            self.stop_recording()

    def start_recording(self, mode="raw"):
        if self.state != "idle":
            return
        self._rec_mode = mode
        try:
            self.recorder.start()
        except Exception:
            log.exception("Mikrofon konnte nicht geoeffnet werden")
            return
        self.record_started = time.time()
        self.state = "recording"
        if self.tray:
            self.tray.set_recording(True)
        if float(self.cfg.get("auto_stop_silence") or 0) > 0:
            threading.Thread(target=self._silence_monitor, daemon=True).start()
        log.info("Aufnahme gestartet (%s)", mode)

    def _silence_monitor(self):
        """Stoppt die Aufnahme automatisch nach laengerer Stille."""
        while self.state == "recording":
            time.sleep(0.1)
            limit = float(self.cfg.get("auto_stop_silence") or 0)
            if limit <= 0:
                return
            if self.recorder.voice_seen and \
                    time.time() - self.recorder.last_voice > limit:
                log.info("Auto-Stopp: %.1fs Stille", limit)
                self.stop_recording()
                return

    def stop_recording(self):
        if self.state != "recording":
            return
        audio_data = self.recorder.stop()
        if self.tray:
            self.tray.set_recording(False)
        if len(audio_data) < 16000 * 0.3:  # kuerzer als 0,3 s -> verwerfen
            self.state = "idle"
            return
        self.state = "transcribing"
        threading.Thread(target=self._transcribe_worker,
                         args=(audio_data, self._rec_mode),
                         daemon=True).start()

    def _transcribe_worker(self, audio_data, mode):
        try:
            # Falls das Modell noch laedt, kurz warten
            for _ in range(600):
                if self.transcriber is not None:
                    break
                time.sleep(0.1)
            if self.transcriber is None:
                raise RuntimeError("Transcriber nicht initialisiert")
            text = self.transcriber.transcribe(
                audio_data,
                language=self.cfg["language"],
                beam_size=self.cfg.get("beam_size", 5),
                initial_prompt=self.cfg.get("initial_prompt", ""),
                task="translate" if mode == "translate" else "transcribe",
            )
            import textrules
            text = textrules.apply(text)
            if text and mode == "polish" and self.cfg.get("cleanup_enabled"):
                # Stil ggf. anhand der aktiven App waehlen (app-profile.txt)
                import winapp
                style = textrules.style_for(
                    winapp.get_foreground_exe(),
                    self.cfg.get("cleanup_style", "neutral"))
                if style != "aus":
                    self.state = "polishing"
                    import polish
                    t0 = time.time()
                    text = polish.polish(
                        text,
                        model=self.cfg.get("cleanup_model", "qwen3:8b"),
                        url=self.cfg.get("ollama_url", "http://127.0.0.1:11434"),
                        style=style,
                    )
                    log.info("KI-Glaettung (%s) in %.2fs: %r", style,
                             time.time() - t0,
                             text[:80] + ("..." if len(text) > 80 else ""))
            if text:
                injector.inject(
                    text,
                    mode=self.cfg.get("paste_mode", "paste"),
                    append_space=self.cfg.get("append_space", True),
                    restore_clipboard=self.cfg.get("restore_clipboard", True),
                )
                import history
                history.add(text, {"raw": "Diktat", "polish": "KI",
                                   "translate": "EN"}.get(mode, "Diktat"))
        except Exception:
            log.exception("Transkription fehlgeschlagen")
        finally:
            self.state = "idle"

    # ---------------------------------------------- Anfragen aus Fremdthreads

    def request(self, what):
        """Aus Tray-/Hotkey-Threads aufrufbar; abgearbeitet im Tk-Thread."""
        self._requests.put(what)

    def process_ui_requests(self):
        """Laeuft im Tk-Thread (Overlay-Tick)."""
        try:
            while True:
                req = self._requests.get_nowait()
                if req == "settings":
                    self._open_settings()
                elif req == "quit":
                    self.quit()
                elif req == "history":
                    import history_ui
                    history_ui.HistoryWindow(self.root, self)
                elif req == "welcome":
                    import welcome_ui
                    welcome_ui.WelcomeWindow(self.root, self)
                elif isinstance(req, tuple) and req[0] == "model":
                    self._change_model(req[1])
                elif isinstance(req, tuple) and req[0] == "style":
                    self.cfg["cleanup_style"] = req[1]
                    config.save(self.cfg)
        except queue.Empty:
            pass

    def _open_settings(self):
        import settings_ui
        settings_ui.SettingsWindow(self.root, self)

    def _change_model(self, name):
        if self.state in ("recording", "transcribing"):
            log.info("Modellwechsel verschoben – gerade beschaeftigt")
            return
        self.cfg["model"] = name
        config.save(self.cfg)
        self.state = "loading"
        self.status_message = f"Lade Modell {name}…"

        def worker():
            try:
                if self.transcriber:
                    self.transcriber.switch_model(name)
            except Exception:
                log.exception("Modellwechsel fehlgeschlagen")
            finally:
                self.status_message = ""
                self.state = "idle"

        threading.Thread(target=worker, daemon=True).start()

    def apply_settings(self, new_cfg):
        old = self.cfg
        hotkey_keys = ("hotkey", "hotkey_mode", "cleanup_hotkey",
                       "cleanup_enabled", "translate_hotkey")
        self.cfg = new_cfg
        config.save(new_cfg)
        self.recorder.device_index = new_cfg.get("device_index")
        if any(new_cfg.get(k) != old.get(k) for k in hotkey_keys):
            self.bind_hotkey()
        set_autostart(new_cfg.get("autostart", False))
        if new_cfg["model"] != old["model"]:
            self._change_model(new_cfg["model"])
        if new_cfg.get("cleanup_enabled") and \
                new_cfg.get("cleanup_model") != old.get("cleanup_model"):
            import polish
            threading.Thread(
                target=polish.warmup,
                args=(new_cfg["cleanup_model"], new_cfg.get("ollama_url")),
                daemon=True).start()
        log.info("Einstellungen gespeichert")

    def quit(self):
        log.info("Beende WisperMe")
        try:
            if self.state == "recording":
                self.recorder.stop()
            keyboard.unhook_all()
        except Exception:
            pass
        if self.tray:
            self.tray.stop()
        self.root.destroy()


def main():
    setup_logging()
    if not ensure_single_instance():
        ctypes.windll.user32.MessageBoxW(
            None, "WisperMe läuft bereits (siehe Tray-Icon).", "WisperMe", 0x40)
        return
    log.info("WisperMe startet (Python %s)", sys.version.split()[0])

    root = tk.Tk()
    app = App(root)

    from overlay import OverlayBar
    OverlayBar(root, app)

    from tray import Tray
    app.tray = Tray(app)
    app.tray.start()

    try:
        root.mainloop()
    finally:
        os._exit(0)  # Tray-/Audio-Threads sicher beenden


if __name__ == "__main__":
    main()
