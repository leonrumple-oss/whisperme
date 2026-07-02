"""Mikrofonaufnahme mit Pegelanzeige (sounddevice, 16 kHz mono)."""
import threading

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self, device_index=None):
        self.device_index = device_index
        self._chunks = []
        self._stream = None
        self._lock = threading.Lock()
        self.level = 0.0  # aktueller Eingangspegel 0..1 fuer die Overlay-Anzeige

    @property
    def recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self._stream is not None:
            return
        self._chunks = []
        self.level = 0.0

        def callback(indata, frames, time_info, status):
            data = indata[:, 0].copy()
            with self._lock:
                self._chunks.append(data)
            rms = float(np.sqrt(np.mean(np.square(data))))
            # Sprach-RMS liegt grob bei 0.02-0.3, auf 0..1 skalieren
            self.level = min(1.0, rms * 8.0)

        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=self.device_index,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Beendet die Aufnahme und liefert das Audio als float32-Array."""
        if self._stream is None:
            return np.zeros(0, dtype=np.float32)
        stream, self._stream = self._stream, None
        stream.stop()
        stream.close()
        self.level = 0.0
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            audio = np.concatenate(self._chunks)
            self._chunks = []
        return audio


def list_input_devices():
    """Liste (index, name) der Eingabegeraete; None steht fuer das Standardmikrofon."""
    result = [(None, "Standardmikrofon (Windows)")]
    try:
        devices = sd.query_devices()
        try:
            default_hostapi = devices[sd.default.device[0]]["hostapi"]
        except Exception:
            default_hostapi = 0
        for idx, dev in enumerate(devices):
            if dev["max_input_channels"] > 0 and dev["hostapi"] == default_hostapi:
                result.append((idx, dev["name"]))
    except Exception:
        pass
    return result
