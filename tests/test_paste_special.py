"""Tests cho Dán đặc biệt (Spec 13). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.table_model import SpreadsheetModel  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


def _src(model, box):
    return (model.block_raw(box), model.block_values(box), model.block_formats(box))


# ------------------------------------------------------------ model.paste_special
def test_values_mode_drops_formula(qapp):
    m = SpreadsheetModel([["10", "", ""], ["=A1*2", "", ""], ["", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 1, 0))
    m.paste_special(0, 2, raw, vals, fmts, mode="values", src_anchor=(0, 0))
    assert m._data[0][2] == "10"
    assert m._data[1][2] == "20"        # ket qua, KHONG phai cong thuc


def test_formulas_mode_offsets_refs(qapp):
    m = SpreadsheetModel([["10", "", "", ""], ["=A1*2", "", "", ""], ["", "", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 1, 0))
    m.paste_special(0, 3, raw, vals, fmts, mode="formulas", src_anchor=(0, 0))
    assert m._data[0][3] == "10"
    assert m._data[1][3] == "=D1*2"     # tham chieu doi theo vi tri


def test_formats_mode_copies_only_format(qapp):
    m = SpreadsheetModel([["src", ""], ["", ""]])
    m.set_format((0, 0, 0, 0), bold=True, bg="#FF0000")
    raw, vals, fmts = _src(m, (0, 0, 0, 0))
    m.setData(m.index(1, 1), "keep")
    m.paste_special(1, 1, raw, vals, fmts, mode="formats", src_anchor=(0, 0))
    assert m.get_format(1, 1).get("bold") is True
    assert m.get_format(1, 1).get("bg") == "#FF0000"
    assert m._data[1][1] == "keep"      # du lieu KHONG bi ghi de


def test_operation_add(qapp):
    m = SpreadsheetModel([["10", "", "", "", ""], ["", "", "", "", ""], ["", "", "", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 0, 0))
    m.setData(m.index(0, 4), "5")
    m.paste_special(0, 4, raw, vals, fmts, mode="values", operation="add", src_anchor=(0, 0))
    assert m._data[0][4] == "15"        # 5 + 10


def test_operation_multiply(qapp):
    m = SpreadsheetModel([["3", "", "", "", ""], ["", "", "", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 0, 0))
    m.setData(m.index(0, 4), "7")
    m.paste_special(0, 4, raw, vals, fmts, mode="values", operation="mul", src_anchor=(0, 0))
    assert m._data[0][4] == "21"


def test_operation_divide_by_zero(qapp):
    m = SpreadsheetModel([["0", "", "", "", ""], ["", "", "", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 0, 0))     # nguon = 0
    m.setData(m.index(0, 4), "10")
    m.paste_special(0, 4, raw, vals, fmts, mode="values", operation="div", src_anchor=(0, 0))
    assert m._data[0][4] == "#DIV/0!"


def test_transpose_ragged_no_truncation(qapp):
    # Clipboard ngoài lệch cột: hàng 1 có 3, hàng 2 có 1 -> đệm rồi transpose, ko mất ô.
    m = SpreadsheetModel([["" for _ in range(4)] for _ in range(4)])
    raw = [["a", "b", "c"], ["d"]]
    vals = [["a", "b", "c"], ["d"]]
    fmts = [[{}, {}, {}], [{}]]
    m.paste_special(0, 0, raw, vals, fmts, mode="values", transpose=True, src_anchor=(0, 0))
    # 2x3 (đệm) -> 3x2: [[a,d],[b,""],[c,""]]
    assert m._data[0][0] == "a" and m._data[0][1] == "d"
    assert m._data[1][0] == "b" and m._data[2][0] == "c"


def test_transpose(qapp):
    m = SpreadsheetModel([["a", "b", "c"], ["", "", ""], ["", "", ""]])
    raw, vals, fmts = _src(m, (0, 0, 0, 2))     # 1 hang 3 cot
    m.paste_special(1, 0, raw, vals, fmts, mode="values", transpose=True, src_anchor=(0, 0))
    assert m._data[1][0] == "a"
    assert m._data[2][0] == "b"
    assert m._data[3][0] == "c"                  # thanh 1 cot 3 hang


def test_skip_blanks_preserves_dest(qapp):
    m = SpreadsheetModel([["X"], [""], ["Z"], ["a"], ["b"], ["c"]])
    raw, vals, fmts = _src(m, (0, 0, 2, 0))     # X / (trong) / Z
    m.paste_special(3, 0, raw, vals, fmts, mode="values", skip_blanks=True, src_anchor=(0, 0))
    assert m._data[3][0] == "X"
    assert m._data[4][0] == "b"                  # nguon trong -> giu ô đích
    assert m._data[5][0] == "Z"


def test_paste_special_single_undo(qapp):
    m = SpreadsheetModel([["1", ""], ["", ""]])
    m.set_format((0, 0, 0, 0), bold=True)
    raw, vals, fmts = _src(m, (0, 0, 0, 0))
    m.paste_special(0, 1, raw, vals, fmts, mode="all", src_anchor=(0, 0))
    assert m._data[0][1] == "1"
    assert m.get_format(0, 1).get("bold") is True
    assert m.undo() is True                      # MOT Ctrl+Z go ca du lieu + dinh dang
    assert m._data[0][1] == ""
    assert m.get_format(0, 1).get("bold") is None


# ------------------------------------------------------------ dialog
def test_dialog_default_options(qapp):
    from excelapp.paste_dialog import PasteSpecialDialog
    d = PasteSpecialDialog(None)
    assert d.options() == {"mode": "all", "operation": "none",
                           "skip_blanks": False, "transpose": False}


def test_dialog_pick_values_add(qapp):
    from excelapp.paste_dialog import PasteSpecialDialog
    d = PasteSpecialDialog(None)
    for b in d._mode_group.buttons():
        if b._value == "values":
            b.setChecked(True)
    for b in d._op_group.buttons():
        if b._value == "add":
            b.setChecked(True)
    d._transpose_cb.setChecked(True)
    o = d.options()
    assert o["mode"] == "values" and o["operation"] == "add" and o["transpose"] is True


# ------------------------------------------------------------ tich hop
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_paste_special_integration(win, monkeypatch):
    from excelapp import main_window as mw

    class FakeDlg:
        def __init__(self, parent=None):
            pass
        def exec(self):
            from PySide6.QtWidgets import QDialog
            return QDialog.Accepted
        def options(self):
            return {"mode": "values", "operation": "none",
                    "skip_blanks": False, "transpose": False}

    monkeypatch.setattr(mw, "PasteSpecialDialog", FakeDlg)
    win.model.setData(win.model.index(0, 0), "=5+5")
    win.view.select_box((0, 0, 0, 0))
    win.copy_selection()
    win.view.setCurrentIndex(win.model.index(2, 2))
    win.paste_special()
    assert win.model._data[2][2] == "10"     # dan gia tri da tinh, khong phai cong thuc
