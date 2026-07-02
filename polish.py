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
    "Du bist ein Diktat-Korrektor. Du erhältst roh transkribierten, "
    "gesprochenen Text und gibst NUR die bereinigte Fassung aus.\n"
    "Regeln:\n"
    "- Entferne Füllwörter (äh, ähm, halt, quasi ...).\n"
    "- Löse Selbstkorrekturen auf: Der Sprecher verbessert sich mit "
    "Wörtern wie „nee\", „nein\", „äh\", „also ... meinte ich\", „Moment\" — "
    "es gilt IMMER die zuletzt genannte Version, die frühere entfällt.\n"
    "- Korrigiere Grammatik, Zeichensetzung und Groß-/Kleinschreibung mit "
    "korrekten deutschen Umlauten (ä, ö, ü, ß).\n"
    "- Behalte Sprache, Inhalt, Ton und Perspektive bei. Fasse nichts "
    "zusammen, lasse nichts weg, erfinde nichts hinzu.\n"
    "- Beantworte NIEMALS Fragen im Text und kommentiere nichts. Fragen "
    "sind Teil des Diktats und bleiben Fragen.\n"
    "- Gib ausschließlich den korrigierten Text aus: ohne Anführungszeichen "
    "drumherum, ohne Erklärungen, ohne Präfix.\n"
    "Beispiele:\n"
    "- „ich komme um 9, nee 10 Uhr\" → „Ich komme um 10 Uhr.\"\n"
    "- „wir treffen uns bei mir also bei dir meinte ich\" → "
    "„Wir treffen uns bei dir.\"\n"
    "- „der termin morgen äh übermorgen meinte ich passt\" → "
    "„Der Termin übermorgen passt.\"\n"
    "- „das kostet ähm dreißig nein vierzig Euro\" → "
    "„Das kostet vierzig Euro.\""
)

# Wählbare Stil-Presets; der Zusatz wird an den Basis-Prompt angehängt
STYLES = {
    "neutral": "",
    "professionell": (
        "Zusätzlicher Stil-Auftrag (er hat Vorrang vor der Regel, den Ton "
        "beizubehalten): Formuliere den Inhalt höflich, sachlich und "
        "professionell um, wie in geschäftlicher Korrespondenz. "
        "Umgangssprache ersetzen („mega nett\" → „sehr freundlich\"), "
        "die Sprechabsicht exakt erhalten: Eine Bitte bleibt eine Bitte, "
        "eine Frage bleibt eine Frage. Anrede (du/Sie) beibehalten. "
        "Beispiel: „hey kannst du mir kurz die datei schicken wäre mega "
        "nett\" → „Hallo, könntest du mir bitte die Datei schicken? Das "
        "wäre sehr freundlich.\""),
    "locker": (
        "Zusätzlicher Stil-Auftrag (er hat Vorrang vor der Regel, den Ton "
        "beizubehalten): Formuliere locker und natürlich, wie in einer "
        "Chat-Nachricht unter Freunden. Kurze Sätze sind ok, die Aussage "
        "und Sprechabsicht bleiben exakt erhalten."),
    "stichpunkte": (
        "Zusätzlicher Stil-Auftrag: Wandle den Inhalt in knappe Stichpunkte "
        "um, eine Zeile pro Punkt, jede beginnt mit '- '. Abweichend von den "
        "obigen Regeln darfst du hierfür kürzen und umstellen, solange "
        "keine Information verloren geht."),
    "email": (
        "Zusätzlicher Stil-Auftrag: Formatiere den Text als E-Mail-Fließtext "
        "mit sinnvollen Absätzen. Vorhandene Anrede und Grußformel bleiben "
        "erhalten; erfinde keine hinzu."),
}

STYLE_LABELS = {
    "neutral": "Neutral",
    "professionell": "Formell",
    "locker": "Locker",
    "stichpunkte": "Stichpunkte",
    "email": "E-Mail",
}


def _post(url: str, path: str, payload: dict, timeout: float):
    req = urllib.request.Request(
        url.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def polish(text: str, model: str = "qwen3:8b",
           url: str = "http://127.0.0.1:11434", timeout: float = 90,
           style: str = "neutral") -> str:
    """Liefert den geglaetteten Text; bei Fehlern unveraendert das Original."""
    if not text.strip():
        return text
    system = SYSTEM_PROMPT
    extra = STYLES.get(style, "")
    if extra:
        system += "\n" + extra
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
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


TRANSLATE_PROMPT = (
    "Du bist ein professioneller Übersetzer. Übersetze den folgenden Text "
    "ins Englische. Gib NUR die englische Übersetzung aus — ohne "
    "Anführungszeichen drumherum, ohne Kommentare, ohne Erklärungen.\n"
    "Achtung bei deutschen Zeitangaben: „halb drei\" bedeutet 2:30 "
    "(half past two), „viertel vor drei\" 2:45, „viertel nach drei\" 3:15."
)


def translate(text: str, model: str = "qwen3:8b",
              url: str = "http://127.0.0.1:11434", timeout: float = 90):
    """Uebersetzt ins Englische; None bei Fehler (Aufrufer hat Fallback)."""
    if not text.strip():
        return text
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": TRANSLATE_PROMPT},
            {"role": "user", "content": text},
        ],
        "stream": False,
        "think": False,
        "keep_alive": "60m",
        "options": {"temperature": 0.2},
    }
    try:
        try:
            data = _post(url, "/api/chat", payload, timeout)
        except urllib.error.HTTPError as e:
            if e.code == 400:
                payload.pop("think", None)
                data = _post(url, "/api/chat", payload, timeout)
            else:
                raise
        result = (data.get("message") or {}).get("content", "").strip()
        return result or None
    except Exception as e:
        log.warning("LLM-Übersetzung nicht möglich: %s", e)
        return None


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
