"""Tests cho hop thoai Dinh dang o (Ctrl+1) — Spec 08. Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.format_dialog import FormatCellsDialog, _build_code, _parse_code  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


# ------------------------------------------------------------ ma dinh dang so
@pytest.mark.parametrize("cat,dec,thou,custom,expect", [
    ("general", 2, True, "", None),
    ("number", 2, True, "", "#,##0.00"),
    ("number", 0, False, "", "0"),
    ("percent", 1, False, "", "0.0%"),
    ("currency_vnd", 0, True, "", "#,##0₫"),
    ("currency_usd", 2, True, "", "$#,##0.00"),
    ("scientific", 2, False, "", "0.00E+00"),
    ("date", 2, True, "", "dd/mm/yyyy"),
    ("custom", 2, True, "0.000\"kg\"", "0.000\"kg\""),
])
def test_build_code(qapp, cat, dec, thou, custom, expect):
    assert _build_code(cat, dec, thou, custom) == expect


@pytest.mark.parametrize("code,expect", [
    (None, ("general", 2, True)),
    ("#,##0.00", ("number", 2, True)),
    ("0%", ("percent", 0, False)),
    ("$#,##0.00", ("currency_usd", 2, True)),
    ("#,##0₫", ("currency_vnd", 0, True)),
    ("0.00E+00", ("scientific", 2, False)),
    ("dd/mm/yyyy", ("date", 2, True)),
])
def test_parse_code(qapp, code, expect):
    assert _parse_code(code) == expect


# ------------------------------------------------------------ changes() diff
def test_changes_empty_when_untouched(qapp):
    d = FormatCellsDialog(None, {"bold": True, "number_format": "0%", "color": "#FF0000"})
    assert d.changes() == {}


def test_changes_only_touched(qapp):
    d = FormatCellsDialog(None, {})
    d._bold_cb.setChecked(True)
    d._italic_cb.setChecked(True)
    out = d.changes()
    assert out == {"bold": True, "italic": True}


def test_changes_clear_bold_to_none(qapp):
    d = FormatCellsDialog(None, {"bold": True})
    d._bold_cb.setChecked(False)
    assert d.changes() == {"bold": None}


def test_border_kind_default_no_change(qapp):
    d = FormatCellsDialog(None, {})
    assert d.border_kind() is None
    d._border_combo.setCurrentIndex(d._border_vals.index("outer"))
    assert d.border_kind() == "outer"


def test_number_change_emits_code(qapp):
    d = FormatCellsDialog(None, {})           # General mac dinh
    d._cat_list.setCurrentRow(d._cat_keys.index("percent"))
    d._dec_spin.setValue(1)
    assert d.changes().get("number_format") == "0.0%"


def test_protection_locked_default_true(qapp):
    # Excel: o khoa mac dinh -> dialog tich san Locked, khong tinh la "doi".
    d = FormatCellsDialog(None, {})
    assert d._locked_cb.isChecked() is True
    assert "locked" not in d.changes()


# ------------------------------------------------------------ tich hop Ctrl+1
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_apply_format_and_border_single_undo(qapp):
    from excelapp.table_model import SpreadsheetModel
    model = SpreadsheetModel([[""] * 4 for _ in range(4)])
    model.apply_format_and_border([(0, 0, 1, 1)], {"bold": True}, border_kind="outer")
    assert model.get_format(0, 0).get("bold") is True
    assert model.get_format(0, 0).get("border")          # vien ngoai
    assert model.undo() is True                            # MOT Ctrl+Z go ca hai
    assert model.get_format(0, 0).get("bold") is None
    assert model.get_format(0, 0).get("border") is None
    assert model.undo() is False


def test_parse_alt_date_codes(qapp):
    assert _parse_code("yyyy-mm-dd")[0] == "date"
    assert _parse_code("hh:mm")[0] == "time"
    assert _parse_code("mm/dd/yyyy")[0] == "date"


def test_show_format_cells_applies(win, monkeypatch):
    from excelapp import main_window as mw

    class FakeDlg:
        def __init__(self, parent, fmt, sample_value=None):
            pass
        def exec(self):
            from PySide6.QtWidgets import QDialog
            return QDialog.Accepted
        def changes(self):
            return {"bold": True, "number_format": "0%"}
        def border_kind(self):
            return "all"

    monkeypatch.setattr(mw, "FormatCellsDialog", FakeDlg)
    win.view.select_box((0, 0, 1, 1))
    win.show_format_cells()
    assert win.model.get_format(0, 0).get("bold") is True
    assert win.model.get_format(1, 1).get("number_format") == "0%"
    assert win.model.get_format(0, 0).get("border")  # vien da ap


def test_show_format_cells_cancel_noop(win, monkeypatch):
    from excelapp import main_window as mw

    class FakeDlg:
        def __init__(self, *a, **k):
            pass
        def exec(self):
            from PySide6.QtWidgets import QDialog
            return QDialog.Rejected
        def changes(self):
            return {"bold": True}
        def border_kind(self):
            return "all"

    monkeypatch.setattr(mw, "FormatCellsDialog", FakeDlg)
    win.view.select_box((0, 0, 0, 0))
    win.show_format_cells()
    assert win.model.get_format(0, 0).get("bold") is None  # huy -> khong ap
