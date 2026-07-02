# Modell-Analyse für diesen PC

Gemessen am 02.07.2026 auf **deiner** Hardware (nicht geschätzt):
RTX 4090 (24 GB VRAM, CUDA float16), Ryzen 9 7900X3D, 32 GB RAM.
Testclip: 91,6 s deutsche Sprache (TTS), inkl. Fachbegriffen, Umlauten, Zahlen.
Messung mit `benchmark.py`, Rohdaten in `benchmark_results.json`.

## Geschwindigkeit

| Modell | Kurzer Satz (8 s Audio) | Langes Diktat (92 s Audio) | Echtzeitfaktor | Modell-Ladezeit |
|---|---|---|---|---|
| base | 0,17 s | 0,51 s | 178× | 1,0 s |
| small | 0,28 s | 0,83 s | 110× | 0,7 s |
| medium | 0,47 s | 1,49 s | 62× | 1,9 s |
| **large-v3-turbo** | **0,22 s** | **0,65 s** | **140×** | 2,1 s |
| large-v3 | 0,60 s | 1,94 s | 47× | 3,4 s |

## Qualität (gleicher Testclip)

- **base:** unbrauchbar für Deutsch — „Ich dikke Tiere gerade", „Prampz", „ländenwirbelsäule"
- **small:** verständlich, aber fehlerhaft — „Rüzen 9", „Text ticktiere", „Gonnathrose"
- **medium:** gut, kleine Patzer — „Text tiktiere", „Gonathrose"
- **large-v3-turbo:** praktisch fehlerfrei — sogar „Gonarthrose", „Lendenwirbelsäule" und
  „propriozeptive neuromuskuläre Fazilitation" korrekt ✔
- **large-v3:** ebenfalls praktisch fehlerfrei, aber ~3× langsamer als Turbo

## Empfehlung

**→ `large-v3-turbo` (ist als Standard eingestellt).**

Es ist auf deiner 4090 *schneller als small* und erreicht fast die Qualität von
large-v3 (Turbo ist ein destilliertes large-v3 mit 4 statt 32 Decoder-Schichten).
Deine Sorge „minutenlang warten bei langen Diktaten" ist damit erledigt:

- 1 Minute Diktat → fertig in **~0,5 s**
- 5 Minuten Diktat → fertig in **~2–3 s**
- 10 Minuten Diktat → fertig in **~5 s**

`large-v3` lohnt nur, wenn du bei sehr undeutlichen Aufnahmen das letzte Prozent
Genauigkeit willst — auch das bleibt mit 47× Echtzeit weit weg von „minutenlang".
Alles unterhalb von medium lohnt auf dieser Hardware nicht: Die kleinen Modelle
sparen Zehntelsekunden, kosten aber sichtbar Qualität.

Hinweis: Die englisch-optimierten Distil-Modelle (z. B. distil-large-v3) wurden
bewusst weggelassen — sie können kein Deutsch.

VRAM-Verbrauch ist kein Thema: large-v3-turbo belegt ~1,7 GB von 24 GB.
