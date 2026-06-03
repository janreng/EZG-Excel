"""Tính thống kê vùng chọn cho Status Bar (Spec 11.2): Sum/Average/Count/...

Module thuần (không phụ thuộc Qt) — kiểm thử headless. Quy ước giống Excel:
- **Count**: đếm ô KHÔNG rỗng (gồm số, chữ, TRUE/FALSE).
- **Numerical Count**: chỉ đếm ô là SỐ (bỏ chữ và boolean).
- **Sum / Average / Min / Max**: chỉ tính trên ô SỐ (bỏ chữ và boolean, đúng
  như status bar Excel — TRUE/FALSE không cộng vào).

Hàm chạy mỗi lần đổi vùng chọn nên tính **một lượt** (running), không cấp phát
list trung gian — tránh phá hot path khi chọn vùng lớn.
"""

from __future__ import annotations

from dataclasses import dataclass


# Khóa item (khớp tên dùng trong menu customize + QSettings).
ITEM_AVERAGE = "average"
ITEM_COUNT = "count"
ITEM_NUMERICAL_COUNT = "numerical_count"
ITEM_MIN = "min"
ITEM_MAX = "max"
ITEM_SUM = "sum"

# Thứ tự hiển thị + mặc định bật/tắt (giống Excel: Avg/Count/Sum bật sẵn).
STAT_ITEMS = (ITEM_AVERAGE, ITEM_COUNT, ITEM_NUMERICAL_COUNT, ITEM_MIN, ITEM_MAX, ITEM_SUM)
DEFAULT_ENABLED = {
    ITEM_AVERAGE: True,
    ITEM_COUNT: True,
    ITEM_NUMERICAL_COUNT: False,
    ITEM_MIN: False,
    ITEM_MAX: False,
    ITEM_SUM: True,
}


@dataclass
class Stats:
    count: int = 0            # ô không rỗng
    numerical_count: int = 0  # ô là số
    total: float = 0.0
    average: float | None = None
    minimum: float | None = None
    maximum: float | None = None

    def value(self, item: str):
        """Trả giá trị theo khóa item, hoặc None nếu không áp dụng."""
        return {
            ITEM_AVERAGE: self.average,
            ITEM_COUNT: self.count,
            ITEM_NUMERICAL_COUNT: self.numerical_count,
            ITEM_MIN: self.minimum,
            ITEM_MAX: self.maximum,
            ITEM_SUM: self.total if self.numerical_count else None,
        }.get(item)


def format_stat_value(val) -> str:
    """Định dạng số cho status bar — KHÔNG dùng ký hiệu khoa học.

    Excel hiển thị `1234567` chứ không phải `1.23457e+06`. Số nguyên (kể cả float
    nguyên) hiện không phần thập phân; số lẻ giữ tối đa 10 chữ số sau dấu chấm rồi
    bỏ số 0 thừa. Không thêm dấu phân tách hàng nghìn để tránh nhầm với dấu thập
    phân kiểu VN (1.000 vs 1,5).
    """
    if isinstance(val, bool):  # phòng xa, không nên xảy ra
        return str(val)
    if isinstance(val, float) and val.is_integer():
        val = int(val)
    if isinstance(val, int):
        return str(val)
    return f"{val:.10f}".rstrip("0").rstrip(".")


def _is_empty(v) -> bool:
    return v is None or v == ""


def compute_stats(values) -> Stats:
    """Duyệt một lượt các giá trị ô (đã tính) -> Stats.

    ``values`` là iterable giá trị thô từ model (số, chuỗi, bool, "" rỗng).
    """
    s = Stats()
    for v in values:
        if _is_empty(v):
            continue
        s.count += 1
        # bool là sub-class của int trong Python -> loại trước khi tính số.
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            f = float(v)
            s.numerical_count += 1
            s.total += f
            s.minimum = f if s.minimum is None else min(s.minimum, f)
            s.maximum = f if s.maximum is None else max(s.maximum, f)
    if s.numerical_count:
        s.average = s.total / s.numerical_count
    return s
