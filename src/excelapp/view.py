"""QTableView kiểu Google Sheets: bôi đen rõ + núm kéo (Fill Handle) AutoFill."""

from __future__ import annotations

from PySide6.QtCore import (
    QEvent,
    QItemSelection,
    QItemSelectionModel,
    QRect,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor, QPainter, QPen, QRegion
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QCompleter,
    QFrame,
    QHeaderView,
    QLineEdit,
    QStyle,
    QStyleOptionHeader,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
)

from .icons import make_icon

_ICON = 15  # cạnh icon phễu trong header (px)


class FilterHeaderView(QHeaderView):
    """Header cột: khi bật filter sẽ vẽ icon phễu, bấm vào mở popup lọc.
    Các cột thuộc vùng chọn được tô nền vàng nhạt kiểu Excel."""

    filterClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.filter_enabled = False
        self.active: set[int] = set()  # các cột đang có bộ lọc
        self.selected_cols: set[int] = set()  # cột đang được chọn
        self._icon = make_icon("filter", "#5f6368", _ICON)
        self._icon_on = make_icon("filter", "#217346", _ICON)
        self.setSectionsClickable(True)
        self.setHighlightSections(False)

    def set_filter_enabled(self, on: bool) -> None:
        self.filter_enabled = on
        self.viewport().update()

    def refresh(self, active: set[int]) -> None:
        self.active = set(active)
        self.viewport().update()

    def set_selected_cols(self, cols: set[int]) -> None:
        self.selected_cols = cols
        self.viewport().update()

    def _icon_left(self, logical: int) -> int:
        right = self.sectionViewportPosition(logical) + self.sectionSize(logical)
        return right - _ICON - 4

    def paintSection(self, painter, rect, logical):
        # Nếu cột đang trong vùng chọn, tô nền vàng nhạt trước khi super paint
        if logical in self.selected_cols:
            painter.save()
            painter.fillRect(rect.adjusted(0, 0, -1, -1), _HDR_SEL_BG)
            # Vẽ border dưới màu xanh lá Excel thay vì xám
            painter.setPen(QPen(_BLUE, 2))
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.restore()
        super().paintSection(painter, rect, logical)
        if not self.filter_enabled:
            return
        icon = self._icon_on if logical in self.active else self._icon
        ir = QRect(rect.right() - _ICON - 4, rect.center().y() - _ICON // 2, _ICON, _ICON)
        icon.paint(painter, ir)

    def mousePressEvent(self, event):
        if self.filter_enabled:
            pos = event.position().toPoint()
            logical = self.logicalIndexAt(pos)
            if logical >= 0 and pos.x() >= self._icon_left(logical):
                self.filterClicked.emit(logical)
                return  # không sort/di chuyển khi bấm vào phễu
        super().mousePressEvent(event)

_BLUE   = QColor("#217346")         # selection border & handle (green)
_WASH   = QColor(33, 115, 70, 25)  # lớp phủ xanh lá nhạt lên vùng chọn
_BAND   = QColor("#F2F8F5")        # nền sọc xen kẽ cho thân Bảng (Ctrl+T)
_HDR_SEL_BG = QColor("#FFFDE7")    # header highlight khi cột/hàng được chọn
_HANDLE = 8                        # cạnh vùng bắt núm kéo (px)


class RowHeaderView(QHeaderView):
    """Header hàng: highlight hàng đang được chọn, kiểu Excel."""

    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)
        self.selected_rows: set[int] = set()
        self.setHighlightSections(False)

    def set_selected_rows(self, rows: set[int]) -> None:
        self.selected_rows = rows
        self.viewport().update()

    def paintSection(self, painter, rect, logical):
        if logical in self.selected_rows:
            painter.save()
            painter.fillRect(rect.adjusted(0, 0, -1, -1), _HDR_SEL_BG)
            painter.setPen(QPen(_BLUE, 2))
            painter.drawLine(rect.right(), rect.top(), rect.right(), rect.bottom())
            painter.restore()
        super().paintSection(painter, rect, logical)


class CellDelegate(QStyledItemDelegate):
    """Tự vẽ nền vùng chọn: ô active để trắng, các ô còn lại tô xanh nhạt."""

    def __init__(self, view: "SpreadsheetView"):
        super().__init__(view)
        self._view = view

    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        # Tự hoàn thành: gợi ý theo các giá trị chữ liền kề cùng cột (kiểu bảng tính).
        model = self._view.model()
        if isinstance(editor, QLineEdit) and model is not None \
                and hasattr(model, "column_entries"):
            entries = model.column_entries(index.row(), index.column())
            if entries:
                comp = QCompleter(entries, editor)
                comp.setCaseSensitivity(Qt.CaseInsensitive)
                comp.setCompletionMode(QCompleter.InlineCompletion)
                editor.setCompleter(comp)
        return editor

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Zoom: scale cỡ chữ theo mức phóng to của view (mọi ô, kể cả font riêng).
        z = self._view.zoom_factor()
        if z != 1.0:
            f = option.font
            pt = f.pointSizeF()
            if pt > 0:
                f.setPointSizeF(pt * z)
                option.font = f
            else:  # font đặt theo pixel -> vẫn scale để khỏi lệch khi zoom
                px = f.pixelSize()
                if px > 0:
                    f.setPixelSize(max(1, round(px * z)))
                    option.font = f
        model = self._view.model()
        if model is None:
            return
        mode = model.wrap_mode(index.row(), index.column())
        if mode == "wrap":
            option.features |= QStyleOptionViewItem.WrapText
        elif mode == "clip":
            option.textElideMode = Qt.ElideNone  # cắt cứng, không "..."

    def paint(self, painter, option, index):
        # Bỏ tô nền/focus mặc định; vùng chọn được vẽ bằng lớp phủ trong suốt
        # ở SpreadsheetView.paintEvent nên nội dung ô vẫn nhìn rõ.
        option.state &= ~QStyle.State_Selected
        option.state &= ~QStyle.State_HasFocus
        # Sọc xen kẽ của Bảng (Ctrl+T): vẽ nền nhạt khi ô không có màu nền riêng.
        model = self._view.model()
        if model is not None and hasattr(model, "table_band"):
            if model.table_band(index.row(), index.column()) \
                    and not model.cell_has_bg(index.row(), index.column()):
                painter.fillRect(option.rect, _BAND)
        super().paint(painter, option, index)
        self._paint_borders(painter, option, index)

    def _paint_borders(self, painter, option, index) -> None:
        model = self._view.model()
        if model is None:
            return
        border = model.get_format(index.row(), index.column()).get("border")
        if not border:
            return
        r = option.rect
        painter.save()
        for side, color in border.items():
            painter.setPen(QPen(QColor(color), 1))
            if side == "top":
                painter.drawLine(r.topLeft(), r.topRight())
            elif side == "bottom":
                painter.drawLine(r.bottomLeft(), r.bottomRight())
            elif side == "left":
                painter.drawLine(r.topLeft(), r.bottomLeft())
            elif side == "right":
                painter.drawLine(r.topRight(), r.bottomRight())
        painter.restore()


class SpreadsheetView(QTableView):
    # Phát khi đang soạn công thức và người dùng bấm 1 ô để chèn tham chiếu.
    cellPicked = Signal(int, int)
    # Phát khi bắt đầu sửa ô trong lưới: True = gõ ký tự (ENTER mode),
    # False = F2/double-click ô có sẵn (EDIT mode). Dùng cho indicator Cell Mode.
    editStarted = Signal(bool)
    # Phát khi mức zoom đổi (phần trăm) — status bar cập nhật nhãn.
    zoomChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        # Callable trả True khi đang soạn công thức (bật chế độ chọn ô chèn ref).
        self.formula_pick_active = None
        self._h_header = FilterHeaderView(self)
        self._v_header = RowHeaderView(self)
        self.setHorizontalHeader(self._h_header)
        self.setVerticalHeader(self._v_header)
        self.setItemDelegate(CellDelegate(self))
        self.setShowGrid(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            # Grid lines màu xám nhạt kiểu Excel
            "QTableView { gridline-color: #D0D0D0; }"
            # Header Excel style
            "QHeaderView::section {"
            "  background-color: #F3F3F3; border: none;"
            "  border-right: 1px solid #D0D0D0; border-bottom: 1px solid #D0D0D0;"
            "  padding: 2px 6px; font-size: 12px; color: #595959; }"
            "QTableCornerButton::section {"
            "  background-color: #F3F3F3; border: none;"
            "  border-right: 1px solid #D0D0D0; border-bottom: 1px solid #D0D0D0; }"
        )
        self._base_row = 20
        self._base_col = 64
        self.verticalHeader().setDefaultSectionSize(self._base_row)
        self.horizontalHeader().setDefaultSectionSize(self._base_col)
        self._zoom = 1.0  # mức phóng to (Ctrl+lăn chuột), 1.0 = 100%
        self._wheel_accum = 0  # gom delta lăn -> chuột mượt/trackpad không nhảy vọt
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

    def refresh_spans(self) -> None:
        """Áp lại span cho các ô gộp theo model.merges()."""
        self.clearSpans()
        model = self.model()
        if model is None or not hasattr(model, "merges"):
            return
        for (t, l, b, r) in model.merges():
            self.setSpan(t, l, b - t + 1, r - l + 1)

    # ------------------------------------------------------------ vùng chọn
    def _selection_box(self) -> tuple[int, int, int, int] | None:
        # Bounding-box theo range (O(số vùng)) — tránh selectedIndexes() liệt kê
        # từng ô; hàm này chạy trong paintEvent/mouse nên phải nhẹ.
        sm = self.selectionModel()
        sel = sm.selection() if sm else None
        if not sel or sel.isEmpty():
            idx = self.currentIndex()
            if not idx.isValid():
                return None
            return (idx.row(), idx.column(), idx.row(), idx.column())
        top = min(r.top() for r in sel)
        left = min(r.left() for r in sel)
        bottom = max(r.bottom() for r in sel)
        right = max(r.right() for r in sel)
        return (top, left, bottom, right)

    def _selection_ranges(self) -> list[tuple[int, int, int, int]]:
        """Danh sách các vùng chọn rời (Ctrl+Click). Mỗi item là 1 bounding box
        của 1 range — duyệt theo range nên nhẹ kể cả khi chọn cả cột/hàng."""
        sm = self.selectionModel()
        sel = sm.selection() if sm else None
        if not sel or sel.isEmpty():
            idx = self.currentIndex()
            if not idx.isValid():
                return []
            return [(idx.row(), idx.column(), idx.row(), idx.column())]
        return [(r.top(), r.left(), r.bottom(), r.right()) for r in sel]

    def _box_rect(self, box: tuple[int, int, int, int]) -> QRect:
        top, left, bottom, right = box
        tl = self.visualRect(self.model().index(top, left))
        br = self.visualRect(self.model().index(bottom, right))
        return tl.united(br)

    def _handle_center(self):
        # Núm kéo (Fill Handle) chỉ hiện khi chọn DUY NHẤT 1 vùng — đúng Excel:
        # chọn nhiều vùng rời thì không có núm kéo.
        ranges = self._selection_ranges()
        if len(ranges) != 1:
            return None
        rect = self._box_rect(ranges[0])
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
        # Đang soạn công thức -> bấm ô chèn tham chiếu (không đổi vùng chọn).
        if (event.button() == Qt.LeftButton and self.formula_pick_active
                and self.formula_pick_active()):
            idx = self.indexAt(event.position().toPoint())
            if idx.isValid():
                self.cellPicked.emit(idx.row(), idx.column())
                event.accept()
                return
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

    # ------------------------------------------------------------ zoom (Ctrl+lăn)
    def zoom_factor(self) -> float:
        return self._zoom

    def zoom_percent(self) -> int:
        return round(self._zoom * 100)

    def set_zoom(self, percent: int) -> None:
        """Đặt mức phóng to 10–400%. Scale cỡ chữ (qua delegate) + cỡ hàng/cột mặc định."""
        percent = max(10, min(400, int(percent)))
        z = percent / 100.0
        if abs(z - self._zoom) < 1e-6:
            return
        self._zoom = z
        self.verticalHeader().setDefaultSectionSize(max(8, round(self._base_row * z)))
        self.horizontalHeader().setDefaultSectionSize(max(16, round(self._base_col * z)))
        self.viewport().update()
        self.zoomChanged.emit(self.zoom_percent())

    def wheelEvent(self, event):
        # Ctrl + lăn chuột -> zoom (như Excel), không cuộn. Gom delta theo từng nấc
        # 120 (chuột thường = 1 nấc/lần; trackpad/chuột mượt gửi nhiều delta nhỏ ->
        # không nhảy vọt thẳng tới min/max).
        if event.modifiers() & Qt.ControlModifier:
            self._wheel_accum += event.angleDelta().y()
            steps = int(self._wheel_accum / 120)
            if steps:
                self._wheel_accum -= steps * 120
                self.set_zoom(self.zoom_percent() + steps * 10)
            event.accept()
            return
        self._wheel_accum = 0
        super().wheelEvent(event)

    # ------------------------------------------------------------ bắt đầu sửa ô
    def edit(self, index, trigger, event):
        """Override để phân biệt ENTER (gõ ký tự) vs EDIT (F2/double-click).

        Phát ``editStarted`` cho main_window cập nhật Cell Mode indicator. Chỉ
        phát với trigger do người dùng chủ động (gõ / F2 / double-click), bỏ qua
        các lần ``edit()`` gọi nội bộ với NoEditTriggers.
        """
        if trigger == QAbstractItemView.AnyKeyPressed:
            self.editStarted.emit(True)   # gõ ký tự -> ENTER
        elif trigger in (
            QAbstractItemView.DoubleClicked,
            QAbstractItemView.EditKeyPressed,  # F2
        ):
            self.editStarted.emit(False)  # F2 / double-click -> EDIT
        return super().edit(index, trigger, event)

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

    def _update_header_highlight(self) -> None:
        """Cập nhật set cột/hàng được chọn để header highlight như Excel.

        Duyệt theo *range* (O số vùng) thay vì selectedIndexes() liệt kê từng ô.
        """
        sm = self.selectionModel()
        cols: set[int] = set()
        rows: set[int] = set()
        if sm is not None:
            for rng in sm.selection():  # theo range, không liệt kê từng ô
                cols.update(range(rng.left(), rng.right() + 1))
                rows.update(range(rng.top(), rng.bottom() + 1))
        cur = self.currentIndex() if sm is not None else None
        if cur is not None and cur.isValid():
            cols.add(cur.column())
            rows.add(cur.row())
        self._h_header.set_selected_cols(cols)
        self._v_header.set_selected_rows(rows)

    def setSelectionModel(self, model):
        super().setSelectionModel(model)
        if model is not None:
            model.selectionChanged.connect(self._on_selection_state_changed)
            model.currentChanged.connect(self._on_selection_state_changed)

    def _on_selection_state_changed(self, *args) -> None:
        """Làm mới header highlight + vẽ lại overlay vùng chọn (một chỗ)."""
        self._update_header_highlight()
        self.viewport().update()

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
        # Đang kéo AutoFill -> vẽ riêng vùng đích (1 box). Bình thường -> vẽ TỪNG
        # vùng chọn rời (Ctrl+Click) chứ không gộp thành 1 bounding box.
        if self._filling and self._dst:
            boxes = [self._dst]
        else:
            boxes = self._selection_ranges()
        if not boxes:
            return
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing)
        cur = self.currentIndex()
        style = Qt.DashLine if self._filling else Qt.SolidLine
        vp = self.viewport().rect()
        for box in boxes:
            rect = self._box_rect(box).adjusted(0, 0, -1, -1)
            # Vùng cuộn khuất hẳn -> bỏ qua (visualRect trả rect rỗng ở gốc toạ độ,
            # united dễ tạo hình chữ nhật rởm chạy từ (0,0) -> vẽ lem góc trên-trái).
            if not rect.intersects(vp):
                continue
            # Lớp phủ xanh trong suốt (vẫn thấy nội dung), chừa ô đang chọn để
            # nó nổi bật như Google Sheets.
            if (cur.isValid() and box[0] <= cur.row() <= box[2]
                    and box[1] <= cur.column() <= box[3]):
                region = QRegion(rect) - QRegion(self.visualRect(cur))
                painter.setClipRegion(region)
                painter.fillRect(rect, _WASH)
                painter.setClipping(False)
            else:
                painter.fillRect(rect, _WASH)
            painter.setPen(QPen(_BLUE, 2, style))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)

        # Núm kéo: chấm vuông xanh Excel ở góc dưới-phải — chỉ khi 1 vùng & không kéo.
        if not self._filling and len(boxes) == 1:
            center = self._box_rect(boxes[0]).adjusted(0, 0, -1, -1).bottomRight()
            painter.setPen(Qt.NoPen)
            painter.setBrush(_BLUE)
            painter.drawRect(center.x() - 3, center.y() - 3, 6, 6)
        painter.end()
