"""Nutzer-editierbare Regeln in einfachen Textdateien:

- ersetzungen.txt   feste Wortersetzungen nach jeder Transkription
- app-profile.txt   KI-Stil abhaengig von der aktiven Anwendung

Format jeweils:  links => rechts   (Zeilen mit # sind Kommentare)
Die Dateien werden beim ersten Zugriff mit Beispielen angelegt und bei
Aenderung (mtime) automatisch neu eingelesen.
"""
import re
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
RULES_FILE = APP_DIR / "ersetzungen.txt"
PROFILE_FILE = APP_DIR / "app-profile.txt"

DEFAULT_RULES = """# WisperMe – Wortersetzungen
# Eine Regel pro Zeile:   gesprochen => geschrieben
# Links ist Gross-/Kleinschreibung egal, ersetzt wird als ganzes Wort.
# Beispiele (zum Aktivieren das # am Zeilenanfang entfernen):
# wisper me => WisperMe
# physio praxis => Physio-Praxis
"""

DEFAULT_PROFILES = """# WisperMe – App-Profile fuer die KI-Glaettung
# Stil je nach aktiver Anwendung:   programm.exe => stil
# Moegliche Stile: neutral, professionell, locker, stichpunkte, email, aus
# ("aus" = Text wird in dieser App gar nicht geglaettet)
# Beispiele (zum Aktivieren das # am Zeilenanfang entfernen):
# outlook.exe => email
# thunderbird.exe => email
# discord.exe => locker
# whatsapp.exe => locker
# teams.exe => professionell
# code.exe => aus
"""

_cache = {}


def ensure_files() -> None:
    if not RULES_FILE.is_file():
        RULES_FILE.write_text(DEFAULT_RULES, encoding="utf-8")
    if not PROFILE_FILE.is_file():
        PROFILE_FILE.write_text(DEFAULT_PROFILES, encoding="utf-8")


def _parse(path: Path) -> dict:
    """Liest 'a => b'-Zeilen; Ergebnis wird per mtime gecacht."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}
    key = str(path)
    if key in _cache and _cache[key][0] == mtime:
        return _cache[key][1]
    rules = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=>" not in line:
                continue
            left, right = line.split("=>", 1)
            if left.strip():
                rules[left.strip()] = right.strip()
    except Exception:
        pass
    _cache[key] = (mtime, rules)
    return rules


def apply(text: str) -> str:
    """Wendet die Wortersetzungen auf einen transkribierten Text an."""
    if not text:
        return text
    ensure_files()
    for old, new in _parse(RULES_FILE).items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.IGNORECASE)
    return text


def style_for(exe_name: str, default: str) -> str:
    """KI-Stil fuer die aktive App laut app-profile.txt, sonst der Standard."""
    ensure_files()
    profiles = {k.lower(): v.lower() for k, v in _parse(PROFILE_FILE).items()}
    return profiles.get((exe_name or "").lower(), default)
