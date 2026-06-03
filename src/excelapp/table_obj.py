"""Đối tượng Bảng (Ctrl+T): vùng dữ liệu có tiêu đề, kẻ sọc xen kẽ, hàng Tổng.

Chỉ giữ TRẠNG THÁI bảng (vùng + cờ hàng tổng); phần tô sọc do delegate vẽ
(không ghi đè định dạng người dùng), hàng Tổng do main_window ghi công thức thật.
Mỗi sheet giữ một :class:`TableModel` riêng.
"""

from __future__ import annotations


class Table:
    __slots__ = ("top", "left", "bottom", "right", "name", "total_row")

    def __init__(self, box, name: str, total_row: bool = False):
        self.top, self.left, self.bottom, self.right = box
        self.name = name
        self.total_row = total_row

    def box(self) -> tuple[int, int, int, int]:
        return (self.top, self.left, self.bottom, self.right)

    def contains(self, r: int, c: int) -> bool:
        return self.top <= r <= self.bottom and self.left <= c <= self.right

    def total_row_index(self) -> int:
        """Chỉ số dòng Tổng (ngay dưới bảng)."""
        return self.bottom + 1


class TableModel:
    def __init__(self):
        self.tables: list[Table] = []

    def add(self, box, name: str) -> Table | None:
        """Tạo bảng mới nếu không chồng lấn bảng sẵn có."""
        top, left, bottom, right = box
        for t in self.tables:
            if not (t.bottom < top or t.top > bottom or t.right < left or t.left > right):
                return None  # chồng lấn -> không tạo
        tbl = Table(box, name)
        self.tables.append(tbl)
        return tbl

    def table_at(self, r: int, c: int) -> Table | None:
        for t in self.tables:
            if t.contains(r, c):
                return t
        return None

    def remove_at(self, r: int, c: int) -> Table | None:
        t = self.table_at(r, c)
        if t is not None:
            self.tables.remove(t)
        return t

    def is_banded(self, r: int, c: int) -> bool:
        """True nếu (r,c) là ô thân bảng thuộc dòng sọc (xen kẽ, bỏ dòng tiêu đề)."""
        t = self.table_at(r, c)
        if t is None or r == t.top:
            return False  # ngoài bảng hoặc dòng tiêu đề
        return (r - (t.top + 1)) % 2 == 1
