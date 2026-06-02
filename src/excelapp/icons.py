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
    # ---- canh lề ngang ----
    "align_left":   "M15 15H3v2h12v-2zm0-8H3v2h12V7zM3 13h18v-2H3v2zm0 8h18v-2H3v2zM3 3v2h18V3H3z",
    "align_center": "M7 15v2h10v-2H7zm-4 6h18v-2H3v2zm0-8h18v-2H3v2zm4-6v2h10V7H7zM3 3v2h18V3H3z",
    "align_right":  "M3 21h18v-2H3v2zm6-4h12v-2H9v2zm-6-4h18v-2H3v2zm6-4h12V7H9v2zM3 3v2h18V3H3z",
    # ---- canh lề dọc ----
    "valign_top":    "M8 11h3v10h2V11h3l-4-4-4 4zM4 3v2h16V3H4z",
    "valign_middle": "M8 19h3v4h2v-4h3l-4-4-4 4zm8-14h-3V1h-2v4H8l4 4 4-4zM4 11v2h16v-2H4z",
    "valign_bottom": "M16 13h-3V3h-2v10H8l4 4 4-4zM4 19v2h16v-2H4z",
    # ---- xuống dòng ----
    "wrap_text": (
        "M4 19h6v-2H4v2zM20 5H4v2h16V5zm-3 6H4v2h13.25c1.1 0 2 .9 2 2s-.9 2-2 2"
        "H15v-2l-3 3 3 3v-2h2c2.21 0 4-1.79 4-4s-1.79-4-4-4z"
    ),
    "wrap_overflow": "M3 5h18v2H3zm0 6h9v2H3zm14.5-1L21 13.5 17.5 17l-1.4-1.4 1.1-1.1H13v-2h4.2l-1.1-1.1z",
    "wrap_clip":     "M3 5h18v2H3zm0 6h11v2H3zm0 6h7v2H3zm15-6h2v8h-2z",
    # ---- lọc ----
    "filter": (
        "M4.25 5.61C6.27 8.2 10 13 10 13v6c0 .55.45 1 1 1h2c.55 0 1-.45 1-1v-6"
        "s3.72-4.8 5.74-7.39c.51-.66.04-1.61-.79-1.61H5.04c-.83 0-1.3.95-.79 1.61z"
    ),
    # ---- định dạng chữ ----
    "bold": (
        "M15.6 10.79c.97-.67 1.65-1.77 1.65-2.79 0-2.26-1.75-4-4-4H7v14h7.04"
        "c2.09 0 3.71-1.7 3.71-3.79 0-1.52-.86-2.82-2.15-3.42z"
        "M10 6.5h3c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5h-3v-3z"
        "m3.5 9H10v-3h3.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5z"
    ),
    "italic":    "M10 4v3h2.21l-3.42 8H6v3h8v-3h-2.21l3.42-8H18V4z",
    "strike":    "M10 19h4v-3h-4v3zM5 4v3h5v3h4V7h5V4H5zM3 14h18v-2H3v2z",
    "underline": (
        "M12 17c3.31 0 6-2.69 6-6V3h-2.5v8c0 1.93-1.57 3.5-3.5 3.5"
        "S8.5 12.93 8.5 11V3H6v8c0 3.31 2.69 6 6 6zm-7 2v2h14v-2H5z"
    ),
    # ---- clipboard ----
    "cut": (
        "M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4"
        "c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14"
        "c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64z"
        "M6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2z"
        "m0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2z"
        "M12 10c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zM20 5h-3l-7 7 3 3 7-7V5z"
    ),
    "copy": (
        "M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1z"
        "m3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2z"
        "m0 16H8V7h11v14z"
    ),
    "paste": (
        "M19 2h-4.18C14.4.84 13.3 0 12 0c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v16"
        "c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"
        "m-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"
        "m7 18H5V4h2v3h10V4h2v16z"
    ),
    # ---- sắp xếp ----
    "sort_asc":  "M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z",
    "sort_desc": (
        "M3 6h6v2H3V6zm0 5h9v2H3v-2zm0 5h12v2H3v-2z"
        "m13-9.17V18h-2V7.83l-2.09 2.09L10.5 8.5l4-4 4 4-1.41 1.41L16 7.83z"
    ),
    # ---- tìm kiếm ----
    "find": (
        "M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5"
        " 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16"
        "c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5z"
        "m-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"
    ),
    # ---- undo / redo ----
    "undo": "M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z",
    "redo": "M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.95 0 3.73.72 5.12 1.88L13 16h9V7l-3.6 3.6z",
    # ---- lưới / border ----
    "borders": (
        "M3 3v18h18V3H3zm8 16H5v-6h6v6zm0-8H5V5h6v6zm8 8h-6v-6h6v6zm0-8h-6V5h6v6z"
    ),
    # ---- màu nền / màu chữ ----
    "fill_color": (
        "M16.56 8.94L7.62 0 6.21 1.41l2.38 2.38-5.15 5.15a1.49 1.49 0 0 0 0 2.12"
        "l5.5 5.5c.29.29.68.44 1.06.44s.77-.15 1.06-.44l5.5-5.5c.59-.58.59-1.53 0-2.12z"
        "M5.21 10L10 5.21 14.79 10H5.21z"
        "M19 11.5s-2 2.17-2 3.5c0 1.1.9 2 2 2s2-.9 2-2c0-1.33-2-3.5-2-3.5z"
        "M0 20h24v4H0z"
    ),
    "font_color": (
        "M11 3L5.5 17h2.25l1.12-3h6.25l1.12 3h2.25L13 3h-2zm-1.38 9L12 5.67 14.38 12H9.62z"
        "M0 20h24v4H0z"
    ),
    # ---- số ----
    "number_format": (
        "M7 15h2c0 1.08 1.37 2 3 2s3-.92 3-2c0-1.1-1.04-1.5-3.24-2.03"
        "C9.64 12.44 7 11.78 7 9c0-1.79 1.47-3.37 3.5-3.82V3h3v2.18"
        "C15.53 5.63 17 7.21 17 9h-2c0-1.08-1.37-2-3-2s-3 .92-3 2"
        "c0 1.1 1.04 1.5 3.24 2.03C14.36 11.56 17 12.22 17 15"
        "c0 1.79-1.47 3.37-3.5 3.82V21h-3v-2.18C8.47 18.37 7 16.79 7 15z"
    ),
    # ---- định dạng có điều kiện (gradient) ----
    "cond_format": (
        "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"
        "m0 16H5V5h14v14zM7 9h2v2H7zm0 4h2v2H7zm4-4h2v2h-2zm0 4h2v2h-2zm4-4h2v2h-2zm0 4h2v2h-2z"
    ),
    # ---- merge cells (stub) ----
    "merge": (
        "M2 6v12h20V6H2zm9 10H4V8h7v8zm9 0h-7V8h7v8z"
        "M11 9l-3 3 3 3v-2h2v2l3-3-3-3v2h-2V9z"
    ),
}

_TEMPLATE = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
    '<path fill="{color}" d="{d}"/></svg>'
)


_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}


def make_icon(name: str, color: str = "#444746", size: int = 20) -> QIcon:
    """Sinh QIcon từ path; có cache theo (name, color, size).

    Render SVG khá tốn, mà nhiều chỗ (toolbar, đồng bộ khi chọn ô) gọi lặp lại
    cùng một icon — cache để tránh dựng pixmap mỗi lần (chọn ô mượt hơn).
    """
    key = (name, color, size)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached
    svg = _TEMPLATE.format(color=color, d=PATHS[name])
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    icon = QIcon(pix)
    _ICON_CACHE[key] = icon
    return icon
