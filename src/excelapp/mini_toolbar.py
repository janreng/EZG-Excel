"""Thanh công cụ định dạng nhanh (Mini Toolbar).

Một dải nút định dạng gọn (đậm/nghiêng/gạch, màu chữ, màu nền, viền, căn lề,
gộp ô) để gắn lên đầu menu chuột phải qua QWidgetAction. Tách riêng để
main_window không phình; logic định dạng vẫn do main_window cung cấp qua callback.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QHBoxLayout, QToolButton, QWidget

from .icons import make_icon


def make_mini_toolbar(parent, specs) -> QWidget:
    """Dựng widget chứa các nút định dạng nhanh.

    specs: danh sách (icon_name, tooltip, callback). ``None`` = vạch ngăn.
    """
    bar = QWidget(parent)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(6, 3, 6, 3)
    lay.setSpacing(2)
    for spec in specs:
        if spec is None:
            sep = QWidget()
            sep.setFixedWidth(8)
            lay.addWidget(sep)
            continue
        icon_name, tooltip, callback = spec
        btn = QToolButton(bar)
        btn.setIcon(make_icon(icon_name))
        btn.setIconSize(QSize(16, 16))
        btn.setToolTip(tooltip)
        btn.setAutoRaise(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        lay.addWidget(btn)
    lay.addStretch()
    return bar
