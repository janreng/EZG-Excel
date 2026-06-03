"""Tests cho chon nhieu vung roi (Ctrl+Click) — Spec 02.

Offscreen, ASCII only. Phu: view._selection_ranges, num keo an khi da vung,
model.set_format_ranges/clear_ranges/set_border_ranges gop 1 buoc undo, va
guard copy nhieu vung kieu Excel.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import QItemSelection, QItemSelectionModel  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402
from excelapp.view import SpreadsheetView  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


def _make_view(rows, cols):
    view = SpreadsheetView()
    model = SpreadsheetModel([[""] * cols for _ in range(rows)])
    view.setModel(model)
    return view, model


def _select_disjoint(view, *boxes):
    """Chon nhieu vung roi nhau (ClearAndSelect vung dau, them cac vung sau)."""
    sm = view.selectionModel()
    sel = QItemSelection()
    for (t, l, b, r) in boxes:
        sel.select(view.model().index(t, l), view.model().index(b, r))
    sm.select(sel, QItemSelectionModel.ClearAndSelect)


# ------------------------------------------------------------ view: ranges
def test_selection_ranges_single(qapp):
    view, model = _make_view(10, 5)
    view.select_box((1, 1, 3, 2))
    assert view._selection_ranges() == [(1, 1, 3, 2)]


def test_selection_ranges_multiple(qapp):
    view, model = _make_view(10, 5)
    _select_disjoint(view, (0, 0, 0, 0), (2, 2, 3, 3))
    ranges = view._selection_ranges()
    assert (0, 0, 0, 0) in ranges
    assert (2, 2, 3, 3) in ranges
    assert len(ranges) == 2


def test_selection_ranges_empty(qapp):
    view, model = _make_view(10, 5)
    view.clearSelection()
    view.selectionModel().clearCurrentIndex()
    assert view._selection_ranges() == []


# ------------------------------------------------------------ view: num keo
def test_fill_handle_visible_single_range(qapp):
    view, model = _make_view(10, 5)
    view.select_box((1, 1, 2, 2))
    assert view._handle_center() is not None  # 1 vung -> co num keo


def test_fill_handle_hidden_multi_range(qapp):
    view, model = _make_view(10, 5)
    _select_disjoint(view, (0, 0, 0, 0), (2, 2, 3, 3))
    assert view._handle_center() is None  # nhieu vung -> an num keo (nhu Excel)


# ------------------------------------------------------------ model: dinh dang da vung, 1 undo
def test_set_format_ranges_applies_all(qapp):
    model = SpreadsheetModel([[""] * 5 for _ in range(5)])
    model.set_format_ranges([(0, 0, 0, 0), (2, 2, 3, 3)], bold=True)
    assert model.get_format(0, 0).get("bold") is True
    assert model.get_format(3, 3).get("bold") is True
    # O ngoai vung khong bi anh huong
    assert model.get_format(1, 1).get("bold") is None


def test_set_format_ranges_single_undo(qapp):
    model = SpreadsheetModel([[""] * 5 for _ in range(5)])
    model.set_format_ranges([(0, 0, 0, 0), (4, 4, 4, 4)], bold=True)
    assert model.undo() is True          # MOT buoc undo go het 2 vung
    assert model.get_format(0, 0).get("bold") is None
    assert model.get_format(4, 4).get("bold") is None
    assert model.undo() is False         # khong con buoc nao


def test_clear_ranges_single_undo(qapp):
    data = [["x"] * 5 for _ in range(5)]
    model = SpreadsheetModel(data)
    model.clear_ranges([(0, 0, 0, 0), (4, 4, 4, 4)])
    assert model.data(model.index(0, 0)) == ""
    assert model.data(model.index(4, 4)) == ""
    assert model.data(model.index(2, 2)) == "x"  # ngoai vung -> con nguyen
    assert model.undo() is True
    assert model.data(model.index(0, 0)) == "x"
    assert model.data(model.index(4, 4)) == "x"


def test_set_border_ranges_per_area_outer(qapp):
    model = SpreadsheetModel([[""] * 5 for _ in range(5)])
    # Hai vung 1x1 roi nhau -> moi vung tu lay mep ngoai cua rieng no.
    model.set_border_ranges([(0, 0, 0, 0), (4, 4, 4, 4)], "outer")
    b0 = model.get_format(0, 0).get("border")
    b1 = model.get_format(4, 4).get("border")
    assert b0 and set(b0) == {"top", "bottom", "left", "right"}
    assert b1 and set(b1) == {"top", "bottom", "left", "right"}
    assert model.undo() is True          # 1 buoc undo
    assert model.get_format(0, 0).get("border") is None


# ------------------------------------------------------------ MainWindow: guard copy
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_copy_multi_range_blocked(win, monkeypatch):
    from excelapp import main_window as mw
    calls = {"n": 0}
    monkeypatch.setattr(
        mw.QMessageBox, "warning", lambda *a, **k: calls.__setitem__("n", calls["n"] + 1)
    )
    win.model.setData(win.model.index(0, 0), "1")
    win.model.setData(win.model.index(2, 2), "3")
    _select_disjoint(win.view, (0, 0, 0, 0), (2, 2, 2, 2))
    win._clip = None
    win.copy_selection()
    assert calls["n"] == 1          # da canh bao kieu Excel
    assert win._clip is None        # khong copy gi


def test_copy_single_range_ok(win, monkeypatch):
    from excelapp import main_window as mw
    monkeypatch.setattr(mw.QMessageBox, "warning", lambda *a, **k: None)
    win.model.setData(win.model.index(0, 0), "1")
    win.view.select_box((0, 0, 1, 0))
    win.copy_selection()
    assert win._clip is not None    # 1 vung -> copy binh thuong


def test_toggle_merge_ranges_single_undo(qapp):
    model = SpreadsheetModel([[""] * 6 for _ in range(6)])
    # Hai vung roi -> gop het trong 1 buoc undo.
    model.toggle_merge_ranges([(0, 0, 0, 1), (3, 3, 3, 4)])
    assert model.merge_at(0, 0) == (0, 0, 0, 1)
    assert model.merge_at(3, 3) == (3, 3, 3, 4)
    assert model.undo() is True            # MOT Ctrl+Z bo het ca 2 vung gop
    assert model.merge_at(0, 0) is None
    assert model.merge_at(3, 3) is None


def test_toggle_merge_ranges_consistent_action(qapp):
    model = SpreadsheetModel([[""] * 6 for _ in range(6)])
    model.toggle_merge_ranges([(0, 0, 0, 1)])     # vung A da gop
    # A da gop, B chua -> "any_merged" True -> bo gop het (nhat quan, khong toggle nguoc)
    model.toggle_merge_ranges([(0, 0, 0, 1), (3, 3, 3, 4)])
    assert model.merge_at(0, 0) is None
    assert model.merge_at(3, 3) is None


def test_apply_format_multi_range(win):
    _select_disjoint(win.view, (0, 0, 0, 0), (3, 3, 4, 4))
    win._apply_format(bold=True)
    assert win.model.get_format(0, 0).get("bold") is True
    assert win.model.get_format(4, 4).get("bold") is True
    assert win.model.get_format(1, 1).get("bold") is None
