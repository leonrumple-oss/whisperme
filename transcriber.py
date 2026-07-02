"""Whisper-Transkription ueber faster-whisper/CTranslate2 (GPU, Fallback CPU)."""
import gc
import logging
import os
import sys
import threading
import time
from pathlib import Path

log = logging.getLogger("wisperme")


def _register_cuda_dlls() -> None:
    """Macht die per pip installierten NVIDIA-DLLs (cuBLAS/cuDNN) auffindbar.

    CTranslate2 laedt sie ueber den PATH, daher reicht add_dll_directory nicht.
    """
    site = Path(sys.prefix) / "Lib" / "site-packages"
    for sub in ("cublas", "cudnn", "cuda_nvrtc"):
        dll_dir = site / "nvidia" / sub / "bin"
        if dll_dir.is_dir():
            os.add_dll_directory(str(dll_dir))
            os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")


_register_cuda_dlls()

# Windows ohne Entwicklermodus kann keine Symlinks anlegen -> beim
# Modell-Download echte Kopien verwenden statt mit WinError 1314 abzubrechen
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import ctranslate2  # noqa: E402
from faster_whisper import BatchedInferencePipeline, WhisperModel  # noqa: E402

# Reihenfolge = Reihenfolge im Einstellungs-Dropdown und Tray-Menue
MODELS = {
    "large-v3-turbo": "Large v3 Turbo — empfohlen: Top-Qualität, sehr schnell (1,6 GB)",
    "large-v3": "Large v3 — maximale Genauigkeit, etwas langsamer (3,1 GB)",
    "medium": "Medium — gute Qualität (1,5 GB)",
    "small": "Small — solide Qualität, sehr schnell (0,5 GB)",
    "base": "Base — einfache Qualität, minimal (0,15 GB)",
    "tiny": "Tiny — niedrigste Qualität, winzig (0,08 GB)",
}

# Ab dieser Audiolaenge lohnt sich die gebatchte Pipeline deutlich
BATCHED_THRESHOLD_S = 20.0


def is_model_downloaded(name: str) -> bool:
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    if not cache.is_dir():
        return False
    needle = f"whisper-{name}".lower()
    # endswith, damit "large-v3" nicht faelschlich "large-v3-turbo" matcht
    return any(p.name.lower().endswith(needle) for p in cache.glob("models--*"))


class Transcriber:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None
        self.batched = None
        self.device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        self._lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self.model is not None

    def ensure_loaded(self) -> None:
        with self._lock:
            if self.model is not None:
                return
            t0 = time.time()
            log.info("Lade Modell %s auf %s (%s) ...", self.model_name, self.device, self.compute_type)
            self.model = WhisperModel(
                self.model_name, device=self.device, compute_type=self.compute_type
            )
            self.batched = BatchedInferencePipeline(model=self.model)
            log.info("Modell %s geladen in %.1fs", self.model_name, time.time() - t0)

    def switch_model(self, name: str) -> None:
        with self._lock:
            if name == self.model_name and self.model is not None:
                return
            self.model_name = name
            self.model = None
            self.batched = None
            gc.collect()
        self.ensure_loaded()

    def transcribe(self, audio, language="de", beam_size=5, initial_prompt="",
                   task="transcribe") -> str:
        """Transkribiert ein float32-Array (16 kHz) und liefert den Text.

        task="translate" liefert eine englische Uebersetzung (Whisper-nativ).
        """
        self.ensure_loaded()
        duration = len(audio) / 16000.0
        lang = None if language in ("", "auto") else language
        kwargs = dict(
            language=lang,
            task=task,
            beam_size=beam_size,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        if initial_prompt.strip():
            kwargs["initial_prompt"] = initial_prompt.strip()

        with self._lock:
            t0 = time.time()
            if duration > BATCHED_THRESHOLD_S:
                segments, _ = self.batched.transcribe(audio, batch_size=8, **kwargs)
            else:
                segments, _ = self.model.transcribe(audio, **kwargs)
            text = " ".join(seg.text.strip() for seg in segments).strip()
            log.info(
                "Transkribiert: %.1fs Audio in %.2fs (%s): %r",
                duration, time.time() - t0, self.model_name,
                text[:80] + ("..." if len(text) > 80 else ""),
            )
        return text
