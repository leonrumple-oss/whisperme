"""Zentrale Pfade — funktioniert im Quelltext-Betrieb UND als PyInstaller-EXE.

- APP_DIR:    Ordner fuer Nutzerdaten (config.json, Verlauf, Regeln, Log).
              Im EXE-Betrieb der Ordner neben WisperMe.exe.
- BUNDLE_DIR: Ordner mit gebuendelten Ressourcen (im EXE-Betrieb `_internal`).
"""
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))

if FROZEN:
    APP_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    BUNDLE_DIR = APP_DIR
