"""Tests cho nhóm gập dòng/cột (Outline, Spec 09) + hiển thị gộp. ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.outline import OutlineModel  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


# ------------------------------------------------------------ OutlineModel thuần
def test_add_and_collapsed():
    o = OutlineModel()
    assert o.add("row", 2, 5) is True
    assert o.add("row", 2, 5) is False        # trung -> bo qua
    assert o.add("row", 6, 6) is False        # khoang khong hop le
    assert not o.is_collapsed("row", 3)
    o.set_collapsed_overlapping("row", 2, 5, True)
    assert o.is_collapsed("row", 3)
    assert not o.is_collapsed("row", 6)


def test_toggle_overlapping():
    o = OutlineModel()
    o.add("col", 1, 3)
    assert o.toggle_overlapping("col", 1, 3) is True
    assert o.is_collapsed("col", 2)           # gap
    o.toggle_overlapping("col", 1, 3)
    assert not o.is_collapsed("col", 2)        # mo lai


def test_remove_overlapping():
    o = OutlineModel()
    o.add("row", 2, 5)
    o.set_collapsed_overlapping("row", 2, 5, True)
    assert o.remove_overlapping("row", 3, 3) is True
    assert not o.is_collapsed("row", 3)        # het nhom -> het gap


# ------------------------------------------------------------ tich hop MainWindow
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_group_and_collapse_rows(win):
    win.view.select_box((2, 0, 4, 0))
    win.group_rows()
    assert not win.view.isRowHidden(3)         # nhom xong van hien
    win.view.select_box((2, 0, 4, 0))
    win.toggle_group_rows()
    assert win.view.isRowHidden(3)             # gap -> an
    win.view.select_box((2, 0, 4, 0))
    win.toggle_group_rows()
    assert not win.view.isRowHidden(3)         # mo -> hien


def test_group_cols(win):
    win.view.select_box((0, 1, 0, 3))
    win.group_cols()
    win.view.select_box((0, 1, 0, 3))
    win.toggle_group_cols()
    assert win.view.isColumnHidden(2)


def test_ungroup_expands(win):
    win.view.select_box((2, 0, 4, 0))
    win.group_rows()
    win.view.select_box((2, 0, 4, 0))
    win.toggle_group_rows()
    assert win.view.isRowHidden(3)
    win.view.select_box((2, 0, 4, 0))
    win.ungroup_rows()
    assert not win.view.isRowHidden(3)         # bo nhom -> hien lai


def test_visibility_composes_filter_manual_outline(win):
    # 3 nguon ẩn hợp lại đúng: lọc + tự ẩn + gập nhóm.
    for i in range(6):
        win.model.setData(win.model.index(i, 0), "keep" if i != 1 else "drop")
    # tu an dong 0
    win.view.select_box((0, 0, 0, 0)); win.hide_rows()
    # nhom + gap dong 3..4
    win.view.select_box((3, 0, 4, 0)); win.group_rows()
    win.view.select_box((3, 0, 4, 0)); win.toggle_group_rows()
    # loc bo dong co "drop" (dong 1)
    win._filters = {0: {"keep"}}
    win._apply_filters()
    assert win.view.isRowHidden(0)             # tu an
    assert win.view.isRowHidden(1)             # bi loc
    assert not win.view.isRowHidden(2)         # hien
    assert win.view.isRowHidden(3)             # gap nhom
    assert win.view.isRowHidden(4)             # gap nhom
    assert not win.view.isRowHidden(5)


def test_manual_hide_survives_sort_after_refactor(win):
    win.view.select_box((2, 0, 2, 0)); win.hide_rows()
    win._apply_filters()                       # mo phong sort/loc chay lai
    assert win.view.isRowHidden(2)


def test_hidden_cols_isolated_per_sheet(win):
    # An cot 2 o sheet 0 -> sang sheet moi khong bi an -> quay lai van an.
    win.view.select_box((0, 2, 0, 2)); win.hide_cols()
    assert win.view.isColumnHidden(2)
    win.add_sheet()                            # chuyen sang sheet 1
    assert not win.view.isColumnHidden(2)      # sheet moi: cot 2 hien
    win.sheet_tabs.setCurrentIndex(0)          # quay lai sheet 0
    assert win.view.isColumnHidden(2)          # van an dung sheet cu


def test_outline_isolated_per_sheet(win):
    win.view.select_box((2, 0, 4, 0)); win.group_rows()
    win.view.select_box((2, 0, 4, 0)); win.toggle_group_rows()
    assert win.view.isRowHidden(3)
    win.add_sheet()
    assert not win.view.isRowHidden(3)         # sheet moi khong co nhom
    win.sheet_tabs.setCurrentIndex(0)
    assert win.view.isRowHidden(3)             # sheet cu: nhom van gap
