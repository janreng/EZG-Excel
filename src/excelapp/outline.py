"""Nhóm gập dòng/cột (outline) đơn giản.

Lưu danh sách nhóm theo từng trục (dòng/cột), mỗi nhóm là một khoảng [start, end]
kèm cờ đã-gập. Không vẽ thanh +/- riêng — gập/mở qua menu & phím tắt; phần hiển
thị (ẩn dòng/cột khi gập) do main_window gộp chung với bộ lọc và ẩn thủ công.
"""

from __future__ import annotations


class OutlineModel:
    def __init__(self):
        # mỗi nhóm: [start, end, collapsed]
        self.rows: list[list] = []
        self.cols: list[list] = []

    def _groups(self, axis: str) -> list[list]:
        return self.rows if axis == "row" else self.cols

    def add(self, axis: str, start: int, end: int) -> bool:
        """Thêm nhóm [start, end]. Bỏ qua nếu khoảng không hợp lệ hoặc trùng y hệt."""
        if end <= start:
            return False
        groups = self._groups(axis)
        if any(g[0] == start and g[1] == end for g in groups):
            return False
        groups.append([start, end, False])
        return True

    def remove_overlapping(self, axis: str, start: int, end: int) -> bool:
        """Bỏ mọi nhóm giao với [start, end] (lệnh Bỏ nhóm)."""
        groups = self._groups(axis)
        keep = [g for g in groups if g[1] < start or g[0] > end]
        changed = len(keep) != len(groups)
        groups[:] = keep
        return changed

    def set_collapsed_overlapping(self, axis: str, start: int, end: int,
                                  collapsed: bool) -> bool:
        """Đặt cờ gập cho mọi nhóm giao với [start, end]."""
        changed = False
        for g in self._groups(axis):
            if not (g[1] < start or g[0] > end) and g[2] != collapsed:
                g[2] = collapsed
                changed = True
        return changed

    def toggle_overlapping(self, axis: str, start: int, end: int) -> bool:
        """Đảo trạng thái gập của các nhóm giao với [start, end].

        Nếu có nhóm đang mở -> gập tất cả; nếu tất cả đã gập -> mở tất cả.
        """
        hit = [g for g in self._groups(axis) if not (g[1] < start or g[0] > end)]
        if not hit:
            return False
        any_open = any(not g[2] for g in hit)
        for g in hit:
            g[2] = any_open
        return True

    def is_collapsed(self, axis: str, idx: int) -> bool:
        """idx có nằm trong nhóm nào đang gập không (bị ẩn)."""
        return any(g[2] and g[0] <= idx <= g[1] for g in self._groups(axis))

    def has_group(self, axis: str, idx: int) -> bool:
        return any(g[0] <= idx <= g[1] for g in self._groups(axis))
