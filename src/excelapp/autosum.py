"""AutoSum (Alt+=) — dò dải số liền kề để chèn =SUM, theo Excel (Spec 23).

Module thuần (không phụ thuộc Qt) — kiểm thử headless. Quy tắc Excel:
- Ưu tiên dải số **liền tục phía trên** ô hiện tại (cùng cột); nếu không có thì
  dò dải số **liền tục bên trái** (cùng hàng).
- Dải dừng ở ô trống / ô chữ / boolean.
- Không có số liền kề -> trả None (caller có thể chèn "=SUM()" rỗng để user tự gõ).
"""

from __future__ import annotations

from .formula import col_index_to_letters


def _is_number(v) -> bool:
    # bool là sub-class của int -> loại ra (giống Sum của Excel).
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def autosum_range(get_value, row: int, col: int):
    """Trả ``(top, left, bottom, right)`` cho =SUM, hoặc None.

    ``get_value(r, c)`` trả giá trị đã tính của ô (số/chuỗi/None).
    Quét số liền tục phía TRÊN trước, rồi BÊN TRÁI.
    """
    # Phía trên (cột cố định).
    r = row - 1
    while r >= 0 and _is_number(get_value(r, col)):
        r -= 1
    if r < row - 1:  # có ít nhất 1 số phía trên
        return (r + 1, col, row - 1, col)

    # Bên trái (hàng cố định).
    c = col - 1
    while c >= 0 and _is_number(get_value(row, c)):
        c -= 1
    if c < col - 1:
        return (row, c + 1, row, col - 1)

    return None


def range_to_ref(box) -> str:
    """``(top,left,bottom,right)`` -> 'A1' (1 ô) hoặc 'A1:A3' (nhiều ô)."""
    top, left, bottom, right = box
    start = f"{col_index_to_letters(left)}{top + 1}"
    if (top, left) == (bottom, right):
        return start
    end = f"{col_index_to_letters(right)}{bottom + 1}"
    return f"{start}:{end}"


def autosum_formula(get_value, row: int, col: int) -> str | None:
    """Trả chuỗi công thức '=SUM(...)' cho ô (row,col), hoặc None nếu không có dải."""
    box = autosum_range(get_value, row, col)
    if box is None:
        return None
    return f"=SUM({range_to_ref(box)})"
