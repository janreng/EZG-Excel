"""Tìm đường dẫn tài nguyên (icon...) khi chạy dev hoặc khi đã đóng gói."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """Trả về đường dẫn tuyệt đối tới một tài nguyên.

    - Khi chạy bằng PyInstaller: lấy từ thư mục tạm ``sys._MEIPASS``.
    - Khi chạy mã nguồn: lấy theo gốc dự án.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative
    # src/excelapp/resources.py -> gốc dự án là cha của 'src'.
    root = Path(__file__).resolve().parent.parent.parent
    return root / relative


def icon_path() -> str:
    return str(resource_path("assets/icon.ico"))
