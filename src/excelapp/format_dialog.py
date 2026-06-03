"""Hộp thoại "Định dạng ô" (Ctrl+1) kiểu Excel — 6 tab.

Tab: Số / Căn lề / Phông chữ / Viền / Tô màu / Bảo vệ. Dialog chỉ đọc định dạng
ô hiện hành để khởi tạo, và trả về:
- :meth:`changes` — dict thuộc tính người dùng ĐÃ đổi (None = xóa về mặc định),
  đưa thẳng vào ``model.set_format_ranges``.
- :meth:`border_kind` — kiểu viền cần áp (hoặc None nếu "không đổi").

Tách module riêng để main_window không phình; logic định dạng số dùng lại
``_apply_number_format`` của model nên xem trước được "Mẫu:".
"""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .i18n import tr
from .table_model import _DATE_CODES, _apply_number_format
from .ui_style import MENU_QSS

# Mã ngày/giờ model hỗ trợ (Spec 08 number tab chỉ phát "dd/mm/yyyy" & "hh:mm:ss",
# nhưng cần NHẬN cả các mã khác để hiển thị đúng thể loại Ngày/Giờ).
_DATE_ONLY = {k for k in _DATE_CODES if "y" in k}
_TIME_ONLY = {k for k in _DATE_CODES if "y" not in k}

# Thứ tự thể loại số ↔ nhãn i18n. "custom" cho mã tùy ý.
_NUM_CATS = [
    ("general", "numfmt_general"),
    ("number", "numfmt_number"),
    ("percent", "numfmt_percent"),
    ("currency_vnd", "numfmt_vnd"),
    ("currency_usd", "numfmt_usd"),
    ("date", "numfmt_date"),
    ("time", "numfmt_time"),
    ("scientific", "numfmt_scientific"),
    ("custom", "fc_custom_code"),
]
_DEC_CATS = {"number", "percent", "currency_vnd", "currency_usd", "scientific"}
_THOUSANDS_CATS = {"number", "currency_vnd", "currency_usd"}


def _build_code(cat: str, decimals: int, thousands: bool, custom: str):
    """Dựng mã định dạng số từ lựa chọn người dùng (None = General)."""
    if cat == "general":
        return None
    if cat == "custom":
        return custom or None
    if cat == "date":
        return "dd/mm/yyyy"
    if cat == "time":
        return "hh:mm:ss"
    if cat == "scientific":
        return ("0." + "0" * decimals + "E+00") if decimals else "0E+00"
    dec = ("." + "0" * decimals) if decimals > 0 else ""
    intpart = "#,##0" if thousands else "0"
    if cat == "percent":
        return "0" + dec + "%"
    if cat == "currency_vnd":
        return intpart + dec + "₫"
    if cat == "currency_usd":
        return "$" + intpart + dec
    return intpart + dec  # number


def _parse_code(code):
    """Suy ra (category, decimals, thousands) từ mã có sẵn để khởi tạo dialog."""
    if not code:
        return "general", 2, True
    if code in _DATE_ONLY:
        return "date", 2, True
    if code in _TIME_ONLY:
        return "time", 2, True
    if "E" in code.upper():
        nd = code.upper().split("E")[0].split(".")
        return "scientific", (nd[1].count("0") if len(nd) > 1 else 2), False
    body = code.replace("%", "")
    decimals = body.split(".", 1)[1].count("0") if "." in body else 0
    thousands = "," in body.split(".")[0]
    if "%" in code:
        return "percent", decimals, thousands
    if "₫" in code:
        return "currency_vnd", decimals, thousands
    if code.startswith("$"):
        return "currency_usd", decimals, thousands
    # Mã thuần số "0" / "#,##0.00"
    if set(body) <= set("#,0."):
        return "number", decimals, thousands
    return "custom", decimals, thousands


class FormatCellsDialog(QDialog):
    def __init__(self, parent, fmt: dict, sample_value=None):
        super().__init__(parent)
        self.setWindowTitle(tr("format_cells"))
        self.setStyleSheet(MENU_QSS)
        self._sample_value = sample_value if isinstance(sample_value, (int, float)) else 1234.567
        self.setMinimumWidth(420)

        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._build_number_tab(fmt), tr("fc_tab_number"))
        self.tabs.addTab(self._build_align_tab(fmt), tr("fc_tab_align"))
        self.tabs.addTab(self._build_font_tab(fmt), tr("fc_tab_font"))
        self.tabs.addTab(self._build_border_tab(), tr("fc_tab_border"))
        self.tabs.addTab(self._build_fill_tab(fmt), tr("fc_tab_fill"))
        self.tabs.addTab(self._build_protect_tab(fmt), tr("fc_tab_protect"))

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("ok"))
        bb.button(QDialogButtonBox.Cancel).setText(tr("cancel"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        root.addWidget(bb)

        # Chụp trạng thái khởi tạo để biết người dùng đổi gì.
        self._init_state = self._collect()

    # ------------------------------------------------------------ Số
    def _build_number_tab(self, fmt: dict) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        cat, decimals, thousands = _parse_code(fmt.get("number_format"))

        self._cat_list = QListWidget()
        for key, label in _NUM_CATS:
            self._cat_list.addItem(tr(label))
        self._cat_keys = [k for k, _ in _NUM_CATS]
        self._cat_list.setCurrentRow(self._cat_keys.index(cat))
        lay.addWidget(QLabel(tr("fc_category")))
        lay.addWidget(self._cat_list)

        self._dec_spin = QSpinBox()
        self._dec_spin.setRange(0, 15)
        self._dec_spin.setValue(decimals)
        self._thousands_cb = QCheckBox(tr("fc_thousands"))
        self._thousands_cb.setChecked(thousands)
        self._custom_edit = QLineEdit(fmt.get("number_format") or "")
        form = QFormLayout()
        form.addRow(tr("fc_decimals"), self._dec_spin)
        form.addRow("", self._thousands_cb)
        form.addRow(tr("fc_custom_code"), self._custom_edit)
        lay.addLayout(form)

        self._sample_lbl = QLabel()
        lay.addWidget(self._sample_lbl)

        for sig in (self._cat_list.currentRowChanged, self._dec_spin.valueChanged):
            sig.connect(self._refresh_number_tab)
        self._thousands_cb.toggled.connect(self._refresh_number_tab)
        self._custom_edit.textChanged.connect(self._refresh_number_tab)
        self._refresh_number_tab()
        return w

    def _current_cat(self) -> str:
        return self._cat_keys[self._cat_list.currentRow()]

    def _refresh_number_tab(self, *_):
        cat = self._current_cat()
        self._dec_spin.setEnabled(cat in _DEC_CATS)
        self._thousands_cb.setEnabled(cat in _THOUSANDS_CATS)
        self._custom_edit.setEnabled(cat == "custom")
        code = self._number_code()
        shown = _apply_number_format(self._sample_value, code) if code else None
        if shown is None:
            shown = format(self._sample_value, ".2f")
        self._sample_lbl.setText(f"{tr('fc_sample')} {shown}")

    def _number_code(self):
        return _build_code(
            self._current_cat(), self._dec_spin.value(),
            self._thousands_cb.isChecked(), self._custom_edit.text().strip(),
        )

    # ------------------------------------------------------------ Căn lề
    def _build_align_tab(self, fmt: dict) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._halign = QComboBox()
        self._halign_vals = [None, "left", "center", "right"]
        for k in ("fc_halign_general", "align_left", "align_center", "align_right"):
            self._halign.addItem(tr(k))
        self._halign.setCurrentIndex(self._halign_vals.index(fmt.get("halign")))

        self._valign = QComboBox()
        self._valign_vals = ["top", "middle", "bottom"]
        for k in ("valign_top", "valign_middle", "valign_bottom"):
            self._valign.addItem(tr(k))
        self._valign.setCurrentIndex(self._valign_vals.index(fmt.get("valign", "bottom")))

        self._wrap_cb = QCheckBox(tr("wrap"))
        self._wrap_cb.setChecked(bool(fmt.get("wrap")))
        form.addRow(tr("fc_horizontal"), self._halign)
        form.addRow(tr("fc_vertical"), self._valign)
        form.addRow("", self._wrap_cb)
        return w

    # ------------------------------------------------------------ Phông chữ
    def _build_font_tab(self, fmt: dict) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._font_combo = QFontComboBox()
        if fmt.get("font"):
            self._font_combo.setEditText(fmt["font"])
        self._size_spin = QSpinBox()
        self._size_spin.setRange(6, 96)
        self._size_spin.setValue(int(fmt.get("size") or 11))
        self._bold_cb = QCheckBox(tr("bold")); self._bold_cb.setChecked(bool(fmt.get("bold")))
        self._italic_cb = QCheckBox(tr("italic")); self._italic_cb.setChecked(bool(fmt.get("italic")))
        self._uline_cb = QCheckBox(tr("underline")); self._uline_cb.setChecked(bool(fmt.get("underline")))
        self._strike_cb = QCheckBox(tr("strike")); self._strike_cb.setChecked(bool(fmt.get("strike")))
        self._color = fmt.get("color")
        self._color_btn = QPushButton(tr("fc_pick_color"))
        self._color_btn.clicked.connect(lambda: self._pick("_color", self._color_btn, "font_color"))
        self._color_reset = QPushButton(tr("fc_no_color"))
        self._color_reset.clicked.connect(lambda: self._reset_color("_color", self._color_btn))
        self._sync_swatch(self._color_btn, self._color)

        form.addRow(tr("fc_font_family"), self._font_combo)
        form.addRow(tr("fc_font_size"), self._size_spin)
        form.addRow("", self._bold_cb)
        form.addRow("", self._italic_cb)
        form.addRow("", self._uline_cb)
        form.addRow("", self._strike_cb)
        crow = QHBoxLayout(); crow.addWidget(self._color_btn); crow.addWidget(self._color_reset)
        cw = QWidget(); cw.setLayout(crow)
        form.addRow(tr("font_color"), cw)
        return w

    # ------------------------------------------------------------ Viền
    def _build_border_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self._border_combo = QComboBox()
        # None = "không đổi" (giữ nguyên viền hiện có).
        self._border_vals = [None, "none", "outer", "all", "top", "bottom", "left", "right"]
        labels = ["—", "border_none", "border_outer", "border_all",
                  "border_top", "border_bottom", "border_left", "border_right"]
        for k in labels:
            self._border_combo.addItem(k if k == "—" else tr(k))
        form.addRow(tr("fc_border_preset"), self._border_combo)
        return w

    # ------------------------------------------------------------ Tô màu
    def _build_fill_tab(self, fmt: dict) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self._bg = fmt.get("bg")
        self._bg_btn = QPushButton(tr("fc_pick_color"))
        self._bg_btn.clicked.connect(lambda: self._pick("_bg", self._bg_btn, "fill_color"))
        self._bg_reset = QPushButton(tr("fc_no_fill"))
        self._bg_reset.clicked.connect(lambda: self._reset_color("_bg", self._bg_btn))
        self._sync_swatch(self._bg_btn, self._bg)
        row = QHBoxLayout(); row.addWidget(self._bg_btn); row.addWidget(self._bg_reset)
        lay.addLayout(row)
        lay.addStretch()
        return w

    # ------------------------------------------------------------ Bảo vệ
    def _build_protect_tab(self, fmt: dict) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        self._locked_cb = QCheckBox(tr("fc_locked"))
        self._locked_cb.setChecked(bool(fmt.get("locked", True)))  # Excel: ô khóa mặc định
        self._hidden_cb = QCheckBox(tr("fc_hidden"))
        self._hidden_cb.setChecked(bool(fmt.get("hidden")))
        note = QLabel(tr("fc_protect_note")); note.setWordWrap(True)
        lay.addWidget(self._locked_cb)
        lay.addWidget(self._hidden_cb)
        lay.addWidget(note)
        lay.addStretch()
        return w

    # ------------------------------------------------------------ tiện ích màu
    def _pick(self, attr: str, btn: QPushButton, title_key: str):
        cur = getattr(self, attr)
        c = QColorDialog.getColor(QColor(cur) if cur else QColor("#000000"), self, tr(title_key))
        if c.isValid():
            setattr(self, attr, c.name())
            self._sync_swatch(btn, c.name())

    def _reset_color(self, attr: str, btn: QPushButton):
        setattr(self, attr, None)
        self._sync_swatch(btn, None)

    def _sync_swatch(self, btn: QPushButton, color):
        if color:
            btn.setStyleSheet(f"background:{color}; padding:4px;")
        else:
            btn.setStyleSheet("padding:4px;")

    # ------------------------------------------------------------ kết quả
    def _collect(self) -> dict:
        """Trạng thái hiện tại của mọi widget dưới dạng thuộc tính model.

        ``changes()`` so cái này với snapshot lúc mở dialog -> widget không đổi
        cho cùng giá trị nên tự loại, khỏi ghi đè thuộc tính người dùng không sờ tới.
        """
        return {
            "number_format": self._number_code(),
            "halign": self._halign_vals[self._halign.currentIndex()],
            "valign": self._valign_vals[self._valign.currentIndex()],
            "wrap": self._wrap_cb.isChecked() or None,
            "font": self._font_combo.currentText(),
            "size": self._size_spin.value(),
            "bold": self._bold_cb.isChecked() or None,
            "italic": self._italic_cb.isChecked() or None,
            "underline": self._uline_cb.isChecked() or None,
            "strike": self._strike_cb.isChecked() or None,
            "color": self._color,
            "bg": self._bg,
            # locked: giữ bool (KHÔNG `or None`) — ô khóa mặc định True, phải lưu
            # được trạng thái False khi người dùng mở khóa. hidden mặc định False
            # nên `or None` để khỏi ghi key thừa.
            "locked": self._locked_cb.isChecked(),
            "hidden": self._hidden_cb.isChecked() or None,
        }

    def changes(self) -> dict:
        """Chỉ những thuộc tính người dùng đã đổi so với lúc mở dialog."""
        cur = self._collect()
        out = {}
        for k, v in cur.items():
            if v != self._init_state.get(k):
                out[k] = v
        return out

    def border_kind(self):
        return self._border_vals[self._border_combo.currentIndex()]
