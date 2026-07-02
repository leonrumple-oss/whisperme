# WisperMe — lokales Diktat für Windows (Wispr-Flow-Stil)

Diktieren per globalem Shortcut in **jede** App: Hotkey drücken, sprechen, Hotkey
erneut drücken — der Text erscheint im aktiven Fenster. Läuft **komplett lokal**
(Whisper auf GPU oder CPU), kein Audio verlässt den Rechner.

**Features**

- 🎙️ Globaler, frei wählbarer Shortcut (Umschalten oder Push-to-Talk)
- 📊 Statusleiste am unteren Bildschirmrand mit Live-Wellenform (Hell/Dunkel)
- 🧠 Auswahl zwischen 6 Whisper-Modellen — automatische Empfehlung passend zur Hardware
- ✨ Optionale KI-Nachbearbeitung über zweiten Shortcut: Grammatik, Füllwörter
  und Selbstkorrekturen („ich komme um 9, nee 10 Uhr" → „Ich komme um 10 Uhr.")
  werden lokal per Ollama geglättet — mit wählbaren **Stilen** (Neutral, Formell,
  Locker, Stichpunkte, E-Mail)
- 🪟 **App-Profile**: KI-Stil automatisch je nach aktiver Anwendung
  (Outlook → E-Mail-Stil, Discord → locker, Editor → aus)
- 🌍 **Übersetzungs-Shortcut**: Deutsch (oder jede andere Sprache) diktieren,
  englischer Text wird eingefügt
- 🕘 **Verlauf** der letzten 50 Diktate (nur lokal), jederzeit erneut kopierbar
- 🔇 **Auto-Stopp bei Stille** (optional): Aufnahme endet freihändig
- 📖 **Wortersetzungen**: eigene Fachwörter/Namen werden zuverlässig korrigiert
- 👋 Erste-Schritte-Assistent mit Mikrofon-Test beim ersten Start
- ⚡ Auf einer RTX 4090: 1 Minute Diktat in ~0,5 s transkribiert
- 🖥️ System-Tray, Einstellungs-App im modernen Karten-Design, Autostart-Option

## Installation

Voraussetzungen: Windows 10/11, [Python 3.10+](https://www.python.org/downloads/)
(beim Installieren „Add python.exe to PATH" anhaken). Eine NVIDIA-GPU ist
empfehlenswert, aber nicht nötig — ohne GPU läuft WisperMe auf der CPU.

```
git clone https://github.com/<user>/wisperme
cd wisperme
install.bat
```

`install.bat` richtet die virtuelle Umgebung ein, installiert alle Abhängigkeiten,
prüft die Hardware und legt eine Desktop-Verknüpfung an. Beim ersten Start wählt
WisperMe automatisch das passende Whisper-Modell:

| Hardware | gewähltes Modell |
|---|---|
| NVIDIA-GPU ab 4 GB VRAM | large-v3-turbo (beste Qualität, sehr schnell) |
| NVIDIA-GPU 2,5–4 GB | small |
| nur CPU, ab 8 Kerne | small (int8) |
| schwächere CPU | base (int8) |

Das Modell wird beim ersten Start automatisch heruntergeladen (large-v3-turbo:
~1,6 GB). Jederzeit änderbar in den Einstellungen.

## Starten

- **Desktop:** Doppelklick auf die Verknüpfung **WisperMe** (Mikrofon-Icon)
- **Ohne Konsole (direkt):** Doppelklick auf `WisperMe starten.vbs`
- **Mit Konsole (Fehlersuche):** `WisperMe mit Konsole (Debug).bat`

Beim Start erscheint unten mittig die Statusleiste und ein Mikrofon-Icon im
System-Tray (ggf. hinter dem Pfeil „ausgeblendete Symbole" — von dort neben die
Uhr ziehen). Bei laufender Aufnahme wird das Tray-Icon rot.

## Bedienung

| Aktion | Wie |
|---|---|
| Diktat starten/stoppen | Standard-Shortcut **Strg+Alt+Leertaste** (änderbar) oder Klick auf die Leiste |
| Diktat mit KI-Glättung | **Strg+Alt+Enter** (änderbar) |
| Diktat → englische Übersetzung | **Strg+Alt+T** (änderbar) |
| Verlauf der letzten Diktate | Rechtsklick Tray-Icon → „Verlauf…" |
| KI-Stil wechseln | Rechtsklick Tray-Icon → „KI-Stil" oder Einstellungen |
| Einstellungen | Rechtsklick auf das Tray-Icon → „Einstellungen…" |
| Modell schnell wechseln | Rechtsklick Tray-Icon → „Modell" |
| Beenden | Rechtsklick Tray-Icon → „Beenden" |

Die Leiste zeigt den Zustand:
**Grün** = bereit · **Rot + Wellenform + Timer** = Aufnahme läuft ·
**Gelb** = transkribiert · **Violett** = KI formuliert · **Blau** = Modell lädt.

## KI-Nachbearbeitung (optional)

Mit dem zweiten Shortcut diktierst du wie gewohnt — zusätzlich glättet danach
ein lokales Sprachmodell den Text:

- Selbstkorrekturen werden aufgelöst: „ich komme um 9, nee 10 Uhr" → „Ich komme um 10 Uhr."
- Füllwörter (äh, ähm, halt …) fliegen raus
- Grammatik, Groß-/Kleinschreibung und Zeichensetzung werden korrigiert
- Fragen im Text bleiben Fragen — das Modell antwortet nie

Dafür wird [Ollama](https://ollama.com) benötigt (`winget install Ollama.Ollama`,
danach `ollama pull qwen3:8b`). Ist Ollama nicht installiert, bleibt die Funktion
automatisch deaktiviert — normales Diktieren funktioniert immer. Schlägt die
Glättung fehl, wird der Rohtext eingefügt; ein Diktat geht nie verloren.
WisperMe startet den Ollama-Server bei Bedarf selbst und lädt das
Korrektur-Modell beim App-Start vor (auf einer RTX 4090: ~0,3–0,5 s pro Diktat).

## Einstellungen

- **Shortcut:** frei wählbar (auf „Ändern…" klicken, Kombination drücken)
- **Aufnahmemodus:** Umschalten (an/aus) oder Halten (Push-to-Talk)
- **Modell:** 6 Whisper-Varianten, Download automatisch beim ersten Einsatz
- **Sprache:** Deutsch, Englisch oder automatische Erkennung
- **Mikrofon:** Auswahl des Eingabegeräts
- **Eigene Begriffe:** Namen/Fachwörter, die häufig vorkommen — verbessert die Erkennung
- **KI-Nachbearbeitung:** ein/aus, eigener Shortcut, Ollama-Modellauswahl
- **Design:** Hell oder Dunkel (Leiste + Einstellungsfenster)
- **Mit Windows starten:** legt einen Autostart-Eintrag an

**Alle Änderungen wirken sofort** — es gibt keinen Speichern-Knopf. Alles wird
automatisch in `config.json` gespeichert. Das Fenster ist frei skalierbar.

## Welches Modell für welche Hardware?

`MODELL-ANALYSE.md` enthält eine Beispielmessung (RTX 4090, 92 s deutsches
Diktat). Kurzfassung: Auf GPUs ist **large-v3-turbo** die beste Wahl — es ist
dort schneller als „small" und fast so genau wie large-v3. Eigene Werte misst
du mit:

```
.venv\Scripts\python benchmark.py <eigene-audiodatei.wav>
```

## Technik

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2),
  CUDA float16 auf NVIDIA-GPUs, CPU-Fallback int8 — Erkennung automatisch
- Diktate über ~20 s laufen über die gebatchte Pipeline (deutlich schneller)
- Text-Einfügen über die Zwischenablage (Strg+V), die vorherige Zwischenablage
  wird wiederhergestellt; alternativ Tipp-Modus (`paste_mode: "type"`) für
  Programme, die kein Einfügen erlauben
- KI-Glättung: Ollama-API (`127.0.0.1:11434`), Standard-Modell `qwen3:8b`
- Overlay/Einstellungen: tkinter + customtkinter, Tray: pystray
- Python ≥ 3.10, alles in `.venv` — keine systemweiten Änderungen

## Lizenz

MIT — siehe [LICENSE](LICENSE).
