"""Diktat-Verlauf: die letzten Diktate lokal in history.json (max. 50)."""
import json
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PATH = APP_DIR / "history.json"
MAX_ENTRIES = 50


def load() -> list:
    try:
        return json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def add(text: str, mode: str) -> None:
    if not text.strip():
        return
    items = load()
    items.insert(0, {
        "zeit": time.strftime("%d.%m.%Y %H:%M"),
        "modus": mode,
        "text": text.strip(),
    })
    del items[MAX_ENTRIES:]
    try:
        PATH.write_text(json.dumps(items, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    except Exception:
        pass


def clear() -> None:
    try:
        PATH.unlink(missing_ok=True)
    except Exception:
        pass
