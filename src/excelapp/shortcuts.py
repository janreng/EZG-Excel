"""Phím tắt có thể tùy chỉnh, lưu bằng QSettings.

Mỗi lệnh có một id. Mặc định lấy từ ``DEFAULTS``; người dùng có thể đổi và
lựa chọn được lưu lại.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

# id lệnh -> phím tắt mặc định (chuỗi kiểu "Ctrl+C"). Thứ tự = thứ tự hiển thị.
DEFAULTS: dict[str, str] = {
    "new": "Ctrl+N",
    "open": "Ctrl+O",
    "save": "Ctrl+S",
    "save_as": "Ctrl+Shift+S",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "copy": "Ctrl+C",
    "cut": "Ctrl+X",
    "paste": "Ctrl+V",
    "paste_special": "Ctrl+Alt+V",
    "clear": "Del",
    "fill_down": "Ctrl+D",
    "fill_right": "Ctrl+R",
    "find": "Ctrl+F",
    "replace": "Ctrl+H",
}


def _settings() -> QSettings:
    return QSettings("PyExcel", "PyExcel")


def get(cmd_id: str) -> str:
    s = _settings()
    return s.value(f"shortcuts/{cmd_id}", DEFAULTS.get(cmd_id, ""))


def all_current() -> dict[str, str]:
    return {cmd_id: get(cmd_id) for cmd_id in DEFAULTS}


def set_many(mapping: dict[str, str]) -> None:
    s = _settings()
    for cmd_id, seq in mapping.items():
        if cmd_id in DEFAULTS:
            s.setValue(f"shortcuts/{cmd_id}", seq)


def reset() -> None:
    s = _settings()
    for cmd_id in DEFAULTS:
        s.remove(f"shortcuts/{cmd_id}")
