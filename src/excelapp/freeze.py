"""Cố định dòng/cột (freeze panes) bằng các bảng phủ chia sẻ model.

Kỹ thuật: đặt thêm 3 QTableView con đè lên view chính:
  - ``top``    : các dòng cố định (cuộn ngang theo view chính)
  - ``left``   : các cột cố định (cuộn dọc theo view chính)
  - ``corner`` : giao của dòng & cột cố định (đứng yên)
Tất cả dùng chung model và selection model nên dữ liệu/lựa chọn luôn đồng bộ.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import QAbstractItemView, QFrame, QTableView


class FreezeManager(QObject):
    def __init__(self, main: QTableView):
        super().__init__(main)
        self.main = main
        self.rows = 0
        self.cols = 0
        self.top = self._make_overlay()
        self.left = self._make_overlay()
        self.corner = self._make_overlay()
        for v in (self.top, self.left, self.corner):
            v.hide()

        main.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        main.verticalScrollBar().valueChanged.connect(self._on_scroll)
        main.horizontalHeader().sectionResized.connect(self._on_col_resized)
        main.verticalHeader().sectionResized.connect(self._on_row_resized)
        # Theo dõi thay đổi kích thước view chính để bố trí lại.
        main.viewport().installEventFilter(self)

    # ------------------------------------------------------------ tạo overlay
    def _make_overlay(self) -> QTableView:
        v = QTableView(self.main)
        v.setModel(self.main.model())
        v.setSelectionModel(self.main.selectionModel())
        v.setItemDelegate(self.main.itemDelegate())
        v.setFocusPolicy(Qt.NoFocus)
        v.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        v.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        v.setStyleSheet(
            "QTableView { background: white; gridline-color: #d9d9d9; }"
            "QHeaderView::section { background-color: #f5f6f7; border: none;"
            " border-right: 1px solid #d9d9d9; border-bottom: 1px solid #d9d9d9;"
            " padding: 2px 4px; color: #3c4043; }"
            "QTableCornerButton::section { background-color: #f5f6f7; border: none;"
            " border-right: 1px solid #d9d9d9; border-bottom: 1px solid #d9d9d9; }"
        )
        v.setFrameShape(QFrame.NoFrame)
        v.setAutoFillBackground(True)
        v.viewport().setAutoFillBackground(True)
        v.setShowGrid(True)
        v.horizontalHeader().setDefaultSectionSize(
            self.main.horizontalHeader().defaultSectionSize()
        )
        v.verticalHeader().setDefaultSectionSize(
            self.main.verticalHeader().defaultSectionSize()
        )
        v.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        # Quan trọng: đảm bảo overlay nằm TRÊN viewport của view chính.
        self.main.viewport().stackUnder(v)
        return v

    # ------------------------------------------------------------ API
    def set_freeze(self, rows: int, cols: int) -> None:
        self.rows = max(0, rows)
        self.cols = max(0, cols)
        self._relayout()

    def rebind(self) -> None:
        """Gắn lại model + selection model cho overlay (khi đổi sheet)."""
        for v in (self.top, self.left, self.corner):
            v.setModel(self.main.model())
            v.setSelectionModel(self.main.selectionModel())
        self._relayout()

    # ------------------------------------------------------------ đồng bộ
    def _on_col_resized(self, idx: int, _old: int, new: int) -> None:
        for v in (self.top, self.left, self.corner):
            v.setColumnWidth(idx, new)
        self._relayout()

    def _on_row_resized(self, idx: int, _old: int, new: int) -> None:
        for v in (self.top, self.left, self.corner):
            v.setRowHeight(idx, new)
        self._relayout()

    def _on_scroll(self) -> None:
        self.top.horizontalScrollBar().setValue(self.main.horizontalScrollBar().value())
        self.left.verticalScrollBar().setValue(self.main.verticalScrollBar().value())
        self._raise_overlays()

    def _raise_overlays(self) -> None:
        for v in (self.top, self.left, self.corner):
            if v.isVisible():
                v.raise_()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Resize:
            self._relayout()
        return False

    # ------------------------------------------------------------ bố trí
    def _relayout(self) -> None:
        model = self.main.model()
        if model is None or (self.rows == 0 and self.cols == 0):
            for v in (self.top, self.left, self.corner):
                v.hide()
            return

        hh = self.main.horizontalHeader().height()
        vh = self.main.verticalHeader().width()
        frozen_w = sum(self.main.columnWidth(c) for c in range(self.cols))
        frozen_h = sum(self.main.rowHeight(r) for r in range(self.rows))
        full_w = self.main.viewport().width() + vh
        full_h = self.main.viewport().height() + hh

        # Đồng bộ kích thước section cho các overlay.
        for v in (self.top, self.left, self.corner):
            for c in range(model.columnCount()):
                v.setColumnWidth(c, self.main.columnWidth(c))
            for r in range(min(self.rows + 2, model.rowCount())):
                v.setRowHeight(r, self.main.rowHeight(r))

        if self.rows > 0:
            self.top.setGeometry(0, 0, full_w, hh + frozen_h)
            self.top.verticalScrollBar().setValue(0)
            self.top.horizontalScrollBar().setValue(
                self.main.horizontalScrollBar().value()
            )
            self.top.show()
            self.top.raise_()
        else:
            self.top.hide()

        if self.cols > 0:
            self.left.setGeometry(0, 0, vh + frozen_w, full_h)
            self.left.horizontalScrollBar().setValue(0)
            self.left.verticalScrollBar().setValue(
                self.main.verticalScrollBar().value()
            )
            self.left.show()
            self.left.raise_()
        else:
            self.left.hide()

        if self.rows > 0 and self.cols > 0:
            self.corner.setGeometry(0, 0, vh + frozen_w, hh + frozen_h)
            self.corner.verticalScrollBar().setValue(0)
            self.corner.horizontalScrollBar().setValue(0)
            self.corner.show()
            self.corner.raise_()
        else:
            self.corner.hide()
