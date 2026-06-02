"""Tạo assets/icon.ico (đa kích thước) từ logo nguồn LOGO-05.png.

Chạy: python tools/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "icon.ico"

# Tìm logo nguồn (ưu tiên trong assets, rồi tới gốc dự án).
CANDIDATES = [
    ROOT / "assets" / "icon.png",
    ROOT / "assets" / "logo.png",
    ROOT / "LOGO-05.png",
]


def main() -> None:
    src = next((p for p in CANDIDATES if p.exists()), None)
    if src is None:
        raise SystemExit("Khong tim thay logo nguon (LOGO-05.png).")

    img = Image.open(src).convert("RGBA")
    # Cắt/đệm về hình vuông để icon không bị méo.
    w, h = img.size
    if w != h:
        side = max(w, h)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - w) // 2, (side - h) // 2))
        img = square

    sizes = [16, 24, 32, 48, 64, 128, 256]
    img.save(OUT, format="ICO", sizes=[(s, s) for s in sizes])
    print(f"Created {OUT} from {src.name}")


if __name__ == "__main__":
    main()
