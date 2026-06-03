"""Tests cho Ẩn / Hiện dòng & cột (Spec 09). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import QItemSelection, QItemSelectionModel  # noqa: E402

from excelapp.i18n import set_lang  # noqa: E402


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def _select(win, box):
    win.view.select_box(box)


def test_hide_rows(win):
    _select(win, (1, 0, 3, 0))          # chon dong 1..3
    win.hide_rows()
    assert win.view.isRowHidden(1)
    assert win.view.isRowHidden(3)
    assert not win.view.isRowHidden(0)


def test_hide_cols(win):
    _select(win, (0, 2, 0, 4))          # chon cot 2..4
    win.hide_cols()
    assert win.view.isColumnHidden(2)
    assert win.view.isColumnHidden(4)
    assert not win.view.isColumnHidden(1)


def test_unhide_in_selection(win):
    win.view.setRowHidden(5, True)      # dong 5 dang an
    _select(win, (4, 0, 6, 0))          # chon 4..6 (trum dong an o giua)
    win.unhide_selection()
    assert not win.view.isRowHidden(5)


def test_unhide_columns_in_selection(win):
    win.view.setColumnHidden(3, True)
    _select(win, (0, 2, 0, 4))
    win.unhide_selection()
    assert not win.view.isColumnHidden(3)


def test_manual_hide_survives_filter_reapply(win):
    # Dong tu an khong bi _apply_filters (sort/loc) lam hien lai.
    _select(win, (2, 0, 2, 0))
    win.hide_rows()
    assert win.view.isRowHidden(2)
    win._apply_filters()                # mo phong sort/loc chay lai
    assert win.view.isRowHidden(2)      # van an


def test_manual_hide_survives_unhide_all(win):
    _select(win, (2, 0, 2, 0))
    win.hide_rows()
    win._unhide_all()                   # clear_filters goi cai nay
    assert win.view.isRowHidden(2)      # tu an -> van giu


def test_hide_multi_range(win):
    # Hai vung roi -> gop tap dong/cot dung.
    sm = win.view.selectionModel()
    sel = QItemSelection()
    sel.select(win.model.index(1, 0), win.model.index(1, 0))
    sel.select(win.model.index(5, 0), win.model.index(5, 0))
    sm.select(sel, QItemSelectionModel.ClearAndSelect)
    win.hide_rows()
    assert win.view.isRowHidden(1)
    assert win.view.isRowHidden(5)
    assert not win.view.isRowHidden(3)
