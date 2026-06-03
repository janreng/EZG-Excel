"""Tests cho tham chiếu chéo sheet Sheet1!A1 (Spec 10). Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp import formula  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


# ------------------------------------------------------------ formula thuần
def _res(r, c, sheet=None):
    data = {"sheet2": {(0, 0): 10, (0, 1): 5, (1, 0): 3, (1, 1): 2}}
    if sheet:
        return data.get(sheet.lower(), {}).get((r, c), 0)
    return {(0, 0): 1}.get((r, c), 0)


def test_eval_single_cross_ref():
    assert formula.evaluate("=Sheet2!A1", _res) == 10


def test_eval_cross_range_sum():
    assert formula.evaluate("=SUM(Sheet2!A1:B2)", _res) == 20.0


def test_eval_mixed_local_and_cross():
    assert formula.evaluate("=A1+Sheet2!A1", _res) == 11.0


def test_quoted_sheet_name():
    val = formula.evaluate("='My Sheet'!A1", lambda r, c, s=None: 99 if s == "My Sheet" else 0)
    assert val == 99


def test_has_external_ref():
    assert formula.has_external_ref("=Sheet2!A1") is True
    assert formula.has_external_ref("=A1+B2") is False
    assert formula.has_external_ref("=SUM(A1:A9)") is False


def test_offset_preserves_sheet():
    assert formula.offset_formula("=Sheet2!A1+B1", 1, 0) == "=Sheet2!A2+B2"


def test_split_sheet_ref():
    assert formula.split_sheet_ref("Sheet2!B3") == ("Sheet2", "B3")
    assert formula.split_sheet_ref("'My Sheet'!A1") == ("My Sheet", "A1")


def test_local_formula_still_works():
    # Token SHEETCELL không phá vỡ công thức nội bộ / hàm.
    assert formula.evaluate("=A1+1", _res) == 2.0
    assert formula.evaluate("=SUM(A1:A1)", _res) == 1.0


# ------------------------------------------------------------ tích hợp workbook
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_cross_sheet_read_and_autorecalc(win):
    win.add_sheet()                          # co Sheet1 + Sheet2
    s1, s2 = win.sheets[0].model, win.sheets[1].model
    s2.setData(s2.index(0, 0), "100")        # Sheet2!A1 = 100
    s1.setData(s1.index(0, 0), "=Sheet2!A1+5")
    assert s1.cell_value(0, 0) == 105.0
    # Sua Sheet2!A1 -> Sheet1 tu tinh lai
    s2.setData(s2.index(0, 0), "200")
    assert s1.cell_value(0, 0) == 205.0


def test_cross_sheet_unknown_sheet_is_ref_error(win):
    s1 = win.sheets[0].model
    s1.setData(s1.index(0, 0), "=NoSuch!A1")
    assert s1.cell_value(0, 0) == formula.ERR_REF


def test_rename_sheet_rewrites_refs(qapp):
    assert formula.rename_sheet_refs("=Sheet2!A1+1", "Sheet2", "Data") == "=Data!A1+1"
    assert formula.rename_sheet_refs("=Sheet2!A1", "Sheet2", "My Data") == "='My Data'!A1"
    assert formula.rename_sheet_refs("=A1+B2", "Sheet2", "Data") == "=A1+B2"  # ko đụng -> nguyên văn


def test_rename_sheet_updates_formula_and_value(win):
    win.add_sheet()
    s1, s2 = win.sheets[0].model, win.sheets[1].model
    s2.setData(s2.index(0, 0), "50")
    s1.setData(s1.index(0, 0), "=Sheet2!A1*2")
    assert s1.cell_value(0, 0) == 100.0
    win._rename_sheet_to(1, "Data") if hasattr(win, "_rename_sheet_to") else None
    # Goi truc tiep logic doi ten (bo qua hop thoai).
    old = win.sheets[1].name
    win.sheets[1].name = "Data"
    for s in win.sheets:
        s.model.rename_sheet_in_formulas(old, "Data")
    assert s1._data[0][0] == "=Data!A1*2"          # cong thuc da viet lai
    assert s1.cell_value(0, 0) == 100.0            # van tinh dung
    s2.setData(s2.index(0, 0), "70")
    assert s1.cell_value(0, 0) == 140.0            # van auto-recalc sau doi ten


def test_sort_propagates_cross_sheet(win):
    win.add_sheet()
    s1, s2 = win.sheets[0].model, win.sheets[1].model
    s2.setData(s2.index(0, 0), "3"); s2.setData(s2.index(1, 0), "1")
    s1.setData(s1.index(0, 0), "=Sheet2!A1")
    assert s1.cell_value(0, 0) == 3.0
    s2.sort_rows(0, ascending=True)                # A1 thanh 1
    assert s1.cell_value(0, 0) == 1.0              # sheet1 tu cap nhat sau sort


def test_cross_sheet_cycle_caught(win):
    win.add_sheet()
    s1, s2 = win.sheets[0].model, win.sheets[1].model
    s1.setData(s1.index(0, 0), "=Sheet2!A1")
    s2.setData(s2.index(0, 0), "=Sheet1!A1")   # vong cheo sheet
    v = s1.cell_value(0, 0)
    assert "VÒNG" in str(v) or v in (0, 0.0, "")  # bat vong, khong treo
