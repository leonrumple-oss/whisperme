"""Erzeugt wisperme.ico (Mikrofon-Design wie das Tray-Icon, mehrere Groessen)."""
from pathlib import Path

from PIL import Image, ImageDraw

APP_DIR = Path(__file__).resolve().parent


def draw_mic(size: int) -> Image.Image:
    s = size / 64.0  # Basisdesign ist 64px, hochskalieren
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2 * s, 2 * s, 62 * s, 62 * s], fill=(35, 35, 48, 255))
    white = (240, 240, 245, 255)
    green = (58, 211, 107, 255)
    d.rounded_rectangle([26 * s, 12 * s, 38 * s, 34 * s], radius=6 * s, fill=white)
    d.arc([20 * s, 22 * s, 44 * s, 44 * s], start=0, end=180,
          fill=white, width=max(1, round(3 * s)))
    d.line([32 * s, 44 * s, 32 * s, 50 * s], fill=white, width=max(1, round(3 * s)))
    d.line([24 * s, 51 * s, 40 * s, 51 * s], fill=white, width=max(1, round(3 * s)))
    # kleiner gruener "bereit"-Punkt unten rechts
    d.ellipse([44 * s, 44 * s, 56 * s, 56 * s], fill=green)
    return img


if __name__ == "__main__":
    base = draw_mic(256)
    out = APP_DIR / "wisperme.ico"
    base.save(out, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Icon geschrieben: {out}")
