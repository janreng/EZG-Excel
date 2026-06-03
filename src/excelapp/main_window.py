"""Cửa sổ chính của ứng dụng bảng tính."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QEvent, QSettings, Qt, QThread, Signal
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPalette,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabBar,
    QTableView,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__, formula, io_utils, shortcuts, updater
from . import statusbar_stats as sbstats
from .autosum import autosum_formula
from .cell_mode import CellMode, ModeEvent, transition as mode_transition
from .format_dialog import FormatCellsDialog
from .freeze import FreezeManager
from .i18n import current_lang, load_lang, set_lang, tr
from .icons import make_icon
from .resources import icon_path
from .table_model import SpreadsheetModel
from .ui_style import MENU_QSS
from .view import SpreadsheetView


def _natural_key(s: str):
    """Khóa sắp xếp tự nhiên: số trong chuỗi so sánh theo giá trị số."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


class _IoWorker(QThread):
    """Chạy io_utils.load_file / save_file trên thread riêng, không chặn UI."""

    finished: Signal = Signal(object)  # kết quả (rows khi load, None khi save)
    failed: Signal = Signal(str)       # thông báo lỗi

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.finished.emit(self._fn())
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class _RibbonSection(QWidget):
    """Một section trong ribbon: hàng nút phía trên + label phía dưới."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(4, 2, 4, 0)
        vlay.setSpacing(0)

        self._btn_area = QWidget()
        self._btn_area.setStyleSheet("QWidget { background: transparent; }")
        self._btn_layout = QHBoxLayout(self._btn_area)
        self._btn_layout.setContentsMargins(0, 0, 0, 0)
        self._btn_layout.setSpacing(2)
        self._btn_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._label_w = QLabel(label)
        self._label_w.setAlignment(Qt.AlignCenter)
        self._label_w.setStyleSheet(
            "QLabel { font-size: 10px; color: #6d6d6d; padding: 1px 0; background: transparent; }"
        )

        vlay.addWidget(self._btn_area, 1)
        vlay.addWidget(self._label_w)

    def add_widget(self, w: QWidget) -> None:
        self._btn_layout.addWidget(w)

    def add_stretch(self) -> None:
        self._btn_layout.addStretch()


class _RibbonBar(QWidget):
    """Ribbon chứa các section, có separator dọc giữa các section."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(68)
        self.setStyleSheet(
            "_RibbonBar { background: #F3F3F3; border-bottom: 1px solid #D0D0D0; }"
            "QToolButton { border: none; border-radius: 3px; padding: 4px 6px;"
            "  min-width: 26px; min-height: 26px; font-size: 13px; color: #3c3c3c; }"
            "QToolButton:hover   { background: #E5E5E5; }"
            "QToolButton:pressed { background: #CCCCCC; }"
            "QToolButton:checked { background: #D9EAD3; color: #217346; }"
            "QComboBox  { border: 1px solid #D0D0D0; background: white;"
            "  padding: 2px 4px; border-radius: 2px; font-size: 12px; color: #1c1c1c; }"
            "QComboBox:hover { border-color: #217346; }"
            "QFontComboBox { border: 1px solid #D0D0D0; background: white;"
            "  padding: 2px 4px; border-radius: 2px; font-size: 12px; color: #1c1c1c; }"
            "QFontComboBox:hover { border-color: #217346; }"
            # Popup danh sách của combo: nền trắng, chữ đen (nếu không style sẽ
            # đen xì do stylesheet một phần). Áp cho cả QComboBox & QFontComboBox.
            "QComboBox QAbstractItemView {"
            "  background: white; color: #1c1c1c; border: 1px solid #D0D0D0;"
            "  selection-background-color: #217346; selection-color: white;"
            "  outline: none; }"
        )
        self._hlay = QHBoxLayout(self)
        self._hlay.setContentsMargins(6, 0, 6, 0)
        self._hlay.setSpacing(0)
        self._sections: list[_RibbonSection] = []

    def add_section(self, label: str) -> "_RibbonSection":
        if self._sections:
            sep = QFrame(self)
            sep.setFrameShape(QFrame.VLine)
            sep.setFixedWidth(1)
            sep.setStyleSheet("QFrame { background: #D0D0D0; margin: 6px 4px; }")
            self._hlay.addWidget(sep)
        sec = _RibbonSection(label, self)
        self._hlay.addWidget(sec)
        self._sections.append(sec)
        return sec

    def add_stretch(self) -> None:
        self._hlay.addStretch()


class _Sheet:
    """Một sheet trong workbook: model dữ liệu + state UI riêng (lọc, freeze)."""

    __slots__ = ("model", "name", "filters", "freeze_rows", "freeze_cols")

    def __init__(self, model, name: str, filters: dict | None = None):
        self.model = model
        self.name = name
        self.filters = filters if filters is not None else {}
        self.freeze_rows = 0
        self.freeze_cols = 0


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        load_lang()
        self.current_path: Path | None = None
        self.model = SpreadsheetModel()
        self._clip: dict | None = None  # clipboard nội bộ (giữ công thức gốc)
        self._replace_dialog: QDialog | None = None
        self._find_dialog: QDialog | None = None
        self._actions: dict[str, QAction] = {}  # phím tắt tùy chỉnh
        self._updating_toolbar = False
        self._fx_picking = False  # True khi đang soạn công thức (bấm ô chèn ref)
        self._cell_mode = CellMode.READY  # Spec 03 — khởi tạo sớm trước khi nối signal
        self._stat_items = self._load_stat_items()  # Spec 11.2 — item nào hiện ở status bar
        self._filters: dict[int, set] = {}  # cột -> tập giá trị được phép hiện

        if os.path.exists(icon_path()):
            self.setWindowIcon(QIcon(icon_path()))
        self._build_ui()
        self._build_toolbar()
        self._build_menu()
        self._style_chrome()
        self._update_title()
        self.resize(1000, 650)

    def _style_chrome(self) -> None:
        """Giao diện menu/toolbar kiểu Microsoft Excel."""
        self.menuBar().setStyleSheet(
            """
            QMenuBar { background: #217346; border-bottom: none;
                       padding: 2px 6px; font-size: 13px; color: #ffffff; }
            QMenuBar::item { padding: 5px 10px; margin: 0 1px; background: transparent;
                             border-radius: 3px; color: #ffffff; }
            QMenuBar::item:selected { background: #185c37; }
            QMenuBar::item:pressed  { background: #145228; }
            QMenu { background: #ffffff; border: 1px solid #C0C0C0; padding: 4px; }
            QMenu::item { padding: 6px 28px 6px 16px; border-radius: 2px; color: #1c1c1c; }
            QMenu::item:selected { background: #EBF3E8; color: #217346; }
            QMenu::separator { height: 1px; background: #D0D0D0; margin: 4px 8px; }
            """
        )
        # Ribbon đã có stylesheet riêng trong _RibbonBar — toolbar holder chỉ cần trong suốt
        if hasattr(self, "_toolbar"):
            self._toolbar.setStyleSheet(
                "QToolBar { background: #F3F3F3; border: none; padding: 0; margin: 0; }"
            )

    # ------------------------------------------------------------ dựng UI
    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ---- Thanh công thức kiểu Excel ----
        formula_bar = QWidget()
        formula_bar.setFixedHeight(28)
        formula_bar.setStyleSheet(
            "QWidget { background: #ffffff; border-bottom: 1px solid #D0D0D0; }"
        )
        fb_layout = QHBoxLayout(formula_bar)
        fb_layout.setContentsMargins(4, 2, 4, 2)
        fb_layout.setSpacing(0)

        # Name Box — QLineEdit gõ được để navigate
        self.name_box = QLineEdit("A1")
        self.name_box.setObjectName("name_box")
        self.name_box.setFixedWidth(80)
        self.name_box.setAlignment(Qt.AlignCenter)
        self.name_box.setStyleSheet(
            "QLineEdit#name_box {"
            "  border: 1px solid #D0D0D0; background: white;"
            "  padding: 1px 4px; font-size: 12px; border-radius: 0;"
            "}"
            "QLineEdit#name_box:focus { border-color: #217346; }"
        )
        self.name_box.returnPressed.connect(self._navigate_to_name_box)
        self.name_box.installEventFilter(self)  # Esc -> khôi phục, trả focus về lưới
        fb_layout.addWidget(self.name_box)

        # Separator dọc
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("QFrame { border: none; background: #D0D0D0; max-width: 1px; margin: 4px 6px; }")
        fb_layout.addWidget(sep)

        # Nút ✕ và ✓ (ẩn mặc định, hiện khi đang sửa)
        self.btn_cancel_edit = QToolButton()
        self.btn_cancel_edit.setText("✕")
        self.btn_cancel_edit.setFixedSize(22, 22)
        self.btn_cancel_edit.setStyleSheet(
            "QToolButton { border: none; color: #595959; font-size: 12px; }"
            "QToolButton:hover { color: #c0392b; }"
        )
        self.btn_cancel_edit.setVisible(False)
        self.btn_cancel_edit.clicked.connect(self._cancel_formula_edit)
        fb_layout.addWidget(self.btn_cancel_edit)

        self.btn_accept_edit = QToolButton()
        self.btn_accept_edit.setText("✓")
        self.btn_accept_edit.setFixedSize(22, 22)
        self.btn_accept_edit.setStyleSheet(
            "QToolButton { border: none; color: #595959; font-size: 12px; }"
            "QToolButton:hover { color: #217346; }"
        )
        self.btn_accept_edit.setVisible(False)
        self.btn_accept_edit.clicked.connect(self._commit_formula_bar)
        fb_layout.addWidget(self.btn_accept_edit)

        # Nút fx
        self.btn_fx = QToolButton()
        self.btn_fx.setText("ƒx")
        self.btn_fx.setFixedSize(28, 22)
        self.btn_fx.setStyleSheet(
            "QToolButton { border: none; color: #217346; font-style: italic;"
            " font-size: 13px; font-weight: bold; }"
            "QToolButton:hover { background: #EBF3E8; border-radius: 2px; }"
        )
        fb_layout.addWidget(self.btn_fx)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("QFrame { border: none; background: #D0D0D0; max-width: 1px; margin: 4px 4px; }")
        fb_layout.addWidget(sep2)

        # Formula input
        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText(tr("formula_placeholder"))
        self.formula_edit.setStyleSheet(
            "QLineEdit { border: none; background: white; padding: 1px 4px; font-size: 12px; }"
            "QLineEdit:focus { border-bottom: 1px solid #217346; }"
        )
        self.formula_edit.returnPressed.connect(self._commit_formula_bar)
        self.formula_edit.textEdited.connect(self._on_formula_edited)
        fb_layout.addWidget(self.formula_edit, 1)

        layout.addWidget(formula_bar)

        # Giữ cell_label alias để code cũ không bị vỡ
        self.cell_label = self.name_box

        # Go To: F5 và Ctrl+G focus Name Box (như Excel). App-wide.
        for seq in ("F5", "Ctrl+G"):
            sc = QShortcut(QKeySequence(seq), self)
            sc.activated.connect(self._focus_name_box)

        # ---- Bảng lưới ----
        self.view = SpreadsheetView()
        self.view.setModel(self.model)
        self.model.mergesChanged.connect(self.view.refresh_spans)
        self.view.refresh_spans()
        # ExtendedSelection: kéo = 1 vùng, Ctrl+Click = thêm vùng rời, Shift = mở rộng (như Excel).
        self.view.setSelectionMode(QTableView.ExtendedSelection)
        self.view.horizontalHeader().setSectionsClickable(True)
        self.view.verticalHeader().setSectionsClickable(True)
        self.view.horizontalHeader().sectionDoubleClicked.connect(self._sort_by_header)
        # Bấm tiêu đề cột/hàng -> bôi đen cả cột/hàng đó (như Excel).
        self.view.horizontalHeader().sectionClicked.connect(self.view.selectColumn)
        self.view.verticalHeader().sectionClicked.connect(self.view.selectRow)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self.view.horizontalHeader().filterClicked.connect(self._open_filter_dialog)
        # Soạn công thức: bấm ô để chèn tham chiếu (như Excel).
        self.view.formula_pick_active = lambda: self._fx_picking
        self.view.cellPicked.connect(self._insert_cell_ref)
        # Cell Mode indicator (Spec 03): bắt đầu/kết thúc sửa ô trong lưới.
        self.view.editStarted.connect(self._on_edit_started)
        self.view.itemDelegate().closeEditor.connect(self._on_editor_closed)
        self._wire_selection()
        layout.addWidget(self.view, 1)

        self.freeze = FreezeManager(self.view)

        # ---- Sheet tab bar kiểu Excel (dưới cùng) + nút thêm sheet ----
        tab_row = QWidget()
        tab_h = QHBoxLayout(tab_row)
        tab_h.setContentsMargins(0, 0, 0, 0)
        tab_h.setSpacing(0)
        self.sheet_tabs = QTabBar()
        self.sheet_tabs.setShape(QTabBar.RoundedSouth)
        self.sheet_tabs.setExpanding(False)
        self.sheet_tabs.setMovable(True)
        self.sheet_tabs.setStyleSheet(
            "QTabBar { background: #D9D9D9; border-top: 1px solid #C0C0C0; }"
            "QTabBar::tab {"
            "  background: #D9D9D9; border: 1px solid #C0C0C0;"
            "  border-bottom: none; border-top-left-radius: 3px; border-top-right-radius: 3px;"
            "  padding: 3px 18px; font-size: 12px; color: #595959;"
            "  margin-right: 2px; }"
            "QTabBar::tab:selected {"
            "  background: #ffffff; color: #217346; font-weight: bold;"
            "  border-bottom: 2px solid #217346; }"
            "QTabBar::tab:hover:!selected { background: #E5E5E5; }"
        )
        self.sheet_tabs.currentChanged.connect(self._activate_sheet)
        self.sheet_tabs.tabBarDoubleClicked.connect(self._rename_sheet)
        self.sheet_tabs.tabMoved.connect(self._on_tab_moved)
        self.sheet_tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sheet_tabs.customContextMenuRequested.connect(self._sheet_context_menu)
        self.btn_add_sheet = QToolButton()
        self.btn_add_sheet.setText("+")
        self.btn_add_sheet.setToolTip(tr("sheet_add"))
        self.btn_add_sheet.setStyleSheet(
            "QToolButton { background: #D9D9D9; border: none; padding: 2px 10px;"
            " font-size: 15px; color: #217346; } QToolButton:hover { background: #E5E5E5; }"
        )
        self.btn_add_sheet.clicked.connect(self.add_sheet)
        tab_h.addWidget(self.sheet_tabs)
        tab_h.addWidget(self.btn_add_sheet)
        tab_h.addStretch()
        layout.addWidget(tab_row)

        # Khởi tạo workbook với một sheet (model đã tạo ở __init__).
        self.sheets: list[_Sheet] = [_Sheet(self.model, "Sheet1", self._filters)]
        self._active = 0
        self.sheet_tabs.blockSignals(True)
        self.sheet_tabs.addTab("Sheet1")
        self.sheet_tabs.blockSignals(False)

        self.setCentralWidget(central)

        # ---- Status bar ----
        # Cell Mode indicator (Ready/Enter/Edit/Point) — góc trái như Excel.
        self._mode_label = QLabel("")
        self._mode_label.setStyleSheet(
            "QLabel { color: #444; font-size: 12px; padding: 0 10px; }"
        )
        self.statusBar().addWidget(self._mode_label)
        self._set_cell_mode(CellMode.READY)
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("QLabel { color: #595959; font-size: 12px; padding: 0 8px; }")
        self.statusBar().addPermanentWidget(self._stats_label)
        # Right-click status bar -> bật/tắt item thống kê (Spec 11.2), lưu QSettings.
        self.statusBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.statusBar().customContextMenuRequested.connect(self._show_statusbar_menu)
        self._stats_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self._stats_label.customContextMenuRequested.connect(
            lambda pos: self._show_statusbar_menu(self._stats_label.mapTo(self.statusBar(), pos))
        )
        # Zoom indicator (Spec 11.3): hiện % phóng to; bấm để về 100%.
        self._zoom_btn = QToolButton()
        self._zoom_btn.setText(f"{self.view.zoom_percent()}%")
        self._zoom_btn.setToolTip(tr("zoom_reset_tip"))
        self._zoom_btn.setAutoRaise(True)
        self._zoom_btn.setStyleSheet(
            "QToolButton { color: #595959; font-size: 12px; padding: 0 8px; border: none; }"
            "QToolButton:hover { background: #E5E5E5; }"
        )
        self._zoom_btn.clicked.connect(lambda: self.view.set_zoom(100))
        self.statusBar().addPermanentWidget(self._zoom_btn)
        self.view.zoomChanged.connect(lambda pct: self._zoom_btn.setText(f"{pct}%"))
        self._version_label = QLabel(f"  {APP_NAME} v{__version__}  ")
        self._version_label.setStyleSheet("QLabel { color: #888; font-size: 11px; }")
        self.statusBar().addPermanentWidget(self._version_label)
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #F3F3F3; border-top: 1px solid #D0D0D0; font-size: 12px; }"
        )

    def _build_toolbar(self) -> None:
        # Dùng QToolBar ẩn để giữ shortcut và action tương thích menu
        hidden_tb = QToolBar()
        hidden_tb.setVisible(False)
        self.addToolBar(hidden_tb)

        # Ribbon bar thực sự (widget tự vẽ, không phải QToolBar)
        self._ribbon = _RibbonBar()
        # Đặt ribbon vào vị trí toolbar area
        tb_holder = QToolBar()
        tb_holder.setMovable(False)
        tb_holder.setFloatable(False)
        tb_holder.setContentsMargins(0, 0, 0, 0)
        w_holder = QWidget()
        hl = QHBoxLayout(w_holder)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        hl.addWidget(self._ribbon)
        tb_holder.addWidget(w_holder)
        tb_holder.setStyleSheet(
            "QToolBar { background: #F3F3F3; border: none; padding: 0; margin: 0; spacing: 0; }"
        )
        self.addToolBar(tb_holder)
        self._toolbar = tb_holder  # cho _style_chrome

        # ---- Section: Clipboard ----
        sec_clip = self._ribbon.add_section(tr("sec_clipboard"))
        btn_paste = self._ribbon_btn(sec_clip, "paste", tr("paste"), self.paste_clipboard)
        btn_cut   = self._ribbon_btn(sec_clip, "cut",   tr("cut"),   self.cut_selection)
        btn_copy  = self._ribbon_btn(sec_clip, "copy",  tr("copy"),  self.copy_selection)

        # ---- Section: Hoàn tác ----
        sec_undo = self._ribbon.add_section(tr("sec_undo"))
        self._ribbon_btn(sec_undo, "undo", tr("undo"), self.undo)
        self._ribbon_btn(sec_undo, "redo", tr("redo"), self.redo)

        # ---- Section: Phông chữ ----
        sec_font = self._ribbon.add_section(tr("sec_font"))
        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(160)
        self.font_combo.setToolTip(tr("tooltip_font"))
        self.font_combo.currentFontChanged.connect(
            lambda f: self._apply_format(font=f.family())
        )
        sec_font.add_widget(self.font_combo)

        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.addItems(
            ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48"]
        )
        self.size_combo.setCurrentText("10")
        self.size_combo.setMaximumWidth(52)
        self.size_combo.setToolTip(tr("tooltip_size"))
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        sec_font.add_widget(self.size_combo)

        # Ép popup combo nền trắng chữ đen (tránh Windows dark mode làm đen xì).
        for _combo in (self.font_combo, self.size_combo):
            self._force_light_popup(_combo)

        # B / I / U / S — hiện chữ cái có style
        self.btn_bold   = self._ribbon_toggle(sec_font, "B", tr("bold"),      "bold",      bold=True)
        self.btn_italic = self._ribbon_toggle(sec_font, "I", tr("italic"),    "italic",    italic=True)
        self.btn_uline  = self._ribbon_toggle(sec_font, "U", tr("underline"), "underline", underline=True)
        self.btn_strike = self._ribbon_toggle(sec_font, "S", tr("strike"),    "strike",    strike=True)
        # QAction aliases để menu/shortcut vẫn hoạt động
        self.act_bold   = self.btn_bold.defaultAction()
        self.act_italic = self.btn_italic.defaultAction()

        # Màu chữ / màu nền (mở hộp chọn màu)
        self.btn_fontcolor = self._ribbon_btn(
            sec_font, "font_color", tr("font_color"), lambda: self._pick_color("color"))
        self.btn_fillcolor = self._ribbon_btn(
            sec_font, "fill_color", tr("fill_color"), lambda: self._pick_color("bg"))

        # ---- Section: Viền & Số ----
        sec_cell = self._ribbon.add_section(tr("sec_cell"))
        self.btn_border = self._ribbon_menu(
            sec_cell, "borders", tr("borders_tip"),
            [("border_all", lambda: self._apply_border("all")),
             ("border_outer", lambda: self._apply_border("outer")),
             ("border_top", lambda: self._apply_border("top")),
             ("border_bottom", lambda: self._apply_border("bottom")),
             ("border_left", lambda: self._apply_border("left")),
             ("border_right", lambda: self._apply_border("right")),
             ("border_none", lambda: self._apply_border("none"))],
        )
        self.btn_numfmt = self._ribbon_menu(
            sec_cell, "number_format", tr("number_format_tip"),
            [("numfmt_general", lambda: self._apply_format(number_format=None)),
             ("numfmt_number", lambda: self._apply_format(number_format="#,##0.00")),
             ("numfmt_percent", lambda: self._apply_format(number_format="0%")),
             ("numfmt_vnd", lambda: self._apply_format(number_format="#,##0₫")),
             ("numfmt_usd", lambda: self._apply_format(number_format="$#,##0.00")),
             ("numfmt_date", lambda: self._apply_format(number_format="dd/mm/yyyy")),
             ("numfmt_time", lambda: self._apply_format(number_format="hh:mm:ss")),
             ("numfmt_scientific", lambda: self._apply_format(number_format="0.00E+00"))],
        )
        self.btn_merge = self._ribbon_btn(
            sec_cell, "merge", tr("merge_tip"), self._toggle_merge)
        self.btn_cond = self._ribbon_menu(
            sec_cell, "cond_format", tr("cond_tip"),
            [("cond_add", self.show_conditional_format),
             ("cond_clear", self._clear_conditional)],
        )

        # ---- Section: Căn lề ----
        sec_align = self._ribbon.add_section(tr("sec_alignment"))
        self.halign_btn = self._ribbon_dropdown(
            sec_align, tr("halign_tip"), "halign", "align_left",
            [("align_left", "align_left", "left"),
             ("align_center", "align_center", "center"),
             ("align_right", "align_right", "right")],
        )
        self.valign_btn = self._ribbon_dropdown(
            sec_align, tr("valign_tip"), "valign", "valign_bottom",
            [("valign_top", "valign_top", "top"),
             ("valign_middle", "valign_middle", "middle"),
             ("valign_bottom", "valign_bottom", "bottom")],
        )
        self.wrap_btn = self._ribbon_dropdown(
            sec_align, tr("wrap_tip"), "wrap", "wrap_overflow",
            [("wrap_overflow", "wrap_overflow", "overflow"),
             ("wrap_text", "wrap_wrap", "wrap"),
             ("wrap_clip", "wrap_clip", "clip")],
        )

        # ---- Section: Sắp xếp & Tìm ----
        sec_edit = self._ribbon.add_section(tr("sec_editing"))
        self._ribbon_btn(sec_edit, "sort_asc",  tr("sort_asc"),  lambda: self._sort_current(True))
        self._ribbon_btn(sec_edit, "sort_desc", tr("sort_desc"), lambda: self._sort_current(False))

        # Filter toggle
        self.btn_filter = QToolButton()
        self.btn_filter.setIcon(make_icon("filter"))
        self.btn_filter.setToolTip(tr("filter_tip"))
        self.btn_filter.setCheckable(True)
        self.btn_filter.toggled.connect(self.toggle_filter)
        sec_edit.add_widget(self.btn_filter)

        self._ribbon_btn(sec_edit, "find", tr("find"), self.show_find)

        self._ribbon.add_stretch()

        # act_filter alias cho toggle_filter
        self.act_filter = QAction(tr("filter_tip"), self, checkable=True)
        self.act_filter.toggled.connect(lambda v: self.btn_filter.setChecked(v))
        self.btn_filter.toggled.connect(lambda v: self.act_filter.setChecked(v))

    # ---- Ribbon helpers ----

    def _force_light_popup(self, combo) -> None:
        """Ép danh sách thả xuống của combo nền trắng chữ đen.

        QSS đặt ở ancestor đôi khi không tới popup (là cửa sổ top-level riêng),
        và Windows dark mode làm nó đen xì. Đặt thẳng stylesheet + palette lên
        view của combo để chắc chắn áp dụng.
        """
        view = combo.view()
        view.setStyleSheet(
            "background:#ffffff; color:#1c1c1c;"
            "selection-background-color:#217346; selection-color:#ffffff;"
        )
        view.setAutoFillBackground(True)
        pal = view.palette()
        pal.setColor(QPalette.Base, QColor("#ffffff"))
        pal.setColor(QPalette.Text, QColor("#1c1c1c"))
        pal.setColor(QPalette.Highlight, QColor("#217346"))
        pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        view.setPalette(pal)
        # Cửa sổ popup chứa view cũng cần palette sáng.
        if view.window() is not None:
            view.window().setPalette(pal)

    def _ribbon_btn(self, section: "_RibbonSection", icon_name: str, tip: str, slot) -> QToolButton:
        """Nút đơn trong ribbon."""
        btn = QToolButton()
        btn.setIcon(make_icon(icon_name))
        btn.setToolTip(tip)
        btn.clicked.connect(slot)
        section.add_widget(btn)
        return btn

    def _ribbon_toggle(self, section: "_RibbonSection", letter: str, tip: str,
                       style: str, **attr) -> QToolButton:
        """Nút toggle định dạng chữ: hiện 1 chữ cái có style (B đậm, I nghiêng,
        U gạch chân, S gạch ngang) thay vì cả từ."""
        btn = QToolButton()
        btn.setText(letter)
        btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        f = QFont()
        f.setPointSize(12)
        if style == "bold":
            f.setBold(True)
        elif style == "italic":
            f.setItalic(True)
        elif style == "underline":
            f.setUnderline(True)
        elif style == "strike":
            f.setStrikeOut(True)
        btn.setFont(f)
        btn.setToolTip(tip)
        btn.setCheckable(True)
        key = next(iter(attr))
        act = QAction(letter, self, checkable=True)  # text = chữ cái, không phải cả từ
        act.setToolTip(tip)
        act.toggled.connect(lambda checked: self._apply_format(**{key: checked}))
        btn.setDefaultAction(act)
        btn.setToolButtonStyle(Qt.ToolButtonTextOnly)  # giữ chỉ-chữ sau setDefaultAction
        section.add_widget(btn)
        return btn

    def _ribbon_dropdown(self, section: "_RibbonSection", tip: str, fmt_key: str,
                         default_icon: str, options: list) -> QToolButton:
        """Nút dropdown định dạng trong ribbon."""
        btn = QToolButton()
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setIcon(make_icon(default_icon))
        btn.setToolTip(tip)
        btn._fmt_key = fmt_key
        btn._default_icon = default_icon
        btn._icon_map = {value: icon for icon, _label, value in options}
        menu = QMenu(btn)
        menu.setStyleSheet(MENU_QSS)  # nền trắng, không bị đen do cascade ribbon
        for icon, label, value in options:
            act = menu.addAction(make_icon(icon), tr(label))
            act.triggered.connect(
                lambda _c=False, k=fmt_key, v=value, b=btn, ic=icon: self._apply_dropdown(k, v, b, ic)
            )
        btn.setMenu(menu)
        section.add_widget(btn)
        return btn

    def _apply_dropdown(self, key, value, btn, icon) -> None:
        self._apply_format(**{key: value})
        btn.setIcon(make_icon(icon))

    def _ribbon_menu(self, section: "_RibbonSection", icon_name: str, tip: str,
                     options: list) -> QToolButton:
        """Nút mở menu chữ (viền, định dạng số...). options: [(label_key, slot)]."""
        btn = QToolButton()
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setIcon(make_icon(icon_name))
        btn.setToolTip(tip)
        menu = QMenu(btn)
        menu.setStyleSheet(MENU_QSS)  # nền trắng, không bị đen do cascade ribbon
        for label_key, slot in options:
            act = menu.addAction(tr(label_key))
            act.triggered.connect(lambda _c=False, s=slot: s())
        btn.setMenu(menu)
        section.add_widget(btn)
        return btn

    def _pick_color(self, key: str) -> None:
        """Mở hộp chọn màu cho 'color' (màu chữ) hoặc 'bg' (màu nền)."""
        box = self._selection_box()
        if box is None:
            return
        cur = self.model.get_format(box[0], box[1]).get(key)
        title = tr("font_color") if key == "color" else tr("fill_color")
        color = QColorDialog.getColor(QColor(cur) if cur else QColor("#000000"), self, title)
        if color.isValid():
            self._apply_format(**{key: color.name()})

    def _apply_border(self, kind: str) -> None:
        boxes = self._selection_ranges()
        if not boxes:
            return
        self.model.set_border_ranges(boxes, kind)

    def _toggle_merge(self) -> None:
        # Gộp/bỏ gộp mọi vùng rời nhất quán trong 1 bước undo (như Excel).
        self.model.toggle_merge_ranges(self._selection_ranges())

    def _clear_conditional(self) -> None:
        self.model.clear_cond_rules(self._selection_box())

    def show_conditional_format(self) -> None:
        """Hộp thoại thêm quy tắc tô màu theo điều kiện cho vùng đang chọn."""
        box = self._selection_box()
        if box is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("cond_title"))
        lay = QVBoxLayout(dlg)

        op_combo = QComboBox()
        for key, label in [("gt", tr("cond_gt")), ("lt", tr("cond_lt")),
                           ("eq", tr("cond_eq")), ("between", tr("cond_between")),
                           ("contains", tr("cond_contains"))]:
            op_combo.addItem(label, key)
        lay.addWidget(op_combo)

        v1 = QLineEdit()
        v1.setPlaceholderText(tr("cond_value"))
        v2 = QLineEdit()
        v2.setPlaceholderText(tr("cond_value2"))
        lay.addWidget(v1)
        lay.addWidget(v2)

        chosen = {"bg": "#FFC7CE"}  # đỏ nhạt kiểu Excel
        color_btn = QPushButton(tr("cond_pick_color"))
        color_btn.setStyleSheet(f"background:{chosen['bg']}")

        def pick():
            c = QColorDialog.getColor(QColor(chosen["bg"]), dlg, tr("fill_color"))
            if c.isValid():
                chosen["bg"] = c.name()
                color_btn.setStyleSheet(f"background:{c.name()}")

        color_btn.clicked.connect(pick)
        lay.addWidget(color_btn)

        def upd():
            v2.setVisible(op_combo.currentData() == "between")

        op_combo.currentIndexChanged.connect(upd)
        upd()

        row = QHBoxLayout()
        ok_btn = QPushButton(tr("ok"))
        cancel_btn = QPushButton(tr("cancel"))
        row.addStretch()
        row.addWidget(ok_btn)
        row.addWidget(cancel_btn)
        lay.addLayout(row)
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)

        if dlg.exec() != QDialog.Accepted:
            return
        op = op_combo.currentData()
        rule = {"box": box, "op": op, "bg": chosen["bg"]}
        if op == "contains":
            rule["v1"] = v1.text()
        else:
            try:
                rule["v1"] = float(v1.text().replace(",", "."))
                if op == "between":
                    rule["v2"] = float(v2.text().replace(",", "."))
            except ValueError:
                QMessageBox.warning(self, tr("cond_title"), tr("cond_invalid"))
                return
        self.model.add_cond_rule(rule)

    def _toolbar_toggle(self, tb, text, tip, icon=None, **attr) -> QAction:
        """Legacy helper — chỉ còn dùng cho menu action."""
        act = QAction(text, self, checkable=True)
        if icon:
            act.setIcon(make_icon(icon))
        act.setToolTip(tip)
        key = next(iter(attr))
        act.toggled.connect(lambda checked: self._apply_format(**{key: checked}))
        return act

    def _toolbar_align(self, tb, text, tip, group, icon=None, **attr) -> QAction:
        act = QAction(text, self, checkable=True)
        if icon:
            act.setIcon(make_icon(icon))
        act.setToolTip(tip)
        key, value = next(iter(attr.items()))
        act.triggered.connect(lambda: self._apply_format(**{key: value}))
        group.addAction(act)
        return act

    def _on_size_changed(self, text: str) -> None:
        try:
            size = int(text)
        except ValueError:
            return
        self._apply_format(size=size)

    # ------------------------------------------------------------ áp dụng định dạng
    def _apply_format(self, **attrs) -> None:
        if self._updating_toolbar:
            return  # đang đồng bộ trạng thái nút, không áp dụng
        boxes = self._selection_ranges()
        if not boxes:
            return
        self.model.set_format_ranges(boxes, **attrs)
        if "wrap" in attrs:
            for box in boxes:
                for r in range(box[0], box[2] + 1):
                    self.view.resizeRowToContents(r)

    def show_format_cells(self) -> None:
        """Hộp thoại Định dạng ô (Ctrl+1) — 6 tab, áp cho mọi vùng đang chọn."""
        boxes = self._selection_ranges()
        if not boxes:
            return
        cur = self.view.currentIndex()
        fmt = self.model.get_format(cur.row(), cur.column()) if cur.isValid() else {}
        sample = self.model.cell_value(cur.row(), cur.column()) if cur.isValid() else None
        dlg = FormatCellsDialog(self, fmt, sample_value=sample)
        if dlg.exec() != QDialog.Accepted:
            return
        changes = dlg.changes()
        kind = dlg.border_kind()
        if not changes and kind is None:
            return
        # Một lần OK = một bước undo: gộp định dạng + viền chung.
        self.model.apply_format_and_border(boxes, changes, border_kind=kind)
        if "wrap" in changes:
            for box in boxes:
                for r in range(box[0], box[2] + 1):
                    self.view.resizeRowToContents(r)

    def _build_menu(self) -> None:
        menubar = self.menuBar()
        menubar.clear()

        # --- Tệp ---
        self._actions.clear()
        file_menu = menubar.addMenu(tr("menu_file"))
        self._cmd_action(file_menu, "new", self.new_file)
        self._cmd_action(file_menu, "open", self.open_file)
        file_menu.addSeparator()
        self._cmd_action(file_menu, "save", self.save_file)
        self._cmd_action(file_menu, "save_as", self.save_file_as)
        file_menu.addSeparator()
        self._add_action(file_menu, tr("quit"), self.close, QKeySequence.Quit)

        # --- Sửa ---
        edit_menu = menubar.addMenu(tr("menu_edit"))
        self._cmd_action(edit_menu, "undo", self.undo)
        self._cmd_action(edit_menu, "redo", self.redo)
        edit_menu.addSeparator()
        self._cmd_action(edit_menu, "copy", self.copy_selection)
        self._cmd_action(edit_menu, "cut", self.cut_selection)
        self._cmd_action(edit_menu, "paste", self.paste_clipboard)
        self._cmd_action(edit_menu, "paste_special", self.paste_special)
        self._cmd_action(edit_menu, "clear", self.clear_selection)
        edit_menu.addSeparator()
        self._cmd_action(edit_menu, "fill_down", self.fill_down)
        self._cmd_action(edit_menu, "fill_right", self.fill_right)
        edit_menu.addSeparator()
        self._add_action(
            edit_menu, tr("format_cells"), self.show_format_cells,
            QKeySequence("Ctrl+1"),
        )

        # --- Cấu trúc ---
        struct_menu = menubar.addMenu(tr("menu_structure"))
        self._add_action(struct_menu, tr("insert_row"), self.insert_row_above)
        self._add_action(struct_menu, tr("insert_row_below"), self.insert_row_below)
        self._add_action(struct_menu, tr("insert_col"), self.insert_col_left)
        self._add_action(struct_menu, tr("insert_col_right"), self.insert_col_right)
        struct_menu.addSeparator()
        self._add_action(struct_menu, tr("delete_row"), self.delete_row)
        self._add_action(struct_menu, tr("delete_col"), self.delete_col)

        # --- Dữ liệu ---
        data_menu = menubar.addMenu(tr("menu_data"))
        self._add_action(data_menu, tr("autosum"), self._autosum, QKeySequence("Alt+="))
        self._add_action(
            data_menu, tr("insert_date"), lambda: self._insert_now("date"),
            QKeySequence("Ctrl+;"),
        )
        self._add_action(
            data_menu, tr("insert_time"), lambda: self._insert_now("time"),
            QKeySequence("Ctrl+Shift+;"),
        )
        data_menu.addSeparator()
        self._cmd_action(data_menu, "find", self.show_find)
        self._cmd_action(data_menu, "replace", self.show_replace)
        data_menu.addSeparator()
        self._add_action(data_menu, tr("sort_asc"), lambda: self._sort_current(True))
        self._add_action(data_menu, tr("sort_desc"), lambda: self._sort_current(False))
        data_menu.addSeparator()
        self._add_action(data_menu, tr("filter_menu"), self.show_filter)
        self._add_action(data_menu, tr("clear_filters"), self.clear_filters)

        # --- Xem (Freeze) ---
        view_menu = menubar.addMenu(tr("menu_view"))
        self._build_freeze_menu(view_menu)
        view_menu.addSeparator()
        self.act_show_formulas = QAction(tr("show_formulas"), self)
        self.act_show_formulas.setCheckable(True)
        self.act_show_formulas.setShortcut(QKeySequence("Ctrl+`"))
        self.act_show_formulas.setChecked(
            self.model.show_formulas() if hasattr(self, "model") else False
        )
        self.act_show_formulas.toggled.connect(self._toggle_show_formulas)
        view_menu.addAction(self.act_show_formulas)

        # --- Cài đặt ---
        settings_menu = menubar.addMenu(tr("menu_settings"))
        self._add_action(settings_menu, tr("keybindings"), self.show_keybindings)

        # --- Ngôn ngữ ---
        lang_menu = menubar.addMenu(tr("menu_language"))
        group = QActionGroup(self)
        for code, key in (("vi", "lang_vi"), ("en", "lang_en")):
            act = QAction(tr(key), self, checkable=True)
            act.setChecked(current_lang() == code)
            act.triggered.connect(lambda _checked, c=code: self.set_language(c))
            group.addAction(act)
            lang_menu.addAction(act)

        # --- Trợ giúp ---
        help_menu = menubar.addMenu(tr("menu_help"))
        self._add_action(help_menu, tr("check_updates"), self.check_for_updates)
        self._add_action(help_menu, tr("about"), self.show_about)

    def _add_action(self, menu, text, slot, shortcut=None) -> QAction:
        action = QAction(text, self)
        action.triggered.connect(slot)
        if shortcut is not None:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def _cmd_action(self, menu, cmd_id: str, slot) -> QAction:
        """Action có phím tắt tùy chỉnh được (đăng ký theo cmd_id)."""
        action = QAction(tr(cmd_id), self)
        action.triggered.connect(slot)
        seq = shortcuts.get(cmd_id)
        if seq:
            action.setShortcut(QKeySequence(seq))
        self._actions[cmd_id] = action
        menu.addAction(action)
        return action

    # ------------------------------------------------------------ freeze (cố định)
    def _build_freeze_menu(self, menu) -> None:
        cur_r = self.view.currentIndex().row()
        cur_c = self.view.currentIndex().column()
        self._add_action(menu, tr("no_rows"), lambda: self._set_freeze(rows=0))
        self._add_action(menu, tr("one_row"), lambda: self._set_freeze(rows=1))
        self._add_action(menu, tr("two_rows"), lambda: self._set_freeze(rows=2))
        if cur_r >= 0:
            self._add_action(
                menu, tr("up_to_row", n=cur_r + 1), lambda: self._set_freeze(rows=cur_r + 1)
            )
        menu.addSeparator()
        self._add_action(menu, tr("no_cols"), lambda: self._set_freeze(cols=0))
        self._add_action(menu, tr("one_col"), lambda: self._set_freeze(cols=1))
        self._add_action(menu, tr("two_cols"), lambda: self._set_freeze(cols=2))
        if cur_c >= 0:
            label = tr("up_to_col", c=formula.col_index_to_letters(cur_c))
            self._add_action(menu, label, lambda: self._set_freeze(cols=cur_c + 1))

    def _set_freeze(self, rows: int | None = None, cols: int | None = None) -> None:
        if rows is not None:
            self.freeze.rows = rows
        if cols is not None:
            self.freeze.cols = cols
        self.freeze.set_freeze(self.freeze.rows, self.freeze.cols)

    # ------------------------------------------------------------ sheet (workbook)
    def _wire_selection(self) -> None:
        """Nối tín hiệu selection model hiện tại (gọi lại sau mỗi setModel)."""
        sm = self.view.selectionModel()
        sm.currentChanged.connect(self._on_current_changed)
        sm.selectionChanged.connect(self._update_stats)

    def _activate_sheet(self, i: int) -> None:
        if not (0 <= i < len(self.sheets)):
            return
        # Lưu trạng thái freeze của sheet đang hoạt động trước khi chuyển.
        if 0 <= self._active < len(self.sheets):
            cur = self.sheets[self._active]
            cur.freeze_rows = self.freeze.rows
            cur.freeze_cols = self.freeze.cols
        self._active = i
        sheet = self.sheets[i]
        self.model = sheet.model
        self._filters = sheet.filters
        self.view.setModel(self.model)
        self._wire_selection()
        self.freeze.rebind()
        self.freeze.set_freeze(sheet.freeze_rows, sheet.freeze_cols)
        self.view.refresh_spans()
        self._apply_filters()
        self.view.horizontalHeader().refresh(set(self._filters.keys()))
        self.view.setCurrentIndex(self.model.index(0, 0))
        self._sync_show_formulas_check()  # đồng bộ tick "Hiện công thức" theo sheet mới

    def _sync_show_formulas_check(self) -> None:
        """Cập nhật tick menu theo trạng thái show-formulas của model hiện tại.

        Chặn signal để tránh kích lại ``_toggle_show_formulas`` (gây lật ngược).
        """
        act = getattr(self, "act_show_formulas", None)
        if act is None:
            return
        act.blockSignals(True)
        act.setChecked(self.model.show_formulas())
        act.blockSignals(False)

    def _unique_sheet_name(self) -> str:
        existing = {s.name for s in self.sheets}
        n = len(self.sheets) + 1
        while f"Sheet{n}" in existing:
            n += 1
        return f"Sheet{n}"

    def add_sheet(self) -> None:
        model = SpreadsheetModel()
        model.mergesChanged.connect(self.view.refresh_spans)
        name = self._unique_sheet_name()
        self.sheets.append(_Sheet(model, name))
        idx = len(self.sheets) - 1
        self.sheet_tabs.blockSignals(True)
        self.sheet_tabs.addTab(name)
        self.sheet_tabs.blockSignals(False)
        self.sheet_tabs.setCurrentIndex(idx)  # phát currentChanged -> _activate_sheet

    def _delete_sheet(self, i: int) -> None:
        if len(self.sheets) <= 1:
            QMessageBox.information(self, APP_NAME, tr("sheet_min"))
            return
        self.sheets.pop(i)
        new_i = min(i, len(self.sheets) - 1)
        self.sheet_tabs.blockSignals(True)
        self.sheet_tabs.removeTab(i)
        self.sheet_tabs.setCurrentIndex(new_i)
        self.sheet_tabs.blockSignals(False)
        self._active = -1
        self._activate_sheet(new_i)

    def _rename_sheet(self, i: int) -> None:
        if not (0 <= i < len(self.sheets)):
            return
        name, ok = QInputDialog.getText(
            self, tr("sheet_rename"), tr("sheet_name"), text=self.sheets[i].name
        )
        name = name.strip()
        if not ok or not name or name == self.sheets[i].name:
            return
        if any(s.name == name for s in self.sheets):
            QMessageBox.information(self, APP_NAME, tr("sheet_dup"))
            return
        self.sheets[i].name = name
        self.sheet_tabs.setTabText(i, name)

    def _duplicate_sheet(self, i: int) -> None:
        src = self.sheets[i]
        model = SpreadsheetModel()
        model.replace_all_with_fmt(
            src.model.raw_grid(), src.model.all_formats(), src.model.merges()
        )
        model.mergesChanged.connect(self.view.refresh_spans)
        name = self._unique_sheet_name()
        self.sheets.insert(i + 1, _Sheet(model, name))
        self.sheet_tabs.blockSignals(True)
        self.sheet_tabs.insertTab(i + 1, name)
        self.sheet_tabs.blockSignals(False)
        self.sheet_tabs.setCurrentIndex(i + 1)

    def _on_tab_moved(self, frm: int, to: int) -> None:
        self.sheets.insert(to, self.sheets.pop(frm))
        self._active = self.sheet_tabs.currentIndex()

    def _sheet_context_menu(self, pos) -> None:
        i = self.sheet_tabs.tabAt(pos)
        if i < 0:
            return
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)
        menu.addAction(tr("sheet_rename"), lambda: self._rename_sheet(i))
        menu.addAction(tr("sheet_duplicate"), lambda: self._duplicate_sheet(i))
        menu.addAction(tr("sheet_delete"), lambda: self._delete_sheet(i))
        menu.exec(self.sheet_tabs.mapToGlobal(pos))

    def _load_sheets(self, sheets_data: list) -> None:
        """Dựng lại toàn bộ workbook từ danh sách (name, rows, fmt, merges)."""
        self.sheet_tabs.blockSignals(True)
        while self.sheet_tabs.count():
            self.sheet_tabs.removeTab(0)
        self.sheets = []
        for name, rows, fmt, merges in sheets_data:
            model = SpreadsheetModel()
            model.replace_all_with_fmt(rows, fmt, merges)
            model.mergesChanged.connect(self.view.refresh_spans)
            self.sheets.append(_Sheet(model, name))
            self.sheet_tabs.addTab(name)
        self.sheet_tabs.setCurrentIndex(0)
        self.sheet_tabs.blockSignals(False)
        self._active = -1
        self._activate_sheet(0)

    # ------------------------------------------------------------ ngôn ngữ
    def set_language(self, lang: str) -> None:
        if lang == current_lang():
            return
        set_lang(lang)
        self._retranslate()

    def _retranslate(self) -> None:
        self._build_menu()
        self.formula_edit.setPlaceholderText(tr("formula_placeholder"))
        self._set_cell_mode(self._cell_mode)  # cập nhật nhãn mode theo ngôn ngữ mới
        self._update_title()
        # Tooltip trên toolbar.
        self.font_combo.setToolTip(tr("tooltip_font"))
        self.size_combo.setToolTip(tr("tooltip_size"))
        self.act_bold.setToolTip(tr("bold"))
        self.act_italic.setToolTip(tr("italic"))
        self.halign_btn.setToolTip(tr("halign_tip"))
        self.valign_btn.setToolTip(tr("valign_tip"))
        self.wrap_btn.setToolTip(tr("wrap_tip"))
        self.act_filter.setToolTip(tr("filter_tip"))
        # Hộp thoại sẽ dựng lại theo ngôn ngữ mới ở lần mở kế tiếp.
        for attr in ("_replace_dialog", "_find_dialog"):
            dlg = getattr(self, attr)
            if dlg is not None:
                dlg.deleteLater()
                setattr(self, attr, None)

    # ------------------------------------------------------------ menu chuột phải
    def _show_context_menu(self, pos) -> None:
        index = self.view.indexAt(pos)
        # Nếu bấm vào ô ngoài vùng chọn -> chọn ô đó trước. Dùng selection().contains()
        # (theo range) thay vì selectedIndexes() để khỏi liệt kê hàng vạn ô khi chọn cả cột.
        if index.isValid() and not self.view.selectionModel().selection().contains(index):
            self.view.setCurrentIndex(index)

        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)
        self._add_action(menu, tr("copy"), self.copy_selection)
        self._add_action(menu, tr("cut"), self.cut_selection)
        self._add_action(menu, tr("paste"), self.paste_clipboard)
        menu.addSeparator()
        self._add_action(menu, tr("insert_row"), self.insert_row_above)
        self._add_action(menu, tr("insert_row_below"), self.insert_row_below)
        self._add_action(menu, tr("insert_col"), self.insert_col_left)
        self._add_action(menu, tr("insert_col_right"), self.insert_col_right)
        self._add_action(menu, tr("delete_row"), self.delete_row)
        self._add_action(menu, tr("delete_col"), self.delete_col)
        menu.addSeparator()
        self._add_action(menu, tr("clear"), self.clear_selection)
        menu.exec(self.view.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------ Cell Mode (Spec 03)
    def _set_cell_mode(self, mode: CellMode) -> None:
        """Đặt mode hiện tại + cập nhật nhãn Status Bar (Ready/Enter/Edit/Point)."""
        self._cell_mode = mode
        labels = {
            CellMode.READY: tr("mode_ready"),
            CellMode.ENTER: tr("mode_enter"),
            CellMode.EDIT: tr("mode_edit"),
            CellMode.POINT: tr("mode_point"),
        }
        self._mode_label.setText(labels.get(mode, ""))

    def _apply_mode_event(self, event: ModeEvent) -> None:
        """Chạy 1 transition của state machine; đổi nhãn nếu mode thay đổi."""
        new = mode_transition(self._cell_mode, event)
        if new != self._cell_mode:
            self._set_cell_mode(new)

    def _on_edit_started(self, is_enter: bool) -> None:
        """View bắt đầu sửa ô: gõ ký tự -> Enter; F2/double-click -> Edit."""
        self._apply_mode_event(
            ModeEvent.TYPE_CHAR if is_enter else ModeEvent.DBLCLICK_DATA
        )

    def _on_editor_closed(self, _editor=None, hint=None) -> None:
        """Editor trong lưới đóng -> về Ready (trừ khi đang chọn ref).

        Phân biệt hủy (Esc -> RevertModelCache) vs xác nhận để event đúng nghĩa;
        cả hai đều dẫn về Ready nhưng giữ ngữ nghĩa cho logic sau này.
        """
        if self._fx_picking:
            return
        if hint == QAbstractItemDelegate.RevertModelCache:
            self._apply_mode_event(ModeEvent.CANCEL)
        else:
            self._apply_mode_event(ModeEvent.COMMIT)

    # ------------------------------------------------------------ thanh công thức
    def _on_current_changed(self, current, _previous) -> None:
        if not current.isValid():
            return
        ref = formula.col_index_to_letters(current.column()) + str(current.row() + 1)
        self.name_box.setText(ref)
        self.formula_edit.setText(self.model.data(current, Qt.EditRole) or "")
        self._hide_formula_buttons()
        self._sync_toolbar(current.row(), current.column())
        # Di chuyển ô (điều hướng/commit) = không còn sửa -> Ready.
        self._apply_mode_event(ModeEvent.COMMIT)

    def _on_formula_edited(self, text: str) -> None:
        """Khi user bắt đầu gõ vào formula bar, hiện nút ✕ và ✓."""
        self.btn_cancel_edit.setVisible(True)
        self.btn_accept_edit.setVisible(True)
        # Bật chế độ chọn ô chèn ref khi nội dung là công thức (bắt đầu '=').
        self._fx_picking = text.startswith("=")
        # Soạn trên thanh công thức = Edit (từ Ready); giữ nguyên nếu đang Point.
        self._apply_mode_event(ModeEvent.FOCUS_FORMULA_BAR)

    def _hide_formula_buttons(self) -> None:
        self.btn_cancel_edit.setVisible(False)
        self.btn_accept_edit.setVisible(False)
        self._fx_picking = False

    def _insert_cell_ref(self, row: int, col: int) -> None:
        """Chèn tham chiếu ô (vd 'B3') vào formula bar tại vị trí con trỏ."""
        ref = formula.col_index_to_letters(col) + str(row + 1)
        le = self.formula_edit
        pos = le.cursorPosition()
        text = le.text()
        le.setText(text[:pos] + ref + text[pos:])
        le.setCursorPosition(pos + len(ref))
        le.setFocus()
        # Chọn ô làm tham chiếu khi đang soạn công thức -> Point mode.
        self._apply_mode_event(ModeEvent.PICK_REF)

    def _cancel_formula_edit(self) -> None:
        """Hủy sửa — khôi phục nội dung cũ."""
        cur = self.view.currentIndex()
        if cur.isValid():
            self.formula_edit.setText(self.model.data(cur, Qt.EditRole) or "")
        self._hide_formula_buttons()
        self._apply_mode_event(ModeEvent.CANCEL)
        self.view.setFocus()

    def eventFilter(self, obj, event):
        """Esc trong Name Box: bỏ chỉnh sửa, khôi phục địa chỉ ô, trả focus về lưới."""
        if obj is self.name_box and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                cur = self.view.currentIndex()
                if cur.isValid():
                    self.name_box.setText(
                        formula.col_index_to_letters(cur.column()) + str(cur.row() + 1)
                    )
                self.view.setFocus()
                return True
        return super().eventFilter(obj, event)

    def _focus_name_box(self) -> None:
        """Go To (F5 / Ctrl+G): đưa con trỏ vào Name Box và bôi đen sẵn."""
        self.name_box.setFocus()
        self.name_box.selectAll()

    def _navigate_to_name_box(self) -> None:
        """Name Box: khi Enter, nhảy tới địa chỉ gõ vào.

        Hỗ trợ ``A1`` / ``A1:C5`` / ``A:A`` / ``1:1`` (xem
        ``formula.parse_grid_reference``). Tham chiếu sai -> hộp thoại kiểu
        Excel, giữ nguyên ô đang chọn.
        """
        box = formula.parse_grid_reference(
            self.name_box.text(), self.model.rowCount(), self.model.columnCount()
        )
        if box is None:
            QMessageBox.warning(self, APP_NAME, tr("name_box_invalid_ref"))
            # Khôi phục địa chỉ ô hiện tại trong Name Box.
            cur = self.view.currentIndex()
            if cur.isValid():
                self.name_box.setText(
                    formula.col_index_to_letters(cur.column()) + str(cur.row() + 1)
                )
            self.name_box.selectAll()
            return
        top, left, bottom, right = box
        if (top, left) == (bottom, right):
            idx = self.model.index(top, left)
            self.view.setCurrentIndex(idx)
            self.view.scrollTo(idx)
        else:
            self.view.select_box(box)
            self.view.scrollTo(self.model.index(top, left))
        self.view.setFocus()

    # ------------------------------------------------------------ status bar thống kê
    # ------------------------------------------------------------ status bar stats (Spec 11.2)
    def _stat_settings(self) -> QSettings:
        return QSettings("PyExcel", "PyExcel")

    def _load_stat_items(self) -> dict[str, bool]:
        """Đọc item thống kê bật/tắt từ QSettings (mặc định giống Excel)."""
        s = self._stat_settings()
        items: dict[str, bool] = {}
        for key, default in sbstats.DEFAULT_ENABLED.items():
            raw = s.value(f"statusbar/{key}", default)
            # QSettings trả str "true"/"false" trên một số nền.
            items[key] = raw if isinstance(raw, bool) else str(raw).lower() == "true"
        return items

    _STAT_LABEL_KEYS = {
        sbstats.ITEM_AVERAGE: "stat_average",
        sbstats.ITEM_COUNT: "stat_count",
        sbstats.ITEM_NUMERICAL_COUNT: "stat_numerical_count",
        sbstats.ITEM_MIN: "stat_min",
        sbstats.ITEM_MAX: "stat_max",
        sbstats.ITEM_SUM: "stat_sum",
    }

    def _show_statusbar_menu(self, pos) -> None:
        """Menu chuột phải: bật/tắt từng item thống kê (lưu QSettings)."""
        menu = QMenu(self)
        menu.setStyleSheet(MENU_QSS)
        title = menu.addAction(tr("statusbar_customize"))
        title.setEnabled(False)
        menu.addSeparator()
        for item in sbstats.STAT_ITEMS:
            act = menu.addAction(tr(self._STAT_LABEL_KEYS[item]))
            act.setCheckable(True)
            act.setChecked(self._stat_items.get(item, False))
            act.toggled.connect(lambda on, it=item: self._toggle_stat_item(it, on))
        menu.exec(self.statusBar().mapToGlobal(pos))

    def _toggle_stat_item(self, item: str, on: bool) -> None:
        self._stat_items[item] = on
        self._stat_settings().setValue(f"statusbar/{item}", on)
        self._update_stats()

    def _update_stats(self) -> None:
        """Cập nhật thống kê vùng chọn (Average/Count/Sum/Min/Max...) khi đổi vùng.

        Duyệt đúng các vùng đã chọn (không phải bounding box) -> đa vùng Ctrl+Click
        cho số liệu chuẩn như Excel, và không quét ô không được chọn.
        """
        sm = self.view.selectionModel()
        sel = sm.selection() if sm else None
        if not sel or sel.isEmpty():
            self._stats_label.setText("")
            return
        n_cells = sum(
            (r.bottom() - r.top() + 1) * (r.right() - r.left() + 1) for r in sel
        )
        if n_cells <= 1:
            self._stats_label.setText("")
            return
        cell_value = self.model.cell_value
        values = (
            cell_value(r, c)
            for rng in sel
            for r in range(rng.top(), rng.bottom() + 1)
            for c in range(rng.left(), rng.right() + 1)
        )
        stats = sbstats.compute_stats(values)
        if stats.count == 0:
            self._stats_label.setText("")
            return
        parts = []
        for item in sbstats.STAT_ITEMS:
            if not self._stat_items.get(item):
                continue
            val = stats.value(item)
            if val is None:
                continue
            label = tr(self._STAT_LABEL_KEYS[item])
            parts.append(f"{label}: {sbstats.format_stat_value(val)}")
        self._stats_label.setText("    ".join(parts))

    def _sync_toolbar(self, row: int, col: int) -> None:
        """Cập nhật trạng thái toolbar theo định dạng ô hiện tại."""
        fmt = self.model.get_format(row, col)
        self._updating_toolbar = True
        try:
            family = fmt.get("font") or self.view.font().family()
            self.font_combo.setCurrentFont(QFont(family))
            self.size_combo.setCurrentText(str(fmt.get("size") or 10))
            self.act_bold.setChecked(bool(fmt.get("bold")))
            self.act_italic.setChecked(bool(fmt.get("italic")))
            self.btn_uline.defaultAction().setChecked(bool(fmt.get("underline")))
            self.btn_strike.defaultAction().setChecked(bool(fmt.get("strike")))
            self._sync_btn(self.halign_btn, fmt.get("halign"))
            self._sync_btn(self.valign_btn, fmt.get("valign"))
            self._sync_btn(self.wrap_btn, fmt.get("wrap") or "overflow")
        finally:
            self._updating_toolbar = False

    def _sync_btn(self, btn, value) -> None:
        icon = btn._icon_map.get(value, btn._default_icon)
        btn.setIcon(make_icon(icon))

    def _commit_formula_bar(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            self.model.setData(index, self.formula_edit.text(), Qt.EditRole)
        self._hide_formula_buttons()
        self._apply_mode_event(ModeEvent.COMMIT)
        self.view.setFocus()

    def _autosum(self) -> None:
        """AutoSum (Alt+=): chèn =SUM dải số liền kề (trên hoặc trái) vào ô hiện tại.

        Có dải -> commit luôn `=SUM(range)`. Không có dải liền kề -> đưa `=SUM()`
        vào thanh công thức, đặt con trỏ trong ngoặc để user tự chọn vùng (Excel
        cũng vậy).
        """
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        f = autosum_formula(self.model.cell_value, idx.row(), idx.column())
        if f is None:
            self.formula_edit.setText("=SUM()")
            self.formula_edit.setFocus()
            self.formula_edit.setCursorPosition(len("=SUM("))
            self._on_formula_edited("=SUM()")  # hiện nút ✓/✗ + bật chọn ô
            return
        self.model.setData(idx, f, Qt.EditRole)
        self.formula_edit.setText(f)
        self.view.setFocus()  # trả focus về lưới để mũi tên di chuyển ô tiếp

    def _toggle_show_formulas(self, on: bool) -> None:
        """Ctrl+` — bật/tắt hiện công thức gốc thay vì kết quả trên toàn sheet."""
        self.model.set_show_formulas(on)

    def _insert_now(self, kind: str, now: datetime | None = None) -> None:
        """Chèn ngày (Ctrl+;) hoặc giờ (Ctrl+Shift+;) hiện tại — giá trị tĩnh.

        ``now`` để tiêm thời gian cố định khi kiểm thử.
        """
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        now = now or datetime.now()
        text = now.strftime("%d/%m/%Y") if kind == "date" else now.strftime("%H:%M")
        self.model.setData(idx, text, Qt.EditRole)
        self.formula_edit.setText(text)
        self.view.setFocus()

    # ------------------------------------------------------------ thao tác tệp
    def new_file(self) -> None:
        self._load_sheets([("Sheet1", [[""] * 26 for _ in range(50)], {}, [])])
        self.current_path = None
        self._update_title()

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("open_title"), "", tr("file_filter"))
        if not path:
            return

        dlg = QProgressDialog(tr("opening_file"), tr("cancel"), 0, 0, self)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(400)  # chỉ hiện nếu quá 400ms

        worker = _IoWorker(lambda: io_utils.load_file(path), self)
        cancelled = [False]

        def on_cancel():
            cancelled[0] = True

        def on_done(result):
            dlg.reset()
            worker.wait()
            if cancelled[0]:
                return
            self._load_sheets(result)
            self.current_path = Path(path)
            self._update_title()
            self.statusBar().showMessage(tr("opened", path=path), 5000)

        def on_error(msg):
            dlg.reset()
            worker.wait()
            if not cancelled[0]:
                QMessageBox.critical(self, tr("open_error"), msg)

        dlg.canceled.connect(on_cancel)
        worker.finished.connect(on_done)
        worker.failed.connect(on_error)
        worker.start()
        dlg.exec()

    def save_file(self) -> None:
        if self.current_path is None:
            self.save_file_as()
            return
        self._save_to(self.current_path)

    def save_file_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, tr("save_title"), "", tr("file_filter"))
        if not path:
            return
        if not Path(path).suffix:
            path += ".csv"
        self._save_to(Path(path))

    def _save_to(self, path: Path) -> None:
        # Snapshot mọi sheet trên main thread trước — worker chỉ ghi file.
        sheets = [
            (s.name, s.model.raw_grid(), s.model.all_formats(), s.model.merges())
            for s in self.sheets
        ]

        dlg = QProgressDialog(tr("saving_file"), tr("cancel"), 0, 0, self)
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(400)

        worker = _IoWorker(lambda: io_utils.save_file(path, sheets), self)
        cancelled = [False]

        def on_cancel():
            cancelled[0] = True

        def on_done(_):
            dlg.reset()
            worker.wait()
            if cancelled[0]:
                return
            self.current_path = path
            self._update_title()
            self.statusBar().showMessage(tr("saved", path=str(path)), 5000)

        def on_error(msg):
            dlg.reset()
            worker.wait()
            if not cancelled[0]:
                QMessageBox.critical(self, tr("save_error"), msg)

        dlg.canceled.connect(on_cancel)
        worker.finished.connect(on_done)
        worker.failed.connect(on_error)
        worker.start()
        dlg.exec()

    # ------------------------------------------------------------ cấu trúc
    def insert_row_above(self) -> None:
        row = self.view.currentIndex().row()
        self.model.insertRows(max(row, 0), 1)

    def insert_row_below(self) -> None:
        row = self.view.currentIndex().row()
        self.model.insertRows(row + 1 if row >= 0 else self.model.rowCount(), 1)

    def insert_col_left(self) -> None:
        col = self.view.currentIndex().column()
        self.model.insertColumns(max(col, 0), 1)

    def insert_col_right(self) -> None:
        col = self.view.currentIndex().column()
        self.model.insertColumns(col + 1 if col >= 0 else self.model.columnCount(), 1)

    def delete_row(self) -> None:
        row = self.view.currentIndex().row()
        if row >= 0 and not self.model.removeRows(row, 1):
            self.statusBar().showMessage(tr("cannot_delete_row"), 3000)

    def delete_col(self) -> None:
        col = self.view.currentIndex().column()
        if col >= 0 and not self.model.removeColumns(col, 1):
            self.statusBar().showMessage(tr("cannot_delete_col"), 3000)

    # ------------------------------------------------------------ điền (fill)
    def _selection_box(self):
        # Lấy bounding-box theo *range* (O(số vùng)) thay vì duyệt từng ô —
        # selectedIndexes() liệt kê mọi ô nên chọn cả cột = hàng vạn index.
        sel = self.view.selectionModel().selection()
        if sel.isEmpty():
            idx = self.view.currentIndex()
            if not idx.isValid():
                return None
            return (idx.row(), idx.column(), idx.row(), idx.column())
        top = min(r.top() for r in sel)
        left = min(r.left() for r in sel)
        bottom = max(r.bottom() for r in sel)
        right = max(r.right() for r in sel)
        return (top, left, bottom, right)

    def _selection_ranges(self):
        """Danh sách bounding box của TỪNG vùng chọn rời (Ctrl+Click).

        Dùng cho thao tác áp được lên nhiều vùng (định dạng, viền, xóa nội dung).
        Duyệt theo range nên nhẹ kể cả khi chọn cả cột/hàng."""
        sel = self.view.selectionModel().selection()
        if sel.isEmpty():
            idx = self.view.currentIndex()
            if not idx.isValid():
                return []
            return [(idx.row(), idx.column(), idx.row(), idx.column())]
        return [(r.top(), r.left(), r.bottom(), r.right()) for r in sel]

    def fill_down(self) -> None:
        # Điền chỉ áp cho 1 vùng liền (đa vùng rời không có nghĩa cho fill).
        ranges = self._selection_ranges()
        if self._reject_fill_multi(ranges):
            return
        top, left, bottom, right = ranges[0]
        if bottom > top:
            self.model.fill((top, left, top, right), ranges[0])

    def fill_right(self) -> None:
        ranges = self._selection_ranges()
        if self._reject_fill_multi(ranges):
            return
        top, left, bottom, right = ranges[0]
        if right > left:
            self.model.fill((top, left, bottom, left), ranges[0])

    def _reject_fill_multi(self, ranges) -> bool:
        """True nếu không thể fill (0 vùng, hoặc nhiều vùng rời -> báo như Excel)."""
        if len(ranges) > 1:
            self.statusBar().showMessage(tr("multi_range_copy"), 3000)
        return len(ranges) != 1

    # ------------------------------------------------------------ undo / redo
    def undo(self) -> None:
        if not self.model.undo():
            self.statusBar().showMessage(tr("nothing_undo"), 2000)

    def redo(self) -> None:
        if not self.model.redo():
            self.statusBar().showMessage(tr("nothing_redo"), 2000)

    # ------------------------------------------------------------ copy / cut / paste
    def copy_selection(self, *, cut: bool = False) -> None:
        # Excel chặn sao chép/cắt khi chọn nhiều vùng rời -> báo đúng kiểu Excel.
        if len(self._selection_ranges()) > 1:
            QMessageBox.warning(self, APP_NAME, tr("multi_range_copy"))
            return
        box = self._selection_box()
        if box is None:
            return
        raw = self.model.block_raw(box)
        tsv = "\n".join("\t".join(row) for row in self.model.block_display(box))
        QApplication.clipboard().setText(tsv)
        self._clip = {
            "block": raw,
            "anchor": (box[0], box[1]),
            "tsv": tsv,
            "adjust": not cut,  # cut = di chuyển, không dịch tham chiếu
        }
        if cut:
            self.model.clear_range(box)
        self.statusBar().showMessage(tr("cut_done") if cut else tr("copied"), 2000)

    def cut_selection(self) -> None:
        self.copy_selection(cut=True)

    def paste_clipboard(self) -> None:
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        top, left = idx.row(), idx.column()
        clip_text = QApplication.clipboard().text()

        if self._clip and clip_text == self._clip["tsv"]:
            block = self._clip["block"]
            anchor = self._clip["anchor"] if self._clip["adjust"] else None
            self.model.paste_block(top, left, block, src_anchor=anchor)
        elif clip_text:
            normalized = clip_text.replace("\r\n", "\n").replace("\r", "\n")
            block = [line.split("\t") for line in normalized.split("\n")]
            if block and block[-1] == [""]:
                block.pop()
            self.model.paste_block(top, left, block, src_anchor=None)
        else:
            return

        if block:
            h, w = len(block), max(len(r) for r in block)
            self.view.select_box((top, left, top + h - 1, left + w - 1))
        self.statusBar().showMessage(tr("pasted"), 2000)

    def paste_special(self) -> None:
        """Dán dạng văn bản thuần (chỉ giá trị, luôn lấy từ clipboard hệ thống)."""
        idx = self.view.currentIndex()
        if not idx.isValid():
            return
        text = QApplication.clipboard().text()
        if not text:
            return
        top, left = idx.row(), idx.column()
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        block = [line.split("\t") for line in normalized.split("\n")]
        if block and block[-1] == [""]:
            block.pop()
        self.model.paste_block(top, left, block, src_anchor=None)
        if block:
            h, w = len(block), max(len(r) for r in block)
            self.view.select_box((top, left, top + h - 1, left + w - 1))
        self.statusBar().showMessage(tr("pasted"), 2000)

    def clear_selection(self) -> None:
        boxes = self._selection_ranges()
        if boxes:
            self.model.clear_ranges(boxes)

    # ------------------------------------------------------------ tìm & thay thế
    def show_find(self) -> None:
        if self._find_dialog is None:
            self._find_dialog = self._make_find_dialog()
        self._find_dialog.show()
        self._find_dialog.raise_()
        self._find_dialog.activateWindow()
        self._find_field.setFocus()
        self._find_field.selectAll()

    def _make_find_dialog(self) -> QDialog:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("find_title"))
        grid = QGridLayout(dlg)
        self._find_field = QLineEdit()
        self._find_match_case = QCheckBox(tr("match_case"))
        grid.addWidget(QLabel(tr("find_label")), 0, 0)
        grid.addWidget(self._find_field, 0, 1)
        grid.addWidget(self._find_match_case, 1, 1)

        buttons = QHBoxLayout()
        btn_find = QPushButton(tr("find_next"))
        btn_close = QPushButton(tr("close"))
        buttons.addWidget(btn_find)
        buttons.addWidget(btn_close)
        grid.addLayout(buttons, 2, 0, 1, 2)

        find_cb = lambda: self._find_text(self._find_field.text(), self._find_match_case.isChecked())
        btn_find.clicked.connect(find_cb)
        self._find_field.returnPressed.connect(find_cb)
        btn_close.clicked.connect(dlg.hide)
        return dlg

    def show_replace(self) -> None:
        if self._replace_dialog is None:
            self._replace_dialog = self._make_replace_dialog()
        self._replace_dialog.show()
        self._replace_dialog.raise_()
        self._replace_dialog.activateWindow()
        self._replace_find_field.setFocus()

    def _make_replace_dialog(self) -> QDialog:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("replace_title"))
        grid = QGridLayout(dlg)
        self._replace_find_field = QLineEdit()
        self._replace_field = QLineEdit()
        self._replace_match_case = QCheckBox(tr("match_case"))
        grid.addWidget(QLabel(tr("find_label")), 0, 0)
        grid.addWidget(self._replace_find_field, 0, 1)
        grid.addWidget(QLabel(tr("replace_with_label")), 1, 0)
        grid.addWidget(self._replace_field, 1, 1)
        grid.addWidget(self._replace_match_case, 2, 1)

        buttons = QHBoxLayout()
        btn_find = QPushButton(tr("find_next"))
        btn_one = QPushButton(tr("replace_btn"))
        btn_all = QPushButton(tr("replace_all_btn"))
        btn_close = QPushButton(tr("close"))
        for b in (btn_find, btn_one, btn_all, btn_close):
            buttons.addWidget(b)
        grid.addLayout(buttons, 3, 0, 1, 2)

        btn_find.clicked.connect(
            lambda: self._find_text(
                self._replace_find_field.text(), self._replace_match_case.isChecked()
            )
        )
        btn_one.clicked.connect(self._replace_one)
        btn_all.clicked.connect(self._replace_all)
        btn_close.clicked.connect(dlg.hide)
        return dlg

    def _replace_one(self) -> None:
        from .table_model import _replace_substr

        find = self._replace_find_field.text()
        repl = self._replace_field.text()
        mc = self._replace_match_case.isChecked()
        if not find:
            return
        idx = self.view.currentIndex()
        if idx.isValid():
            raw = self.model.data(idx, Qt.EditRole) or ""
            new = _replace_substr(raw, find, repl, mc)
            if new != raw:
                self.model.setData(idx, new, Qt.EditRole)
        self._find_text(find, mc)

    def _replace_all(self) -> None:
        n = self.model.replace_text(
            self._replace_find_field.text(),
            self._replace_field.text(),
            self._replace_match_case.isChecked(),
        )
        self.statusBar().showMessage(tr("replaced_n", n=n), 4000)

    def _find_text(self, needle: str, match_case: bool = False) -> bool:
        key = needle if match_case else needle.lower()
        if not key.strip():
            return False
        start = self.view.currentIndex()
        start_row = start.row() if start.isValid() else 0
        start_col = start.column() if start.isValid() else -1
        rows, cols = self.model.rowCount(), self.model.columnCount()

        # Bắt đầu từ ngay sau ô hiện tại, quét tuần tự rồi vòng lại.
        begin = start_row * cols + start_col + 1
        for offset in range(rows * cols):
            pos = (begin + offset) % (rows * cols)
            r, c = divmod(pos, cols)
            text = str(self.model.data(self.model.index(r, c), Qt.DisplayRole) or "")
            haystack = text if match_case else text.lower()
            if key in haystack:
                idx = self.model.index(r, c)
                self.view.setCurrentIndex(idx)
                self.view.scrollTo(idx)
                ref = formula.col_index_to_letters(c) + str(r + 1)
                self.statusBar().showMessage(tr("found_at", ref=ref), 4000)
                return True
        self.statusBar().showMessage(tr("not_found"), 3000)
        return False

    # ------------------------------------------------------------ bộ lọc
    def toggle_filter(self, on: bool) -> None:
        """Bật/tắt chế độ lọc: hiện/ẩn icon phễu trên header."""
        self.view.horizontalHeader().set_filter_enabled(on)
        if not on:
            self._filters.clear()
            self._unhide_all()
            self.view.horizontalHeader().refresh(set())

    def show_filter(self) -> None:
        """Menu Dữ liệu → Lọc: bật chế độ lọc rồi mở popup cho cột hiện tại."""
        if not self.act_filter.isChecked():
            self.act_filter.setChecked(True)  # kích hoạt toggle
        col = self.view.currentIndex().column()
        if col >= 0:
            self._open_filter_dialog(col)

    def _open_filter_dialog(self, col: int) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("filter_title", col=formula.col_index_to_letters(col)))
        layout = QVBoxLayout(dlg)

        # Sắp xếp.
        sort_row = QHBoxLayout()
        b_az = QPushButton(tr("sort_az"))
        b_za = QPushButton(tr("sort_za"))
        sort_row.addWidget(b_az)
        sort_row.addWidget(b_za)
        layout.addLayout(sort_row)
        b_az.clicked.connect(lambda: (self.model.sort_rows(col, True), self._apply_filters(), dlg.accept()))
        b_za.clicked.connect(lambda: (self.model.sort_rows(col, False), self._apply_filters(), dlg.accept()))

        # Ô tìm trong danh sách.
        search = QLineEdit()
        search.setPlaceholderText(tr("search_ph"))
        layout.addWidget(search)

        # Danh sách giá trị duy nhất (có tick).
        listw = QListWidget()
        layout.addWidget(listw)
        allowed = self._filters.get(col)
        values = self._distinct_values(col)
        for disp, raw in values:
            item = QListWidgetItem(disp if raw != "" else tr("blanks"))
            item.setData(Qt.UserRole, raw)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            checked = (allowed is None) or (raw in allowed)
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            listw.addItem(item)

        def do_search(text):
            t = text.lower()
            for i in range(listw.count()):
                it = listw.item(i)
                it.setHidden(t not in it.text().lower())

        search.textChanged.connect(do_search)

        # Chọn tất cả / Bỏ chọn.
        sel_row = QHBoxLayout()
        b_all = QPushButton(tr("select_all"))
        b_clear = QPushButton(tr("clear_sel"))
        sel_row.addWidget(b_all)
        sel_row.addWidget(b_clear)
        layout.addLayout(sel_row)

        def set_all(state):
            for i in range(listw.count()):
                if not listw.item(i).isHidden():
                    listw.item(i).setCheckState(state)

        b_all.clicked.connect(lambda: set_all(Qt.Checked))
        b_clear.clicked.connect(lambda: set_all(Qt.Unchecked))

        # OK / Hủy.
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        b_cancel = QPushButton(tr("cancel"))
        b_ok = QPushButton(tr("ok"))
        b_ok.setDefault(True)
        btn_row.addWidget(b_cancel)
        btn_row.addWidget(b_ok)
        layout.addLayout(btn_row)
        b_cancel.clicked.connect(dlg.reject)

        def apply_ok():
            total = listw.count()
            chosen = set()
            for i in range(total):
                it = listw.item(i)
                if it.checkState() == Qt.Checked:
                    chosen.add(it.data(Qt.UserRole))
            if len(chosen) == total:
                self._filters.pop(col, None)  # chọn hết = không lọc
            else:
                self._filters[col] = chosen
            self._apply_filters()
            dlg.accept()

        b_ok.clicked.connect(apply_ok)
        dlg.resize(320, 460)
        dlg.exec()

    def _distinct_values(self, col: int) -> list[tuple[str, str]]:
        """Danh sách (hiển_thị, thô) giá trị duy nhất của một cột, đã sắp xếp."""
        seen = {}
        for r in range(self.model.rowCount()):
            disp = str(self.model.data(self.model.index(r, col), Qt.DisplayRole) or "")
            seen.setdefault(disp, disp)
        # rỗng đứng đầu, còn lại sắp xếp tự nhiên.
        keys = sorted(seen, key=lambda s: (s != "", _natural_key(s)))
        return [(k, k) for k in keys]

    def _apply_filters(self) -> None:
        """Ẩn các dòng không khớp mọi bộ lọc đang bật."""
        for r in range(self.model.rowCount()):
            visible = all(
                str(self.model.data(self.model.index(r, col), Qt.DisplayRole) or "") in allowed
                for col, allowed in self._filters.items()
            )
            self.view.setRowHidden(r, not visible)
        self.view.horizontalHeader().refresh(set(self._filters.keys()))
        self.view.viewport().update()

    def _unhide_all(self) -> None:
        for r in range(self.model.rowCount()):
            self.view.setRowHidden(r, False)
        self.view.viewport().update()

    def clear_filters(self) -> None:
        """Xóa tiêu chí lọc, hiện lại mọi dòng (giữ chế độ lọc đang bật)."""
        self._filters.clear()
        self._unhide_all()
        self.view.horizontalHeader().refresh(set())

    # ------------------------------------------------------------ sắp xếp
    def _sort_by_header(self, col: int) -> None:
        self._sort_column(col, ascending=True)

    def _sort_current(self, ascending: bool) -> None:
        col = self.view.currentIndex().column()
        if col >= 0:
            self._sort_column(col, ascending)

    def _sort_column(self, col: int, ascending: bool) -> None:
        self.model.sort_rows(col, ascending)
        if self._filters:
            self._apply_filters()
        direction = tr("dir_asc") if ascending else tr("dir_desc")
        self.statusBar().showMessage(
            tr("sorted_msg", col=formula.col_index_to_letters(col), dir=direction), 4000
        )

    # ------------------------------------------------------------ tiện ích
    def _update_title(self) -> None:
        name = self.current_path.name if self.current_path else tr("untitled")
        self.setWindowTitle(f"{name} — {APP_NAME} v{__version__}")

    def show_about(self) -> None:
        QMessageBox.about(self, tr("about"), tr("about_body", ver=__version__))

    # ------------------------------------------------------------ cập nhật
    def check_for_updates(self) -> None:
        self.statusBar().showMessage(tr("checking_updates"))
        QApplication.processEvents()
        try:
            latest = updater.check_latest()
        except updater.UpdateError as exc:
            self.statusBar().clearMessage()
            QMessageBox.warning(
                self, tr("update_error"), tr("update_check_failed", err=str(exc))
            )
            return
        self.statusBar().clearMessage()

        if not updater.is_newer(latest["version"], __version__):
            QMessageBox.information(
                self, tr("menu_help").replace("&", ""), tr("up_to_date", ver=__version__)
            )
            return

        notes = (latest["notes"] or "").strip()
        if len(notes) > 600:
            notes = notes[:600] + "..."
        box = QMessageBox(self)
        box.setWindowTitle(tr("update_available"))
        box.setTextFormat(Qt.RichText)
        box.setText(
            tr(
                "update_prompt",
                new=latest["version"],
                cur=__version__,
                notes=notes.replace("\n", "<br>"),
            )
        )
        update_btn = box.addButton(tr("update_now"), QMessageBox.AcceptRole)
        box.addButton(tr("close"), QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is update_btn:
            self._download_and_run(latest)

    def _download_and_run(self, latest: dict) -> None:
        import os
        import tempfile

        dest = os.path.join(tempfile.gettempdir(), latest["name"])
        dlg = QProgressDialog(tr("downloading"), tr("close"), 0, 100, self)
        dlg.setWindowTitle(tr("update_available"))
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)

        self._dl_thread = updater.DownloadThread(latest["url"], dest, self)
        self._dl_thread.progress.connect(dlg.setValue)
        self._dl_thread.failed.connect(
            lambda err: (dlg.cancel(), QMessageBox.warning(self, tr("update_error"), err))
        )
        self._dl_thread.done.connect(lambda path: self._run_installer(path, dlg))
        dlg.canceled.connect(self._dl_thread.terminate)
        self._dl_thread.start()

    def _run_installer(self, path: str, dlg) -> None:
        import subprocess

        dlg.close()
        QMessageBox.information(self, tr("update_available"), tr("update_ready"))
        subprocess.Popen([path])
        QApplication.instance().quit()

    # ------------------------------------------------------------ phím tắt
    def _apply_shortcuts(self) -> None:
        for cmd_id, action in self._actions.items():
            seq = shortcuts.get(cmd_id)
            action.setShortcut(QKeySequence(seq) if seq else QKeySequence())

    def show_keybindings(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("keybindings_title"))
        outer = QVBoxLayout(dlg)

        container = QWidget()
        grid = QGridLayout(container)
        grid.addWidget(QLabel(f"<b>{tr('col_command')}</b>"), 0, 0)
        grid.addWidget(QLabel(f"<b>{tr('col_shortcut')}</b>"), 0, 1)
        edits: dict[str, QKeySequenceEdit] = {}
        for i, cmd_id in enumerate(shortcuts.DEFAULTS, start=1):
            grid.addWidget(QLabel(tr(cmd_id).replace("&", "")), i, 0)
            edit = QKeySequenceEdit(QKeySequence(shortcuts.get(cmd_id)))
            edits[cmd_id] = edit
            grid.addWidget(edit, i, 1)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        buttons = QHBoxLayout()
        b_reset = QPushButton(tr("reset_defaults"))
        b_save = QPushButton(tr("save_close"))
        b_close = QPushButton(tr("close"))
        buttons.addWidget(b_reset)
        buttons.addStretch()
        buttons.addWidget(b_save)
        buttons.addWidget(b_close)
        outer.addLayout(buttons)

        def do_save():
            shortcuts.set_many(
                {cid: e.keySequence().toString() for cid, e in edits.items()}
            )
            self._apply_shortcuts()
            dlg.accept()

        def do_reset():
            shortcuts.reset()
            for cid, e in edits.items():
                e.setKeySequence(QKeySequence(shortcuts.get(cid)))

        b_save.clicked.connect(do_save)
        b_reset.clicked.connect(do_reset)
        b_close.clicked.connect(dlg.reject)
        dlg.resize(440, 520)
        dlg.exec()
