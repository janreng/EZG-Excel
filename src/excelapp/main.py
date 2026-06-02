"""Điểm khởi chạy ứng dụng."""

from __future__ import annotations

import os
import sys

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .main_window import MainWindow
from .resources import icon_path


def _light_palette() -> QPalette:
    """Bảng màu SÁNG cố định — không chạy theo dark mode của Windows.

    Nếu để Fusion theo theme hệ thống, máy đang bật dark mode sẽ khiến popup
    combobox / menu nền đen chữ tối. App thiết kế nền sáng nên ép light palette.
    """
    p = QPalette()
    white = QColor("#ffffff")
    text = QColor("#1c1c1c")
    p.setColor(QPalette.Window, QColor("#f3f3f3"))
    p.setColor(QPalette.WindowText, text)
    p.setColor(QPalette.Base, white)
    p.setColor(QPalette.AlternateBase, QColor("#f6f6f6"))
    p.setColor(QPalette.ToolTipBase, white)
    p.setColor(QPalette.ToolTipText, text)
    p.setColor(QPalette.Text, text)
    p.setColor(QPalette.Button, QColor("#f3f3f3"))
    p.setColor(QPalette.ButtonText, text)
    p.setColor(QPalette.BrightText, QColor("#d93025"))
    p.setColor(QPalette.Highlight, QColor("#217346"))
    p.setColor(QPalette.HighlightedText, white)
    p.setColor(QPalette.PlaceholderText, QColor("#9aa0a6"))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor("#a0a0a0"))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor("#a0a0a0"))
    return p


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # Fusion: giao diện đồng nhất, bỏ "thanh accent" chọn ô của Windows 11.
    app.setStyle("Fusion")
    app.setPalette(_light_palette())  # ép nền sáng, tránh dark mode làm đen popup
    if os.path.exists(icon_path()):
        app.setWindowIcon(QIcon(icon_path()))
    window = MainWindow()

    # Nếu truyền đường dẫn file qua dòng lệnh thì mở luôn.
    if len(sys.argv) > 1:
        try:
            from . import io_utils

            window._load_sheets(io_utils.load_file(sys.argv[1]))
            from pathlib import Path

            window.current_path = Path(sys.argv[1])
            window._update_title()
        except Exception:  # noqa: BLE001
            pass

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
