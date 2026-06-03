"""Integration test cho Cell Mode indicator wiring (MainWindow + view).

Chay offscreen (conftest dat QT_QPA_PLATFORM). ASCII only.
Kiem tra cac handler da noi day du va doi mode dung qua duong di thuc.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtWidgets import QAbstractItemView, QAbstractItemDelegate  # noqa: E402

from excelapp.cell_mode import CellMode, ModeEvent  # noqa: E402


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    w = MainWindow()
    yield w
    w.close()


def test_initial_mode_ready(win):
    assert win._cell_mode == CellMode.READY
    assert win._mode_label.text()  # nhan khong rong


def test_journey_through_handlers(win):
    win._on_edit_started(True)          # go ky tu -> Enter
    assert win._cell_mode == CellMode.ENTER
    win._on_editor_closed()             # editor dong -> Ready
    assert win._cell_mode == CellMode.READY
    win._on_edit_started(False)         # F2/dblclick -> Edit
    assert win._cell_mode == CellMode.EDIT
    win._fx_picking = True
    win._apply_mode_event(ModeEvent.PICK_REF)  # chon ref -> Point
    assert win._cell_mode == CellMode.POINT
    win._apply_mode_event(ModeEvent.CANCEL)    # Esc -> Ready
    assert win._cell_mode == CellMode.READY


def test_editor_closed_skips_commit_while_picking(win):
    # Dang chon ref (Point) thi editor dong KHONG duoc keo ve Ready
    win._on_edit_started(False)         # -> Edit
    win._fx_picking = True
    win._apply_mode_event(ModeEvent.PICK_REF)  # -> Point
    assert win._cell_mode == CellMode.POINT
    win._on_editor_closed()             # picking=True -> bo qua
    assert win._cell_mode == CellMode.POINT


def test_editor_closed_revert_hint_is_cancel(win):
    # Esc trong editor (RevertModelCache) van ve Ready
    win._on_edit_started(True)          # -> Enter
    assert win._cell_mode == CellMode.ENTER
    win._on_editor_closed(None, QAbstractItemDelegate.RevertModelCache)
    assert win._cell_mode == CellMode.READY


def test_current_changed_resets_to_ready(win):
    win._on_edit_started(True)          # -> Enter
    assert win._cell_mode == CellMode.ENTER
    idx = win.model.index(2, 1)         # di chuyen o
    win._on_current_changed(idx, win.model.index(0, 0))
    assert win._cell_mode == CellMode.READY


def test_edit_override_emits_editstarted(win):
    # view.edit() phat editStarted: True voi AnyKeyPressed, False voi F2/dblclick
    got = []
    win.view.editStarted.connect(got.append)
    idx = win.model.index(0, 0)
    try:
        win.view.edit(idx, QAbstractItemView.AnyKeyPressed, None)
        win.view.closePersistentEditor(idx)
        win.view.edit(idx, QAbstractItemView.DoubleClicked, None)
        win.view.closePersistentEditor(idx)
    finally:
        pass
    assert got[:2] == [True, False]


def test_formula_bar_edit_sets_edit_mode(win):
    win._on_formula_edited("=A1")
    assert win._cell_mode == CellMode.EDIT
