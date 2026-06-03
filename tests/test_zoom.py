"""Test zoom (Ctrl+lan chuot) — Spec 11.3. Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import Qt, QPoint  # noqa: E402
from PySide6.QtGui import QWheelEvent  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402
from excelapp.view import SpreadsheetView  # noqa: E402


@pytest.fixture
def view(qapp):
    v = SpreadsheetView()
    v.setModel(SpreadsheetModel([["1", "2"], ["3", "4"]]))
    return v


def test_default_zoom_100(view):
    assert view.zoom_percent() == 100
    assert view.zoom_factor() == 1.0


def test_set_zoom_changes_section_sizes(view):
    base_row = view.verticalHeader().defaultSectionSize()
    base_col = view.horizontalHeader().defaultSectionSize()
    view.set_zoom(200)
    assert view.zoom_percent() == 200
    assert view.zoom_factor() == 2.0
    assert view.verticalHeader().defaultSectionSize() == base_row * 2
    assert view.horizontalHeader().defaultSectionSize() == base_col * 2


def test_zoom_clamped(view):
    view.set_zoom(1)
    assert view.zoom_percent() == 10      # ke tu duoi (giong Excel)
    view.set_zoom(999)
    assert view.zoom_percent() == 400     # tran tren


def test_zoom_emits_signal(view):
    got = []
    view.zoomChanged.connect(got.append)
    view.set_zoom(150)
    assert got == [150]
    # set lai cung muc -> khong phat them
    view.set_zoom(150)
    assert got == [150]


def test_set_zoom_back_to_100(view):
    view.set_zoom(200)
    view.set_zoom(100)
    assert view.zoom_percent() == 100
    assert view.zoom_factor() == 1.0


def _wheel(view, dy, mods=Qt.ControlModifier):
    return QWheelEvent(
        QPoint(10, 10), view.mapToGlobal(QPoint(10, 10)),
        QPoint(0, 0), QPoint(0, dy),
        Qt.NoButton, mods, Qt.ScrollUpdate, False,
    )


def test_ctrl_wheel_zoom_in_and_out(view):
    start = view.zoom_percent()
    view.wheelEvent(_wheel(view, 120))   # 1 nac len
    assert view.zoom_percent() == start + 10
    view.wheelEvent(_wheel(view, -120))  # 1 nac xuong
    assert view.zoom_percent() == start


def test_trackpad_small_deltas_accumulate(view):
    start = view.zoom_percent()
    # 4 delta nho 30 = 120 -> dung 1 nac (khong nhay 4 nac)
    for _ in range(3):
        view.wheelEvent(_wheel(view, 30))
        assert view.zoom_percent() == start  # chua du 120
    view.wheelEvent(_wheel(view, 30))
    assert view.zoom_percent() == start + 10


def test_non_ctrl_wheel_does_not_zoom(view):
    start = view.zoom_percent()
    view.wheelEvent(_wheel(view, 120, mods=Qt.NoModifier))
    assert view.zoom_percent() == start


def test_delegate_scales_font_at_zoom(view):
    from PySide6.QtWidgets import QStyleOptionViewItem
    delegate = view.itemDelegate()
    idx = view.model().index(0, 0)
    opt = QStyleOptionViewItem()
    delegate.initStyleOption(opt, idx)
    base = opt.font.pointSizeF()
    view.set_zoom(200)
    opt2 = QStyleOptionViewItem()
    delegate.initStyleOption(opt2, idx)
    assert abs(opt2.font.pointSizeF() - base * 2) < 0.01


def test_delegate_no_scale_at_100(view):
    from PySide6.QtWidgets import QStyleOptionViewItem
    delegate = view.itemDelegate()
    idx = view.model().index(0, 0)
    opt = QStyleOptionViewItem()
    delegate.initStyleOption(opt, idx)
    base = opt.font.pointSizeF()
    # van o 100% -> khong doi
    opt2 = QStyleOptionViewItem()
    delegate.initStyleOption(opt2, idx)
    assert opt2.font.pointSizeF() == base
