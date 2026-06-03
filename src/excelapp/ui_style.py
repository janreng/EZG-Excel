"""Stylesheet dùng chung cho UI Ezcel.

Tách riêng để cả ``main`` (app-wide) lẫn ``main_window`` (đặt thẳng lên từng
QMenu) dùng chung một định nghĩa — tránh popup menu bị nền đen.
"""

from __future__ import annotations

# Popup menu nền trắng, chữ tối. Đặt THẲNG lên mỗi QMenu (widget-level) để thắng
# cascade từ stylesheet của widget cha (vd ribbon) — nếu chỉ đặt app-level sẽ bị
# rule của cha đè, popup thành nền đen.
MENU_QSS = (
    "QMenu { background: #ffffff; border: 1px solid #C0C0C0; padding: 4px; }"
    "QMenu::item { padding: 6px 28px 6px 16px; border-radius: 2px; color: #1c1c1c;"
    "  background: transparent; }"
    "QMenu::item:selected { background: #EBF3E8; color: #217346; }"
    "QMenu::item:disabled { color: #a0a0a0; }"
    "QMenu::separator { height: 1px; background: #D0D0D0; margin: 4px 8px; }"
    "QMenu::icon { padding-left: 6px; }"
)
