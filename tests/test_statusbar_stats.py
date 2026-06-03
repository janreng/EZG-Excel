"""Unit test cho statusbar_stats.compute_stats (Spec 11.2). ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from excelapp import statusbar_stats as st  # noqa: E402
from excelapp.statusbar_stats import compute_stats  # noqa: E402


def test_basic_numbers():
    s = compute_stats([1, 2, 3, 4, 5])
    assert s.count == 5
    assert s.numerical_count == 5
    assert s.total == 15
    assert s.average == 3
    assert s.minimum == 1
    assert s.maximum == 5


def test_empty_cells_skipped():
    s = compute_stats(["", None, 10, "", 20])
    assert s.count == 2            # chi 2 o khong rong
    assert s.numerical_count == 2
    assert s.total == 30
    assert s.average == 15


def test_text_counts_but_not_numeric():
    s = compute_stats(["apple", "banana", 5])
    assert s.count == 3           # 2 text + 1 so
    assert s.numerical_count == 1
    assert s.total == 5
    assert s.average == 5
    assert s.minimum == 5
    assert s.maximum == 5


def test_only_text_no_numeric():
    s = compute_stats(["a", "b", "c"])
    assert s.count == 3
    assert s.numerical_count == 0
    assert s.total == 0
    assert s.average is None
    assert s.minimum is None
    assert s.maximum is None
    # Sum khong ap dung khi khong co so
    assert s.value(st.ITEM_SUM) is None


def test_bool_counted_but_not_numeric():
    # TRUE/FALSE: tinh vao Count nhung KHONG vao Sum/Numerical (giong Excel)
    s = compute_stats([True, False, 10])
    assert s.count == 3
    assert s.numerical_count == 1
    assert s.total == 10
    assert s.average == 10


def test_negative_and_float():
    s = compute_stats([-5, 2.5, 2.5])
    assert s.numerical_count == 3
    assert s.total == 0.0
    assert s.minimum == -5
    assert s.maximum == 2.5
    assert s.average == 0.0


def test_all_empty():
    s = compute_stats(["", None, ""])
    assert s.count == 0
    assert s.numerical_count == 0
    assert s.average is None
    assert s.value(st.ITEM_MIN) is None


def test_value_accessor_maps_items():
    s = compute_stats([2, 4, 6])
    assert s.value(st.ITEM_AVERAGE) == 4
    assert s.value(st.ITEM_COUNT) == 3
    assert s.value(st.ITEM_NUMERICAL_COUNT) == 3
    assert s.value(st.ITEM_MIN) == 2
    assert s.value(st.ITEM_MAX) == 6
    assert s.value(st.ITEM_SUM) == 12


def test_format_no_scientific_notation():
    # Loi cu: :g doi sum lon thanh 1.23457e+06 -> phai hien so day du
    assert st.format_stat_value(1234567) == "1234567"
    assert st.format_stat_value(1234567.0) == "1234567"
    assert st.format_stat_value(15) == "15"
    assert st.format_stat_value(3.0) == "3"


def test_format_floats_trim_zeros():
    assert st.format_stat_value(1.5) == "1.5"
    assert st.format_stat_value(2.50) == "2.5"
    # trung binh 1,2,2 = 1.6666... giu nhieu chu so, khong sci-notation
    out = st.format_stat_value((1 + 2 + 2) / 3)
    assert out.startswith("1.6666")
    assert "e" not in out.lower()


def test_format_negative():
    assert st.format_stat_value(-5) == "-5"
    assert st.format_stat_value(-2.5) == "-2.5"


def test_defaults_match_excel():
    # Avg/Count/Sum bat san; Numerical/Min/Max tat
    assert st.DEFAULT_ENABLED[st.ITEM_AVERAGE] is True
    assert st.DEFAULT_ENABLED[st.ITEM_COUNT] is True
    assert st.DEFAULT_ENABLED[st.ITEM_SUM] is True
    assert st.DEFAULT_ENABLED[st.ITEM_NUMERICAL_COUNT] is False
    assert st.DEFAULT_ENABLED[st.ITEM_MIN] is False
    assert st.DEFAULT_ENABLED[st.ITEM_MAX] is False
    assert len(st.STAT_ITEMS) == 6
