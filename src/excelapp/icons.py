"""Sinh QIcon từ bộ icon Lucide (https://lucide.dev, ISC license).

Icon Lucide là kiểu nét (stroke) hiện đại, sắc. Render từ SVG vector ở độ phân
giải cao rồi đặt devicePixelRatio nên **nét trên cả màn HiDPI** (khắc phục icon
cũ bị mờ). Màu mặc định #444746 khớp tông toolbar.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from .lucide_data import ICONS

# Wrapper Lucide: fill none + stroke màu mong muốn (các path con thừa hưởng).
_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
    'stroke="{color}" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round">{inner}</svg>'
)

# Render gấp 4 lần kích thước logic -> downscale mượt, không vỡ nét trên HiDPI.
_RENDER_SCALE = 4

_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}


def make_icon(name: str, color: str = "#444746", size: int = 20) -> QIcon:
    """Sinh QIcon Lucide từ tên; có cache theo (name, color, size).

    Render SVG ở độ phân giải cao (``size * _RENDER_SCALE``) rồi đặt
    ``devicePixelRatio`` để icon nét trên màn thường lẫn HiDPI. Cache vì nhiều
    chỗ (toolbar, đồng bộ khi chọn ô) gọi lặp cùng một icon.
    """
    key = (name, color, size)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached
    inner = ICONS.get(name)
    if inner is None:  # tên thiếu -> icon rỗng, không vỡ UI
        icon = QIcon()
        _ICON_CACHE[key] = icon
        return icon
    svg = _TEMPLATE.format(color=color, inner=inner)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    px = size * _RENDER_SCALE
    pix = QPixmap(px, px)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()
    pix.setDevicePixelRatio(_RENDER_SCALE)
    icon = QIcon(pix)
    _ICON_CACHE[key] = icon
    return icon
