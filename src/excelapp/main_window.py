"""Cửa sổ chính của ứng dụng bảng tính."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QGridLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__, formula, io_utils, shortcuts, updater
from .freeze import FreezeManager
from .i18n import current_lang, load_lang, set_lang, tr
from .icons import make_icon
from .resources import icon_path
from .table_model import SpreadsheetModel
from .view import SpreadsheetView


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

        if os.path.exists(icon_path()):
            self.setWindowIcon(QIcon(icon_path()))
        self._build_ui()
        self._build_toolbar()
        self._build_menu()
        self._style_chrome()
        self._update_title()
        self.resize(1000, 650)

    def _style_chrome(self) -> None:
        """Giao diện menu/toolbar thoáng, dễ nhìn (kiểu Google Sheets)."""
        self.menuBar().setStyleSheet(
            """
            QMenuBar { background: #ffffff; border-bottom: 1px solid #e8eaed;
                       padding: 3px 6px; font-size: 13px; }
            QMenuBar::item { padding: 6px 12px; margin: 0 1px; background: transparent;
                             border-radius: 4px; color: #3c4043; }
            QMenuBar::item:selected { background: #f1f3f4; }
            QMenuBar::item:pressed { background: #e8f0fe; color: #1a73e8; }
            QMenu { background: #ffffff; border: 1px solid #dadce0; padding: 4px; }
            QMenu::item { padding: 6px 28px 6px 16px; border-radius: 4px; }
            QMenu::item:selected { background: #e8f0fe; color: #1a73e8; }
            QMenu::separator { height: 1px; background: #e8eaed; margin: 4px 8px; }
            """
        )
        self._toolbar.setStyleSheet(
            """
            QToolBar { background: #ffffff; border-bottom: 1px solid #e8eaed;
                       spacing: 2px; padding: 3px; }
            QToolButton { border: none; border-radius: 4px; padding: 4px 7px;
                          font-size: 14px; color: #3c4043; }
            QToolButton:hover { background: #f1f3f4; }
            QToolButton:checked { background: #e8f0fe; color: #1a73e8; }
            QToolBar::separator { background: #e8eaed; width: 1px; margin: 4px 4px; }
            """
        )

    # ------------------------------------------------------------ dựng UI
    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Thanh công thức: ô địa chỉ + nội dung ô hiện tại.
        bar = QHBoxLayout()
        self.cell_label = QLabel("A1")
        self.cell_label.setMinimumWidth(60)
        self.cell_label.setAlignment(Qt.AlignCenter)
        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText(tr("formula_placeholder"))
        self.formula_edit.returnPressed.connect(self._commit_formula_bar)
        bar.addWidget(self.cell_label)
        bar.addWidget(QLabel("ƒx"))
        bar.addWidget(self.formula_edit)
        layout.addLayout(bar)

        # Bảng lưới.
        self.view = SpreadsheetView()
        self.view.setModel(self.model)
        self.view.setSelectionMode(QTableView.ContiguousSelection)
        self.view.horizontalHeader().setSectionsClickable(True)
        self.view.horizontalHeader().sectionDoubleClicked.connect(self._sort_by_header)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)
        self.view.selectionModel().currentChanged.connect(self._on_current_changed)
        layout.addWidget(self.view)

        self.freeze = FreezeManager(self.view)

        self.setCentralWidget(central)
        self.statusBar().showMessage(tr("ready"))
        self._version_label = QLabel(f"{APP_NAME} v{__version__}")
        self.statusBar().addPermanentWidget(self._version_label)

    def _build_toolbar(self) -> None:
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)
        self._toolbar = tb

        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(180)
        self.font_combo.setToolTip(tr("tooltip_font"))
        self.font_combo.currentFontChanged.connect(
            lambda f: self._apply_format(font=f.family())
        )
        tb.addWidget(self.font_combo)

        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        self.size_combo.addItems(
            ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "36", "48"]
        )
        self.size_combo.setCurrentText("10")
        self.size_combo.setMaximumWidth(60)
        self.size_combo.setToolTip(tr("tooltip_size"))
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        tb.addWidget(self.size_combo)
        tb.addSeparator()

        self.act_bold = self._toolbar_toggle(tb, "B", tr("bold"), bold=True)
        self.act_italic = self._toolbar_toggle(tb, "I", tr("italic"), italic=True)
        tb.addSeparator()

        # Canh ngang (loại trừ lẫn nhau, cho phép bỏ chọn hết).
        self.halign_group = QActionGroup(self)
        self.halign_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        self.act_left = self._toolbar_align(tb, "", tr("align_left"), self.halign_group, "align_left", halign="left")
        self.act_center = self._toolbar_align(tb, "", tr("align_center"), self.halign_group, "align_center", halign="center")
        self.act_right = self._toolbar_align(tb, "", tr("align_right"), self.halign_group, "align_right", halign="right")
        tb.addSeparator()

        # Canh dọc.
        self.valign_group = QActionGroup(self)
        self.valign_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        self.act_top = self._toolbar_align(tb, "", tr("valign_top"), self.valign_group, "valign_top", valign="top")
        self.act_mid = self._toolbar_align(tb, "", tr("valign_middle"), self.valign_group, "valign_middle", valign="middle")
        self.act_bot = self._toolbar_align(tb, "", tr("valign_bottom"), self.valign_group, "valign_bottom", valign="bottom")
        tb.addSeparator()

        self.act_wrap = self._toolbar_toggle(tb, "", tr("wrap"), icon="wrap_text", wrap=True)

    def _toolbar_toggle(self, tb, text, tip, icon=None, **attr) -> QAction:
        act = QAction(text, self, checkable=True)
        if icon:
            act.setIcon(make_icon(icon))
        act.setToolTip(tip)
        key = next(iter(attr))
        act.toggled.connect(lambda checked: self._apply_format(**{key: checked}))
        tb.addAction(act)
        return act

    def _toolbar_align(self, tb, text, tip, group, icon=None, **attr) -> QAction:
        act = QAction(text, self, checkable=True)
        if icon:
            act.setIcon(make_icon(icon))
        act.setToolTip(tip)
        key, value = next(iter(attr.items()))
        act.triggered.connect(lambda: self._apply_format(**{key: value}))
        group.addAction(act)
        tb.addAction(act)
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
        box = self._selection_box()
        if box is None:
            return
        self.model.set_format(box, **attrs)
        if "wrap" in attrs:
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
        self._cmd_action(data_menu, "find", self.show_find)
        self._cmd_action(data_menu, "replace", self.show_replace)
        data_menu.addSeparator()
        self._add_action(data_menu, tr("sort_asc"), lambda: self._sort_current(True))
        self._add_action(data_menu, tr("sort_desc"), lambda: self._sort_current(False))

        # --- Xem (Freeze) ---
        view_menu = menubar.addMenu(tr("menu_view"))
        self._build_freeze_menu(view_menu)

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

    # ------------------------------------------------------------ ngôn ngữ
    def set_language(self, lang: str) -> None:
        if lang == current_lang():
            return
        set_lang(lang)
        self._retranslate()

    def _retranslate(self) -> None:
        self._build_menu()
        self.formula_edit.setPlaceholderText(tr("formula_placeholder"))
        self.statusBar().showMessage(tr("ready"))
        self._update_title()
        # Tooltip trên toolbar.
        self.font_combo.setToolTip(tr("tooltip_font"))
        self.size_combo.setToolTip(tr("tooltip_size"))
        for act, key in (
            (self.act_bold, "bold"), (self.act_italic, "italic"),
            (self.act_left, "align_left"), (self.act_center, "align_center"),
            (self.act_right, "align_right"), (self.act_top, "valign_top"),
            (self.act_mid, "valign_middle"), (self.act_bot, "valign_bottom"),
            (self.act_wrap, "wrap"),
        ):
            act.setToolTip(tr(key))
        # Hộp thoại sẽ dựng lại theo ngôn ngữ mới ở lần mở kế tiếp.
        for attr in ("_replace_dialog", "_find_dialog"):
            dlg = getattr(self, attr)
            if dlg is not None:
                dlg.deleteLater()
                setattr(self, attr, None)

    # ------------------------------------------------------------ menu chuột phải
    def _show_context_menu(self, pos) -> None:
        index = self.view.indexAt(pos)
        # Nếu bấm vào ô ngoài vùng chọn -> chọn ô đó trước.
        if index.isValid() and index not in self.view.selectionModel().selectedIndexes():
            self.view.setCurrentIndex(index)

        menu = QMenu(self)
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

    # ------------------------------------------------------------ thanh công thức
    def _on_current_changed(self, current, _previous) -> None:
        if not current.isValid():
            return
        ref = formula.col_index_to_letters(current.column()) + str(current.row() + 1)
        self.cell_label.setText(ref)
        self.formula_edit.setText(self.model.data(current, Qt.EditRole) or "")
        self._sync_toolbar(current.row(), current.column())

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
            self.act_wrap.setChecked(bool(fmt.get("wrap")))
            h = fmt.get("halign")
            self.act_left.setChecked(h == "left")
            self.act_center.setChecked(h == "center")
            self.act_right.setChecked(h == "right")
            v = fmt.get("valign")
            self.act_top.setChecked(v == "top")
            self.act_mid.setChecked(v == "middle")
            self.act_bot.setChecked(v == "bottom")
        finally:
            self._updating_toolbar = False

    def _commit_formula_bar(self) -> None:
        index = self.view.currentIndex()
        if index.isValid():
            self.model.setData(index, self.formula_edit.text(), Qt.EditRole)
            self.view.setFocus()

    # ------------------------------------------------------------ thao tác tệp
    def new_file(self) -> None:
        self.model.replace_all([[""] * 26 for _ in range(50)])
        self.current_path = None
        self._update_title()

    def open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("open_title"), "", tr("file_filter"))
        if not path:
            return
        try:
            rows = io_utils.load_file(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("open_error"), str(exc))
            return
        self.model.replace_all(rows)
        self.current_path = Path(path)
        self._update_title()
        self.statusBar().showMessage(tr("opened", path=path), 5000)

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
        try:
            io_utils.save_file(path, self.model.raw_grid())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("save_error"), str(exc))
            return
        self.current_path = path
        self._update_title()
        self.statusBar().showMessage(tr("saved", path=str(path)), 5000)

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
        indexes = self.view.selectionModel().selectedIndexes()
        if not indexes:
            idx = self.view.currentIndex()
            if not idx.isValid():
                return None
            return (idx.row(), idx.column(), idx.row(), idx.column())
        rows = [i.row() for i in indexes]
        cols = [i.column() for i in indexes]
        return (min(rows), min(cols), max(rows), max(cols))

    def fill_down(self) -> None:
        box = self._selection_box()
        if box is None:
            return
        top, left, bottom, right = box
        if bottom > top:
            self.model.fill((top, left, top, right), box)

    def fill_right(self) -> None:
        box = self._selection_box()
        if box is None:
            return
        top, left, bottom, right = box
        if right > left:
            self.model.fill((top, left, bottom, left), box)

    # ------------------------------------------------------------ undo / redo
    def undo(self) -> None:
        if not self.model.undo():
            self.statusBar().showMessage(tr("nothing_undo"), 2000)

    def redo(self) -> None:
        if not self.model.redo():
            self.statusBar().showMessage(tr("nothing_redo"), 2000)

    # ------------------------------------------------------------ copy / cut / paste
    def copy_selection(self, *, cut: bool = False) -> None:
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
        box = self._selection_box()
        if box is not None:
            self.model.clear_range(box)

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

    # ------------------------------------------------------------ sắp xếp
    def _sort_by_header(self, col: int) -> None:
        self._sort_column(col, ascending=True)

    def _sort_current(self, ascending: bool) -> None:
        col = self.view.currentIndex().column()
        if col >= 0:
            self._sort_column(col, ascending)

    def _sort_column(self, col: int, ascending: bool) -> None:
        self.model.sort_rows(col, ascending)
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
