# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Rezept: erzeugt dist/WisperMe/ mit WisperMe.exe (Onedir).

Build:  .venv\\Scripts\\python -m PyInstaller wisperme.spec --noconfirm
Die NVIDIA-CUDA-DLLs (cuBLAS/cuDNN) werden mit eingepackt, damit die EXE
auf NVIDIA-Systemen ohne weitere Installation die GPU nutzt; ohne NVIDIA
faellt die App automatisch auf die CPU zurueck.
"""
import glob
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

venv_sp = Path(".venv") / "Lib" / "site-packages"

datas = [("wisperme.ico", ".")]
binaries = []
hiddenimports = [
    "audio", "config", "hardware", "history", "history_ui", "injector",
    "overlay", "paths", "polish", "settings_ui", "textrules", "transcriber",
    "tray", "welcome_ui", "winapp",
]

for pkg in ("customtkinter", "faster_whisper"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# NVIDIA-Laufzeit-DLLs unter nvidia/<paket>/bin einsammeln
for dll in glob.glob(str(venv_sp / "nvidia" / "*" / "bin" / "*.dll")):
    rel_dir = Path(dll).relative_to(venv_sp).parent
    binaries.append((dll, str(rel_dir)))

a = Analysis(
    ["app.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["PyInstaller"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="WisperMe",
    icon="wisperme.ico",
    console=False,
    upx=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="WisperMe",
    upx=False,
)
