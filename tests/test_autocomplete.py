"""Tests cho tự hoàn thành khi gõ (AutoComplete, Spec 05). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QLineEdit, QStyleOptionViewItem  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402
from excelapp.view import SpreadsheetView  # noqa: E402


def test_entries_contiguous_block(qapp):
    m = SpreadsheetModel([["Apple"], ["Banana"], [""], ["Cherry"], ["Date"]])
    # row1 (Banana): khoi lien ke = Apple(tren), Banana, dung o row2 trong
    assert m.column_entries(1, 0) == ["Apple"]
    # row3 (Cherry): khoi = Cherry, Date (tren bi chan boi row2 trong)
    assert m.column_entries(3, 0) == ["Date"]


def test_entries_skip_numbers_and_dedup(qapp):
    m = SpreadsheetModel([["Banana"], ["Apple"], ["Banana"], ["5"], ["Cherry"]])
    # row0 (dang sua): xuong Apple, Banana, 5(so -> bo), Cherry; Banana xuat hien 1 lan
    assert m.column_entries(0, 0) == ["Apple", "Banana", "Cherry"]


def test_entries_isolated_cell_empty(qapp):
    m = SpreadsheetModel([["A"], [""], ["Lonely"], [""], ["B"]])
    assert m.column_entries(2, 0) == []        # bi cô lập boi 2 o trong


def test_entries_excludes_current(qapp):
    m = SpreadsheetModel([["X"], ["Y"]])
    assert "Y" in m.column_entries(0, 0)        # o khac
    # o hien tai (row0) khong tu goi y chinh no
    assert m.column_entries(0, 0).count("X") == 0


def test_editor_gets_completer(qapp):
    m = SpreadsheetModel([["Apple"], ["Banana"], ["Cherry"]])
    v = SpreadsheetView()
    v.setModel(m)
    d = v.itemDelegate()
    opt = QStyleOptionViewItem()
    editor = d.createEditor(v.viewport(), opt, m.index(1, 0))
    assert isinstance(editor, QLineEdit)
    comp = editor.completer()
    assert comp is not None
    assert comp.model().rowCount() >= 1          # co goi y (Apple, Cherry)


def test_editor_no_completer_when_no_entries(qapp):
    m = SpreadsheetModel([["", ""], ["", ""]])
    v = SpreadsheetView()
    v.setModel(m)
    d = v.itemDelegate()
    opt = QStyleOptionViewItem()
    editor = d.createEditor(v.viewport(), opt, m.index(0, 0))
    assert editor.completer() is None            # khong co gi de goi y
