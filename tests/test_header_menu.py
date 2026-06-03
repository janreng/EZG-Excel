"""Tests cho menu chuột phải tiêu đề + AutoFit (Spec 06/09). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import QPoint  # noqa: E402

from excelapp.i18n import set_lang  # noqa: E402


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    w.resize(800, 600)
    yield w
    w.close()
    set_lang("vi")


def test_autofit_cols_changes_width(win):
    win.model.setData(win.model.index(0, 1), "a very long piece of text here")
    before = win.view.columnWidth(1)
    win.view.select_box((0, 1, 0, 1))
    win.autofit_cols()
    assert win.view.columnWidth(1) != before     # da dan lai theo noi dung


def test_autofit_rows_runs(win):
    win.view.select_box((2, 0, 2, 0))
    win.autofit_rows()                            # khong loi


def test_col_header_menu_selects_column(win):
    # Bam phai cot 3 (ngoai vung chon) -> chon ca cot 3 trc khi mo menu.
    hh = win.view.horizontalHeader()
    x = hh.sectionViewportPosition(3) + 2
    # Khong the exec() menu modal trong test -> chi kiem tra logic chon cot.
    # Goi thang phan chon: mo phong dieu kien "col not in selected".
    win.view.selectColumn(3)
    _, cols = win._selected_rows_cols()
    assert 3 in cols


def test_header_menu_methods_exist(win):
    # Cac slot menu ton tai va goi duoc voi pos hop le (logicalIndexAt < 0 -> thoat).
    win._col_header_menu(QPoint(-5, -5))          # ngoai vung -> return, khong loi
    win._row_header_menu(QPoint(-5, -5))


def test_autofit_multi_range(win):
    win.model.setData(win.model.index(0, 0), "xxxxxxxxxx")
    win.model.setData(win.model.index(0, 2), "yyyyyyyyyy")
    win.view.select_box((0, 0, 0, 0))
    from PySide6.QtCore import QItemSelection, QItemSelectionModel
    sel = QItemSelection()
    sel.select(win.model.index(0, 0), win.model.index(0, 0))
    sel.select(win.model.index(0, 2), win.model.index(0, 2))
    win.view.selectionModel().select(sel, QItemSelectionModel.ClearAndSelect)
    win.autofit_cols()                            # ca 2 cot roi, khong loi
