"""Unit test cho engine cong thuc (formula.py).

Chi dung ASCII trong test (console Windows cp1252).
Chay: python -m pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp import formula as f  # noqa: E402


def make_resolver(grid):
    """grid: dict[(row,col)] -> value. Tra ve resolver(row,col)."""
    return lambda row, col: grid.get((row, col), "")


# Luoi mau:
#   A      B       C
# 1 10     apple   1
# 2 20     banana  2
# 3 30     cherry  3
# 4 40     apple   4
GRID = {
    (0, 0): 10, (0, 1): "apple", (0, 2): 1,
    (1, 0): 20, (1, 1): "banana", (1, 2): 2,
    (2, 0): 30, (2, 1): "cherry", (2, 2): 3,
    (3, 0): 40, (3, 1): "apple", (3, 2): 4,
}
R = make_resolver(GRID)


def ev(expr):
    return f.evaluate(expr, R)


# ---------------------------------------------------------------- gop (cu)


def test_aggregates_still_work():
    assert ev("=SUM(A1:A4)") == 100
    assert ev("=AVERAGE(A1:A4)") == 25
    assert ev("=MIN(A1:A4)") == 10
    assert ev("=MAX(A1:A4)") == 40
    assert ev("=COUNT(A1:A4)") == 4
    assert ev("=SUM(A1:A2, A3, 100)") == 160


def test_aggregate_multi_column_range():
    assert ev("=SUM(A1:C2)") == 10 + 1 + 20 + 2  # text bi bo qua


# ---------------------------------------------------------------- logic


def test_logic():
    assert ev("=AND(A1>5, A2>5)") is True
    assert ev("=AND(A1>5, A2>50)") is False
    assert ev("=OR(A1>50, A2>5)") is True
    assert ev("=NOT(A1>50)") is True
    assert ev("=TRUE()") is True
    assert ev("=FALSE()") is False


def test_if_lazy_branches():
    assert ev('=IF(A1>5,"big","small")') == "big"
    assert ev('=IF(A1>50,"big","small")') == "small"
    # nhanh sai co loi chia 0 nhung khong duoc tinh -> khong loi
    assert ev("=IF(A1>5, 99, 1/0)") == 99


def test_iferror():
    assert ev("=IFERROR(1/0, -1)") == -1
    assert ev("=IFERROR(A1/A2, -1)") == 0.5
    assert ev('=IFERROR(VLOOKUP(999,A1:B4,2,FALSE()),"NA")') == "NA"


def test_ifs():
    assert ev('=IFS(A1>100,"a", A1>5,"b", TRUE(),"c")') == "b"
    with pytest.raises(f.FormulaError):
        ev('=IFS(A1>100,"a", A1>100,"b")')


# ---------------------------------------------------------------- dieu kien


def test_countif_sumif():
    assert ev('=COUNTIF(A1:A4,">15")') == 3
    assert ev('=COUNTIF(B1:B4,"apple")') == 2
    assert ev('=COUNTIF(B1:B4,"a*")') == 2  # wildcard
    assert ev('=SUMIF(A1:A4,">=20")') == 90
    assert ev('=SUMIF(B1:B4,"apple",A1:A4)') == 50  # 10 + 40


def test_countifs_sumifs():
    assert ev('=COUNTIFS(B1:B4,"apple",A1:A4,">15")') == 1
    assert ev('=SUMIFS(A1:A4,B1:B4,"apple")') == 50
    assert ev('=AVERAGEIF(A1:A4,">15")') == 30


def test_counta_countblank():
    grid = {(0, 0): "x", (1, 0): "", (2, 0): 5}
    r = make_resolver(grid)
    assert f.evaluate("=COUNTA(A1:A3)", r) == 2
    assert f.evaluate("=COUNTBLANK(A1:A3)", r) == 1


# ---------------------------------------------------------------- tra cuu


def test_vlookup():
    assert ev("=VLOOKUP(30,A1:B4,2,FALSE())") == "cherry"
    assert ev("=VLOOKUP(20,A1:C4,3,FALSE())") == 2
    assert ev("=VLOOKUP(25,A1:B4,2,TRUE())") == "banana"  # xap xi: <= 25 -> 20


def test_hlookup():
    grid = {(0, 0): "id", (0, 1): "name", (0, 2): "age",
            (1, 0): 1, (1, 1): "Tom", (1, 2): 30}
    r = make_resolver(grid)
    assert f.evaluate('=HLOOKUP("name",A1:C2,2,FALSE())', r) == "Tom"


def test_index_match():
    assert ev("=INDEX(A1:A4,3)") == 30
    assert ev("=INDEX(A1:C1,1,2)") == "apple"
    assert ev("=MATCH(30,A1:A4,0)") == 3
    assert ev('=MATCH("cherry",B1:B4,0)') == 3
    assert ev("=INDEX(B1:B4, MATCH(40,A1:A4,0))") == "apple"


def test_lookup():
    assert ev("=LOOKUP(25,A1:A4,B1:B4)") == "banana"


# ---------------------------------------------------------------- chuoi


def test_string_funcs():
    assert ev('=LEFT("hello",3)') == "hel"
    assert ev('=RIGHT("hello",2)') == "lo"
    assert ev('=MID("hello",2,3)') == "ell"
    assert ev('=LEN("hello")') == 5
    assert ev('=TRIM("  a  b  ")') == "a b"
    assert ev('=UPPER("abc")') == "ABC"
    assert ev('=LOWER("ABC")') == "abc"
    assert ev('=PROPER("hello world")') == "Hello World"
    assert ev('=REPT("ab",3)') == "ababab"
    assert ev('=REPLACE("abcdef",2,3,"XY")') == "aXYef"
    assert ev('=SUBSTITUTE("a-b-c","-","+")') == "a+b+c"
    assert ev('=SUBSTITUTE("a-b-c","-","+",2)') == "a-b+c"
    assert ev('=FIND("b","abc")') == 2
    assert ev('=SEARCH("B","abc")') == 2
    assert ev('=VALUE("42")') == 42
    assert ev('=CONCAT("a",1,"b")') == "a1b"


def test_text_format():
    assert ev('=TEXT(0.5,"0%")') == "50%"
    assert ev('=TEXT(1234.5,"#,##0.00")') == "1,234.50"


# ---------------------------------------------------------------- toan


def test_math_funcs():
    assert ev("=CEILING(4.2)") == 5
    assert ev("=CEILING(4.1,0.5)") == 4.5
    assert ev("=FLOOR(4.8)") == 4
    assert ev("=TRUNC(4.78,1)") == 4.7
    assert ev("=SIGN(-3)") == -1
    assert ev("=PRODUCT(A1:A2)") == 200
    assert ev("=SUMPRODUCT(A1:A2,C1:C2)") == 10 * 1 + 20 * 2
    assert ev("=ROUNDUP(4.12,1)") == 4.2
    assert ev("=ROUNDDOWN(4.18,1)") == 4.1
    assert round(ev("=PI()"), 4) == 3.1416
    assert ev("=LOG(100)") == 2
    assert ev("=LOG(8,2)") == 3


# ---------------------------------------------------------------- ngay/gio


def test_date_funcs():
    serial = ev("=DATE(2020,1,15)")
    assert ev(f"=YEAR({serial})") == 2020
    assert ev(f"=MONTH({serial})") == 1
    assert ev(f"=DAY({serial})") == 15
    # 2020-01-15 la thu Tu -> WEEKDAY mac dinh (CN=1): thu Tu = 4
    assert ev(f"=WEEKDAY({serial})") == 4
    assert ev("=DATEDIF(DATE(2020,1,1),DATE(2020,1,31),\"D\")") == 30
    assert ev("=DATEDIF(DATE(2020,1,1),DATE(2022,1,1),\"Y\")") == 2


def test_today_now():
    # chi kiem tra kieu so, khong kiem tra gia tri tuyet doi
    assert isinstance(ev("=TODAY()"), float)
    assert ev("=NOW()") >= ev("=TODAY()")


# ---------------------------------------------------------------- thong ke


def test_stats_funcs():
    assert ev("=MEDIAN(A1:A4)") == 25
    assert ev("=LARGE(A1:A4,1)") == 40
    assert ev("=LARGE(A1:A4,2)") == 30
    assert ev("=SMALL(A1:A4,1)") == 10
    assert ev("=RANK(30,A1:A4)") == 2       # giam dan: 40,30 -> 30 hang 2
    assert ev("=RANK(30,A1:A4,1)") == 3     # tang dan: 10,20,30 -> hang 3
    assert round(ev("=STDEV(A1:A4)"), 4) == round(__import__("statistics").stdev([10, 20, 30, 40]), 4)


# ---------------------------------------------------------------- loi


def test_errors():
    with pytest.raises(f.FormulaError):
        ev("=KHONGCOHAM(1)")
    with pytest.raises(f.FormulaError):
        ev("=1/0")
    with pytest.raises(f.FormulaError):
        ev("=VLOOKUP(999,A1:B4,2,FALSE())")


# ---------------------------------------------------------------- nguoc tuong thich


def test_offset_formula_with_range():
    assert f.offset_formula("=SUM(A1:A3)", 1, 0) == "=SUM(A2:A4)"
    assert f.offset_formula("=VLOOKUP(A1,$B$1:$C$5,2)", 2, 0) == "=VLOOKUP(A3,$B$1:$C$5,2)"
