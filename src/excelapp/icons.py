"""Sinh QIcon từ path Material Design (cùng bộ icon Google dùng).

Dùng cho các nút canh lề / xuống dòng trên toolbar. Render từ SVG nên nét ở
mọi kích thước; màu xám #444746 khớp tông toolbar.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Path Material Design (viewBox 0 0 24 24).
PATHS: dict[str, str] = {
    "align_left": "M15 15H3v2h12v-2zm0-8H3v2h12V7zM3 13h18v-2H3v2zm0 8h18v-2H3v2zM3 3v2h18V3H3z",
    "align_center": "M7 15v2h10v-2H7zm-4 6h18v-2H3v2zm0-8h18v-2H3v2zm4-6v2h10V7H7zM3 3v2h18V3H3z",
    "align_right": "M3 21h18v-2H3v2zm6-4h12v-2H9v2zm-6-4h18v-2H3v2zm6-4h12V7H9v2zM3 3v2h18V3H3z",
    "valign_top": "M8 11h3v10h2V11h3l-4-4-4 4zM4 3v2h16V3H4z",
    "valign_middle": "M8 19h3v4h2v-4h3l-4-4-4 4zm8-14h-3V1h-2v4H8l4 4 4-4zM4 11v2h16v-2H4z",
    "valign_bottom": "M16 13h-3V3h-2v10H8l4 4 4-4zM4 19v2h16v-2H4z",
    "wrap_text": (
        "M4 19h6v-2H4v2zM20 5H4v2h16V5zm-3 6H4v2h13.25c1.1 0 2 .9 2 2s-.9 2-2 2"
        "H15v-2l-3 3 3 3v-2h2c2.21 0 4-1.79 4-4s-1.79-4-4-4z"
    ),
}

_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path fill="{color}" d="{d}"/></svg>'
)


def make_icon(name: str, color: str = "#444746", size: int = 20) -> QIcon:
    svg = _TEMPLATE.format(color=color, d=PATHS[name])
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)
