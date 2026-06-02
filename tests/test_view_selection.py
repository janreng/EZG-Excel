"""Tests for the cell-selection hot path (view.py). ASCII only."""
import time

from excelapp.table_model import SpreadsheetModel
from excelapp.view import SpreadsheetView


def _make_view(rows, cols):
    view = SpreadsheetView()
    model = SpreadsheetModel([[""] * cols for _ in range(rows)])
    view.setModel(model)
    return view, model


def test_selection_box_single_cell(qapp):
    view, model = _make_view(10, 5)
    view.setCurrentIndex(model.index(3, 2))
    assert view._selection_box() == (3, 2, 3, 2)


def test_selection_box_rectangular_range(qapp):
    view, model = _make_view(10, 5)
    view.select_box((1, 1, 4, 3))
    assert view._selection_box() == (1, 1, 4, 3)


def test_selection_box_no_selection_returns_none(qapp):
    view, model = _make_view(10, 5)
    view.clearSelection()
    view.selectionModel().clearCurrentIndex()
    assert view._selection_box() is None


def test_selection_box_full_column_is_fast(qapp):
    view, model = _make_view(100_000, 5)
    view.select_box((0, 0, 99_999, 0))
    assert view._selection_box() == (0, 0, 99_999, 0)
    start = time.perf_counter()
    for _ in range(50):
        view._selection_box()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"too slow: {elapsed:.3f}s"


def test_header_highlight_full_column(qapp):
    view, model = _make_view(10, 5)
    view.select_box((0, 2, 9, 2))  # select the whole column 2
    view._update_header_highlight()
    assert 2 in view._h_header.selected_cols
    assert view._v_header.selected_rows == set(range(10))


def test_header_highlight_is_fast(qapp):
    view, model = _make_view(100_000, 5)
    view.select_box((0, 0, 99_999, 0))
    start = time.perf_counter()
    for _ in range(20):
        view._update_header_highlight()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"too slow: {elapsed:.3f}s"


def test_selection_change_updates_header(qapp):
    view, model = _make_view(10, 5)
    view.select_box((0, 1, 0, 1))
    view._on_selection_state_changed()
    assert 1 in view._h_header.selected_cols
    assert 0 in view._v_header.selected_rows
