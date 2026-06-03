"""Model lưới (QAbstractTableModel) lưu dữ liệu thô và tính công thức."""

from __future__ import annotations

import datetime
import functools
import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QFont

from . import formula

# Các thuộc tính định dạng hợp lệ cho một ô.
#   font, size, bold, italic, underline, strike — chữ
#   halign, valign, wrap                        — căn lề / xuống dòng
#   bg, color                                   — màu nền / màu chữ (hex)
#   border                                      — dict {top,bottom,left,right}
#   number_format                               — mã định dạng số kiểu Excel
_FORMAT_KEYS = (
    "font", "size", "bold", "italic", "underline", "strike",
    "halign", "valign", "wrap", "bg", "color", "border", "number_format",
    # Bảo vệ ô — lưu sẵn, có hiệu lực khi bật Bảo vệ trang tính (Spec 29).
    "locked", "hidden",
)

_HALIGN = {
    "left": Qt.AlignLeft,
    "center": Qt.AlignHCenter,
    "right": Qt.AlignRight,
}
_VALIGN = {
    "top": Qt.AlignTop,
    "middle": Qt.AlignVCenter,
    "bottom": Qt.AlignBottom,
}


class SpreadsheetModel(QAbstractTableModel):
    """Lưu nội dung thô của ô (chuỗi/công thức) và tính giá trị hiển thị."""

    mergesChanged = Signal()  # phát khi danh sách ô gộp thay đổi (view cập nhật span)

    def __init__(self, rows: list[list[str]] | None = None, parent=None):
        super().__init__(parent)
        self._data: list[list[str]] = rows or [[""] * 26 for _ in range(50)]
        self._merges: list[tuple[int, int, int, int]] = []  # vùng ô gộp
        self._cond_rules: list[dict] = []  # quy tắc định dạng có điều kiện
        self._show_formulas = False  # Ctrl+` — hiện công thức thay vì kết quả
        self._eval_cache: dict[tuple[int, int], object] = {}
        self._computing: set[tuple[int, int]] = set()
        self._fmt: dict[tuple[int, int], dict] = {}  # định dạng theo ô
        # Cache QFont theo nội dung định dạng (nhiều ô cùng style dùng chung).
        self._font_cache: dict[tuple, QFont | None] = {}
        # Dependency maps cho selective recalc.
        # _deps[A] = tập ô mà công thức tại A tham chiếu tới.
        # _dependents[B] = tập ô có công thức tham chiếu tới B.
        self._deps: dict[tuple[int, int], set] = {}
        self._dependents: dict[tuple[int, int], set] = {}
        self._rebuild_deps()
        self._undo: list[tuple] = []
        self._redo: list[tuple] = []
        self._undo_limit = 100

    # ------------------------------------------------------------ kích thước
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else (len(self._data[0]) if self._data else 0)

    # ------------------------------------------------------------ đọc dữ liệu
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        raw = self._data[row][col]

        if role == Qt.EditRole:
            return raw  # khi sửa thì hiện công thức gốc
        if role == Qt.DisplayRole:
            if self._show_formulas:
                return raw  # hiện đúng nội dung gốc (công thức/số/chữ như đã gõ)
            return self._display_value(row, col)
        if role == Qt.TextAlignmentRole:
            return int(self._alignment(row, col))
        if role == Qt.FontRole:
            return self._font(row, col)
        if role == Qt.BackgroundRole:
            if self._cond_rules:
                rule = self._matching_rule(row, col)
                if rule and rule.get("bg"):
                    return QColor(rule["bg"])
            bg = self._fmt.get((row, col), {}).get("bg")
            return QColor(bg) if bg else None
        if role == Qt.ForegroundRole:
            if self._cond_rules:
                rule = self._matching_rule(row, col)
                if rule and rule.get("color"):
                    return QColor(rule["color"])
            color = self._fmt.get((row, col), {}).get("color")
            return QColor(color) if color else None
        return None

    # ------------------------------------------------------------ hiện công thức (Ctrl+`)
    def show_formulas(self) -> bool:
        return self._show_formulas

    def set_show_formulas(self, on: bool) -> None:
        """Bật/tắt hiện công thức gốc thay vì kết quả; refresh toàn lưới."""
        on = bool(on)
        if on == self._show_formulas:
            return
        self._show_formulas = on
        rows, cols = self.rowCount(), self.columnCount()
        if rows and cols:
            self.dataChanged.emit(
                self.index(0, 0), self.index(rows - 1, cols - 1), [Qt.DisplayRole]
            )

    # ------------------------------------------------------------ điều kiện
    def _matching_rule(self, row: int, col: int):
        """Quy tắc định dạng có điều kiện khớp ô (rule thêm sau ưu tiên), hoặc None."""
        for rule in reversed(self._cond_rules):
            t, l, b, r = rule["box"]
            if t <= row <= b and l <= col <= r and self._cond_match(row, col, rule):
                return rule
        return None

    def _cond_match(self, row: int, col: int, rule: dict) -> bool:
        value = self._cell_value(row, col)
        op = rule["op"]
        if op == "contains":
            return str(rule.get("v1", "")).lower() in _format(value).lower()
        try:
            num = float(value)
        except (TypeError, ValueError):
            return False
        v1 = rule.get("v1")
        v2 = rule.get("v2")
        if op == "gt":
            return num > v1
        if op == "lt":
            return num < v1
        if op == "eq":
            return num == v1
        if op == "between":
            return v1 <= num <= v2
        return False

    def _alignment(self, row: int, col: int):
        fmt = self._fmt.get((row, col), {})
        # Ngang: theo định dạng, nếu không thì số canh phải / chữ canh trái.
        if "halign" in fmt:
            h = _HALIGN.get(fmt["halign"], Qt.AlignLeft)
        else:
            h = Qt.AlignRight if _looks_numeric(self._cell_value(row, col)) else Qt.AlignLeft
        v = _VALIGN.get(fmt.get("valign", "middle"), Qt.AlignVCenter)
        return h | v

    def _font(self, row: int, col: int):
        fmt = self._fmt.get((row, col))
        if not fmt:
            return None
        # Khóa chỉ gồm thuộc tính ảnh hưởng tới font -> nhiều ô cùng style
        # chia sẻ một QFont đã tạo sẵn, tránh cấp phát mỗi lần repaint.
        key = (fmt.get("font"), fmt.get("size"), bool(fmt.get("bold")),
               bool(fmt.get("italic")), bool(fmt.get("underline")), bool(fmt.get("strike")))
        if key in self._font_cache:
            return self._font_cache[key]
        family, size, bold, italic, underline, strike = key
        if not (family or size or bold or italic or underline or strike):
            self._font_cache[key] = None
            return None
        f = QFont()
        if family:
            f.setFamily(family)
        if size:
            f.setPointSize(int(size))
        f.setBold(bold)
        f.setItalic(italic)
        f.setUnderline(underline)
        f.setStrikeOut(strike)
        self._font_cache[key] = f
        return f

    def wrap_mode(self, row: int, col: int) -> str:
        """'overflow' (mặc định) | 'wrap' (xuống dòng) | 'clip' (cắt)."""
        return self._fmt.get((row, col), {}).get("wrap") or "overflow"

    def _display_value(self, row: int, col: int) -> str:
        value = self._cell_value(row, col)
        code = self._fmt.get((row, col), {}).get("number_format")
        if code:
            shown = _apply_number_format(value, code)
            if shown is not None:
                return shown
        return _format(value)

    def cell_value(self, row: int, col: int):
        """Giá trị đã tính của ô (public). Dùng cho status bar / tính toán ngoài."""
        return self._cell_value(row, col)

    def _cell_value(self, row: int, col: int):
        """Giá trị đã tính của ô (số/chuỗi). Có cache và phát hiện vòng lặp."""
        key = (row, col)
        if key in self._eval_cache:
            return self._eval_cache[key]

        raw = self._data[row][col]
        if not formula.is_formula(raw):
            value = _coerce_literal(raw)
            self._eval_cache[key] = value
            return value

        if key in self._computing:
            return "#VÒNG_LẶP!"
        self._computing.add(key)
        try:
            value = formula.evaluate(raw, self._cell_value)
        except formula.FormulaError as exc:
            # Hiển thị mã lỗi kiểu Excel (#DIV/0!, #N/A, #VALUE!, ...).
            value = getattr(exc, "etype", None) or "#VALUE!"
        except RecursionError:
            value = "#VÒNG_LẶP!"
        finally:
            self._computing.discard(key)
        self._eval_cache[key] = value
        return value

    # ------------------------------------------------------------ ghi dữ liệu
    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if role != Qt.EditRole or not index.isValid():
            return False
        new = "" if value is None else str(value)
        row, col = index.row(), index.column()
        old = self._data[row][col]
        if old == new:
            return True
        self._push_undo(("cells", [(row, col, old, new)]))
        self._data[row][col] = new
        self._update_deps(row, col)           # cập nhật dep map cho ô này
        self._recalculate((row, col))         # selective: chỉ dirty ô bị ảnh hưởng
        return True

    # ------------------------------------------------------------ dependency graph

    def _rebuild_deps(self) -> None:
        """Xây lại toàn bộ dependency map từ dữ liệu thô hiện tại."""
        self._deps.clear()
        self._dependents.clear()
        for r, row in enumerate(self._data):
            for c, raw in enumerate(row):
                if formula.is_formula(raw):
                    refs = formula.extract_refs(raw)
                    if refs:
                        self._deps[(r, c)] = refs
                        for dep in refs:
                            self._dependents.setdefault(dep, set()).add((r, c))

    def _update_deps(self, row: int, col: int) -> None:
        """Cập nhật dependency map cho một ô sau khi nội dung thay đổi."""
        key = (row, col)
        for dep in self._deps.pop(key, ()):
            s = self._dependents.get(dep)
            if s is not None:
                s.discard(key)
                if not s:
                    del self._dependents[dep]
        raw = self._data[row][col]
        if formula.is_formula(raw):
            refs = formula.extract_refs(raw)
            if refs:
                self._deps[key] = refs
                for dep in refs:
                    self._dependents.setdefault(dep, set()).add(key)

    def _recalculate(self, changed: tuple[int, int] | None = None) -> None:
        """Xóa cache công thức bị ảnh hưởng và yêu cầu Qt vẽ lại.

        Nếu ``changed`` là None (thao tác bulk / cấu trúc), xóa toàn bộ cache và
        vẽ lại toàn bộ lưới.  Nếu cho biết ô cụ thể, BFS theo _dependents để chỉ
        xóa cache các ô bị ảnh hưởng và emit vùng bounding-box của chúng.
        """
        if changed is None:
            self._eval_cache.clear()
            if self.rowCount() and self.columnCount():
                tl = self.index(0, 0)
                br = self.index(self.rowCount() - 1, self.columnCount() - 1)
                self.dataChanged.emit(tl, br, [Qt.DisplayRole])
            return

        # Selective invalidation: BFS từ ô vừa đổi qua đồ thị phụ thuộc ngược.
        dirty: set[tuple[int, int]] = set()
        queue = [changed]
        while queue:
            cell = queue.pop()
            if cell in dirty:
                continue
            dirty.add(cell)
            for dep in self._dependents.get(cell, ()):
                if dep not in dirty:
                    queue.append(dep)

        for cell in dirty:
            self._eval_cache.pop(cell, None)

        rows_ = [r for r, _ in dirty]
        cols_ = [c for _, c in dirty]
        tl = self.index(min(rows_), min(cols_))
        br = self.index(max(rows_), max(cols_))
        self.dataChanged.emit(tl, br, [Qt.DisplayRole])

    def _recalc_cells(self, cells) -> set[tuple[int, int]]:
        """Vô hiệu cache của ``cells`` + mọi ô phụ thuộc (BFS ngược).

        Trả về tập 'dirty' đã bị xóa cache. KHÔNG emit dataChanged (bên gọi tự
        quyết định vùng vẽ lại). Dùng cho thao tác đổi NHIỀU ô (fill/paste).
        """
        dirty: set[tuple[int, int]] = set()
        queue = list(cells)
        while queue:
            cell = queue.pop()
            if cell in dirty:
                continue
            dirty.add(cell)
            for dep in self._dependents.get(cell, ()):
                if dep not in dirty:
                    queue.append(dep)
        for cell in dirty:
            self._eval_cache.pop(cell, None)
        return dirty

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    # ------------------------------------------------------------ tiêu đề
    def headerData(self, section: int, orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return formula.col_index_to_letters(section)
        return str(section + 1)

    # ------------------------------------------------------------ cấu trúc
    def insertRows(self, row: int, count: int = 1, parent=QModelIndex()) -> bool:
        width = self.columnCount() or 1
        self._push_undo(self._full_snapshot())
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for _ in range(count):
            self._data.insert(row, [""] * width)
        self._shift_fmt(lambda r, c: (r + count, c) if r >= row else (r, c))
        self.endInsertRows()
        self._rebuild_deps()
        self._recalculate()
        return True

    def removeRows(self, row: int, count: int = 1, parent=QModelIndex()) -> bool:
        if self.rowCount() - count < 1:
            return False
        self._push_undo(self._full_snapshot())
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self._data[row : row + count]
        self._shift_fmt(
            lambda r, c: None if row <= r < row + count else (r - count if r >= row else r, c)
        )
        self.endRemoveRows()
        self._rebuild_deps()
        self._recalculate()
        return True

    def insertColumns(self, col: int, count: int = 1, parent=QModelIndex()) -> bool:
        self._push_undo(self._full_snapshot())
        self.beginInsertColumns(QModelIndex(), col, col + count - 1)
        for r in self._data:
            for _ in range(count):
                r.insert(col, "")
        self._shift_fmt(lambda r, c: (r, c + count) if c >= col else (r, c))
        self.endInsertColumns()
        self._rebuild_deps()
        self._recalculate()
        return True

    def removeColumns(self, col: int, count: int = 1, parent=QModelIndex()) -> bool:
        if self.columnCount() - count < 1:
            return False
        self._push_undo(self._full_snapshot())
        self.beginRemoveColumns(QModelIndex(), col, col + count - 1)
        for r in self._data:
            del r[col : col + count]
        self._shift_fmt(
            lambda r, c: None if col <= c < col + count else (r, c - count if c >= col else c)
        )
        self.endRemoveColumns()
        self._rebuild_deps()
        self._recalculate()
        return True

    def move_column(self, src: int, dst: int) -> None:
        """Di chuyển cột từ vị trí ``src`` tới ``dst`` (kéo header)."""
        n = self.columnCount()
        if src == dst or not (0 <= src < n) or not (0 <= dst < n):
            return
        self._push_undo(self._full_snapshot())
        order = list(range(n))
        order.insert(dst, order.pop(src))
        inv = {old: new for new, old in enumerate(order)}
        for i, row in enumerate(self._data):
            self._data[i] = [row[j] for j in order]
        self._fmt = {(r, inv[c]): v for (r, c), v in self._fmt.items()}
        self._rebuild_deps()
        self._recalculate()

    def move_row(self, src: int, dst: int) -> None:
        """Di chuyển dòng từ vị trí ``src`` tới ``dst`` (kéo header)."""
        n = self.rowCount()
        if src == dst or not (0 <= src < n) or not (0 <= dst < n):
            return
        self._push_undo(self._full_snapshot())
        order = list(range(n))
        order.insert(dst, order.pop(src))
        inv = {old: new for new, old in enumerate(order)}
        self._data = [self._data[j] for j in order]
        self._fmt = {(inv[r], c): v for (r, c), v in self._fmt.items()}
        self._rebuild_deps()
        self._recalculate()

    def _shift_fmt(self, mapper) -> None:
        """Dời khóa định dạng theo phép biến đổi (r,c)->(r,c) hoặc None để bỏ."""
        new: dict[tuple[int, int], dict] = {}
        for (r, c), v in self._fmt.items():
            mapped = mapper(r, c)
            if mapped is not None:
                new[mapped] = v
        self._fmt = new

    # ------------------------------------------------------------ tiện ích
    def replace_all(self, rows: list[list[str]]) -> None:
        """Thay toàn bộ dữ liệu (khi mở file mới)."""
        self.beginResetModel()
        self._data = rows if rows else [[""] * 26 for _ in range(50)]
        self._fmt = {}
        self._merges = []
        self._cond_rules = []
        self._eval_cache.clear()
        self._undo.clear()
        self._redo.clear()
        self._rebuild_deps()
        self.endResetModel()
        self.mergesChanged.emit()

    def replace_all_with_fmt(self, rows: list[list[str]], fmt: dict,
                             merges: list | None = None) -> None:
        """Như replace_all nhưng kèm định dạng + ô gộp (khi mở file xlsx)."""
        self.replace_all(rows)
        self.beginResetModel()
        self._fmt = fmt or {}
        self._merges = list(merges or [])
        self.endResetModel()
        self.mergesChanged.emit()

    def raw_grid(self) -> list[list[str]]:
        """Bản sao dữ liệu thô để lưu file."""
        return [list(r) for r in self._data]

    # ------------------------------------------------------------ định dạng
    def set_format(self, box: tuple[int, int, int, int], **attrs) -> None:
        """Đặt thuộc tính định dạng cho mọi ô trong vùng. ``None`` để xóa."""
        self.set_format_ranges([box], **attrs)

    def set_format_ranges(self, boxes, **attrs) -> None:
        """Như :meth:`set_format` nhưng cho nhiều vùng rời (Ctrl+Click) trong MỘT
        bước undo. Các vùng rời nhau nên không đụng key ô nào."""
        attrs = {k: v for k, v in attrs.items() if k in _FORMAT_KEYS}
        if attrs:
            self.apply_format_and_border(boxes, attrs)

    @staticmethod
    def _with_attrs(fmt: dict, attrs: dict) -> dict:
        """Bản sao fmt sau khi đặt/xóa thuộc tính (v=None -> xóa key)."""
        new = dict(fmt)
        for k, v in attrs.items():
            if v is None:
                new.pop(k, None)
            else:
                new[k] = v
        return new

    @staticmethod
    def _with_border(fmt: dict, r: int, c: int,
                     box: tuple[int, int, int, int], kind: str, color: str) -> dict:
        """Bản sao fmt sau khi áp viền 'kind' cho ô (r,c) theo vị trí trong box."""
        top, left, bottom, right = box
        new = dict(fmt)
        b = dict(new.get("border") or {})
        if kind == "none":
            b = {}
        elif kind == "all":
            b = {s: color for s in ("top", "bottom", "left", "right")}
        elif kind == "outer":
            if r == top:
                b["top"] = color
            if r == bottom:
                b["bottom"] = color
            if c == left:
                b["left"] = color
            if c == right:
                b["right"] = color
        elif kind in ("top", "bottom", "left", "right"):
            edge = {"top": r == top, "bottom": r == bottom,
                    "left": c == left, "right": c == right}[kind]
            if edge:
                b[kind] = color
        if b:
            new["border"] = b
        else:
            new.pop("border", None)
        return new

    def apply_format_and_border(self, boxes, attrs: dict | None = None,
                                border_kind: str | None = None,
                                border_color: str = "#000000") -> None:
        """Áp định dạng + (tuỳ chọn) viền cho nhiều vùng trong MỘT bước undo.

        Dùng cho hộp thoại Định dạng ô (Ctrl+1): bấm OK 1 lần -> Ctrl+Z 1 lần.
        """
        attrs = {k: v for k, v in (attrs or {}).items() if k in _FORMAT_KEYS}
        cell_fmts: dict[tuple[int, int], tuple[dict, dict]] = {}
        for box in boxes:
            top, left, bottom, right = box
            for r in range(top, bottom + 1):
                for c in range(left, right + 1):
                    old = dict(self._fmt.get((r, c), {}))
                    new = self._with_attrs(old, attrs) if attrs else dict(old)
                    if border_kind is not None:
                        new = self._with_border(new, r, c, box, border_kind, border_color)
                    if new != old:
                        cell_fmts[(r, c)] = (old, new)
        self._apply_fmt_changes(cell_fmts)

    def _apply_fmt_changes(
        self, cell_fmts: dict[tuple[int, int], tuple[dict, dict]]
    ) -> None:
        """Đẩy undo + áp định dạng + báo dataChanged cho tập ô đã đổi."""
        if not cell_fmts:
            return
        self._push_undo(("fmt", cell_fmts))
        for (r, c), (_, new_fmt) in cell_fmts.items():
            if new_fmt:
                self._fmt[(r, c)] = new_fmt
            else:
                self._fmt.pop((r, c), None)
        rs = [r for r, _ in cell_fmts]
        cs = [c for _, c in cell_fmts]
        self.dataChanged.emit(
            self.index(min(rs), min(cs)), self.index(max(rs), max(cs)), []
        )

    def set_border(self, box: tuple[int, int, int, int], kind: str,
                   color: str = "#000000") -> None:
        """Đặt viền cho vùng. kind: all/outer/top/bottom/left/right/none.

        Viền lưu trong fmt['border'] = {side: color_hex}. Mỗi ô chỉ nhận cạnh
        phù hợp với vị trí của nó trong vùng (vd 'outer' chỉ viền mép ngoài).
        """
        self.set_border_ranges([box], kind, color)

    def set_border_ranges(self, boxes, kind: str, color: str = "#000000") -> None:
        """Như :meth:`set_border` nhưng cho nhiều vùng rời, gộp 1 bước undo.
        Mỗi vùng tự tính mép ngoài của riêng nó (outer/top/bottom...)."""
        self.apply_format_and_border(boxes, border_kind=kind, border_color=color)

    def get_format(self, row: int, col: int) -> dict:
        """Định dạng của một ô (rỗng nếu mặc định)."""
        return dict(self._fmt.get((row, col), {}))

    def all_formats(self) -> dict:
        return {k: dict(v) for k, v in self._fmt.items()}

    # ------------------------------------------------------------ gộp ô (merge)
    def merges(self) -> list[tuple[int, int, int, int]]:
        return list(self._merges)

    def merge_at(self, row: int, col: int):
        """Trả vùng gộp chứa ô (row,col), hoặc None."""
        for (t, l, b, r) in self._merges:
            if t <= row <= b and l <= col <= r:
                return (t, l, b, r)
        return None

    def _merge_box(self, box: tuple[int, int, int, int]) -> bool:
        """Gộp 1 vùng (KHÔNG đẩy undo). Trả True nếu có thay đổi."""
        top, left, bottom, right = box
        if top == bottom and left == right:
            return False  # một ô thì không cần gộp
        # Bỏ các vùng gộp cũ giao với vùng mới.
        self._merges = [m for m in self._merges if not _boxes_overlap(m, box)]
        # Xóa nội dung mọi ô trừ ô góc trên-trái.
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if (r, c) != (top, left):
                    self._data[r][c] = ""
        self._merges.append((top, left, bottom, right))
        self._eval_cache.clear()
        self._rebuild_deps()
        self.dataChanged.emit(self.index(top, left), self.index(bottom, right), [])
        return True

    def _unmerge_box(self, box: tuple[int, int, int, int]) -> bool:
        """Bỏ gộp mọi vùng giao với box (KHÔNG đẩy undo). Trả True nếu có đổi."""
        hit = [m for m in self._merges if _boxes_overlap(m, box)]
        if not hit:
            return False
        self._merges = [m for m in self._merges if m not in hit]
        return True

    def merge_cells(self, box: tuple[int, int, int, int]) -> None:
        """Gộp vùng thành một ô. Giữ nội dung ô góc trên-trái, xóa phần còn lại."""
        snapshot = self._full_snapshot()
        if self._merge_box(box):
            self._push_undo(snapshot)
            self.mergesChanged.emit()

    def unmerge_cells(self, box: tuple[int, int, int, int]) -> None:
        """Bỏ gộp mọi vùng giao với box."""
        snapshot = self._full_snapshot()
        if self._unmerge_box(box):
            self._push_undo(snapshot)
            self.mergesChanged.emit()

    def toggle_merge(self, box: tuple[int, int, int, int]) -> None:
        """Nếu vùng đã có ô gộp thì bỏ gộp, ngược lại thì gộp."""
        self.toggle_merge_ranges([box])

    def toggle_merge_ranges(self, boxes) -> None:
        """Gộp/bỏ gộp NHIỀU vùng rời trong MỘT bước undo, với hành động NHẤT QUÁN
        cho mọi vùng (như Excel): nếu bất kỳ vùng nào đang gộp -> bỏ gộp tất cả;
        ngược lại -> gộp tất cả."""
        if not boxes:
            return
        any_merged = any(
            _boxes_overlap(m, b) for b in boxes for m in self._merges
        )
        snapshot = self._full_snapshot()
        changed = False
        for box in boxes:
            if any_merged:
                changed = self._unmerge_box(box) or changed
            else:
                changed = self._merge_box(box) or changed
        if changed:
            self._push_undo(snapshot)
            self.mergesChanged.emit()

    # ------------------------------------------------------------ định dạng có điều kiện
    def cond_rules(self) -> list[dict]:
        return [dict(r) for r in self._cond_rules]

    def add_cond_rule(self, rule: dict) -> None:
        """Thêm quy tắc tô màu theo điều kiện. rule: {box, op, v1, [v2], bg, [color]}."""
        self._push_undo(self._full_snapshot())
        self._cond_rules.append(dict(rule))
        t, l, b, r = rule["box"]
        self.dataChanged.emit(self.index(t, l), self.index(b, r), [])

    def clear_cond_rules(self, box: tuple[int, int, int, int] | None = None) -> None:
        """Xóa quy tắc giao với ``box`` (hoặc tất cả nếu box=None)."""
        if box is None:
            hit = list(self._cond_rules)
        else:
            hit = [r for r in self._cond_rules if _boxes_overlap(r["box"], box)]
        if not hit:
            return
        self._push_undo(self._full_snapshot())
        self._cond_rules = [r for r in self._cond_rules if r not in hit]
        self.layoutChanged.emit()

    # ------------------------------------------------------------ undo / redo
    #
    # Stack entries (tagged tuples):
    #   ("snapshot", data_copy, fmt_copy)   — thao tác cấu trúc (hiếm)
    #   ("cells",  [(r, c, old, new), ...]) — thay đổi nội dung ô
    #   ("fmt",    {(r,c): (old_fmt, new_fmt)}) — thay đổi định dạng

    def _full_snapshot(self) -> tuple:
        return ("snapshot", [list(r) for r in self._data],
                {k: dict(v) for k, v in self._fmt.items()}, list(self._merges),
                [dict(rule) for rule in self._cond_rules])

    def _push_undo(self, entry: tuple) -> None:
        self._undo.append(entry)
        if len(self._undo) > self._undo_limit:
            self._undo.pop(0)
        self._redo.clear()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> bool:
        if not self._undo:
            return False
        entry = self._undo.pop()
        # Delta entries carry both old+new — same entry goes to redo stack.
        # Snapshot entries only carry pre-op state; capture post-undo state for redo.
        redo_entry = self._full_snapshot() if entry[0] == "snapshot" else entry
        self._apply_entry(entry, direction="undo")
        self._redo.append(redo_entry)
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        entry = self._redo.pop()
        # Snapshot redo entry already holds the target post-op state (captured by undo).
        undo_entry = self._full_snapshot() if entry[0] == "snapshot" else entry
        self._apply_entry(entry, direction="redo")
        self._undo.append(undo_entry)
        return True

    def _apply_entry(self, entry: tuple, direction: str) -> None:
        kind = entry[0]
        if kind == "snapshot":
            _, data, fmt, merges, cond = entry
            self.beginResetModel()
            self._data = data
            self._fmt = fmt
            self._merges = list(merges)
            self._cond_rules = [dict(r) for r in cond]
            self._eval_cache.clear()
            self._rebuild_deps()
            self.endResetModel()
            self.mergesChanged.emit()
        elif kind == "cells":
            _, changes = entry
            # direction="undo" -> restore old; direction="redo" -> restore new
            idx = 2 if direction == "undo" else 3  # old=index2, new=index3
            for r, c, old, new in changes:
                self._data[r][c] = old if direction == "undo" else new
            self._rebuild_deps()
            self._recalculate()
        elif kind == "fmt":
            _, cell_fmts = entry
            idx_restore = 0 if direction == "undo" else 1  # old=0, new=1
            for (r, c), (old_fmt, new_fmt) in cell_fmts.items():
                restored = old_fmt if direction == "undo" else new_fmt
                if restored:
                    self._fmt[(r, c)] = dict(restored)
                else:
                    self._fmt.pop((r, c), None)
            # Emit bounding box of changed cells
            rs = [r for r, c in cell_fmts]
            cs = [c for r, c in cell_fmts]
            self.dataChanged.emit(
                self.index(min(rs), min(cs)), self.index(max(rs), max(cs)), []
            )

    # ------------------------------------------------------------ copy / paste / xóa
    def block_raw(self, box: tuple[int, int, int, int]) -> list[list[str]]:
        """Lấy dữ liệu thô của một vùng (để copy)."""
        top, left, bottom, right = box
        return [
            [self._data[r][c] for c in range(left, right + 1)]
            for r in range(top, bottom + 1)
        ]

    def block_display(self, box: tuple[int, int, int, int]) -> list[list[str]]:
        """Lấy giá trị hiển thị của một vùng (để đưa lên clipboard hệ thống)."""
        top, left, bottom, right = box
        return [
            [self._display_value(r, c) for c in range(left, right + 1)]
            for r in range(top, bottom + 1)
        ]

    def block_values(self, box: tuple[int, int, int, int]) -> list[list[str]]:
        """Giá trị ĐÃ TÍNH của vùng (công thức -> kết quả), dạng chuỗi gọn.
        Dùng cho Dán đặc biệt > Giá trị."""
        top, left, bottom, right = box
        return [
            [_format(self._cell_value(r, c)) for c in range(left, right + 1)]
            for r in range(top, bottom + 1)
        ]

    def block_formats(self, box: tuple[int, int, int, int]) -> list[list[dict]]:
        """Bản sao định dạng từng ô trong vùng. Dùng cho Dán đặc biệt > Định dạng."""
        top, left, bottom, right = box
        return [
            [dict(self._fmt.get((r, c), {})) for c in range(left, right + 1)]
            for r in range(top, bottom + 1)
        ]

    def paste_special(self, top: int, left: int, raw_block, value_block, fmt_block,
                      *, mode: str = "all", operation: str = "none",
                      skip_blanks: bool = False, transpose: bool = False,
                      src_anchor=None) -> None:
        """Dán đặc biệt từ ô (top,left).

        mode: all / values / formulas / formats.
        operation: none / add / sub / mul / div (tính giữa ô đích và giá trị nguồn).
        skip_blanks: bỏ qua ô nguồn trống (không ghi đè đích).
        transpose: xoay hàng <-> cột.

        Dùng undo dạng snapshot để một lần dán (đổi cả dữ liệu lẫn định dạng,
        kể cả khi lưới phải mở rộng) = một bước Ctrl+Z.
        """
        if not raw_block:
            return
        # Đệm hàng về cùng độ rộng (clipboard ngoài có thể lệch số cột) -> transpose
        # không cắt cụt dữ liệu và vùng chọn lại sau khi dán đúng hình chữ nhật.
        w = max(len(r) for r in raw_block)
        raw_block = [list(r) + [""] * (w - len(r)) for r in raw_block]
        value_block = [list(r) + [""] * (w - len(r)) for r in value_block]
        fmt_block = [list(r) + [{}] * (w - len(r)) for r in fmt_block]
        if transpose:
            raw_block = [list(r) for r in zip(*raw_block)]
            value_block = [list(r) for r in zip(*value_block)]
            fmt_block = [list(r) for r in zip(*fmt_block)]
        rows = len(raw_block)
        cols = len(raw_block[0])

        snapshot = self._full_snapshot()
        grew = top + rows > self.rowCount() or left + cols > self.columnCount()
        if grew:
            self.beginResetModel()
        self._grow_to(top + rows, left + cols)

        touch_data = mode in ("all", "values", "formulas") or operation != "none"
        touch_fmt = mode in ("all", "formats")
        for i in range(rows):
            for j in range(len(raw_block[i])):
                r, c = top + i, left + j
                raw, val = raw_block[i][j], value_block[i][j]
                if skip_blanks and raw == "":
                    continue
                if touch_fmt:
                    src_fmt = dict(fmt_block[i][j]) if i < len(fmt_block) and j < len(fmt_block[i]) else {}
                    if src_fmt:
                        self._fmt[(r, c)] = src_fmt
                    else:
                        self._fmt.pop((r, c), None)
                if touch_data:
                    self._data[r][c] = self._paste_cell_value(
                        r, c, raw, val, mode, operation, src_anchor, top, left
                    )

        self._push_undo(snapshot)
        self._eval_cache.clear()
        self._rebuild_deps()
        self._recalculate()
        if grew:
            self.endResetModel()
        else:
            self.dataChanged.emit(
                self.index(top, left), self.index(top + rows - 1, left + cols - 1),
                [Qt.DisplayRole, Qt.EditRole],
            )

    def _paste_cell_value(self, r, c, raw, val, mode, operation, src_anchor,
                          top, left) -> str:
        """Tính chuỗi dữ liệu cho 1 ô đích theo mode/operation của Dán đặc biệt.

        operation != none -> ưu tiên phép tính số (bất kể mode), dùng giá trị
        ĐÃ TÍNH của nguồn (val); không tính được thì dán nguyên val.
        """
        if operation != "none":
            dst = self._cell_value(r, c)
            src = _parse_number(val) if val != "" else None
            dnum = dst if _looks_numeric(dst) else _parse_number(_format(dst))
            if src is not None and dnum is not None:
                if operation == "div" and src == 0:
                    return "#DIV/0!"
                ops = {"add": dnum + src, "sub": dnum - src,
                       "mul": dnum * src, "div": dnum / src if src else 0}
                return _format(ops[operation])
            return val  # không tính được -> dán giá trị nguồn
        if mode == "values":
            return val
        # all / formulas: giữ công thức, dịch tham chiếu tương đối nếu dán trong app.
        if src_anchor and formula.is_formula(raw):
            return formula.offset_formula(raw, top - src_anchor[0], left - src_anchor[1])
        return raw

    def clear_range(self, box: tuple[int, int, int, int]) -> None:
        self.clear_ranges([box])

    def clear_ranges(self, boxes) -> None:
        """Xóa nội dung nhiều vùng rời (Ctrl+Click) trong MỘT bước undo."""
        changes = [
            (r, c, self._data[r][c], "")
            for (top, left, bottom, right) in boxes
            for r in range(top, bottom + 1)
            for c in range(left, right + 1)
            if self._data[r][c] != ""
        ]
        if not changes:
            return
        self._push_undo(("cells", changes))
        for r, c, _old, new in changes:
            self._data[r][c] = new
        self._rebuild_deps()
        self._recalculate()

    def paste_block(
        self,
        top: int,
        left: int,
        block: list[list[str]],
        src_anchor: tuple[int, int] | None = None,
    ) -> None:
        """Dán ``block`` vào từ ô (top, left). Nếu có ``src_anchor`` thì dịch
        tham chiếu tương đối của công thức (dán trong app)."""
        if not block:
            return
        rows = len(block)
        cols = max(len(r) for r in block)
        need_rows, need_cols = top + rows, left + cols
        grew = need_rows > self.rowCount() or need_cols > self.columnCount()
        # Capture old values (only cells that exist; grown cells have old="" by definition)
        changes = []
        for i, row_ in enumerate(block):
            for j in range(len(row_)):
                r_, c_ = top + i, left + j
                old_v = self._data[r_][c_] if r_ < self.rowCount() and c_ < self.columnCount() else ""
                changes.append((r_, c_, old_v, None))  # new filled below
        if grew:
            self.beginResetModel()
        self._grow_to(need_rows, need_cols)
        for idx, (i, row) in enumerate([(i, r) for i, r in enumerate(block)]):
            for j, val in enumerate(row):
                if src_anchor and formula.is_formula(val):
                    val = formula.offset_formula(
                        val, top - src_anchor[0], left - src_anchor[1]
                    )
                self._data[top + i][left + j] = val
        # Fill in new values for delta
        changes = [(r, c, old, self._data[r][c]) for r, c, old, _ in changes]
        self._push_undo(("cells", changes))
        if grew:
            # Đổi kích thước -> rebuild deps + clear toàn bộ là an toàn nhất.
            self._rebuild_deps()
            self._eval_cache.clear()
            self.endResetModel()
        else:
            # Cập nhật deps cục bộ + vô hiệu cache chọn lọc.
            for r, c, _old, _new in changes:
                self._update_deps(r, c)
            changed_cells = {(r, c) for r, c, _o, _n in changes}
            dirty = self._recalc_cells(changed_cells)
            rows_ = [top, top + rows - 1] + [r for r, _ in dirty]
            cols_ = [left, left + cols - 1] + [c for _, c in dirty]
            self.dataChanged.emit(
                self.index(min(rows_), min(cols_)),
                self.index(max(rows_), max(cols_)),
                [Qt.DisplayRole, Qt.EditRole],
            )

    def _grow_to(self, rows: int, cols: int) -> None:
        cur_cols = self.columnCount()
        if cols > cur_cols:
            for r in self._data:
                r.extend([""] * (cols - cur_cols))
        if rows > len(self._data):
            width = self.columnCount()
            for _ in range(rows - len(self._data)):
                self._data.append([""] * width)

    def replace_text(self, find: str, repl: str, match_case: bool = False) -> int:
        """Thay mọi lần xuất hiện của ``find`` trong dữ liệu thô. Trả về số ô đổi."""
        if not find:
            return 0
        changes: list[tuple[int, int, str, str]] = []
        for r in range(len(self._data)):
            for c in range(len(self._data[r])):
                cell = self._data[r][c]
                new = _replace_substr(cell, find, repl, match_case)
                if new != cell:
                    changes.append((r, c, cell, new))
        if not changes:
            return 0
        self._push_undo(("cells", changes))
        for r, c, _old, new in changes:
            self._data[r][c] = new
        self._rebuild_deps()
        self._recalculate()
        return len(changes)

    def fill(self, src: tuple[int, int, int, int], dst: tuple[int, int, int, int]) -> None:
        """Kéo-điền (AutoFill) từ vùng nguồn ``src`` ra vùng đích ``dst``.

        Mỗi cái là (top, left, bottom, right) bao trùm. ``dst`` chứa ``src`` và
        mở rộng theo đúng một chiều (lên/xuống hoặc trái/phải).
        """
        st, sl, sb, sr = src
        dt, dl, db, dr = dst
        vertical = (dt < st) or (db > sb)  # mở rộng theo hàng -> điền dọc
        changes: list[tuple[int, int, str, str]] = []

        if vertical:
            for c in range(sl, sr + 1):
                source = [self._data[r][c] for r in range(st, sb + 1)]
                for r in range(dt, db + 1):
                    if st <= r <= sb:
                        continue  # giữ nguyên ô nguồn
                    new_v = self._fill_value(source, r - st, axis="row")
                    changes.append((r, c, self._data[r][c], new_v))
                    self._data[r][c] = new_v
        else:
            for r in range(dt, db + 1):
                source = [self._data[r][c] for c in range(sl, sr + 1)]
                for c in range(dl, dr + 1):
                    if sl <= c <= sr:
                        continue
                    new_v = self._fill_value(source, c - sl, axis="col")
                    changes.append((r, c, self._data[r][c], new_v))
                    self._data[r][c] = new_v

        self._push_undo(("cells", changes))

        # Cập nhật deps cục bộ cho các ô vừa ghi (không quét toàn lưới).
        for r, c, _old, _new in changes:
            self._update_deps(r, c)
        # Vô hiệu cache chọn lọc: ô đã đổi + ô phụ thuộc.
        changed_cells = {(r, c) for r, c, _o, _n in changes}
        dirty = self._recalc_cells(changed_cells)
        # Vẽ lại bounding-box phủ vùng đích + các ô phụ thuộc ngoài vùng.
        rows_ = [dt, db] + [r for r, _ in dirty]
        cols_ = [dl, dr] + [c for _, c in dirty]
        self.dataChanged.emit(
            self.index(min(rows_), min(cols_)),
            self.index(max(rows_), max(cols_)),
            [Qt.DisplayRole, Qt.EditRole],
        )

    def _fill_value(self, source: list[str], pos: int, axis: str) -> str:
        """Giá trị điền cho ô ở vị trí ``pos`` (0 = ô nguồn đầu tiên)."""
        n = len(source)
        si = ((pos % n) + n) % n  # chỉ số ô nguồn (lặp vòng)
        base = source[si]

        # Công thức: sao chép kèm dịch tham chiếu tương đối.
        if formula.is_formula(base):
            delta = pos - si
            drow, dcol = (delta, 0) if axis == "row" else (0, delta)
            return formula.offset_formula(base, drow, dcol)

        # Dãy số cấp số cộng (hoặc 1 ô số -> sao chép).
        series = _as_series(source)
        if series is not None:
            first, step = series
            return _format(first + pos * step)

        # 1 ô chữ có số ở cuối -> tăng dần (vd "Item1" -> "Item2").
        if n == 1:
            inc = _increment_trailing_number(base, pos)
            if inc is not None:
                return inc

        # Mặc định: lặp lại mẫu nguồn.
        return base

    def sort_rows(self, col: int, ascending: bool = True) -> None:
        """Sắp xếp các dòng theo giá trị (đã tính) của một cột."""
        if col < 0 or col >= self.columnCount():
            return
        self._push_undo(self._full_snapshot())
        self.layoutAboutToBeChanged.emit()
        # Khóa sắp xếp: số đứng trước, rồi đến chuỗi; ô rỗng xuống cuối.
        def key(row_index: int):
            value = self._cell_value(row_index, col)
            if value == "" or value is None:
                return (2, 0.0, "")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return (0, float(value), "")
            return (1, 0.0, str(value).lower())

        order = sorted(range(len(self._data)), key=key, reverse=not ascending)
        self._data = [self._data[i] for i in order]
        self._rebuild_deps()
        self._eval_cache.clear()
        self.layoutChanged.emit()


# ---------------------------------------------------------------- tiện ích định dạng


def _coerce_literal(raw: str):
    if raw == "":
        return ""
    try:
        if "." in raw or "e" in raw.lower():
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _format(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}"
    return str(value)


# Các mã định dạng ngày/giờ -> chuỗi strftime tương ứng.
_DATE_CODES = {
    "dd/mm/yyyy": "%d/%m/%Y",
    "mm/dd/yyyy": "%m/%d/%Y",
    "yyyy-mm-dd": "%Y-%m-%d",
    "hh:mm:ss": "%H:%M:%S",
    "hh:mm": "%H:%M",
}
def _boxes_overlap(a: tuple, b: tuple) -> bool:
    """Hai vùng (top,left,bottom,right) có giao nhau không."""
    at, al, ab, ar = a
    bt, bl, bb, br = b
    return not (ab < bt or bb < at or ar < bl or br < al)


_EXCEL_EPOCH = datetime.datetime(1899, 12, 30)
# Phần số trong mã định dạng (vd '#,##0.00') để tách prefix/suffix (tiền tệ...).
_NUM_PAT = re.compile(r"[#0][#0,]*(\.[0#]+)?")


def _apply_number_format(value, code: str):
    """Áp mã định dạng số kiểu Excel lên ``value``.

    Trả về chuỗi đã định dạng, hoặc ``None`` nếu không áp dụng được
    (giá trị không phải số -> để hàm gọi dùng _format mặc định).
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    if code in _DATE_CODES:
        try:
            dt = _EXCEL_EPOCH + datetime.timedelta(days=float(value))
            return dt.strftime(_DATE_CODES[code])
        except (OverflowError, ValueError):
            return None
    percent = "%" in code
    body = code.replace("%", "")
    v = value * 100 if percent else value
    if "E" in body.upper():  # khoa học
        decimals = body.upper().split("E")[0].split(".")
        nd = decimals[1].count("0") if len(decimals) > 1 else 2
        return format(v, f".{nd}E") + ("%" if percent else "")
    m = _NUM_PAT.search(body)
    if not m:
        return _format(value)
    prefix, suffix = body[:m.start()], body[m.end():]
    numpart = m.group()
    thousands = "," in numpart.split(".")[0]
    decimals = numpart.split(".", 1)[1].count("0") if "." in numpart else 0
    spec = f"{',' if thousands else ''}.{decimals}f"
    sign = "-" if v < 0 else ""
    core = format(abs(v), spec)
    return f"{sign}{prefix}{core}{suffix}" + ("%" if percent else "")


def _looks_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _parse_number(text: str):
    if formula.is_formula(text):
        return None
    try:
        return float(text)
    except (ValueError, TypeError):
        return None


def _as_series(source: list[str]):
    """Nếu các ô là số: trả (giá_trị_đầu, bước). 1 ô -> bước 0 (sao chép)."""
    nums = []
    for cell in source:
        num = _parse_number(cell)
        if num is None:
            return None
        nums.append(num)
    if len(nums) == 1:
        return (nums[0], 0.0)
    diffs = [nums[i + 1] - nums[i] for i in range(len(nums) - 1)]
    if all(abs(d - diffs[0]) < 1e-9 for d in diffs):
        return (nums[0], diffs[0])
    return None


@functools.lru_cache(maxsize=64)
def _ci_pattern(find: str):
    """Regex (đã compile, cache) để tìm ``find`` không phân biệt hoa/thường."""
    return re.compile(re.escape(find), re.IGNORECASE)


def _replace_substr(text: str, find: str, repl: str, match_case: bool) -> str:
    if match_case:
        return text.replace(find, repl)
    # Thay không phân biệt hoa/thường, giữ phần còn lại nguyên vẹn.
    # Pattern compile sẵn & cache theo ``find`` (replace_all loop toàn lưới).
    return _ci_pattern(find).sub(lambda _m: repl, text)


_TRAILING_NUM_RE = re.compile(r"^(.*?)(\d+)$")


def _increment_trailing_number(text: str, pos: int):
    """'Item1' + pos -> 'Item{1+pos}'. Trả None nếu không có phần chữ ở đầu."""
    m = _TRAILING_NUM_RE.match(text)
    if not m or m.group(1) == "":
        return None  # chuỗi rỗng phần đầu nghĩa là số thuần -> để nơi khác xử lý
    prefix, digits = m.group(1), m.group(2)
    new_num = int(digits) + pos
    if new_num < 0:
        new_num = 0
    return f"{prefix}{new_num}"
