"""Test Ctrl+` Show Formulas — model hien cong thuc goc thay vi ket qua. ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402


@pytest.fixture
def model(qapp):
    return SpreadsheetModel([["=1+2", "hello", "5"]])


def test_default_shows_results(model):
    assert model.show_formulas() is False
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "3"


def test_show_formulas_shows_raw(model):
    model.set_show_formulas(True)
    assert model.show_formulas() is True
    # cong thuc -> hien nguyen van
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "=1+2"
    # chu / so -> hien nhu da go
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "hello"
    assert model.data(model.index(0, 2), Qt.DisplayRole) == "5"


def test_toggle_back_shows_results(model):
    model.set_show_formulas(True)
    model.set_show_formulas(False)
    assert model.data(model.index(0, 0), Qt.DisplayRole) == "3"


def test_edit_role_always_raw(model):
    # EditRole luon la cong thuc goc, du o che do nao
    assert model.data(model.index(0, 0), Qt.EditRole) == "=1+2"
    model.set_show_formulas(True)
    assert model.data(model.index(0, 0), Qt.EditRole) == "=1+2"


def test_set_same_value_is_noop(model):
    # set lai cung gia tri khong loi
    model.set_show_formulas(False)
    assert model.show_formulas() is False


def test_datachanged_emitted_on_toggle(model):
    got = []
    model.dataChanged.connect(lambda tl, br, roles: got.append((tl.row(), br.row())))
    model.set_show_formulas(True)
    assert got  # co phat dataChanged de view refresh


def test_menu_check_syncs_per_sheet(qapp):
    # Tick "Hien cong thuc" phai dong bo theo tung sheet khi chuyen tab
    from excelapp.main_window import MainWindow
    w = MainWindow()
    try:
        w.act_show_formulas.setChecked(True)        # bat o Sheet1 (qua duong toggled)
        assert w.model.show_formulas() is True
        w.add_sheet()                               # Sheet2 -> tu activate
        assert w.model.show_formulas() is False     # sheet moi: tat
        assert w.act_show_formulas.isChecked() is False  # tick dong bo
        w.sheet_tabs.setCurrentIndex(0)             # quay lai Sheet1
        assert w.model.show_formulas() is True
        assert w.act_show_formulas.isChecked() is True
    finally:
        w.close()
