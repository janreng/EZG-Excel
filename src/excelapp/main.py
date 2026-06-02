"""Điểm khởi chạy ứng dụng."""

from __future__ import annotations

import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import APP_NAME
from .main_window import MainWindow
from .resources import icon_path


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    # Fusion: giao diện đồng nhất, bỏ "thanh accent" chọn ô của Windows 11.
    app.setStyle("Fusion")
    if os.path.exists(icon_path()):
        app.setWindowIcon(QIcon(icon_path()))
    window = MainWindow()

    # Nếu truyền đường dẫn file qua dòng lệnh thì mở luôn.
    if len(sys.argv) > 1:
        try:
            from . import io_utils

            window.model.replace_all(io_utils.load_file(sys.argv[1]))
            from pathlib import Path

            window.current_path = Path(sys.argv[1])
            window._update_title()
        except Exception:  # noqa: BLE001
            pass

    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
