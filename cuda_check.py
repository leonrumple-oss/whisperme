"""Schneller Test: erkennt CTranslate2 die GPU und laeuft ein Mini-Modell?"""
import os
import sys
import time
from pathlib import Path

# Die NVIDIA-Pip-Pakete legen ihre DLLs unter site-packages/nvidia/*/bin ab.
# Windows findet sie nur, wenn wir die Verzeichnisse explizit registrieren.
venv_site = Path(sys.prefix) / "Lib" / "site-packages"
for sub in ("cublas", "cudnn", "cuda_nvrtc"):
    dll_dir = venv_site / "nvidia" / sub / "bin"
    if dll_dir.is_dir():
        os.add_dll_directory(str(dll_dir))
        # ctranslate2 laedt cuBLAS ueber den PATH, nicht ueber add_dll_directory
        os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")

import ctranslate2
import numpy as np

print("CUDA devices:", ctranslate2.get_cuda_device_count())

from faster_whisper import WhisperModel

t0 = time.time()
model = WhisperModel("tiny", device="cuda", compute_type="float16")
print(f"Modell 'tiny' auf GPU geladen in {time.time() - t0:.1f}s")

# 3 Sekunden Stille transkribieren, nur um die Pipeline zu testen
audio = np.zeros(16000 * 3, dtype=np.float32)
t0 = time.time()
segments, info = model.transcribe(audio, language="de")
list(segments)
print(f"Transkription OK in {time.time() - t0:.2f}s — GPU-Pipeline funktioniert.")
