"""QTableView kiểu Google Sheets: bôi đen rõ + núm kéo (Fill Handle) AutoFill."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelection, QItemSelectionModel, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QRegion
from PySide6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QStyle,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
)

_BLUE = QColor("#1a73e8")          # màu xanh nhấn (giống Google Sheets)
_WASH = QColor(26, 115, 232, 38)   # lớp phủ xanh trong suốt (alpha) lên vùng chọn
_HANDLE = 8                        # cạnh vùng bắt núm kéo (px)


class CellDelegate(QStyledItemDelegate):
    """Tự vẽ nền vùng chọn: ô active để trắng, các ô còn lại tô xanh nhạt."""

    def __init__(self, view: "SpreadsheetView"):
        super().__init__(view)
        self._view = view

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Bật xuống dòng cho ô có bật wrap.
        model = self._view.model()
        if model is not None and model.cell_wrap(index.row(), index.column()):
            option.features |= QStyleOptionViewItem.WrapText

    def paint(self, painter, option, index):
        # Bỏ tô nền/focus mặc định; vùng chọn được vẽ bằng lớp phủ trong suốt
        # ở SpreadsheetView.paintEvent nên nội dung ô vẫn nhìn rõ.
        option.state &= ~QStyle.State_Selected
        option.state &= ~QStyle.State_HasFocus
        super().paint(painter, option, index)


class SpreadsheetView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setItemDelegate(CellDelegate(self))
        self.setShowGrid(True)
        self.setFrameShape(QFrame.NoFrame)  # khớp với overlay freeze (không lệch 1px)
        self.setStyleSheet(
            "QTableView { gridline-color: #d9d9d9; }"
            "QHeaderView::section { background-color: #f5f6f7; border: none;"
            " border-right: 1px solid #d9d9d9; border-bottom: 1px solid #d9d9d9;"
            " padding: 2px 4px; color: #3c4043; }"
            "QTableCornerButton::section { background-color: #f5f6f7; border: none;"
            " border-right: 1px solid #d9d9d9; border-bottom: 1px solid #d9d9d9; }"
        )
        self.verticalHeader().setDefaultSectionSize(24)
        self._filling = False
        self._src: tuple[int, int, int, int] | None = None
        self._dst: tuple[int, int, int, int] | None = None

        # Kéo tiêu đề để di chuyển cột/hàng (dời dữ liệu thật).
        self.horizontalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionsMovable(True)
        self.horizontalHeader().sectionMoved.connect(self._on_col_moved)
        self.verticalHeader().sectionMoved.connect(self._on_row_moved)

        # Nhấp đúp viền tiêu đề -> tự dãn vừa nội dung (auto-fit) như Excel.
        self.horizontalHeader().sectionHandleDoubleClicked.connect(
            self.resizeColumnToContents
        )
        self.verticalHeader().sectionHandleDoubleClicked.connect(
            self.resizeRowToContents
        )
        # Nhấp đúp nút góc trên-trái -> auto-fit toàn bộ cột & hàng.
        self._corner_btn = self.findChild(QAbstractButton)
        if self._corner_btn is not None:
            self._corner_btn.installEventFilter(self)

    # ------------------------------------------------------------ vùng chọn
    def _selection_box(self) -> tuple[int, int, int, int] | None:
        indexes = self.selectionModel().selectedIndexes()
        if not indexes:
            idx = self.currentIndex()
            if not idx.isValid():
                return None
            return (idx.row(), idx.column(), idx.row(), idx.column())
        rows = [i.row() for i in indexes]
        cols = [i.column() for i in indexes]
        return (min(rows), min(cols), max(rows), max(cols))

    def _box_rect(self, box: tuple[int, int, int, int]) -> QRect:
        top, left, bottom, right = box
        tl = self.visualRect(self.model().index(top, left))
        br = self.visualRect(self.model().index(bottom, right))
        return tl.united(br)

    def _handle_center(self):
        box = self._selection_box()
        if box is None:
            return None
        rect = self._box_rect(box)
        return rect.bottomRight()

    def _handle_rect(self) -> QRect | None:
        center = self._handle_center()
        if center is None:
            return None
        return QRect(
            center.x() - _HANDLE // 2, center.y() - _HANDLE // 2, _HANDLE, _HANDLE
        )

    # ------------------------------------------------------------ chuột
    def mousePressEvent(self, event):
        handle = self._handle_rect()
        if (
            event.button() == Qt.LeftButton
            and handle is not None
            and handle.contains(event.position().toPoint())
        ):
            self._filling = True
            self._src = self._selection_box()
            self._dst = self._src
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._filling and self._src is not None:
            self._dst = self._compute_dst(event.position().toPoint())
            self.viewport().update()
            event.accept()
            return
        handle = self._handle_rect()
        if handle is not None and handle.contains(event.position().toPoint()):
            self.viewport().setCursor(Qt.CrossCursor)
        else:
            self.viewport().setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._filling:
            self._filling = False
            if self._src and self._dst and self._dst != self._src:
                self.model().fill(self._src, self._dst)
                self.select_box(self._dst)
            self._dst = None
            self.viewport().update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ------------------------------------------------------------ tính vùng đích
    def _compute_dst(self, point) -> tuple[int, int, int, int]:
        assert self._src is not None
        st, sl, sb, sr = self._src
        idx = self.indexAt(point)
        if not idx.isValid():
            return self._src
        tr, tc = idx.row(), idx.column()
        d_row = (tr - sb) if tr > sb else (tr - st) if tr < st else 0
        d_col = (tc - sr) if tc > sr else (tc - sl) if tc < sl else 0

        if abs(d_row) >= abs(d_col):  # điền dọc
            if tr > sb:
                return (st, sl, tr, sr)
            if tr < st:
                return (tr, sl, sb, sr)
            return self._src
        if tc > sr:  # điền ngang
            return (st, sl, sb, tc)
        if tc < sl:
            return (st, tc, sb, sr)
        return self._src

    # ------------------------------------------------------------ di chuyển cột/hàng
    def _on_col_moved(self, _logical: int, old_visual: int, new_visual: int) -> None:
        h = self.horizontalHeader()
        h.blockSignals(True)
        h.moveSection(new_visual, old_visual)  # khôi phục header về thứ tự gốc
        h.blockSignals(False)
        self.model().move_column(old_visual, new_visual)
        self.select_box((0, new_visual, self.model().rowCount() - 1, new_visual))

    def _on_row_moved(self, _logical: int, old_visual: int, new_visual: int) -> None:
        v = self.verticalHeader()
        v.blockSignals(True)
        v.moveSection(new_visual, old_visual)
        v.blockSignals(False)
        self.model().move_row(old_visual, new_visual)
        self.select_box((new_visual, 0, new_visual, self.model().columnCount() - 1))

    # ------------------------------------------------------------ Ctrl+Shift+mũi tên
    def keyPressEvent(self, event):
        mods = event.modifiers()
        ctrl = bool(mods & Qt.ControlModifier)
        shift = bool(mods & Qt.ShiftModifier)
        arrows = {
            Qt.Key_Up: (-1, 0),
            Qt.Key_Down: (1, 0),
            Qt.Key_Left: (0, -1),
            Qt.Key_Right: (0, 1),
        }
        if ctrl and event.key() in arrows:
            dr, dc = arrows[event.key()]
            self._jump_to_edge(dr, dc, extend=shift)
            event.accept()
            return
        super().keyPressEvent(event)

    def _jump_to_edge(self, dr: int, dc: int, extend: bool) -> None:
        cur = self.currentIndex()
        if not cur.isValid():
            return
        target = self._data_edge(cur.row(), cur.column(), dr, dc)
        t_idx = self.model().index(*target)
        if extend:
            box = self._selection_box() or (cur.row(), cur.column(), cur.row(), cur.column())
            top, left, bottom, right = box
            # Mỏ neo = góc đối diện với ô hiện tại.
            ar = top if cur.row() == bottom else bottom
            ac = left if cur.column() == right else right
            anchor = self.model().index(ar, ac)
            sel = QItemSelection(anchor, t_idx)
            self.selectionModel().select(sel, QItemSelectionModel.ClearAndSelect)
            self.selectionModel().setCurrentIndex(t_idx, QItemSelectionModel.NoUpdate)
        else:
            self.setCurrentIndex(t_idx)
        self.scrollTo(t_idx)

    def _data_edge(self, row: int, col: int, dr: int, dc: int) -> tuple[int, int]:
        """Tìm ô 'mép dữ liệu' theo hướng (dr,dc) — giống Ctrl+Arrow của Excel."""
        m = self.model()
        rows, cols = m.rowCount(), m.columnCount()

        def filled(r, c):
            return bool(str(m.data(m.index(r, c), Qt.DisplayRole) or ""))

        def inside(r, c):
            return 0 <= r < rows and 0 <= c < cols

        nr, nc = row + dr, col + dc
        if not inside(nr, nc):
            return row, col

        r, c = row, col
        if filled(r, c) and filled(nr, nc):
            # Đang trong vùng dữ liệu -> nhảy tới ô cuối cùng còn dữ liệu liền kề.
            while inside(r + dr, c + dc) and filled(r + dr, c + dc):
                r, c = r + dr, c + dc
        else:
            # Nhảy tới ô có dữ liệu kế tiếp (bỏ qua các ô trống).
            r, c = nr, nc
            while inside(r + dr, c + dc) and not filled(r, c):
                r, c = r + dr, c + dc
        return r, c

    def setSelectionModel(self, model):
        super().setSelectionModel(model)
        if model is not None:
            # Vẽ lại toàn viewport khi đổi vùng chọn -> không sót lớp phủ ô cũ.
            model.selectionChanged.connect(lambda *a: self.viewport().update())
            model.currentChanged.connect(lambda *a: self.viewport().update())

    def eventFilter(self, obj, event):
        if obj is getattr(self, "_corner_btn", None) and event.type() == QEvent.MouseButtonDblClick:
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
            return True
        return super().eventFilter(obj, event)

    def select_box(self, box: tuple[int, int, int, int]) -> None:
        top, left, bottom, right = box
        sel = QItemSelection(
            self.model().index(top, left), self.model().index(bottom, right)
        )
        # Đặt ô hiện tại trước (NoUpdate) để không xóa mất vùng chọn bên dưới.
        self.selectionModel().setCurrentIndex(
            self.model().index(top, left), QItemSelectionModel.NoUpdate
        )
        self.selectionModel().select(sel, QItemSelectionModel.ClearAndSelect)

    # ------------------------------------------------------------ vẽ phủ
    def paintEvent(self, event):
        super().paintEvent(event)
        box = self._dst if (self._filling and self._dst) else self._selection_box()
        if box is None:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self._box_rect(box).adjusted(0, 0, -1, -1)

        # Lớp phủ xanh trong suốt lên vùng chọn (vẫn thấy nội dung bên dưới),
        # chừa ô đang chọn để nó nổi bật như Google Sheets.
        cur = self.currentIndex()
        if cur.isValid() and box[0] <= cur.row() <= box[2] and box[1] <= cur.column() <= box[3]:
            region = QRegion(rect) - QRegion(self.visualRect(cur))
            painter.setClipRegion(region)
            painter.fillRect(rect, _WASH)
            painter.setClipping(False)
        else:
            painter.fillRect(rect, _WASH)

        # Viền xanh quanh vùng chọn.
        style = Qt.DashLine if self._filling else Qt.SolidLine
        painter.setPen(QPen(_BLUE, 2, style))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        # Núm kéo: chấm tròn xanh ở góc dưới-phải (ẩn khi đang kéo).
        if not self._filling:
            center = rect.bottomRight()
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(_BLUE)
            painter.drawEllipse(center, 4, 4)
        painter.end()
