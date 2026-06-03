"""Tests cho Mini Toolbar định dạng nhanh (Spec 06). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtWidgets import QToolButton  # noqa: E402

from excelapp.mini_toolbar import make_mini_toolbar  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


def test_make_mini_toolbar_builds_buttons(qapp):
    calls = []
    specs = [
        ("bold", "Bold", lambda: calls.append("b")),
        None,                                    # vach ngan
        ("italic", "Italic", lambda: calls.append("i")),
    ]
    w = make_mini_toolbar(None, specs)
    btns = w.findChildren(QToolButton)
    assert len(btns) == 2
    btns[0].click(); btns[1].click()
    assert calls == ["b", "i"]


@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_toggle_fmt_on_off(win):
    win.view.select_box((0, 0, 0, 0))
    win._toggle_fmt("bold")
    assert win.model.get_format(0, 0).get("bold") is True
    win._toggle_fmt("bold")
    assert win.model.get_format(0, 0).get("bold") is None     # tat -> xoa key


def test_mini_toolbar_applies_to_selection(win):
    from PySide6.QtWidgets import QMenu, QToolButton
    win.view.select_box((0, 0, 1, 1))
    menu = QMenu(win)
    bar = win._make_mini_toolbar(menu)
    btns = bar.findChildren(QToolButton)
    # Nut dau = Bold -> ap cho ca vung chon.
    btns[0].click()
    assert win.model.get_format(0, 0).get("bold") is True
    assert win.model.get_format(1, 1).get("bold") is True


def test_mini_toolbar_align(win):
    from PySide6.QtWidgets import QMenu, QToolButton
    win.view.select_box((0, 0, 0, 0))
    menu = QMenu(win)
    bar = win._make_mini_toolbar(menu)
    btns = bar.findChildren(QToolButton)
    # Thu tu: bold,italic,underline, fontcolor,fill,borders, alignL,alignC,alignR, merge
    align_center = btns[7]
    align_center.click()
    assert win.model.get_format(0, 0).get("halign") == "center"
