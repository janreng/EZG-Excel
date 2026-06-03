"""Hộp thoại "Dán đặc biệt" (Ctrl+Alt+V).

Cho chọn dán phần nào (Tất cả / Công thức / Giá trị / Định dạng), phép tính
áp giữa ô đích và giá trị nguồn (Cộng/Trừ/Nhân/Chia), bỏ qua ô trống, và xoay
hàng↔cột. Trả kết quả qua :meth:`options`.

Tách module riêng để main_window không phình.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
)

from .i18n import tr
from .ui_style import MENU_QSS

_MODES = [("all", "ps_all"), ("formulas", "ps_formulas"),
          ("values", "ps_values"), ("formats", "ps_formats")]
_OPS = [("none", "ps_op_none"), ("add", "ps_op_add"), ("sub", "ps_op_sub"),
        ("mul", "ps_op_mul"), ("div", "ps_op_div")]


class PasteSpecialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("paste_special"))
        self.setStyleSheet(MENU_QSS)
        root = QVBoxLayout(self)

        self._mode_group, mode_box = self._radio_group("ps_paste_group", _MODES, "all")
        self._op_group, op_box = self._radio_group("ps_op_group", _OPS, "none")
        body = QHBoxLayout()
        body.addWidget(mode_box)
        body.addWidget(op_box)
        root.addLayout(body)

        self._skip_cb = QCheckBox(tr("ps_skip_blanks"))
        self._transpose_cb = QCheckBox(tr("ps_transpose"))
        root.addWidget(self._skip_cb)
        root.addWidget(self._transpose_cb)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("ok"))
        bb.button(QDialogButtonBox.Cancel).setText(tr("cancel"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

    def _radio_group(self, title_key, items, default):
        box = QGroupBox(tr(title_key))
        lay = QVBoxLayout(box)
        group = QButtonGroup(box)
        for key, label in items:
            rb = QRadioButton(tr(label))
            rb._value = key
            if key == default:
                rb.setChecked(True)
            group.addButton(rb)
            lay.addWidget(rb)
        return group, box

    @staticmethod
    def _checked_value(group: QButtonGroup):
        btn = group.checkedButton()
        return btn._value if btn else None

    def options(self) -> dict:
        return {
            "mode": self._checked_value(self._mode_group),
            "operation": self._checked_value(self._op_group),
            "skip_blanks": self._skip_cb.isChecked(),
            "transpose": self._transpose_cb.isChecked(),
        }
