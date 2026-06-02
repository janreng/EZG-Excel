"""Model lưới (QAbstractTableModel) lưu dữ liệu thô và tính công thức."""

from __future__ import annotations

import functools
import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont

from . import formula

# Các thuộc tính định dạng hợp lệ cho một ô.
_FORMAT_KEYS = ("font", "size", "bold", "italic", "halign", "valign", "wrap")

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

    def __init__(self, rows: list[list[str]] | None = None, parent=None):
        super().__init__(parent)
        self._data: list[list[str]] = rows or [[""] * 26 for _ in range(50)]
        self._eval_cache: dict[tuple[int, int], object] = {}
        self._computing: set[tuple[int, int]] = set()
        self._fmt: dict[tuple[int, int], dict] = {}  # định dạng theo ô
        # Cache QFont theo nội dung định dạng (nhiều ô cùng style dùng chung).
        self._font_cache: dict[tuple, QFont | None] = {}
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
            return self._display_value(row, col)
        if role == Qt.TextAlignmentRole:
            return int(self._alignment(row, col))
        if role == Qt.FontRole:
            return self._font(row, col)
        return None

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
        key = (fmt.get("font"), fmt.get("size"), bool(fmt.get("bold")), bool(fmt.get("italic")))
        if key in self._font_cache:
            return self._font_cache[key]
        family, size, bold, italic = key
        if not (family or size or bold or italic):
            self._font_cache[key] = None
            return None
        f = QFont()
        if family:
            f.setFamily(family)
        if size:
            f.setPointSize(int(size))
        f.setBold(bold)
        f.setItalic(italic)
        self._font_cache[key] = f
        return f

    def wrap_mode(self, row: int, col: int) -> str:
        """'overflow' (mặc định) | 'wrap' (xuống dòng) | 'clip' (cắt)."""
        return self._fmt.get((row, col), {}).get("wrap") or "overflow"

    def _display_value(self, row: int, col: int) -> str:
        value = self._cell_value(row, col)
        return _format(value)

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
        except formula.FormulaError:
            value = "#LỖI!"
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
        if self._data[index.row()][index.column()] == new:
            return True
        self._push_undo()
        self._data[index.row()][index.column()] = new
        self._recalculate()
        return True

    def _recalculate(self) -> None:
        """Xóa cache và báo toàn bộ lưới vẽ lại (công thức có thể phụ thuộc nhau)."""
        self._eval_cache.clear()
        if self.rowCount() and self.columnCount():
            top_left = self.index(0, 0)
            bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

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
        self._push_undo()
        self.beginInsertRows(QModelIndex(), row, row + count - 1)
        for _ in range(count):
            self._data.insert(row, [""] * width)
        self._shift_fmt(lambda r, c: (r + count, c) if r >= row else (r, c))
        self.endInsertRows()
        self._recalculate()
        return True

    def removeRows(self, row: int, count: int = 1, parent=QModelIndex()) -> bool:
        if self.rowCount() - count < 1:
            return False
        self._push_undo()
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        del self._data[row : row + count]
        self._shift_fmt(
            lambda r, c: None if row <= r < row + count else (r - count if r >= row else r, c)
        )
        self.endRemoveRows()
        self._recalculate()
        return True

    def insertColumns(self, col: int, count: int = 1, parent=QModelIndex()) -> bool:
        self._push_undo()
        self.beginInsertColumns(QModelIndex(), col, col + count - 1)
        for r in self._data:
            for _ in range(count):
                r.insert(col, "")
        self._shift_fmt(lambda r, c: (r, c + count) if c >= col else (r, c))
        self.endInsertColumns()
        self._recalculate()
        return True

    def removeColumns(self, col: int, count: int = 1, parent=QModelIndex()) -> bool:
        if self.columnCount() - count < 1:
            return False
        self._push_undo()
        self.beginRemoveColumns(QModelIndex(), col, col + count - 1)
        for r in self._data:
            del r[col : col + count]
        self._shift_fmt(
            lambda r, c: None if col <= c < col + count else (r, c - count if c >= col else c)
        )
        self.endRemoveColumns()
        self._recalculate()
        return True

    def move_column(self, src: int, dst: int) -> None:
        """Di chuyển cột từ vị trí ``src`` tới ``dst`` (kéo header)."""
        n = self.columnCount()
        if src == dst or not (0 <= src < n) or not (0 <= dst < n):
            return
        self._push_undo()
        order = list(range(n))
        order.insert(dst, order.pop(src))
        inv = {old: new for new, old in enumerate(order)}
        for i, row in enumerate(self._data):
            self._data[i] = [row[j] for j in order]
        self._fmt = {(r, inv[c]): v for (r, c), v in self._fmt.items()}
        self._eval_cache.clear()
        # Emit toàn lưới: công thức ở cột bất kỳ có thể tham chiếu cột vừa di
        # chuyển nên giá trị có thể đổi ngoài phạm vi src..dst.
        self.dataChanged.emit(
            self.index(0, 0), self.index(self.rowCount() - 1, n - 1), []
        )

    def move_row(self, src: int, dst: int) -> None:
        """Di chuyển dòng từ vị trí ``src`` tới ``dst`` (kéo header)."""
        n = self.rowCount()
        if src == dst or not (0 <= src < n) or not (0 <= dst < n):
            return
        self._push_undo()
        order = list(range(n))
        order.insert(dst, order.pop(src))
        inv = {old: new for new, old in enumerate(order)}
        self._data = [self._data[j] for j in order]
        self._fmt = {(inv[r], c): v for (r, c), v in self._fmt.items()}
        self._eval_cache.clear()
        # Emit toàn lưới: công thức ở dòng bất kỳ có thể tham chiếu dòng vừa di
        # chuyển nên giá trị có thể đổi ngoài phạm vi src..dst.
        self.dataChanged.emit(
            self.index(0, 0), self.index(n - 1, self.columnCount() - 1), []
        )

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
        self._eval_cache.clear()
        self._undo.clear()
        self._redo.clear()
        self.endResetModel()

    def replace_all_with_fmt(self, rows: list[list[str]], fmt: dict) -> None:
        """Như replace_all nhưng kèm định dạng (khi mở file xlsx)."""
        self.replace_all(rows)
        self.beginResetModel()
        self._fmt = fmt
        self.endResetModel()

    def raw_grid(self) -> list[list[str]]:
        """Bản sao dữ liệu thô để lưu file."""
        return [list(r) for r in self._data]

    # ------------------------------------------------------------ định dạng
    def set_format(self, box: tuple[int, int, int, int], **attrs) -> None:
        """Đặt thuộc tính định dạng cho mọi ô trong vùng. ``None`` để xóa."""
        attrs = {k: v for k, v in attrs.items() if k in _FORMAT_KEYS}
        if not attrs:
            return
        top, left, bottom, right = box
        self._push_undo()
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                fmt = dict(self._fmt.get((r, c), {}))
                for k, v in attrs.items():
                    if v is None:
                        fmt.pop(k, None)
                    else:
                        fmt[k] = v
                if fmt:
                    self._fmt[(r, c)] = fmt
                else:
                    self._fmt.pop((r, c), None)
        self.dataChanged.emit(
            self.index(top, left), self.index(bottom, right), []
        )

    def get_format(self, row: int, col: int) -> dict:
        """Định dạng của một ô (rỗng nếu mặc định)."""
        return dict(self._fmt.get((row, col), {}))

    def all_formats(self) -> dict:
        return {k: dict(v) for k, v in self._fmt.items()}

    # ------------------------------------------------------------ undo / redo
    def _snapshot(self) -> tuple:
        return ([list(r) for r in self._data], {k: dict(v) for k, v in self._fmt.items()})

    def _push_undo(self) -> None:
        self._undo.append(self._snapshot())
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
        self._redo.append(self._snapshot())
        self._apply_snapshot(self._undo.pop())
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        self._undo.append(self._snapshot())
        self._apply_snapshot(self._redo.pop())
        return True

    def _apply_snapshot(self, snapshot: tuple) -> None:
        data, fmt = snapshot
        self.beginResetModel()
        self._data = data
        self._fmt = fmt
        self._eval_cache.clear()
        self.endResetModel()

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

    def clear_range(self, box: tuple[int, int, int, int]) -> None:
        top, left, bottom, right = box
        self._push_undo()
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                self._data[r][c] = ""
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
        self._push_undo()
        rows = len(block)
        cols = max(len(r) for r in block)
        need_rows, need_cols = top + rows, left + cols
        grew = need_rows > self.rowCount() or need_cols > self.columnCount()
        if grew:
            self.beginResetModel()
        self._grow_to(need_rows, need_cols)
        for i, row in enumerate(block):
            for j, val in enumerate(row):
                if src_anchor and formula.is_formula(val):
                    val = formula.offset_formula(
                        val, top - src_anchor[0], left - src_anchor[1]
                    )
                self._data[top + i][left + j] = val
        self._eval_cache.clear()
        if grew:
            self.endResetModel()
        else:
            self.dataChanged.emit(
                self.index(top, left),
                self.index(top + rows - 1, left + cols - 1),
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
        self._push_undo()
        count = 0
        for r in range(len(self._data)):
            for c in range(len(self._data[r])):
                cell = self._data[r][c]
                new = _replace_substr(cell, find, repl, match_case)
                if new != cell:
                    self._data[r][c] = new
                    count += 1
        if count:
            self._recalculate()
        else:
            self._undo.pop()  # không đổi gì -> bỏ snapshot vừa lưu
        return count

    def fill(self, src: tuple[int, int, int, int], dst: tuple[int, int, int, int]) -> None:
        """Kéo-điền (AutoFill) từ vùng nguồn ``src`` ra vùng đích ``dst``.

        Mỗi cái là (top, left, bottom, right) bao trùm. ``dst`` chứa ``src`` và
        mở rộng theo đúng một chiều (lên/xuống hoặc trái/phải).
        """
        st, sl, sb, sr = src
        dt, dl, db, dr = dst
        vertical = (dt < st) or (db > sb)  # mở rộng theo hàng -> điền dọc
        self._push_undo()

        if vertical:
            for c in range(sl, sr + 1):
                source = [self._data[r][c] for r in range(st, sb + 1)]
                for r in range(dt, db + 1):
                    if st <= r <= sb:
                        continue  # giữ nguyên ô nguồn
                    self._data[r][c] = self._fill_value(source, r - st, axis="row")
        else:
            for r in range(dt, db + 1):
                source = [self._data[r][c] for c in range(sl, sr + 1)]
                for c in range(dl, dr + 1):
                    if sl <= c <= sr:
                        continue
                    self._data[r][c] = self._fill_value(source, c - sl, axis="col")

        self._eval_cache.clear()
        self.dataChanged.emit(
            self.index(dt, dl), self.index(db, dr), [Qt.DisplayRole, Qt.EditRole]
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
        self._push_undo()
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
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}"
    return str(value)


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
