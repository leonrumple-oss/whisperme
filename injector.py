"""Fuegt den transkribierten Text in das aktive Fenster ein."""
import threading
import time

import keyboard
import pyperclip


def inject(text: str, mode: str = "paste", append_space: bool = True,
           restore_clipboard: bool = True) -> None:
    if not text:
        return
    if append_space and not text.endswith((" ", "\n")):
        text += " "

    if mode == "type":
        keyboard.write(text, delay=0.004)
        return

    old = None
    if restore_clipboard:
        try:
            old = pyperclip.paste()
        except Exception:
            old = None
    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")

    if restore_clipboard and old is not None:
        def _restore(previous=old):
            # der Ziel-App Zeit zum Einfuegen lassen
            time.sleep(1.5)
            try:
                pyperclip.copy(previous)
            except Exception:
                pass
        threading.Thread(target=_restore, daemon=True).start()
