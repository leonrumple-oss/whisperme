"""KI-Nachbearbeitung: glaettet diktierten Text ueber ein lokales Ollama-Modell.

Selbstkorrekturen ("um 9, nee 10 Uhr" -> "um 10 Uhr"), Fuellwoerter und
Grammatik werden bereinigt. Faellt bei jedem Fehler auf den Rohtext zurueck,
damit ein Diktat nie verloren geht.
"""
import json
import logging
import urllib.request

log = logging.getLogger("wisperme")

SYSTEM_PROMPT = (
    "Du bist ein Diktat-Korrektor. Du erhaeltst roh transkribierten, "
    "gesprochenen Text und gibst NUR die bereinigte Fassung aus.\n"
    "Regeln:\n"
    "- Entferne Fuellwoerter (aeh, aehm, halt, quasi ...).\n"
    "- Loese Selbstkorrekturen auf: Der Sprecher verbessert sich mit "
    "Woertern wie \"nee\", \"nein\", \"also ... meinte ich\", \"Moment\" — "
    "es gilt IMMER die zuletzt genannte Version, die fruehere entfaellt.\n"
    "- Korrigiere Grammatik, Zeichensetzung und Gross-/Kleinschreibung.\n"
    "- Behalte Sprache, Inhalt, Ton und Perspektive bei. Fasse nichts "
    "zusammen, lasse nichts weg, erfinde nichts hinzu.\n"
    "- Beantworte NIEMALS Fragen im Text und kommentiere nichts. Fragen "
    "sind Teil des Diktats und bleiben Fragen.\n"
    "- Gib ausschliesslich den korrigierten Text aus: ohne Anfuehrungszeichen "
    "drumherum, ohne Erklaerungen, ohne Praefix.\n"
    "Beispiele:\n"
    "- \"ich komme um 9, nee 10 Uhr\" -> \"Ich komme um 10 Uhr.\"\n"
    "- \"wir treffen uns bei mir also bei dir meinte ich\" -> "
    "\"Wir treffen uns bei dir.\"\n"
    "- \"das kostet aehm dreissig nein vierzig Euro\" -> "
    "\"Das kostet vierzig Euro.\""
)


def _post(url: str, path: str, payload: dict, timeout: float):
    req = urllib.request.Request(
        url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def polish(text: str, model: str = "qwen3:8b",
           url: str = "http://127.0.0.1:11434", timeout: float = 90) -> str:
    """Liefert den geglaetteten Text; bei Fehlern unveraendert das Original."""
    if not text.strip():
        return text
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "stream": False,
        "think": False,  # Qwen3 & Co: Denkmodus aus -> schnelle Antwort
        "keep_alive": "60m",
        "options": {"temperature": 0.2},
    }
    try:
        try:
            data = _post(url, "/api/chat", payload, timeout)
        except urllib.error.HTTPError as e:
            # Modelle ohne Denkmodus lehnen den "think"-Parameter mitunter ab
            if e.code == 400:
                payload.pop("think", None)
                data = _post(url, "/api/chat", payload, timeout)
            else:
                raise
        result = (data.get("message") or {}).get("content", "").strip()
        if not result:
            return text
        return result
    except Exception:
        log.exception("KI-Nachbearbeitung fehlgeschlagen – nutze Rohtext")
        return text


def ensure_server(url: str = "http://127.0.0.1:11434") -> bool:
    """Prueft ob Ollama laeuft und startet es sonst unsichtbar."""
    import os
    import subprocess
    import time as _time

    def alive() -> bool:
        try:
            req = urllib.request.Request(url.rstrip("/") + "/api/version")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False

    if alive():
        return True
    exe = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                       "Programs", "Ollama", "ollama.exe")
    if not os.path.isfile(exe):
        log.warning("Ollama nicht gefunden (%s)", exe)
        return False
    try:
        subprocess.Popen([exe, "serve"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
        log.info("Ollama-Server gestartet")
    except Exception:
        log.exception("Ollama-Server konnte nicht gestartet werden")
        return False
    for _ in range(30):
        if alive():
            return True
        _time.sleep(0.5)
    return False


def warmup(model: str, url: str = "http://127.0.0.1:11434") -> None:
    """Laedt das Modell in den VRAM, damit das erste Diktat nicht wartet."""
    try:
        if not ensure_server(url):
            return
        _post(url, "/api/generate",
              {"model": model, "prompt": "", "keep_alive": "60m"}, timeout=180)
        log.info("Korrektur-Modell %s vorgeladen", model)
    except Exception as e:
        log.warning("Korrektur-Modell %s nicht vorladbar: %s", model, e)


def list_models(url: str = "http://127.0.0.1:11434") -> list:
    """Namen der lokal installierten Ollama-Modelle (leer bei Fehler)."""
    try:
        req = urllib.request.Request(url.rstrip("/") + "/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []
