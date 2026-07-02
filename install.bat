@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo  WisperMe – Installation
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [FEHLER] Python wurde nicht gefunden.
    echo Bitte Python 3.10 oder neuer installieren: https://www.python.org/downloads/
    echo Wichtig: beim Installieren "Add python.exe to PATH" anhaken.
    pause
    exit /b 1
)

echo [1/4] Erstelle virtuelle Umgebung...
python -m venv .venv || (echo [FEHLER] venv fehlgeschlagen & pause & exit /b 1)

echo [2/4] Installiere Abhaengigkeiten (inkl. CUDA-Bibliotheken, ~1 GB)...
.venv\Scripts\python -m pip install --upgrade pip --quiet
.venv\Scripts\python -m pip install -r requirements.txt || (echo [FEHLER] pip install fehlgeschlagen & pause & exit /b 1)

echo [3/4] Pruefe Hardware...
.venv\Scripts\python hardware.py

echo [4/4] Erstelle Desktop-Verknuepfung...
powershell -NoProfile -ExecutionPolicy Bypass -File create_shortcut.ps1

echo.
echo ============================================
echo  Fertig! Start ueber die Desktop-Verknuepfung
echo  "WisperMe" oder "WisperMe starten.vbs".
echo  Das Whisper-Modell laedt beim ersten Start
echo  automatisch herunter.
echo ============================================
pause
