"""Unit test cho cac ham cong thuc moi them o v0.11.3 (formula.py).

Chi dung ASCII (console Windows cp1252). Chay: python -m pytest tests/
Moi gia tri ky vong doi chieu voi Excel that.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp import formula as f  # noqa: E402


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
R = lambda row, col: GRID.get((row, col), "")  # noqa: E731


def ev(expr):
    return f.evaluate(expr, R)


def approx(a, b, tol=1e-9):
    return abs(a - b) < tol


# ---------------------------------------------------------------- Information


def test_isnumber_istext_isblank():
    assert ev("=ISNUMBER(A1)") is True
    assert ev('=ISNUMBER("5")') is False        # text khong phai so
    assert ev("=ISNUMBER(TRUE())") is False     # bool khong phai so
    assert ev("=ISTEXT(B1)") is True
    assert ev("=ISTEXT(A1)") is False
    assert ev("=ISNONTEXT(A1)") is True
    assert ev("=ISBLANK(Z9)") is True
    assert ev("=ISBLANK(A1)") is False
    assert ev("=ISLOGICAL(TRUE())") is True
    assert ev("=ISLOGICAL(A1)") is False


def test_iseven_isodd():
    assert ev("=ISEVEN(4)") is True
    assert ev("=ISEVEN(3)") is False
    assert ev("=ISEVEN(3.9)") is False          # truncate -> 3
    assert ev("=ISEVEN(-2)") is True
    assert ev("=ISODD(-3)") is True
    assert ev("=ISODD(2)") is False


def test_na_raises():
    with pytest.raises(f.FormulaError) as e:
        ev("=NA()")
    assert e.value.etype == "#N/A"


# ---------------------------------------------------------------- Logical


def test_xor():
    assert ev("=XOR(TRUE(),FALSE())") is True
    assert ev("=XOR(TRUE(),TRUE())") is False
    assert ev("=XOR(TRUE(),TRUE(),TRUE())") is True
    assert ev("=XOR(1,0,0)") is True


def test_switch():
    assert ev('=SWITCH(2,1,"a",2,"b",3,"c")') == "b"
    assert ev('=SWITCH(9,1,"a",2,"b","default")') == "default"
    with pytest.raises(f.FormulaError):
        ev('=SWITCH(9,1,"a",2,"b")')            # khong khop, khong default


def test_ifna():
    assert ev('=IFNA(NA(),"fallback")') == "fallback"
    assert ev('=IFNA(42,"fallback")') == 42
    # loi khac #N/A thi KHONG bi nuot
    with pytest.raises(f.FormulaError) as e:
        ev('=IFNA(1/0,"fallback")')
    assert e.value.etype == "#DIV/0!"


def test_iserror_iserr_isna():
    assert ev("=ISERROR(1/0)") is True
    assert ev("=ISERROR(A1)") is False
    assert ev("=ISNA(NA())") is True
    assert ev("=ISNA(1/0)") is False            # div0 khong phai #N/A
    assert ev("=ISERR(1/0)") is True            # div0 la loi (khac #N/A)
    assert ev("=ISERR(NA())") is False          # #N/A khong tinh la ISERR


# ---------------------------------------------------------------- Text


def test_textjoin():
    assert ev('=TEXTJOIN("-",TRUE(),A1:A4)') == "10-20-30-40"
    assert ev('=TEXTJOIN(",",TRUE(),"a","","b")') == "a,b"      # bo rong
    assert ev('=TEXTJOIN(",",FALSE(),"a","","b")') == "a,,b"    # giu rong


def test_exact_char_code_clean_t():
    assert ev('=EXACT("abc","abc")') is True
    assert ev('=EXACT("abc","ABC")') is False
    assert ev("=CHAR(65)") == "A"
    assert ev('=CODE("A")') == 65.0
    assert ev('=CLEAN("a\tb")') == "ab"
    assert ev('=T("hello")') == "hello"
    assert ev("=T(A1)") == ""                    # so -> ""


def test_fixed():
    assert ev("=FIXED(1234.567,2)") == "1,234.57"
    assert ev("=FIXED(1234.567,2,TRUE())") == "1234.57"
    assert ev("=FIXED(1234.567,0)") == "1,235"


# ---------------------------------------------------------------- Lookup


def test_choose():
    assert ev('=CHOOSE(1,"x","y","z")') == "x"
    assert ev('=CHOOSE(3,"x","y","z")') == "z"
    with pytest.raises(f.FormulaError):
        ev('=CHOOSE(5,"x","y")')


def test_xlookup_exact():
    assert ev('=XLOOKUP("banana",B1:B4,A1:A4)') == 20
    assert ev('=XLOOKUP("apple",B1:B4,A1:A4)') == 10     # first match
    assert ev('=XLOOKUP("zzz",B1:B4,A1:A4,"none")') == "none"
    with pytest.raises(f.FormulaError) as e:
        ev('=XLOOKUP("zzz",B1:B4,A1:A4)')
    assert e.value.etype == "#N/A"


def test_xlookup_reverse_and_approx():
    # search_mode -1: tim tu duoi len -> apple cuoi (hang 4) tra 40
    assert ev('=XLOOKUP("apple",B1:B4,A1:A4,"none",0,-1)') == 40
    # match_mode -1 (exact-or-next-smaller) tren so
    assert ev('=XLOOKUP(25,A1:A4,C1:C4,"none",-1)') == 2   # 20 -> hang 2 -> C=2
    # match_mode 1 (exact-or-next-larger)
    assert ev('=XLOOKUP(25,A1:A4,C1:C4,"none",1)') == 3    # 30 -> hang 3 -> C=3


# ---------------------------------------------------------------- Math


def test_trig():
    assert approx(ev("=SIN(0)"), 0.0)
    assert approx(ev("=COS(0)"), 1.0)
    assert approx(ev("=DEGREES(PI())"), 180.0)
    assert approx(ev("=RADIANS(180)"), math.pi)
    assert approx(ev("=ATAN2(1,1)"), math.pi / 4)   # Excel ATAN2(x,y)
    assert approx(ev("=LOG10(1000)"), 3.0)


def test_trig_domain_error():
    with pytest.raises(f.FormulaError) as e:
        ev("=ASIN(2)")
    assert e.value.etype == "#NUM!"


def test_gcd_lcm_fact_combin_permut():
    assert ev("=GCD(12,18)") == 6.0
    assert ev("=GCD(12,18,24)") == 6.0
    assert ev("=LCM(4,6)") == 12.0
    assert ev("=LCM(4,6,10)") == 60.0
    assert ev("=FACT(5)") == 120.0
    assert ev("=COMBIN(5,2)") == 10.0
    assert ev("=PERMUT(5,2)") == 20.0


def test_mround_even_odd_quotient_sumsq():
    assert ev("=MROUND(10,3)") == 9.0
    assert ev("=MROUND(2.5,1)") == 3.0          # half away from zero
    assert ev("=MROUND(-2.5,-1)") == -3.0
    assert ev("=EVEN(3)") == 4.0
    assert ev("=EVEN(2)") == 2.0
    assert ev("=ODD(2)") == 3.0
    assert ev("=ODD(1)") == 1.0
    assert ev("=QUOTIENT(7,2)") == 3.0
    assert ev("=QUOTIENT(-7,2)") == -3.0        # truncate toward zero
    assert ev("=SUMSQ(3,4)") == 25.0
    with pytest.raises(f.FormulaError) as e:
        ev("=QUOTIENT(1,0)")
    assert e.value.etype == "#DIV/0!"
    with pytest.raises(f.FormulaError) as e2:
        ev("=MROUND(5,-1)")                      # khac dau
    assert e2.value.etype == "#NUM!"


# ---------------------------------------------------------------- Stats


def test_conditional_stats():
    assert ev('=AVERAGEIFS(A1:A4,B1:B4,"apple")') == 25.0   # (10+40)/2
    assert ev('=MAXIFS(A1:A4,B1:B4,"apple")') == 40.0
    assert ev('=MINIFS(A1:A4,B1:B4,"apple")') == 10.0
    assert ev('=MAXIFS(A1:A4,B1:B4,"nope")') == 0.0          # khong khop -> 0
    with pytest.raises(f.FormulaError) as e:
        ev('=AVERAGEIFS(A1:A4,B1:B4,"nope")')
    assert e.value.etype == "#DIV/0!"


def test_stdevp_varp_geomean_harmean():
    assert approx(ev("=VARP(A1:A4)"), 125.0)    # pop variance cua 10,20,30,40
    assert approx(ev("=STDEVP(A1:A4)"), math.sqrt(125.0))
    assert approx(ev("=GEOMEAN(1,4,16)"), 4.0)
    assert approx(ev("=HARMEAN(1,2,4)"), 12.0 / 7.0)


def test_averagea():
    # AVERAGEA: text -> 0. A1:A4=10,20,30,40 + 1 text "x" => (100+0)/5 = 20
    g2 = dict(GRID)
    g2[(4, 0)] = "x"
    r2 = lambda row, col: g2.get((row, col), "")  # noqa: E731
    assert f.evaluate("=AVERAGEA(A1:A5)", r2) == 20.0


# ---------------------------------------------------------------- Date/Time


def test_edate_eomonth():
    # DATE(2024,1,31) + 1 thang -> 2024-02-29 (kep cuoi thang, nam nhuan)
    assert ev("=DAY(EDATE(DATE(2024,1,31),1))") == 29.0
    assert ev("=MONTH(EDATE(DATE(2024,1,31),1))") == 2.0
    assert ev("=DAY(EOMONTH(DATE(2024,2,15),0))") == 29.0   # leap Feb
    assert ev("=DAY(EOMONTH(DATE(2023,2,15),0))") == 28.0
    assert ev("=MONTH(EOMONTH(DATE(2024,1,15),2))") == 3.0


def test_time_second_days():
    assert approx(ev("=TIME(6,0,0)"), 0.25)     # 6h = 1/4 ngay
    assert approx(ev("=TIME(12,0,0)"), 0.5)
    assert ev("=DAYS(DATE(2024,1,10),DATE(2024,1,1))") == 9.0


def test_datevalue():
    assert ev('=DATEVALUE("2024-01-01")') == ev("=DATE(2024,1,1)")
    assert ev('=YEAR(DATEVALUE("2024-03-15"))') == 2024.0
    with pytest.raises(f.FormulaError):
        ev('=DATEVALUE("khong-phai-ngay")')


def test_weeknum_isoweeknum():
    # 2024-01-01 la thu Hai
    assert ev("=WEEKNUM(DATE(2024,1,1),1)") == 1.0    # he CN
    assert ev("=WEEKNUM(DATE(2024,1,7),1)") == 2.0    # CN dau tuan 2
    assert ev("=WEEKNUM(DATE(2024,1,1),2)") == 1.0    # he T2
    assert ev("=ISOWEEKNUM(DATE(2024,1,1))") == 1.0


# ---------------------------------------------------------------- Error taxonomy


def test_error_etypes():
    cases = {
        "=1/0": "#DIV/0!",
        "=MOD(5,0)": "#DIV/0!",
        "=SQRT(-1)": "#NUM!",
        "=NOTAREALFUNC(1)": "#NAME?",
        '=VLOOKUP("zzz",A1:B4,2,FALSE())': "#N/A",
    }
    for expr, etype in cases.items():
        with pytest.raises(f.FormulaError) as e:
            ev(expr)
        assert e.value.etype == etype, (expr, e.value.etype, etype)


def test_old_functions_still_work():
    # khong pha vo gi cu
    assert ev("=SUM(A1:A4)") == 100
    assert ev('=IF(A1>5,"big","small")') == "big"
    assert ev("=VLOOKUP(20,A1:C4,3,FALSE())") == 2
    assert ev('=CONCAT("a","b")') == "ab"


# ------------------------------------------------ review fixes: crash guards


def _etype(expr):
    with pytest.raises(f.FormulaError) as e:
        ev(expr)
    return e.value.etype


def test_ifs_mismatched_ranges_no_crash():
    # Vung tieu chi ngan hon vung gia tri -> #VALUE!, KHONG crash IndexError
    assert _etype('=COUNTIFS(A1:A4,">0",B1:B2,"apple")') == "#VALUE!"
    assert _etype('=SUMIFS(A1:A4,B1:B2,"apple")') == "#VALUE!"
    assert _etype('=AVERAGEIFS(A1:A4,B1:B2,"apple")') == "#VALUE!"
    assert _etype('=MAXIFS(A1:A4,B1:B2,"apple")') == "#VALUE!"
    assert _etype('=MINIFS(A1:A4,B1:B2,"apple")') == "#VALUE!"


def test_inf_nan_no_crash():
    # _to_number tu choi inf/nan -> khong loi int()/trunc()
    assert _etype('=VALUE("inf")') in ("#VALUE!", "#NUM!")
    assert _etype('=VALUE("nan")') in ("#VALUE!", "#NUM!")
    assert _etype('=ISEVEN(VALUE("nan"))') in ("#VALUE!", "#NUM!")
    assert _etype('=CHAR(VALUE("inf"))') in ("#VALUE!", "#NUM!")


def test_overflow_guards():
    assert ev("=FACT(170)") > 0          # 170! van tinh duoc
    assert _etype("=FACT(171)") == "#NUM!"
    assert _etype("=POWER(10,1000)") == "#NUM!"
    assert _etype("=UNICHAR(1114112)") == "#VALUE!"
    assert ev("=UNICHAR(65)") == "A"
    assert _etype("=COMBIN(2000,1000)") == "#NUM!"    # ket qua qua lon
    # SUMSQ tran -> inf -> #NUM! (engine chua ho tro 1E300, dung o gia tri lon)
    big = lambda row, col: 1e200  # noqa: E731
    with pytest.raises(f.FormulaError) as e:
        f.evaluate("=SUMSQ(A1,A1)", big)
    assert e.value.etype == "#NUM!"


def test_date_range_guard():
    assert _etype("=EOMONTH(0,-100000)") == "#NUM!"


def test_gcd_lcm_negative_num_error():
    assert _etype("=GCD(-4,8)") == "#NUM!"
    assert _etype("=LCM(-4,6)") == "#NUM!"


def test_choose_range_not_garbage():
    # CHOOSE tra ve vung nhieu o, lam ket qua cuoi -> #VALUE!, khong in repr
    assert _etype("=CHOOSE(1,A1:A4)") == "#VALUE!"
    # nhung dung trong ham gop thi van ok
    assert ev("=SUM(CHOOSE(1,A1:A4))") == 100


def test_textjoin_range_delimiter():
    assert _etype("=TEXTJOIN(A1:A2,TRUE(),1,2)") == "#VALUE!"


def test_is_functions_multicell_range():
    # IS* tren vung nhieu o -> #VALUE! thay vi False am tham
    assert _etype("=ISNUMBER(A1:A2)") == "#VALUE!"
    # vung 1 o van hoat dong
    assert ev("=ISNUMBER(A1:A1)") is True


def test_wildcard_brackets_literal():
    # fnmatch coi [..] la char-class; Excel coi la literal. Kiem tra COUNTIF.
    g2 = {(0, 0): "a[1]", (1, 0): "a[2]", (2, 0): "ax"}
    r2 = lambda row, col: g2.get((row, col), "")  # noqa: E731
    # "a[1]" chi khop chinh no, khong khop "ax"
    assert f.evaluate('=COUNTIF(A1:A3,"a[1]")', r2) == 1
    # wildcard * van hoat dong
    assert f.evaluate('=COUNTIF(A1:A3,"a*")', r2) == 3


def test_criteria_still_correct_after_compile_refactor():
    assert ev('=COUNTIF(A1:A4,">15")') == 3
    assert ev('=SUMIF(A1:A4,">=20")') == 90
    assert ev('=COUNTIF(B1:B4,"apple")') == 2
    assert ev('=COUNTIF(B1:B4,"<>apple")') == 2
    assert ev('=SUMIFS(A1:A4,B1:B4,"apple",A1:A4,">10")') == 40
