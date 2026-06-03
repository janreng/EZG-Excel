"""Integration test cho status bar stats (Spec 11.2) — duong di thuc qua MainWindow.

Offscreen, ASCII only. Kiem tra da-vung Ctrl+Click dem dung (khong over-count
theo bounding box) va customize an/hien item.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import QItemSelection, QItemSelectionModel  # noqa: E402

from excelapp import statusbar_stats as st  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")           # nhan ASCII de assert
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def _put(w, r, c, val):
    w.model.setData(w.model.index(r, c), str(val))


def test_contiguous_range_stats(win):
    for i in range(5):
        _put(win, i, 0, i + 1)        # A1..A5 = 1..5
    win.view.select_box((0, 0, 4, 0))
    win._update_stats()
    text = win._stats_label.text()
    assert "Average: 3" in text
    assert "Count: 5" in text
    assert "Sum: 15" in text


def test_multirange_not_overcounted(win):
    # A1=1, C3=3 chon roi; B2=99 nam trong bounding box NHUNG khong duoc chon.
    _put(win, 0, 0, 1)
    _put(win, 1, 1, 99)
    _put(win, 2, 2, 3)
    sm = win.view.selectionModel()
    sel = QItemSelection()
    sel.select(win.model.index(0, 0), win.model.index(0, 0))
    sel.select(win.model.index(2, 2), win.model.index(2, 2))
    sm.select(sel, QItemSelectionModel.ClearAndSelect)
    win._update_stats()
    text = win._stats_label.text()
    # Chi A1 + C3 -> Count 2, Sum 4 (KHONG gom B2=99)
    assert "Count: 2" in text
    assert "Sum: 4" in text
    assert "99" not in text


def test_customize_toggle_min_max(win):
    for i in range(5):
        _put(win, i, 0, i + 1)
    win.view.select_box((0, 0, 4, 0))
    win._toggle_stat_item(st.ITEM_MIN, True)
    win._toggle_stat_item(st.ITEM_MAX, True)
    text = win._stats_label.text()
    assert "Min: 1" in text
    assert "Max: 5" in text
    # cleanup persisted toggles
    win._toggle_stat_item(st.ITEM_MIN, False)
    win._toggle_stat_item(st.ITEM_MAX, False)


def test_large_sum_no_scientific(win):
    _put(win, 0, 0, 1000000)
    _put(win, 1, 0, 234567)
    win.view.select_box((0, 0, 1, 0))
    win._update_stats()
    text = win._stats_label.text()
    assert "1234567" in text          # khong phai 1.23457e+06
    assert "e+" not in text.lower()
