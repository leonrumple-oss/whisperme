"""Misst pro Whisper-Modell: Ladezeit, Latenz fuer einen kurzen Satz (8 s)
und fuer langes Diktat (kompletter Testclip), jeweils auf dieser Maschine.

Aufruf:  .venv\\Scripts\\python.exe benchmark.py [wav-datei]
Ergebnis: Konsole + benchmark_results.json
"""
import gc
import json
import sys
import time
from pathlib import Path

import transcriber  # registriert die CUDA-DLLs
import ctranslate2
from faster_whisper import BatchedInferencePipeline, WhisperModel, decode_audio

APP_DIR = Path(__file__).resolve().parent
MODELS = ["base", "small", "medium", "large-v3-turbo", "large-v3"]


def main():
    wav = sys.argv[1] if len(sys.argv) > 1 else str(APP_DIR / "benchmark_sample_de.wav")
    audio = decode_audio(wav, sampling_rate=16000)
    duration = len(audio) / 16000.0
    short = audio[: 8 * 16000]

    cuda = ctranslate2.get_cuda_device_count() > 0
    device = "cuda" if cuda else "cpu"
    compute = "float16" if cuda else "int8"
    print(f"Testclip: {duration:.1f}s | Geraet: {device} ({compute})\n")

    kwargs = dict(language="de", beam_size=5, vad_filter=True,
                  condition_on_previous_text=False)
    results = []
    for name in MODELS:
        print(f"=== {name} ===")
        t0 = time.time()
        model = WhisperModel(name, device=device, compute_type=compute)
        load_s = time.time() - t0

        # Warmup (CUDA-Kernel-Initialisierung nicht mitmessen)
        segs, _ = model.transcribe(short, **kwargs)
        list(segs)

        t0 = time.time()
        segs, _ = model.transcribe(short, **kwargs)
        text_short = " ".join(s.text.strip() for s in segs)
        short_s = time.time() - t0

        batched = BatchedInferencePipeline(model=model)
        segs, _ = batched.transcribe(short, batch_size=8, **kwargs)  # Warmup batched
        list(segs)
        t0 = time.time()
        segs, _ = batched.transcribe(audio, batch_size=8, **kwargs)
        text_full = " ".join(s.text.strip() for s in segs)
        full_s = time.time() - t0

        r = {
            "modell": name,
            "ladezeit_s": round(load_s, 2),
            "kurzer_satz_8s_latenz_s": round(short_s, 2),
            "langes_diktat_s": round(full_s, 2),
            "clip_laenge_s": round(duration, 1),
            "echtzeitfaktor_lang": round(duration / full_s, 1),
            "text_kurz": text_short,
            "text_lang": text_full,
        }
        results.append(r)
        print(f"  Laden: {load_s:.2f}s | 8s-Satz: {short_s:.2f}s | "
              f"{duration:.0f}s-Diktat: {full_s:.2f}s "
              f"({duration / full_s:.0f}x Echtzeit)")
        print(f"  Text (kurz): {text_short[:100]}")

        del model, batched
        gc.collect()

    out = APP_DIR / "benchmark_results.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nErgebnisse gespeichert: {out}")


if __name__ == "__main__":
    main()
