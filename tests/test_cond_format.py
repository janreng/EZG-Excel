"""Tests cho định dạng có điều kiện mở rộng (Spec 17). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402


def _m(values):
    """1 cột dữ liệu từ list."""
    return SpreadsheetModel([[str(v)] for v in values])


def _match(model, rule, row=0, col=0):
    return model._cond_match(row, col, rule)


def test_duplicate():
    m = _m([5, 5, 3, 7, 3])
    box = (0, 0, 4, 0)
    rule = {"box": box, "op": "duplicate", "bg": "#f00"}
    assert _match(m, rule, 0) is True     # 5 trùng
    assert _match(m, rule, 2) is True     # 3 trùng
    assert _match(m, rule, 3) is False    # 7 duy nhất


def test_unique():
    m = _m([5, 5, 7])
    rule = {"box": (0, 0, 2, 0), "op": "unique", "bg": "#f00"}
    assert _match(m, rule, 2) is True     # 7 duy nhất
    assert _match(m, rule, 0) is False


def test_above_below_average():
    m = _m([10, 20, 30])               # avg = 20
    box = (0, 0, 2, 0)
    assert _match(m, {"box": box, "op": "above_avg", "bg": "#f"}, 2) is True   # 30>20
    assert _match(m, {"box": box, "op": "above_avg", "bg": "#f"}, 1) is False  # 20 not >20
    assert _match(m, {"box": box, "op": "below_avg", "bg": "#f"}, 0) is True   # 10<20


def test_top_n():
    m = _m([1, 9, 5, 7, 3])
    box = (0, 0, 4, 0)
    rule = {"box": box, "op": "top_n", "v1": 2, "bg": "#f"}   # top 2 = {9,7}
    assert _match(m, rule, 1) is True     # 9
    assert _match(m, rule, 3) is True     # 7
    assert _match(m, rule, 2) is False    # 5


def test_begins_ends():
    m = SpreadsheetModel([["Apple"], ["Banana"], ["Avocado"]])
    box = (0, 0, 2, 0)
    assert _match(m, {"box": box, "op": "begins", "v1": "A", "bg": "#f"}, 0) is True
    assert _match(m, {"box": box, "op": "begins", "v1": "A", "bg": "#f"}, 1) is False
    assert _match(m, {"box": box, "op": "ends", "v1": "na", "bg": "#f"}, 1) is True


def test_remove_cond_rule():
    m = _m([1, 2, 3])
    m.add_cond_rule({"box": (0, 0, 2, 0), "op": "gt", "v1": 1, "bg": "#f"})
    m.add_cond_rule({"box": (0, 0, 2, 0), "op": "lt", "v1": 3, "bg": "#0f0"})
    assert len(m.cond_rules()) == 2
    m.remove_cond_rule(0)
    assert len(m.cond_rules()) == 1
    assert m.cond_rules()[0]["op"] == "lt"
    m.remove_cond_rule(5)                 # ngoài phạm vi -> bỏ qua, không lỗi
    assert len(m.cond_rules()) == 1


def test_duplicate_ignores_blank():
    m = _m(["", "", "x"])
    rule = {"box": (0, 0, 2, 0), "op": "duplicate", "bg": "#f"}
    assert _match(m, rule, 0) is False    # ô trống không tính trùng


def test_aggregate_cache_invalidated_on_edit(qapp):
    # Sua o trong vung -> ket qua quy tac theo-vung phai cap nhat (cache het han).
    m = _m([10, 20, 30])                      # avg = 20
    box = (0, 0, 2, 0)
    rule = {"box": box, "op": "above_avg", "bg": "#f"}
    assert _match(m, rule, 1) is False        # 20 not > 20
    assert _match(m, rule, 2) is True         # 30 > 20
    m.setData(m.index(2, 0), "0")             # avg moi = (10+20+0)/3 = 10
    assert _match(m, rule, 1) is True         # 20 > 10  (neu cache cu thi van False)
    assert _match(m, rule, 0) is False        # 10 not > 10
    assert _match(m, rule, 2) is False        # 0 not > 10


def test_background_role_applies_new_rule(qapp):
    from PySide6.QtCore import Qt
    m = _m([5, 5, 3])
    m.add_cond_rule({"box": (0, 0, 2, 0), "op": "duplicate", "bg": "#FFC7CE"})
    bg0 = m.data(m.index(0, 0), Qt.BackgroundRole)
    bg2 = m.data(m.index(2, 0), Qt.BackgroundRole)
    assert bg0 is not None                # 5 trùng -> có nền
    assert bg2 is None                    # 3 duy nhất -> không
