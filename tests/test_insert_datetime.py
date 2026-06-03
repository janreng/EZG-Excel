"""Test chen ngay/gio (Ctrl+; / Ctrl+Shift+;). Offscreen, ASCII only."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    w = MainWindow()
    yield w
    w.close()


def test_insert_date(win):
    win.view.setCurrentIndex(win.model.index(1, 2))
    win._insert_now("date", now=datetime(2026, 6, 2, 14, 30))
    assert win.model.data(win.model.index(1, 2), Qt.EditRole) == "02/06/2026"


def test_insert_time(win):
    win.view.setCurrentIndex(win.model.index(0, 0))
    win._insert_now("time", now=datetime(2026, 6, 2, 9, 5))
    assert win.model.data(win.model.index(0, 0), Qt.EditRole) == "09:05"


def test_insert_updates_formula_bar(win):
    win.view.setCurrentIndex(win.model.index(0, 0))
    win._insert_now("date", now=datetime(2026, 12, 25, 0, 0))
    assert win.formula_edit.text() == "25/12/2026"


def test_insert_noop_when_no_current(win):
    # khong co o hop le -> khong loi
    win.view.clearSelection()
    win.view.setCurrentIndex(win.model.index(-1, -1))
    win._insert_now("date", now=datetime(2026, 6, 2))  # khong nem exception
