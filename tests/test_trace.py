"""Tests cho Truy vết ô tham chiếu / phụ thuộc (Spec 12). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


def test_precedents_and_dependents():
    m = SpreadsheetModel([["1"], ["2"], ["3"]])
    # C? dung 1 cot; dung A3 = A1 + A2
    m.setData(m.index(2, 0), "=A1+A2")
    assert m.precedents(2, 0) == [(0, 0), (1, 0)]    # A3 tham chieu A1, A2
    assert m.dependents(0, 0) == [(2, 0)]            # A1 bi A3 phu thuoc
    assert m.dependents(1, 0) == [(2, 0)]
    assert m.precedents(0, 0) == []                  # A1 la so, ko tham chieu


def test_dependents_updates_on_edit():
    m = SpreadsheetModel([["1"], [""], [""]])
    m.setData(m.index(1, 0), "=A1*2")
    assert m.dependents(0, 0) == [(1, 0)]
    m.setData(m.index(1, 0), "5")                    # bo cong thuc
    assert m.dependents(0, 0) == []                  # het phu thuoc


def test_range_precedents():
    m = SpreadsheetModel([["1"], ["2"], ["3"], [""]])
    m.setData(m.index(3, 0), "=SUM(A1:A3)")
    assert m.precedents(3, 0) == [(0, 0), (1, 0), (2, 0)]


# ------------------------------------------------------------ tích hợp
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def _sel_cells(win):
    return {(i.row(), i.column()) for i in win.view.selectionModel().selectedIndexes()}


def test_trace_precedents_selects(win):
    m = win.model
    m.setData(m.index(0, 0), "10")
    m.setData(m.index(1, 0), "20")
    m.setData(m.index(2, 0), "=A1+A2")
    win.view.setCurrentIndex(m.index(2, 0))
    win.trace_precedents()
    assert _sel_cells(win) == {(0, 0), (1, 0)}
    assert win.statusBar().currentMessage() != ""


def test_trace_dependents_selects(win):
    m = win.model
    m.setData(m.index(0, 0), "5")
    m.setData(m.index(1, 0), "=A1*2")
    m.setData(m.index(2, 0), "=A1+1")
    win.view.setCurrentIndex(m.index(0, 0))
    win.trace_dependents()
    assert _sel_cells(win) == {(1, 0), (2, 0)}


def test_trace_none_message(win):
    win.model.setData(win.model.index(0, 0), "42")   # so, ko tham chieu
    win.view.setCurrentIndex(win.model.index(0, 0))
    win.trace_precedents()
    assert win.statusBar().currentMessage() != ""    # bao "khong co", ko treo
