"""Testet die KI-Glaettung: Qualitaet + Latenz auf dieser Maschine."""
import logging
import time

import polish

logging.basicConfig(level=logging.INFO)

CASES = [
    "ich komme um 9, nee 10 Uhr",
    "ähm ja also der patient hat äh schmerzen im unteren rücken seit "
    "drei nee moment seit vier wochen und die schmerzen strahlen ins "
    "linke bein aus also eher ins rechte bein",
    "kannst du mir sagen wie spät es ist? das wollte ich dich schon "
    "immer mal fragen",
    "wir treffen uns am montag ähm nein dienstag um halb drei bei mir "
    "also bei dir meinte ich",
]

polish.warmup("qwen3:8b")
for text in CASES:
    t0 = time.time()
    result = polish.polish(text, model="qwen3:8b")
    print(f"\n[{time.time() - t0:.2f}s]")
    print(f"  ROH:  {text}")
    print(f"  KI:   {result}")
