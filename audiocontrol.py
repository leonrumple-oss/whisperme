"""Schaltet waehrend der Aufnahme andere Audioquellen stumm (Musik, Videos).

Nutzt die Windows-Audio-Sessions (pycaw). Es werden nur Sessions stumm
geschaltet, die vorher NICHT stumm waren — und genau diese werden danach
wieder aktiviert. Eigene und System-Sessions bleiben unangetastet.
"""
import logging
import os
import threading

log = logging.getLogger("wisperme")

_lock = threading.Lock()
_muted = []  # [(pid, name)] der von uns stummgeschalteten Sessions


def _sessions():
    import comtypes
    try:
        comtypes.CoInitialize()
    except Exception:
        pass  # Thread ist bereits initialisiert
    from pycaw.pycaw import AudioUtilities
    return AudioUtilities.GetAllSessions()


def mute_others() -> None:
    """Schaltet alle fremden, aktuell hoerbaren Audio-Sessions stumm."""
    global _muted
    with _lock:
        muted_now = []
        try:
            own_pid = os.getpid()
            for session in _sessions():
                proc = session.Process
                if proc is None or proc.pid == own_pid:
                    continue
                try:
                    volume = session.SimpleAudioVolume
                    if not volume.GetMute():
                        volume.SetMute(1, None)
                        muted_now.append((proc.pid, proc.name()))
                except Exception:
                    continue
            if muted_now:
                log.info("Stummgeschaltet: %s",
                         ", ".join(name for _, name in muted_now))
        except Exception:
            log.exception("Stummschalten fehlgeschlagen")
        _muted = muted_now


def unmute_others() -> None:
    """Hebt genau die von uns gesetzten Stummschaltungen wieder auf."""
    global _muted
    with _lock:
        if not _muted:
            return
        pids = {pid for pid, _ in _muted}
        try:
            for session in _sessions():
                proc = session.Process
                if proc is None or proc.pid not in pids:
                    continue
                try:
                    session.SimpleAudioVolume.SetMute(0, None)
                except Exception:
                    continue
            log.info("Stummschaltung aufgehoben (%d Apps)", len(pids))
        except Exception:
            log.exception("Aufheben der Stummschaltung fehlgeschlagen")
        _muted = []
