"""Hardware-Erkennung: waehlt beim ersten Start ein passendes Whisper-Modell.

Bewusst leichtgewichtig (kein ctranslate2-Import): NVIDIA-GPUs werden ueber
nvidia-smi erkannt. Ob CUDA wirklich nutzbar ist, entscheidet spaeter
transcriber.py — dort gibt es ohnehin den CPU-Fallback (int8).
"""
import os
import shutil
import subprocess
import urllib.request


def gpu_info():
    """(Name, VRAM in MB) der ersten NVIDIA-GPU, sonst (None, 0)."""
    exe = shutil.which("nvidia-smi") or r"C:\Windows\System32\nvidia-smi.exe"
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW)
        line = out.stdout.strip().splitlines()[0]
        name, mem = line.rsplit(",", 1)
        return name.strip(), int(mem.strip())
    except Exception:
        return None, 0


def recommend_model() -> str:
    """Bestes Whisper-Modell fuer diese Maschine (Qualitaet vor Groesse).

    - NVIDIA-GPU ab ~4 GB VRAM: large-v3-turbo (float16 braucht ~3 GB)
    - kleinere NVIDIA-GPU:      small
    - nur CPU:                  small ab 8 Kernen, sonst base (int8)
    """
    _name, vram = gpu_info()
    if vram >= 4000:
        return "large-v3-turbo"
    if vram >= 2500:
        return "small"
    cores = os.cpu_count() or 4
    return "small" if cores >= 8 else "base"


def ollama_available(url: str = "http://127.0.0.1:11434") -> bool:
    """True wenn ein Ollama-Server laeuft oder Ollama installiert ist."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/api/version", timeout=2):
            return True
    except Exception:
        pass
    exe = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                       "Programs", "Ollama", "ollama.exe")
    return os.path.isfile(exe)


def summary() -> str:
    name, vram = gpu_info()
    gpu = f"{name} ({vram} MB VRAM)" if name else "keine NVIDIA-GPU (CPU-Modus)"
    return (f"GPU: {gpu} | CPU-Threads: {os.cpu_count()} | "
            f"Ollama: {'ja' if ollama_available() else 'nein'} | "
            f"Empfehlung: {recommend_model()}")


if __name__ == "__main__":
    print(summary())
