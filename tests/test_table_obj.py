"""Tests cho Bảng (Ctrl+T) — Spec 16. Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.table_obj import TableModel  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


# ------------------------------------------------------------ TableModel thuần
def test_add_and_table_at():
    tm = TableModel()
    t = tm.add((0, 0, 3, 2), "Bang1")
    assert t is not None
    assert tm.table_at(1, 1) is t
    assert tm.table_at(9, 9) is None


def test_add_rejects_overlap():
    tm = TableModel()
    tm.add((0, 0, 3, 2), "Bang1")
    assert tm.add((2, 1, 5, 4), "Bang2") is None     # chong lan
    assert tm.add((10, 0, 12, 2), "Bang3") is not None


def test_banding_alternates_skip_header():
    tm = TableModel()
    tm.add((0, 0, 4, 1), "B")
    assert tm.is_banded(0, 0) is False    # tieu de
    assert tm.is_banded(1, 0) is False    # than dong 0
    assert tm.is_banded(2, 0) is True     # than dong 1 -> soc
    assert tm.is_banded(3, 0) is False
    assert tm.is_banded(4, 0) is True


def test_remove_at():
    tm = TableModel()
    tm.add((0, 0, 2, 2), "B")
    assert tm.remove_at(1, 1) is not None
    assert tm.table_at(1, 1) is None


def test_total_row_index():
    tm = TableModel()
    t = tm.add((1, 0, 4, 2), "B")
    assert t.total_row_index() == 5


# ------------------------------------------------------------ tích hợp MainWindow
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def _fill(win, box):
    top, left, bottom, right = box
    for r in range(top, bottom + 1):
        for c in range(left, right + 1):
            win.model.setData(win.model.index(r, c), str((r + 1) * (c + 1)))


def test_create_table_bolds_header_and_registers(win):
    _fill(win, (0, 0, 2, 1))
    win.view.select_box((0, 0, 2, 1))
    win.create_table()
    assert len(win.sheets[0].tables.tables) == 1
    assert win.model.get_format(0, 0).get("bold") is True
    assert win.view.horizontalHeader().filter_enabled is True   # bat phieu loc


def test_table_band_via_model(win):
    win.view.select_box((0, 0, 4, 1))
    win.create_table()
    assert win.model.table_band(2, 0) is True
    assert win.model.table_band(0, 0) is False


def test_total_row_sums_and_toggles(win):
    _fill(win, (0, 0, 2, 1))      # B cot: 2,4,6 (1-based body B2:B3 = 4,6)
    win.view.select_box((0, 0, 2, 1))
    win.create_table()
    win.view.select_box((1, 0, 1, 0))
    win.toggle_total_row()
    t = win.sheets[0].tables.tables[0]
    trow = t.total_row_index()
    assert win.model._data[trow][0] == "Total"
    assert win.model.cell_value(trow, 1) == 10.0     # 4 + 6
    # tat
    win.view.select_box((1, 0, 1, 0))
    win.toggle_total_row()
    assert win.model._data[trow][1] == ""
    assert t.total_row is False


def test_total_row_refuses_overwrite(win):
    _fill(win, (0, 0, 2, 1))
    win.model.setData(win.model.index(3, 1), "keepme")   # dong duoi bang co data
    win.view.select_box((0, 0, 2, 1))
    win.create_table()
    win.view.select_box((1, 0, 1, 0))
    win.toggle_total_row()
    assert win.model._data[3][1] == "keepme"             # KHONG bi de
    assert win.sheets[0].tables.tables[0].total_row is False


def test_total_row_requires_table(win):
    win.view.select_box((5, 5, 5, 5))   # ngoai moi bang
    win.toggle_total_row()              # khong loi, chi bao status
    assert win.statusBar().currentMessage() != ""
