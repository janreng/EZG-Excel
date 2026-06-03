"""Unit test cho autosum (Alt+=) — do dai so lien ke. ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from excelapp.autosum import autosum_range, autosum_formula, range_to_ref  # noqa: E402


def make_grid(cells: dict):
    """cells: {(r,c): value}. Tra ve get_value(r,c)."""
    return lambda r, c: cells.get((r, c), "")


# ---------------------------------------------------------------- phia tren
def test_sum_column_above():
    g = make_grid({(0, 0): 10, (1, 0): 20, (2, 0): 30})
    # o A4 (row=3) -> SUM(A1:A3)
    assert autosum_range(g, 3, 0) == (0, 0, 2, 0)
    assert autosum_formula(g, 3, 0) == "=SUM(A1:A3)"


def test_sum_above_stops_at_text():
    g = make_grid({(0, 0): "Header", (1, 0): 5, (2, 0): 7})
    # o A4 (row=3): so lien tuc tu A2..A3, dung o A1 (text)
    assert autosum_range(g, 3, 0) == (1, 0, 2, 0)
    assert autosum_formula(g, 3, 0) == "=SUM(A2:A3)"


def test_sum_above_stops_at_blank():
    g = make_grid({(0, 0): 1, (2, 0): 5, (3, 0): 6})  # A2 (row1) trong
    # o A5 (row=4): A3..A4 lien tuc, dung o A2 trong
    assert autosum_range(g, 4, 0) == (2, 0, 3, 0)


def test_single_number_above_no_colon():
    g = make_grid({(0, 0): 42})
    assert autosum_formula(g, 1, 0) == "=SUM(A1)"


def test_leading_blank_above_returns_none():
    # O ngay tren active trong -> KHONG nhay qua khoang trong de lay so cao hon
    g = make_grid({(0, 0): 1, (1, 0): 2})  # A1,A2 co so; A3 (row2) trong
    # active A4 (row=3): o tren (A3) trong -> dung luon, dò ben trai (cung khong co)
    assert autosum_range(g, 3, 0) is None


def test_text_above_falls_to_left():
    # O tren la text -> chuyen sang do ben trai
    g = make_grid({(0, 2): "Header", (1, 0): 4, (1, 1): 6})
    # active C2 (row=1,col=2): tren la text (C1) -> trai A2:B2
    assert autosum_formula(g, 1, 2) == "=SUM(A2:B2)"


# ---------------------------------------------------------------- ben trai
def test_sum_row_left_when_nothing_above():
    g = make_grid({(0, 0): 1, (0, 1): 2, (0, 2): 3})
    # o D1 (row=0,col=3) -> khong co tren -> SUM(A1:C1)
    assert autosum_range(g, 0, 3) == (0, 0, 0, 2)
    assert autosum_formula(g, 0, 3) == "=SUM(A1:C1)"


def test_above_takes_priority_over_left():
    g = make_grid({
        (0, 1): 5, (1, 1): 5,   # tren o B3
        (2, 0): 9,              # ben trai o B3
    })
    # o B3 (row=2,col=1): uu tien tren -> SUM(B1:B2)
    assert autosum_formula(g, 2, 1) == "=SUM(B1:B2)"


# ---------------------------------------------------------------- khong co
def test_no_neighbors_returns_none():
    g = make_grid({})
    assert autosum_range(g, 5, 5) is None
    assert autosum_formula(g, 5, 5) is None


def test_text_neighbors_returns_none():
    g = make_grid({(0, 0): "a", (1, 0): "b"})
    assert autosum_range(g, 2, 0) is None


def test_top_left_corner_no_neighbors():
    g = make_grid({(0, 0): 5})
    assert autosum_range(g, 0, 0) is None  # A1 khong co tren/trai


def test_bool_not_summed():
    g = make_grid({(0, 0): True, (1, 0): True})
    assert autosum_range(g, 2, 0) is None  # bool khong tinh la so


# ---------------------------------------------------------------- range_to_ref
def test_range_to_ref():
    assert range_to_ref((0, 0, 2, 0)) == "A1:A3"
    assert range_to_ref((0, 0, 0, 2)) == "A1:C1"
    assert range_to_ref((4, 1, 4, 1)) == "B5"
