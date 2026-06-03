"""Unit test cho Name Box "Go To" parser (formula.parse_grid_reference).

Chi dung ASCII (console Windows cp1252). Chay: python -m pytest tests/
Doi chieu hanh vi voi Excel that (Go To / F5).

Grid mau dung trong test: 50 hang x 26 cot (A1:Z50) tru khi ghi ro khac.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from excelapp import formula as f  # noqa: E402

ROWS, COLS = 50, 26  # A1:Z50


def gr(text, rows=ROWS, cols=COLS):
    return f.parse_grid_reference(text, rows, cols)


# ---------------------------------------------------------------- o don
def test_single_cell():
    assert gr("A1") == (0, 0, 0, 0)
    assert gr("B3") == (2, 1, 2, 1)
    assert gr("Z50") == (49, 25, 49, 25)


def test_single_case_insensitive():
    assert gr("b3") == (2, 1, 2, 1)
    assert gr("z50") == (49, 25, 49, 25)


def test_single_with_dollar():
    assert gr("$A$1") == (0, 0, 0, 0)
    assert gr("$B3") == (2, 1, 2, 1)
    assert gr("A$1") == (0, 0, 0, 0)


def test_single_trims_whitespace():
    assert gr("  C5  ") == (4, 2, 4, 2)
    assert gr("\tA1\n") == (0, 0, 0, 0)


# ---------------------------------------------------------------- vung o
def test_cell_range():
    assert gr("A1:C5") == (0, 0, 4, 2)
    assert gr("B2:D4") == (1, 1, 3, 3)


def test_cell_range_reversed_normalized():
    # Excel chuan hoa C5:A1 -> A1:C5
    assert gr("C5:A1") == (0, 0, 4, 2)
    assert gr("D4:B2") == (1, 1, 3, 3)


def test_cell_range_with_dollar():
    assert gr("$A$1:$C$5") == (0, 0, 4, 2)


# ---------------------------------------------------------------- ca cot
def test_whole_column():
    assert gr("A:A") == (0, 0, ROWS - 1, 0)
    assert gr("C:C") == (0, 2, ROWS - 1, 2)


def test_column_range():
    assert gr("A:C") == (0, 0, ROWS - 1, 2)
    assert gr("C:A") == (0, 0, ROWS - 1, 2)  # reversed


# ---------------------------------------------------------------- ca hang
def test_whole_row():
    assert gr("1:1") == (0, 0, 0, COLS - 1)
    assert gr("5:5") == (4, 0, 4, COLS - 1)


def test_row_range():
    assert gr("2:5") == (1, 0, 4, COLS - 1)
    assert gr("5:2") == (1, 0, 4, COLS - 1)  # reversed


# ---------------------------------------------------------------- kep trong luoi
def test_range_clamped_to_grid():
    # Z50 la goc duoi-phai; AB100 vuot ca 2 chieu -> kep ve goc luoi
    assert gr("A1:AB100") == (0, 0, ROWS - 1, COLS - 1)


def test_range_partial_clamp_rows():
    assert gr("A1:A100") == (0, 0, ROWS - 1, 0)


def test_range_partial_clamp_cols():
    assert gr("A1:AZ1") == (0, 0, 0, COLS - 1)


# ---------------------------------------------------------------- ngoai luoi -> None
def test_single_out_of_grid_rows():
    assert gr("A51") is None  # hang 51 > 50


def test_single_out_of_grid_cols():
    assert gr("AA1") is None  # cot 27 > 26


def test_range_top_left_out_of_grid():
    # goc tren-trai da vuot luoi -> vo nghia
    assert gr("AA1:AB5") is None
    assert gr("A60:C70") is None


# ---------------------------------------------------------------- cu phap sai -> None
def test_invalid_syntax():
    for bad in ("", "   ", "ABC", "1A", "A1:", ":B2", "A1 B2",
                "A-1", "A1:B2:C3", "!@#", "Sheet1!A1", "A1,B2"):
        assert gr(bad) is None, f"expected None for {bad!r}"


def test_empty_grid():
    assert f.parse_grid_reference("A1", 0, 0) is None
    assert f.parse_grid_reference("A1", 0, 26) is None
    assert f.parse_grid_reference("A1", 50, 0) is None


# ---------------------------------------------------------------- bound chinh xac
def test_exact_boundary_in_and_out():
    # luoi 50x26: Z50 in, Z51 out, AA50 out
    assert gr("Z50") == (49, 25, 49, 25)
    assert gr("Z51") is None
    assert gr("AA50") is None


# ---------------------------------------------------------------- edge cases (review)
def test_dollar_on_col_row_ranges():
    assert gr("$A:$C") == (0, 0, ROWS - 1, 2)
    assert gr("$1:$5") == (0, 0, 4, COLS - 1)
    assert gr("$A$1:$C$5") == (0, 0, 4, 2)


def test_zero_and_leading_zero_rows():
    assert gr("A0") is None       # hang 0 khong ton tai
    assert gr("A00") is None      # 00 -> hang 0 -> None
    assert gr("A01") == (0, 0, 0, 0)  # 01 -> hang 1 (Excel chap nhan)


def test_mixed_col_row_ranges_invalid():
    # Tron cot va hang trong cung mot range -> vo nghia
    for bad in ("A1:1", "1:A1", "A:A1", "1:A", "A1:A", "1:A:5"):
        assert gr(bad) is None, f"expected None for {bad!r}"


def test_huge_row_number_no_overflow():
    # So hang khong lo trong range: khong tran int, kep ve luoi
    assert gr("A1:A99999999999") == (0, 0, ROWS - 1, 0)
    # Single cell khong lo -> ngoai luoi -> None (khong crash)
    assert gr("A99999999999") is None


def test_space_separators_invalid():
    # Space = intersection trong Excel (chua ho tro) -> None, khong crash
    for bad in ("A1 C5", "2:4 B:F", "A1 :C5"):
        assert gr(bad) is None, f"expected None for {bad!r}"
