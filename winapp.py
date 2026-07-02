"""Erkennt die gerade aktive Anwendung (fuer App-abhaengige KI-Stile)."""
import ctypes
import os
from ctypes import wintypes

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def get_foreground_exe() -> str:
    """EXE-Name des Vordergrundfensters in Kleinbuchstaben, z.B. 'outlook.exe'."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            ok = ctypes.windll.kernel32.QueryFullProcessImageNameW(
                handle, 0, buf, ctypes.byref(size))
            return os.path.basename(buf.value).lower() if ok else ""
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        return ""
