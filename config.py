"""Laden und Speichern der Einstellungen (config.json im App-Ordner)."""
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"

DEFAULTS = {
    "hotkey": "ctrl+alt+space",   # globaler Shortcut
    "hotkey_mode": "toggle",      # "toggle" = einmal druecken an/aus, "hold" = gedrueckt halten
    "model": "large-v3-turbo",
    "language": "de",             # "auto", "de", "en", ...
    "device_index": None,         # None = Windows-Standardmikrofon
    "paste_mode": "paste",        # "paste" = ueber Zwischenablage, "type" = Zeichen tippen
    "append_space": True,         # Leerzeichen ans Ende des diktierten Texts anhaengen
    "restore_clipboard": True,    # alte Zwischenablage nach dem Einfuegen wiederherstellen
    "show_idle_bar": True,        # Leiste auch im Leerlauf anzeigen
    "theme": "light",             # Design der Leiste: "light" oder "dark"
    "beam_size": 5,
    "initial_prompt": "",         # optionale Wortliste/Kontext fuer bessere Erkennung
    "autostart": False,
    # KI-Nachbearbeitung (zweiter Hotkey): Diktat wird nach der Transkription
    # von einem lokalen Ollama-Modell grammatikalisch geglaettet
    "cleanup_enabled": True,
    "cleanup_hotkey": "ctrl+alt+enter",
    "cleanup_model": "qwen3:8b",
    "ollama_url": "http://127.0.0.1:11434",
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.is_file():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except Exception:
            pass
        return cfg
    # Erster Start auf dieser Maschine: Modell passend zur Hardware waehlen
    # und die KI-Glaettung nur aktivieren, wenn Ollama vorhanden ist
    try:
        import hardware
        cfg["model"] = hardware.recommend_model()
        cfg["cleanup_enabled"] = hardware.ollama_available()
    except Exception:
        pass
    save(cfg)
    return cfg


def save(cfg: dict) -> None:
    data = {k: cfg.get(k, v) for k, v in DEFAULTS.items()}
    CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
