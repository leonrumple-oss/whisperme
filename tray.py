"""Systemtray-Icon mit Menue (pystray). Callbacks laufen im Tray-Thread und
melden Aktionen nur als Flags an die App - Tk-Aufrufe passieren im Hauptthread."""
import pystray
from PIL import Image, ImageDraw

import transcriber


def _make_icon(recording: bool = False) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bg = (220, 60, 60, 255) if recording else (35, 35, 48, 255)
    d.ellipse([2, 2, 62, 62], fill=bg)
    white = (240, 240, 245, 255)
    # Mikrofon: Kapsel + Buegel + Fuss
    d.rounded_rectangle([26, 12, 38, 34], radius=6, fill=white)
    d.arc([20, 22, 44, 44], start=0, end=180, fill=white, width=3)
    d.line([32, 44, 32, 50], fill=white, width=3)
    d.line([24, 51, 40, 51], fill=white, width=3)
    return img


class Tray:
    def __init__(self, app):
        self.app = app
        self.icon = pystray.Icon("WisperMe", _make_icon(), "WisperMe – lokales Diktat")
        self.icon.menu = pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda item: "Aufnahme stoppen" if app.state == "recording" else "Aufnahme starten",
                lambda: app.toggle_recording(),
                default=True,
            ),
            pystray.MenuItem("Einstellungen…", lambda: app.request("settings")),
            pystray.MenuItem("Modell", pystray.Menu(*self._model_items())),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Beenden", lambda: app.request("quit")),
        )

    def _status_text(self, item):
        return f"Modell: {self.app.cfg['model']}"

    def _model_items(self):
        items = []
        for name in transcriber.MODELS:
            items.append(pystray.MenuItem(
                name,
                (lambda n: lambda: self.app.request(("model", n)))(name),
                checked=(lambda n: lambda item: self.app.cfg["model"] == n)(name),
                radio=True,
            ))
        return items

    def set_recording(self, recording: bool):
        try:
            self.icon.icon = _make_icon(recording)
        except Exception:
            pass

    def start(self):
        self.icon.run_detached()

    def stop(self):
        try:
            self.icon.stop()
        except Exception:
            pass
