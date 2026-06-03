"""Một engine công thức nhỏ kiểu Excel.

Hỗ trợ:
  - Số, chuỗi ("..."), toán tử + - * / ^ và ngoặc ().
  - Tham chiếu ô kiểu A1 và vùng A1:B3 (vùng 2 chiều cho VLOOKUP/INDEX...).
  - ~120 hàm: gộp (SUM, AVERAGE, MIN, MAX, COUNT...), logic (IF, AND, OR,
    NOT, IFERROR, IFS), điều kiện (COUNTIF, SUMIF, COUNTIFS, SUMIFS...),
    tra cứu (VLOOKUP, HLOOKUP, INDEX, MATCH, LOOKUP), chuỗi (LEFT, RIGHT,
    MID, LEN, TRIM, UPPER, LOWER, SUBSTITUTE...), toán (CEILING, FLOOR,
    PRODUCT, SUMPRODUCT, LOG...), ngày/giờ (TODAY, NOW, DATE, YEAR...),
    thống kê (MEDIAN, STDEV, LARGE, SMALL, RANK...).

Công thức là chuỗi bắt đầu bằng dấu '='. Việc lấy giá trị ô do
``resolver(row, col)`` đảm nhiệm (trả về số/chuỗi đã tính xong).
"""

from __future__ import annotations

import calendar
import datetime
import fnmatch
import math
import random
import re
import statistics
from typing import Callable

# ---------------------------------------------------------------- lỗi


class FormulaError(Exception):
    """Lỗi khi phân tích hoặc tính công thức.

    ``etype`` mang mã lỗi kiểu Excel (#DIV/0!, #N/A, #VALUE!, #NUM!, #NAME?,
    #REF!) để hiển thị giống Excel và để các hàm IS* (ISERROR/ISNA/ISERR)
    phân loại đúng. Mặc định #VALUE! (lỗi kiểu/giá trị — phổ biến nhất).
    """

    def __init__(self, message: str = "", etype: str = "#VALUE!"):
        super().__init__(message)
        self.etype = etype


# Mã lỗi chuẩn Excel (dùng cho etype + nhận diện trong hàm IS*).
ERR_DIV0 = "#DIV/0!"
ERR_NA = "#N/A"
ERR_VALUE = "#VALUE!"
ERR_NUM = "#NUM!"
ERR_NAME = "#NAME?"
ERR_REF = "#REF!"


# ---------------------------------------------------------------- tiện ích ô


_CELL_RE = re.compile(r"^\$?([A-Za-z]+)\$?(\d+)$")


def col_letters_to_index(letters: str) -> int:
    """'A' -> 0, 'B' -> 1, 'Z' -> 25, 'AA' -> 26 ..."""
    result = 0
    for ch in letters.upper():
        result = result * 26 + (ord(ch) - ord("A") + 1)
    return result - 1


def col_index_to_letters(index: int) -> str:
    """0 -> 'A', 25 -> 'Z', 26 -> 'AA' ..."""
    result = ""
    index += 1
    while index > 0:
        index, rem = divmod(index - 1, 26)
        result = chr(ord("A") + rem) + result
    return result


def split_sheet_ref(value: str) -> tuple[str, str]:
    """'Sheet1!B3' -> ('Sheet1', 'B3'); \"'Báo cáo'!A1\" -> ('Báo cáo', 'A1').

    Bỏ dấu nháy đơn quanh tên sheet (cho tên có khoảng trắng)."""
    sheet, _, cell = value.partition("!")
    sheet = sheet.strip()
    if len(sheet) >= 2 and sheet[0] == "'" and sheet[-1] == "'":
        sheet = sheet[1:-1]
    return sheet, cell


def parse_cell_ref(ref: str) -> tuple[int, int]:
    """'B3' -> (row=2, col=1). Raise nếu sai cú pháp."""
    m = _CELL_RE.match(ref)
    if not m:
        raise FormulaError(f"Tham chiếu ô không hợp lệ: {ref}")
    col = col_letters_to_index(m.group(1))
    row = int(m.group(2)) - 1
    if row < 0:
        raise FormulaError(f"Tham chiếu ô không hợp lệ: {ref}")
    return row, col


# Regex cho Name Box "Go To" — compile once ở module level (hot path khi user gõ).
# Cho phép '$' tùy ý (Excel chấp nhận $A$1 trong Name Box), không phân biệt hoa thường.
_NB_CELL = r"\$?[A-Za-z]+\$?\d+"
_NB_COL = r"\$?[A-Za-z]+"
_NB_ROW = r"\$?\d+"
_NB_CELL_RANGE_RE = re.compile(rf"^({_NB_CELL}):({_NB_CELL})$")
_NB_COL_RANGE_RE = re.compile(rf"^({_NB_COL}):({_NB_COL})$")
_NB_ROW_RANGE_RE = re.compile(rf"^({_NB_ROW}):({_NB_ROW})$")
_NB_SINGLE_RE = re.compile(rf"^({_NB_CELL})$")
# Tách cột/hàng từ một ô — dùng lại _CELL_RE (cùng pattern $?col$?row).
_NB_CELL_PARTS_RE = _CELL_RE


def _nb_col_index(token: str) -> int:
    """'$AB' / 'ab' -> chỉ số cột 0-based."""
    return col_letters_to_index(token.lstrip("$"))


def _nb_row_index(token: str) -> int:
    """'$10' / '10' -> chỉ số hàng 0-based."""
    return int(token.lstrip("$")) - 1


def parse_grid_reference(
    text: str, n_rows: int, n_cols: int
) -> tuple[int, int, int, int] | None:
    """Phân tích chuỗi Name Box thành vùng chọn ``(top, left, bottom, right)``.

    Hỗ trợ (không phân biệt hoa thường, bỏ khoảng trắng hai đầu, chấp nhận '$'):
      - Ô đơn:        ``A1``  ``$A$1``
      - Vùng ô:       ``A1:C5``  (tự chuẩn hóa nếu đảo ngược ``C5:A1``)
      - Cả cột:       ``A:A``  ``A:C``   -> mọi hàng
      - Cả hàng:      ``1:1``  ``2:5``   -> mọi cột

    Trả về box đã kẹp trong lưới ``n_rows × n_cols``; ``None`` nếu cú pháp sai
    hoặc tham chiếu nằm hoàn toàn ngoài lưới (caller hiện hộp thoại lỗi).

    Hàm thuần (không phụ thuộc Qt) — kiểm thử headless được. Named range &
    multi-range (``A1:B3,D5``) chưa hỗ trợ ở bản này (cần Spec 31 + lớp vẽ
    đa vùng) — sẽ bổ sung ở Phase sau.
    """
    if not text:
        return None
    s = text.strip()
    if not s:
        return None
    last = n_rows - 1
    last_col = n_cols - 1
    if last < 0 or last_col < 0:
        return None

    m = _NB_CELL_RANGE_RE.match(s)
    if m:
        m1 = _NB_CELL_PARTS_RE.match(m.group(1))
        m2 = _NB_CELL_PARTS_RE.match(m.group(2))
        if not m1 or not m2:
            return None
        c1 = col_letters_to_index(m1.group(1))
        r1 = int(m1.group(2)) - 1
        c2 = col_letters_to_index(m2.group(1))
        r2 = int(m2.group(2)) - 1
        return _nb_clamp(min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2), last, last_col)

    m = _NB_COL_RANGE_RE.match(s)
    if m:
        c1 = _nb_col_index(m.group(1))
        c2 = _nb_col_index(m.group(2))
        return _nb_clamp(0, min(c1, c2), last, max(c1, c2), last, last_col)

    m = _NB_ROW_RANGE_RE.match(s)
    if m:
        r1 = _nb_row_index(m.group(1))
        r2 = _nb_row_index(m.group(2))
        return _nb_clamp(min(r1, r2), 0, max(r1, r2), last_col, last, last_col)

    m = _NB_SINGLE_RE.match(s)
    if m:
        mp = _NB_CELL_PARTS_RE.match(m.group(1))
        if not mp:
            return None
        col = col_letters_to_index(mp.group(1))
        row = int(mp.group(2)) - 1
        return _nb_clamp(row, col, row, col, last, last_col)

    return None


def _nb_clamp(
    top: int, left: int, bottom: int, right: int, last_row: int, last_col: int
) -> tuple[int, int, int, int] | None:
    """Kẹp box vào lưới; trả None nếu phần đầu vùng đã vượt ngoài lưới hẳn."""
    # top/left vượt lưới => tham chiếu vô nghĩa (Excel báo lỗi, không cuộn tới đâu).
    if top > last_row or left > last_col or top < 0 or left < 0:
        return None
    bottom = min(bottom, last_row)
    right = min(right, last_col)
    return (top, left, bottom, right)


# ---------------------------------------------------------------- tokenizer

_TOKEN_RE = re.compile(
    r"""
      (?P<NUMBER>\d+\.\d+|\d+|\.\d+)
    | (?P<STRING>"(?:[^"\\]|\\.)*")
    | (?P<SHEETCELL>(?:'[^']*'|[A-Za-z_][A-Za-z0-9_]*)!\$?[A-Za-z]+\$?\d+(?![A-Za-z0-9_])(?!\s*\())
    | (?P<CELL>\$?[A-Za-z]+\$?\d+(?![A-Za-z0-9_])(?!\s*\())
    | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<OP>>=|<=|<>|[+\-*/^(),:<>=])
    | (?P<WS>\s+)
    """,
    re.VERBOSE,
)


class _Token:
    __slots__ = ("kind", "value")

    def __init__(self, kind: str, value: str):
        self.kind = kind
        self.value = value

    def __repr__(self):  # pragma: no cover - debug
        return f"Token({self.kind!r}, {self.value!r})"


def _tokenize(text: str) -> list[_Token]:
    tokens: list[_Token] = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise FormulaError(f"Ký tự không hợp lệ tại: {text[pos:]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "WS":
            continue
        tokens.append(_Token(kind, m.group()))
    return tokens


# ---------------------------------------------------------------- vùng 2 chiều


class _Range:
    """Vùng 2 chiều các giá trị ô (ma trận row×col).

    Hàm gộp (SUM…) coi như list phẳng qua ``_flatten``; còn các hàm cần cấu
    trúc 2 chiều (VLOOKUP/HLOOKUP/INDEX/MATCH) dùng trực tiếp ``rows``.
    """

    __slots__ = ("rows",)

    def __init__(self, rows: list[list]):
        self.rows = rows

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    def flat(self) -> list:
        return [v for row in self.rows for v in row]

    def column(self, idx: int) -> list:
        return [row[idx] for row in self.rows]

    def row(self, idx: int) -> list:
        return list(self.rows[idx])


def _flatten(args) -> list:
    """Trải mọi _Range trong args thành các giá trị đơn."""
    out: list = []
    for a in args:
        if isinstance(a, _Range):
            out.extend(a.flat())
        else:
            out.append(a)
    return out


# ---------------------------------------------------------------- hàm dựng sẵn


def _to_number(value) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        try:
            n = float(value)
        except OverflowError:
            raise FormulaError("Số quá lớn", ERR_NUM)
        if not math.isfinite(n):
            raise FormulaError(f"Số không hữu hạn: {value!r}", ERR_NUM)
        return n
    if value is None or value == "":
        return 0.0
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise FormulaError(f"Không phải số: {value!r}")
    # Excel coi "inf"/"nan" là #VALUE!, không phải số hợp lệ.
    if not math.isfinite(n):
        raise FormulaError(f"Không phải số: {value!r}")
    return n


def _to_int(value) -> int:
    """Đổi sang int an toàn (chặn inf/NaN trước khi int() ném lỗi)."""
    return int(_to_number(value))


def _text(value) -> str:
    """Đổi giá trị thành chuỗi để hiển thị/nối (số nguyên không có '.0')."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _to_bool(value) -> bool:
    """Diễn giải giá trị thành luận lý kiểu Excel."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        s = value.strip().upper()
        if s == "TRUE":
            return True
        if s in ("FALSE", ""):
            return False
        try:
            return float(value) != 0
        except ValueError:
            return True
    return _to_number(value) != 0


def _cmp(a, b) -> int:
    """So sánh: ưu tiên số, nếu không thì so chuỗi (không phân biệt hoa/thường)."""
    try:
        na, nb = _to_number(a), _to_number(b)
        return (na > nb) - (na < nb)
    except FormulaError:
        sa, sb = _text(a).lower(), _text(b).lower()
        return (sa > sb) - (sa < sb)


def _loose_equal(a, b) -> bool:
    try:
        return _to_number(a) == _to_number(b)
    except FormulaError:
        return _text(a).lower() == _text(b).lower()


def _wildcard_to_regex(pat: str):
    """Chuyển wildcard kiểu Excel (* ? và ~ để escape) sang regex đã biên dịch.

    Khác fnmatch: KHÔNG diễn giải '[...]' thành character-class (Excel không có),
    và hỗ trợ ~* ~? ~~ thành ký tự literal. So khớp không phân biệt hoa/thường.
    """
    out = []
    i = 0
    n = len(pat)
    while i < n:
        ch = pat[i]
        if ch == "~" and i + 1 < n and pat[i + 1] in "*?~":
            out.append(re.escape(pat[i + 1]))
            i += 2
            continue
        if ch == "*":
            out.append(".*")
        elif ch == "?":
            out.append(".")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$", re.DOTALL | re.IGNORECASE)


def _compile_criteria(criteria) -> Callable[[object], bool]:
    """Phân tích tiêu chí kiểu Excel MỘT LẦN, trả về predicate(value)->bool.

    Hot path của COUNTIF/SUMIF/AVERAGEIF/COUNTIFS/SUMIFS/AVERAGEIFS/MAXIFS/MINIFS:
    parse tiêu chí một lần ở ngoài vòng lặp, mỗi ô chỉ gọi predicate (không cấp
    phát dict, không parse lại chuỗi, không try/except float lặp lại).
    """
    if isinstance(criteria, bool):
        def pred_bool(v):
            try:
                return _to_bool(v) == criteria
            except FormulaError:
                return False
        return pred_bool
    if isinstance(criteria, (int, float)):
        target = float(criteria)

        def pred_num(v):
            try:
                return _to_number(v) == target
            except FormulaError:
                return False
        return pred_num

    crit = str(criteria)
    op = None
    for o in (">=", "<=", "<>", ">", "<", "="):
        if crit.startswith(o):
            op, crit = o, crit[len(o):]
            break
    try:
        crit_num = float(crit)
        if not math.isfinite(crit_num):
            crit_num = None
    except ValueError:
        crit_num = None

    if op in (">", "<", ">=", "<="):
        if crit_num is None:
            return lambda v: False
        if op == ">":
            comparator = lambda x: x > crit_num   # noqa: E731
        elif op == "<":
            comparator = lambda x: x < crit_num   # noqa: E731
        elif op == ">=":
            comparator = lambda x: x >= crit_num  # noqa: E731
        else:
            comparator = lambda x: x <= crit_num  # noqa: E731

        def pred_cmp(v):
            try:
                return comparator(_to_number(v))
            except FormulaError:
                return False
        return pred_cmp

    negate = op == "<>"
    if crit_num is not None:
        def pred_eq(v):
            try:
                eq = _to_number(v) == crit_num
            except FormulaError:
                eq = False
            return (not eq) if negate else eq
        return pred_eq

    rx = _wildcard_to_regex(crit) if any(c in crit for c in "*?~") else None
    crit_low = crit.lower()

    def pred_text(v):
        s = _text(v)
        eq = (rx.match(s) is not None) if rx is not None else (s.lower() == crit_low)
        return (not eq) if negate else eq
    return pred_text


def _match_criteria(value, criteria) -> bool:
    """So khớp 1 giá trị với 1 tiêu chí (tiện ích; biên dịch lại mỗi lần gọi).

    Đường nóng nên dùng ``_compile_criteria`` ngoài vòng lặp; hàm này giữ lại cho
    các chỗ gọi lẻ và để tương thích ngược.
    """
    return _compile_criteria(criteria)(value)


def _numbers(args) -> list[float]:
    """Lấy các giá trị số, bỏ qua ô rỗng / không phải số (trải _Range)."""
    out = []
    for a in _flatten(args):
        if a is None or a == "":
            continue
        try:
            out.append(_to_number(a))
        except FormulaError:
            continue
    return out


def _fn_sum(args):
    return sum(_numbers(args))


def _fn_average(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("AVERAGE cần ít nhất một số")
    return sum(nums) / len(nums)


def _fn_min(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("MIN cần ít nhất một số")
    return min(nums)


def _fn_max(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("MAX cần ít nhất một số")
    return max(nums)


def _fn_count(args):
    return float(len(_numbers(args)))


def _fn_abs(args):
    if len(args) != 1:
        raise FormulaError("ABS cần đúng 1 đối số")
    return abs(_to_number(args[0]))


def _fn_round(args):
    if len(args) not in (1, 2):
        raise FormulaError("ROUND cần 1 hoặc 2 đối số")
    ndigits = int(_to_number(args[1])) if len(args) == 2 else 0
    return round(_to_number(args[0]), ndigits)


def _fn_sqrt(args):
    if len(args) != 1:
        raise FormulaError("SQRT cần đúng 1 đối số")
    n = _to_number(args[0])
    if n < 0:
        raise FormulaError("SQRT của số âm", ERR_NUM)
    return n ** 0.5


def _fn_int(args):
    if len(args) != 1:
        raise FormulaError("INT cần đúng 1 đối số")
    import math

    return float(math.floor(_to_number(args[0])))


def _fn_mod(args):
    if len(args) != 2:
        raise FormulaError("MOD cần đúng 2 đối số")
    b = _to_number(args[1])
    if b == 0:
        raise FormulaError("MOD chia cho 0", ERR_DIV0)
    return _to_number(args[0]) % b


def _fn_power(args):
    if len(args) != 2:
        raise FormulaError("POWER cần đúng 2 đối số")
    try:
        result = _to_number(args[0]) ** _to_number(args[1])
    except OverflowError:
        raise FormulaError("POWER: kết quả quá lớn", ERR_NUM)
    except ZeroDivisionError:
        raise FormulaError("POWER: 0 mũ âm", ERR_DIV0)
    if isinstance(result, complex) or not math.isfinite(result):
        raise FormulaError("POWER: kết quả không hợp lệ", ERR_NUM)
    return result


def _fn_concat(args):
    return "".join(_text(a) for a in _flatten(args))


def _fn_rand(args):
    if args:
        raise FormulaError("RAND không nhận đối số")
    return random.random()


def _fn_randbetween(args):
    if len(args) != 2:
        raise FormulaError("RANDBETWEEN cần đúng 2 đối số")
    low = int(_to_number(args[0]))
    high = int(_to_number(args[1]))
    if low > high:
        low, high = high, low
    return float(random.randint(low, high))


# --- logic (eager) ---


def _fn_and(args):
    vals = _flatten(args)
    if not vals:
        raise FormulaError("AND cần ít nhất 1 đối số")
    return all(_to_bool(v) for v in vals)


def _fn_or(args):
    vals = _flatten(args)
    if not vals:
        raise FormulaError("OR cần ít nhất 1 đối số")
    return any(_to_bool(v) for v in vals)


def _fn_not(args):
    if len(args) != 1:
        raise FormulaError("NOT cần đúng 1 đối số")
    return not _to_bool(args[0])


def _fn_true(args):
    if args:
        raise FormulaError("TRUE không nhận đối số")
    return True


def _fn_false(args):
    if args:
        raise FormulaError("FALSE không nhận đối số")
    return False


# --- thống kê có điều kiện ---


def _crit_values(arg) -> list:
    return arg.flat() if isinstance(arg, _Range) else [arg]


def _fn_countif(args):
    if len(args) != 2:
        raise FormulaError("COUNTIF cần đúng 2 đối số")
    pred = _compile_criteria(args[1])
    return float(sum(1 for v in _crit_values(args[0]) if pred(v)))


def _fn_sumif(args):
    if len(args) not in (2, 3):
        raise FormulaError("SUMIF cần 2 hoặc 3 đối số")
    crit_vals = _crit_values(args[0])
    sum_vals = _crit_values(args[2]) if len(args) == 3 else crit_vals
    pred = _compile_criteria(args[1])
    total = 0.0
    for cv, sv in zip(crit_vals, sum_vals):
        if pred(cv):
            try:
                total += _to_number(sv)
            except FormulaError:
                pass
    return total


def _fn_averageif(args):
    if len(args) not in (2, 3):
        raise FormulaError("AVERAGEIF cần 2 hoặc 3 đối số")
    crit_vals = _crit_values(args[0])
    avg_vals = _crit_values(args[2]) if len(args) == 3 else crit_vals
    pred = _compile_criteria(args[1])
    picked = []
    for cv, av in zip(crit_vals, avg_vals):
        if pred(cv):
            try:
                picked.append(_to_number(av))
            except FormulaError:
                pass
    if not picked:
        raise FormulaError("AVERAGEIF: không có ô khớp", ERR_DIV0)
    return sum(picked) / len(picked)


def _check_equal_lengths(ranges, fname):
    """Tất cả vùng phải cùng độ dài, nếu không Excel trả #VALUE! (tránh IndexError)."""
    if len({len(r) for r in ranges}) > 1:
        raise FormulaError(f"{fname}: các vùng lệch kích thước", ERR_VALUE)


def _fn_countifs(args):
    if len(args) < 2 or len(args) % 2 != 0:
        raise FormulaError("COUNTIFS cần các cặp (vùng, tiêu_chí)")
    ranges = [_crit_values(args[i]) for i in range(0, len(args), 2)]
    _check_equal_lengths(ranges, "COUNTIFS")
    preds = [_compile_criteria(args[i + 1]) for i in range(0, len(args), 2)]
    rows = zip(*ranges)
    return float(sum(
        1 for row in rows
        if all(preds[k](row[k]) for k in range(len(preds)))
    ))


def _fn_sumifs(args):
    if len(args) < 3 or len(args) % 2 == 0:
        raise FormulaError("SUMIFS cần vùng_tổng + các cặp (vùng, tiêu_chí)")
    sum_vals = _crit_values(args[0])
    ranges = [_crit_values(args[i]) for i in range(1, len(args), 2)]
    _check_equal_lengths([sum_vals] + ranges, "SUMIFS")
    preds = [_compile_criteria(args[i + 1]) for i in range(1, len(args), 2)]
    total = 0.0
    for sv, row in zip(sum_vals, zip(*ranges)):
        if all(preds[k](row[k]) for k in range(len(preds))):
            try:
                total += _to_number(sv)
            except FormulaError:
                pass
    return total


def _fn_counta(args):
    return float(sum(1 for v in _flatten(args) if not (v is None or v == "")))


def _fn_countblank(args):
    return float(sum(1 for v in _flatten(args) if v is None or v == ""))


# --- tra cứu ---


def _fn_vlookup(args):
    if len(args) not in (3, 4):
        raise FormulaError("VLOOKUP cần 3 hoặc 4 đối số")
    key, table = args[0], args[1]
    if not isinstance(table, _Range):
        raise FormulaError("VLOOKUP: đối số 2 phải là vùng")
    col_idx = int(_to_number(args[2]))
    approx = _to_bool(args[3]) if len(args) == 4 else True
    if col_idx < 1 or col_idx > table.width:
        raise FormulaError("VLOOKUP: số cột vượt phạm vi")
    first = table.column(0)
    if approx:
        best = None
        for i, v in enumerate(first):
            if _cmp(v, key) <= 0:
                best = i
        if best is None:
            raise FormulaError("VLOOKUP: không tìm thấy", ERR_NA)
        return table.rows[best][col_idx - 1]
    for i, v in enumerate(first):
        if _loose_equal(v, key):
            return table.rows[i][col_idx - 1]
    raise FormulaError("VLOOKUP: không tìm thấy", ERR_NA)


def _fn_hlookup(args):
    if len(args) not in (3, 4):
        raise FormulaError("HLOOKUP cần 3 hoặc 4 đối số")
    key, table = args[0], args[1]
    if not isinstance(table, _Range):
        raise FormulaError("HLOOKUP: đối số 2 phải là vùng")
    row_idx = int(_to_number(args[2]))
    approx = _to_bool(args[3]) if len(args) == 4 else True
    if row_idx < 1 or row_idx > table.height:
        raise FormulaError("HLOOKUP: số hàng vượt phạm vi")
    first = table.row(0)
    if approx:
        best = None
        for i, v in enumerate(first):
            if _cmp(v, key) <= 0:
                best = i
        if best is None:
            raise FormulaError("HLOOKUP: không tìm thấy", ERR_NA)
        return table.rows[row_idx - 1][best]
    for i, v in enumerate(first):
        if _loose_equal(v, key):
            return table.rows[row_idx - 1][i]
    raise FormulaError("HLOOKUP: không tìm thấy", ERR_NA)


def _fn_index(args):
    if len(args) not in (2, 3):
        raise FormulaError("INDEX cần 2 hoặc 3 đối số")
    table = args[0]
    if not isinstance(table, _Range):
        raise FormulaError("INDEX: đối số 1 phải là vùng")
    r = int(_to_number(args[1]))
    if len(args) == 3:
        c = int(_to_number(args[2]))
    elif table.height == 1:
        r, c = 1, r
    else:
        c = 1
    if not (1 <= r <= table.height and 1 <= c <= table.width):
        raise FormulaError("INDEX: chỉ số vượt phạm vi", ERR_REF)
    return table.rows[r - 1][c - 1]


def _fn_match(args):
    if len(args) not in (2, 3):
        raise FormulaError("MATCH cần 2 hoặc 3 đối số")
    key, rng = args[0], args[1]
    if not isinstance(rng, _Range):
        raise FormulaError("MATCH: đối số 2 phải là vùng")
    vals = rng.flat()
    mtype = int(_to_number(args[2])) if len(args) == 3 else 1
    if mtype == 0:
        for i, v in enumerate(vals):
            if _loose_equal(v, key):
                return float(i + 1)
        raise FormulaError("MATCH: không tìm thấy", ERR_NA)
    best = None
    for i, v in enumerate(vals):
        if (mtype == 1 and _cmp(v, key) <= 0) or (mtype != 1 and _cmp(v, key) >= 0):
            best = i
    if best is None:
        raise FormulaError("MATCH: không tìm thấy", ERR_NA)
    return float(best + 1)


def _fn_lookup(args):
    if len(args) not in (2, 3):
        raise FormulaError("LOOKUP cần 2 hoặc 3 đối số")
    key = args[0]
    sv = _crit_values(args[1])
    rv = _crit_values(args[2]) if len(args) == 3 else sv
    best = None
    for i, v in enumerate(sv):
        if _cmp(v, key) <= 0:
            best = i
    if best is None or best >= len(rv):
        raise FormulaError("LOOKUP: không tìm thấy", ERR_NA)
    return rv[best]


# --- chuỗi ---


def _fn_left(args):
    if len(args) not in (1, 2):
        raise FormulaError("LEFT cần 1 hoặc 2 đối số")
    n = int(_to_number(args[1])) if len(args) == 2 else 1
    return _text(args[0])[:max(0, n)]


def _fn_right(args):
    if len(args) not in (1, 2):
        raise FormulaError("RIGHT cần 1 hoặc 2 đối số")
    n = int(_to_number(args[1])) if len(args) == 2 else 1
    s = _text(args[0])
    return s[len(s) - max(0, n):] if n > 0 else ""


def _fn_mid(args):
    if len(args) != 3:
        raise FormulaError("MID cần đúng 3 đối số")
    start = int(_to_number(args[1]))
    length = int(_to_number(args[2]))
    if start < 1 or length < 0:
        raise FormulaError("MID: vị trí/độ dài không hợp lệ")
    return _text(args[0])[start - 1:start - 1 + length]


def _fn_len(args):
    if len(args) != 1:
        raise FormulaError("LEN cần đúng 1 đối số")
    return float(len(_text(args[0])))


def _fn_trim(args):
    if len(args) != 1:
        raise FormulaError("TRIM cần đúng 1 đối số")
    return " ".join(_text(args[0]).split())


def _fn_upper(args):
    if len(args) != 1:
        raise FormulaError("UPPER cần đúng 1 đối số")
    return _text(args[0]).upper()


def _fn_lower(args):
    if len(args) != 1:
        raise FormulaError("LOWER cần đúng 1 đối số")
    return _text(args[0]).lower()


def _fn_proper(args):
    if len(args) != 1:
        raise FormulaError("PROPER cần đúng 1 đối số")
    return _text(args[0]).title()


def _fn_rept(args):
    if len(args) != 2:
        raise FormulaError("REPT cần đúng 2 đối số")
    return _text(args[0]) * max(0, int(_to_number(args[1])))


def _fn_replace(args):
    if len(args) != 4:
        raise FormulaError("REPLACE cần đúng 4 đối số")
    old = _text(args[0])
    start = int(_to_number(args[1]))
    num = int(_to_number(args[2]))
    if start < 1 or num < 0:
        raise FormulaError("REPLACE: vị trí/độ dài không hợp lệ")
    return old[:start - 1] + _text(args[3]) + old[start - 1 + num:]


def _fn_substitute(args):
    if len(args) not in (3, 4):
        raise FormulaError("SUBSTITUTE cần 3 hoặc 4 đối số")
    text, old, new = _text(args[0]), _text(args[1]), _text(args[2])
    if old == "":
        return text
    if len(args) == 3:
        return text.replace(old, new)
    inst = int(_to_number(args[3]))
    if inst < 1:
        raise FormulaError("SUBSTITUTE: số thứ tự phải >= 1")
    idx = -1
    for _ in range(inst):
        idx = text.find(old, idx + 1)
        if idx == -1:
            return text
    return text[:idx] + new + text[idx + len(old):]


def _fn_find(args):
    if len(args) not in (2, 3):
        raise FormulaError("FIND cần 2 hoặc 3 đối số")
    needle, hay = _text(args[0]), _text(args[1])
    start = int(_to_number(args[2])) if len(args) == 3 else 1
    pos = hay.find(needle, max(0, start - 1))
    if pos == -1:
        raise FormulaError("FIND: không tìm thấy")
    return float(pos + 1)


def _fn_search(args):
    if len(args) not in (2, 3):
        raise FormulaError("SEARCH cần 2 hoặc 3 đối số")
    needle, hay = _text(args[0]).lower(), _text(args[1]).lower()
    start = int(_to_number(args[2])) if len(args) == 3 else 1
    pos = hay.find(needle, max(0, start - 1))
    if pos == -1:
        raise FormulaError("SEARCH: không tìm thấy")
    return float(pos + 1)


def _fn_value(args):
    if len(args) != 1:
        raise FormulaError("VALUE cần đúng 1 đối số")
    return _to_number(args[0])


def _fn_text(args):
    if len(args) != 2:
        raise FormulaError("TEXT cần đúng 2 đối số")
    return _format_number(_to_number(args[0]), _text(args[1]))


# --- toán bổ sung ---


def _fn_ceiling(args):
    if len(args) not in (1, 2):
        raise FormulaError("CEILING cần 1 hoặc 2 đối số")
    sig = _to_number(args[1]) if len(args) == 2 else 1.0
    if sig == 0:
        return 0.0
    return math.ceil(_to_number(args[0]) / sig) * sig


def _fn_floor(args):
    if len(args) not in (1, 2):
        raise FormulaError("FLOOR cần 1 hoặc 2 đối số")
    sig = _to_number(args[1]) if len(args) == 2 else 1.0
    if sig == 0:
        return 0.0
    return math.floor(_to_number(args[0]) / sig) * sig


def _fn_trunc(args):
    if len(args) not in (1, 2):
        raise FormulaError("TRUNC cần 1 hoặc 2 đối số")
    digits = int(_to_number(args[1])) if len(args) == 2 else 0
    factor = 10 ** digits
    return math.trunc(_to_number(args[0]) * factor) / factor


def _fn_sign(args):
    if len(args) != 1:
        raise FormulaError("SIGN cần đúng 1 đối số")
    n = _to_number(args[0])
    return float((n > 0) - (n < 0))


def _fn_product(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("PRODUCT cần ít nhất một số")
    result = 1.0
    for n in nums:
        result *= n
    return result


def _fn_sumproduct(args):
    arrays = [_crit_values(a) for a in args]
    if not arrays:
        return 0.0
    n = min(len(a) for a in arrays)
    total = 0.0
    for i in range(n):
        prod = 1.0
        for a in arrays:
            prod *= _to_number(a[i])
        total += prod
    return total


def _fn_roundup(args):
    if len(args) not in (1, 2):
        raise FormulaError("ROUNDUP cần 1 hoặc 2 đối số")
    digits = int(_to_number(args[1])) if len(args) == 2 else 0
    factor = 10 ** digits
    return math.ceil(abs(_to_number(args[0])) * factor) / factor * (1 if _to_number(args[0]) >= 0 else -1)


def _fn_rounddown(args):
    if len(args) not in (1, 2):
        raise FormulaError("ROUNDDOWN cần 1 hoặc 2 đối số")
    digits = int(_to_number(args[1])) if len(args) == 2 else 0
    factor = 10 ** digits
    return math.floor(abs(_to_number(args[0])) * factor) / factor * (1 if _to_number(args[0]) >= 0 else -1)


def _fn_pi(args):
    if args:
        raise FormulaError("PI không nhận đối số")
    return math.pi


def _fn_exp(args):
    if len(args) != 1:
        raise FormulaError("EXP cần đúng 1 đối số")
    return math.exp(_to_number(args[0]))


def _fn_log(args):
    if len(args) not in (1, 2):
        raise FormulaError("LOG cần 1 hoặc 2 đối số")
    base = _to_number(args[1]) if len(args) == 2 else 10.0
    return math.log(_to_number(args[0]), base)


def _fn_ln(args):
    if len(args) != 1:
        raise FormulaError("LN cần đúng 1 đối số")
    return math.log(_to_number(args[0]))


# --- ngày/giờ (serial date chuẩn Excel, mốc 1899-12-30) ---

_EXCEL_EPOCH = datetime.date(1899, 12, 30)


def _date_to_serial(d: datetime.date) -> float:
    return float((d - _EXCEL_EPOCH).days)


def _serial_to_date(n: float) -> datetime.date:
    try:
        return _EXCEL_EPOCH + datetime.timedelta(days=int(n))
    except (OverflowError, ValueError):
        raise FormulaError("Ngày ngoài phạm vi", ERR_NUM)


def _fn_today(args):
    if args:
        raise FormulaError("TODAY không nhận đối số")
    return _date_to_serial(datetime.date.today())


def _fn_now(args):
    if args:
        raise FormulaError("NOW không nhận đối số")
    now = datetime.datetime.now()
    serial = (now.date() - _EXCEL_EPOCH).days
    frac = (now.hour * 3600 + now.minute * 60 + now.second) / 86400.0
    return serial + frac


def _fn_date(args):
    if len(args) != 3:
        raise FormulaError("DATE cần đúng 3 đối số")
    y, m, d = (int(_to_number(args[i])) for i in range(3))
    try:
        return _date_to_serial(datetime.date(y, m, d))
    except ValueError as e:
        raise FormulaError(f"DATE không hợp lệ: {e}")


def _fn_year(args):
    if len(args) != 1:
        raise FormulaError("YEAR cần đúng 1 đối số")
    return float(_serial_to_date(_to_number(args[0])).year)


def _fn_month(args):
    if len(args) != 1:
        raise FormulaError("MONTH cần đúng 1 đối số")
    return float(_serial_to_date(_to_number(args[0])).month)


def _fn_day(args):
    if len(args) != 1:
        raise FormulaError("DAY cần đúng 1 đối số")
    return float(_serial_to_date(_to_number(args[0])).day)


def _fn_hour(args):
    if len(args) != 1:
        raise FormulaError("HOUR cần đúng 1 đối số")
    serial = _to_number(args[0])
    return float(int(round((serial - math.floor(serial)) * 86400)) // 3600 % 24)


def _fn_minute(args):
    if len(args) != 1:
        raise FormulaError("MINUTE cần đúng 1 đối số")
    serial = _to_number(args[0])
    return float(int(round((serial - math.floor(serial)) * 86400)) // 60 % 60)


def _fn_weekday(args):
    if len(args) not in (1, 2):
        raise FormulaError("WEEKDAY cần 1 hoặc 2 đối số")
    iso = _serial_to_date(_to_number(args[0])).isoweekday()  # T2=1..CN=7
    t = int(_to_number(args[1])) if len(args) == 2 else 1
    if t == 1:
        return float(iso % 7 + 1)   # CN=1..T7=7
    if t == 2:
        return float(iso)           # T2=1..CN=7
    if t == 3:
        return float(iso - 1)       # T2=0..CN=6
    raise FormulaError("WEEKDAY: type không hỗ trợ")


def _fn_datedif(args):
    if len(args) != 3:
        raise FormulaError("DATEDIF cần đúng 3 đối số")
    start = _serial_to_date(_to_number(args[0]))
    end = _serial_to_date(_to_number(args[1]))
    unit = _text(args[2]).upper()
    if unit == "D":
        return float((end - start).days)
    if unit == "Y":
        return float(end.year - start.year
                     - ((end.month, end.day) < (start.month, start.day)))
    if unit == "M":
        return float((end.year - start.year) * 12 + (end.month - start.month)
                     - (end.day < start.day))
    raise FormulaError("DATEDIF: unit phải là D/M/Y")


# --- thống kê ---


def _fn_median(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("MEDIAN cần ít nhất một số")
    return statistics.median(nums)


def _fn_mode(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("MODE cần ít nhất một số")
    return statistics.multimode(nums)[0]


def _fn_stdev(args):
    nums = _numbers(args)
    if len(nums) < 2:
        raise FormulaError("STDEV cần ít nhất hai số")
    return statistics.stdev(nums)


def _fn_var(args):
    nums = _numbers(args)
    if len(nums) < 2:
        raise FormulaError("VAR cần ít nhất hai số")
    return statistics.variance(nums)


def _fn_large(args):
    if len(args) != 2:
        raise FormulaError("LARGE cần đúng 2 đối số")
    nums = _numbers([args[0]])
    k = int(_to_number(args[1]))
    if k < 1 or k > len(nums):
        raise FormulaError("LARGE: k vượt phạm vi")
    return sorted(nums, reverse=True)[k - 1]


def _fn_small(args):
    if len(args) != 2:
        raise FormulaError("SMALL cần đúng 2 đối số")
    nums = _numbers([args[0]])
    k = int(_to_number(args[1]))
    if k < 1 or k > len(nums):
        raise FormulaError("SMALL: k vượt phạm vi")
    return sorted(nums)[k - 1]


def _fn_rank(args):
    if len(args) not in (2, 3):
        raise FormulaError("RANK cần 2 hoặc 3 đối số")
    x = _to_number(args[0])
    nums = _numbers([args[1]])
    order = int(_to_number(args[2])) if len(args) == 3 else 0
    ordered = sorted(nums) if order else sorted(nums, reverse=True)
    for i, v in enumerate(ordered):
        if v == x:
            return float(i + 1)
    raise FormulaError("RANK: không tìm thấy số trong vùng")


# --- hàm logic tính LƯỜI (đối số chỉ tính khi cần) ---


def _fn_if_lazy(thunks):
    if len(thunks) != 3:
        raise FormulaError("IF cần đúng 3 đối số: IF(điều_kiện, đúng, sai)")
    return thunks[1]() if _to_bool(thunks[0]()) else thunks[2]()


def _fn_iferror_lazy(thunks):
    if len(thunks) != 2:
        raise FormulaError("IFERROR cần đúng 2 đối số")
    try:
        return thunks[0]()
    except FormulaError:
        return thunks[1]()


def _fn_ifs_lazy(thunks):
    if len(thunks) < 2 or len(thunks) % 2 != 0:
        raise FormulaError("IFS cần các cặp (điều_kiện, giá_trị)")
    for i in range(0, len(thunks), 2):
        if _to_bool(thunks[i]()):
            return thunks[i + 1]()
    raise FormulaError("IFS: không điều kiện nào đúng")


def _format_number(value: float, fmt: str) -> str:
    """Định dạng số tối giản cho hàm TEXT (sẽ tái dùng/mở rộng ở Phase 2).

    Hỗ trợ: phần trăm ('%'), số chữ số thập phân theo số '0' sau dấu '.',
    và dấu phân tách hàng nghìn (',').
    """
    percent = "%" in fmt
    body = fmt.replace("%", "")
    if percent:
        value *= 100
    thousands = "," in body.split(".")[0]
    decimals = 0
    if "." in body:
        decimals = body.split(".", 1)[1].count("0")
    spec = f"{',' if thousands else ''}.{decimals}f"
    out = format(value, spec)
    return out + "%" if percent else out


# ============================================================ HÀM MỚI (v0.11.3)
# Bổ sung loạt hàm Excel chuẩn còn thiếu. Tất cả đều "scalar" (không tạo spill
# range), khớp mô hình đối số hiện có (giá trị đơn hoặc _Range). Giữ nguyên các
# helper hiện có (_to_number, _text, _flatten, _numbers, _match_criteria...).


def _round_half_up(x: float) -> float:
    """Làm tròn nửa-ra-xa-0 (kiểu Excel), khác round() của Python (banker)."""
    return math.floor(x + 0.5) if x >= 0 else math.ceil(x - 0.5)


def _is_number(v) -> bool:
    """True nếu là số thực (bool KHÔNG tính là số, giống Excel)."""
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _scalar(v):
    """Ép một đối số về giá trị đơn. Vùng 1 ô -> giá trị ô đó; vùng nhiều ô ->
    #VALUE! (tránh sai âm thầm khi truyền A1:A9 vào hàm cần 1 giá trị)."""
    if isinstance(v, _Range):
        flat = v.flat()
        if len(flat) == 1:
            return flat[0]
        raise FormulaError("Cần một giá trị đơn, nhận vùng nhiều ô", ERR_VALUE)
    return v


# --- thông tin (Information) ---


def _fn_isnumber(args):
    if len(args) != 1:
        raise FormulaError("ISNUMBER cần đúng 1 đối số")
    return _is_number(_scalar(args[0]))


def _fn_istext(args):
    if len(args) != 1:
        raise FormulaError("ISTEXT cần đúng 1 đối số")
    v = _scalar(args[0])
    return isinstance(v, str) and v != ""


def _fn_isnontext(args):
    if len(args) != 1:
        raise FormulaError("ISNONTEXT cần đúng 1 đối số")
    v = _scalar(args[0])
    return not (isinstance(v, str) and v != "")


def _fn_isblank(args):
    if len(args) != 1:
        raise FormulaError("ISBLANK cần đúng 1 đối số")
    v = _scalar(args[0])
    return v is None or v == ""


def _fn_islogical(args):
    if len(args) != 1:
        raise FormulaError("ISLOGICAL cần đúng 1 đối số")
    return isinstance(_scalar(args[0]), bool)


def _fn_iseven(args):
    if len(args) != 1:
        raise FormulaError("ISEVEN cần đúng 1 đối số")
    return math.trunc(_to_number(_scalar(args[0]))) % 2 == 0


def _fn_isodd(args):
    if len(args) != 1:
        raise FormulaError("ISODD cần đúng 1 đối số")
    return math.trunc(_to_number(_scalar(args[0]))) % 2 != 0


def _fn_na(args):
    if args:
        raise FormulaError("NA không nhận đối số", ERR_VALUE)
    raise FormulaError("#N/A", ERR_NA)


# --- logic bổ sung ---


def _fn_xor(args):
    vals = _flatten(args)
    if not vals:
        raise FormulaError("XOR cần ít nhất 1 đối số")
    return sum(1 for v in vals if _to_bool(v)) % 2 == 1


# --- chuỗi bổ sung ---


def _fn_textjoin(args):
    if len(args) < 3:
        raise FormulaError("TEXTJOIN cần delimiter, ignore_empty và ít nhất 1 text")
    if isinstance(args[0], _Range):
        raise FormulaError("TEXTJOIN: delimiter phải là 1 giá trị", ERR_VALUE)
    delim = _text(args[0])
    ignore_empty = _to_bool(args[1])
    parts = []
    for v in _flatten(args[2:]):
        if ignore_empty and (v is None or v == ""):
            continue
        parts.append(_text(v))
    return delim.join(parts)


def _fn_exact(args):
    if len(args) != 2:
        raise FormulaError("EXACT cần đúng 2 đối số")
    return _text(args[0]) == _text(args[1])


def _fn_char(args):
    if len(args) != 1:
        raise FormulaError("CHAR cần đúng 1 đối số")
    n = int(_to_number(args[0]))
    if not (1 <= n <= 255):
        raise FormulaError("CHAR: mã phải trong 1..255", ERR_VALUE)
    return chr(n)


def _fn_unichar(args):
    if len(args) != 1:
        raise FormulaError("UNICHAR cần đúng 1 đối số")
    n = int(_to_number(args[0]))
    if not (1 <= n <= 0x10FFFF):
        raise FormulaError("UNICHAR: mã ngoài phạm vi", ERR_VALUE)
    return chr(n)


def _fn_code(args):
    if len(args) != 1:
        raise FormulaError("CODE cần đúng 1 đối số")
    s = _text(args[0])
    if not s:
        raise FormulaError("CODE: chuỗi rỗng", ERR_VALUE)
    return float(ord(s[0]))


def _fn_unicode(args):
    if len(args) != 1:
        raise FormulaError("UNICODE cần đúng 1 đối số")
    s = _text(args[0])
    if not s:
        raise FormulaError("UNICODE: chuỗi rỗng", ERR_VALUE)
    return float(ord(s[0]))


def _fn_clean(args):
    if len(args) != 1:
        raise FormulaError("CLEAN cần đúng 1 đối số")
    return "".join(ch for ch in _text(args[0]) if ord(ch) >= 32)


def _fn_t(args):
    if len(args) != 1:
        raise FormulaError("T cần đúng 1 đối số")
    v = args[0]
    return v if isinstance(v, str) else ""


def _fn_fixed(args):
    if len(args) not in (1, 2, 3):
        raise FormulaError("FIXED cần 1..3 đối số")
    num = _to_number(args[0])
    decimals = int(_to_number(args[1])) if len(args) >= 2 else 2
    no_commas = _to_bool(args[2]) if len(args) == 3 else False
    if decimals < 0:
        factor = 10 ** (-decimals)
        num = _round_half_up(num / factor) * factor
        decimals = 0
    spec = f"{'' if no_commas else ','}.{decimals}f"
    return format(num, spec)


# --- tra cứu bổ sung ---


def _fn_choose(args):
    if len(args) < 2:
        raise FormulaError("CHOOSE cần index và ít nhất 1 giá trị")
    idx = int(_to_number(args[0]))
    if idx < 1 or idx > len(args) - 1:
        raise FormulaError("CHOOSE: index vượt phạm vi", ERR_VALUE)
    return args[idx]


def _fn_xlookup(args):
    if not (3 <= len(args) <= 6):
        raise FormulaError("XLOOKUP cần 3..6 đối số")
    key = args[0]
    look_vals = _crit_values(args[1])
    ret_vals = _crit_values(args[2])
    if_nf = args[3] if len(args) >= 4 else None
    match_mode = int(_to_number(args[4])) if len(args) >= 5 else 0
    search_mode = int(_to_number(args[5])) if len(args) >= 6 else 1
    n = len(look_vals)
    order = range(n) if search_mode >= 0 else range(n - 1, -1, -1)
    found = None
    if match_mode == 0:
        for i in order:
            if _loose_equal(look_vals[i], key):
                found = i
                break
    elif match_mode == 2:  # wildcard (kiểu Excel: * ? ~)
        rx = _wildcard_to_regex(_text(key))
        for i in order:
            if rx.match(_text(look_vals[i])):
                found = i
                break
    elif match_mode in (-1, 1):  # exact-or-next-smaller / -larger
        want_smaller = match_mode == -1
        best = None
        for i in order:
            c = _cmp(look_vals[i], key)
            if c == 0:
                found = i
                break
            if (want_smaller and c < 0) or (not want_smaller and c > 0):
                if best is None or (
                    _cmp(look_vals[i], look_vals[best]) > 0 if want_smaller
                    else _cmp(look_vals[i], look_vals[best]) < 0
                ):
                    best = i
        if found is None:
            found = best
    else:
        raise FormulaError("XLOOKUP: match_mode không hỗ trợ", ERR_VALUE)
    if found is None:
        if if_nf is not None:
            return if_nf
        raise FormulaError("XLOOKUP: không tìm thấy", ERR_NA)
    if found >= len(ret_vals):
        raise FormulaError("XLOOKUP: vùng trả về không khớp kích thước", ERR_VALUE)
    return ret_vals[found]


# --- toán bổ sung ---


def _math1(name: str, fn: Callable[[float], float]) -> Callable:
    """Sinh hàm 1-đối-số gói lỗi miền xác định thành #NUM!."""
    def impl(args):
        if len(args) != 1:
            raise FormulaError(f"{name} cần đúng 1 đối số")
        try:
            return fn(_to_number(args[0]))
        except (ValueError, OverflowError):
            raise FormulaError(f"{name}: ngoài miền xác định", ERR_NUM)
    return impl


def _fn_atan2(args):
    if len(args) != 2:
        raise FormulaError("ATAN2 cần đúng 2 đối số")
    x = _to_number(args[0])
    y = _to_number(args[1])
    if x == 0 and y == 0:
        raise FormulaError("ATAN2: cả hai bằng 0", ERR_DIV0)
    return math.atan2(y, x)  # Excel: ATAN2(x_num, y_num)


def _fn_degrees(args):
    if len(args) != 1:
        raise FormulaError("DEGREES cần đúng 1 đối số")
    return math.degrees(_to_number(args[0]))


def _fn_radians(args):
    if len(args) != 1:
        raise FormulaError("RADIANS cần đúng 1 đối số")
    return math.radians(_to_number(args[0]))


def _int_list(args) -> list[int]:
    """Danh sách số nguyên (truncate) cho GCD/LCM. Excel: số âm -> #NUM!."""
    out = []
    for v in _flatten(args):
        if v is None or v == "":
            continue
        n = math.trunc(_to_number(v))
        if n < 0:
            raise FormulaError("GCD/LCM: không nhận số âm", ERR_NUM)
        out.append(n)
    return out


def _fn_gcd(args):
    nums = _int_list(args)
    if not nums:
        raise FormulaError("GCD cần ít nhất 1 số")
    result = 0
    for n in nums:
        result = math.gcd(result, n)
    return float(result)


def _fn_lcm(args):
    nums = _int_list(args)
    if not nums:
        raise FormulaError("LCM cần ít nhất 1 số")
    result = 1
    for n in nums:
        if n == 0:
            return 0.0
        result = result * n // math.gcd(result, n)
    return float(result)


# Ngưỡng log10 mà float64 còn biểu diễn được (~1.8e308). Dùng lgamma để CHẶN
# kết quả quá lớn TRƯỚC khi tính (tránh vừa tràn float vừa treo CPU với n khổng lồ).
_LN10 = math.log(10)
_FLOAT_MAX_LOG10 = 308.0


def _fn_fact(args):
    if len(args) != 1:
        raise FormulaError("FACT cần đúng 1 đối số")
    n = math.trunc(_to_number(args[0]))
    if n < 0:
        raise FormulaError("FACT: số âm", ERR_NUM)
    if n > 170:  # 171! đã tràn float64 (Excel cũng trả #NUM!)
        raise FormulaError("FACT: kết quả quá lớn", ERR_NUM)
    return float(math.factorial(n))


def _fn_combin(args):
    if len(args) != 2:
        raise FormulaError("COMBIN cần đúng 2 đối số")
    n = math.trunc(_to_number(args[0]))
    k = math.trunc(_to_number(args[1]))
    if n < 0 or k < 0 or k > n:
        raise FormulaError("COMBIN: tham số không hợp lệ", ERR_NUM)
    log10 = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / _LN10
    if log10 > _FLOAT_MAX_LOG10:
        raise FormulaError("COMBIN: kết quả quá lớn", ERR_NUM)
    return float(math.comb(n, k))


def _fn_permut(args):
    if len(args) != 2:
        raise FormulaError("PERMUT cần đúng 2 đối số")
    n = math.trunc(_to_number(args[0]))
    k = math.trunc(_to_number(args[1]))
    if n < 0 or k < 0 or k > n:
        raise FormulaError("PERMUT: tham số không hợp lệ", ERR_NUM)
    log10 = (math.lgamma(n + 1) - math.lgamma(n - k + 1)) / _LN10
    if log10 > _FLOAT_MAX_LOG10:
        raise FormulaError("PERMUT: kết quả quá lớn", ERR_NUM)
    return float(math.perm(n, k))


def _fn_mround(args):
    if len(args) != 2:
        raise FormulaError("MROUND cần đúng 2 đối số")
    num = _to_number(args[0])
    mult = _to_number(args[1])
    if mult == 0:
        return 0.0
    if num != 0 and (num > 0) != (mult > 0):
        raise FormulaError("MROUND: num và multiple khác dấu", ERR_NUM)
    return _round_half_up(num / mult) * mult


def _fn_even(args):
    if len(args) != 1:
        raise FormulaError("EVEN cần đúng 1 đối số")
    n = _to_number(args[0])
    if n == 0:
        return 0.0
    k = math.ceil(abs(n) / 2) * 2
    return float(k if n > 0 else -k)


def _fn_odd(args):
    if len(args) != 1:
        raise FormulaError("ODD cần đúng 1 đối số")
    n = _to_number(args[0])
    if n == 0:
        return 1.0
    k = math.ceil((abs(n) + 1) / 2) * 2 - 1
    return float(k if n > 0 else -k)


def _fn_quotient(args):
    if len(args) != 2:
        raise FormulaError("QUOTIENT cần đúng 2 đối số")
    b = _to_number(args[1])
    if b == 0:
        raise FormulaError("QUOTIENT chia cho 0", ERR_DIV0)
    return float(math.trunc(_to_number(args[0]) / b))


def _fn_sumsq(args):
    return sum(n * n for n in _numbers(args))


# --- thống kê bổ sung ---


def _conditional_pick(args, fname: str) -> list[float]:
    """Lấy list số từ vùng[0] khớp các cặp (vùng, tiêu_chí) sau đó (cho
    AVERAGEIFS/MAXIFS/MINIFS)."""
    if len(args) < 3 or len(args) % 2 == 0:
        raise FormulaError(f"{fname} cần vùng_giá_trị + các cặp (vùng, tiêu_chí)")
    target = _crit_values(args[0])
    ranges = [_crit_values(args[i]) for i in range(1, len(args), 2)]
    _check_equal_lengths([target] + ranges, fname)
    preds = [_compile_criteria(args[i + 1]) for i in range(1, len(args), 2)]
    picked = []
    for tv, row in zip(target, zip(*ranges)):
        if all(preds[k](row[k]) for k in range(len(preds))):
            try:
                picked.append(_to_number(tv))
            except FormulaError:
                pass
    return picked


def _fn_averageifs(args):
    picked = _conditional_pick(args, "AVERAGEIFS")
    if not picked:
        raise FormulaError("AVERAGEIFS: không có ô khớp", ERR_DIV0)
    return sum(picked) / len(picked)


def _fn_maxifs(args):
    picked = _conditional_pick(args, "MAXIFS")
    return max(picked) if picked else 0.0


def _fn_minifs(args):
    picked = _conditional_pick(args, "MINIFS")
    return min(picked) if picked else 0.0


def _fn_stdevp(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("STDEVP cần ít nhất một số")
    return statistics.pstdev(nums)


def _fn_varp(args):
    nums = _numbers(args)
    if not nums:
        raise FormulaError("VARP cần ít nhất một số")
    return statistics.pvariance(nums)


def _fn_geomean(args):
    nums = _numbers(args)
    if not nums or any(n <= 0 for n in nums):
        raise FormulaError("GEOMEAN cần các số dương", ERR_NUM)
    return statistics.geometric_mean(nums)


def _fn_harmean(args):
    nums = _numbers(args)
    if not nums or any(n <= 0 for n in nums):
        raise FormulaError("HARMEAN cần các số dương", ERR_NUM)
    return statistics.harmonic_mean(nums)


def _fn_averagea(args):
    vals = []
    for v in _flatten(args):
        if v is None or v == "":
            continue
        if isinstance(v, bool):
            vals.append(1.0 if v else 0.0)
        elif _is_number(v):
            vals.append(float(v))
        else:
            vals.append(0.0)  # text -> 0 (giống Excel)
    if not vals:
        raise FormulaError("AVERAGEA cần ít nhất một giá trị", ERR_DIV0)
    return sum(vals) / len(vals)


# --- ngày/giờ bổ sung ---


def _add_months(d: datetime.date, months: int) -> datetime.date:
    """Cộng số tháng vào ngày, kẹp về ngày cuối tháng nếu tràn."""
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    try:
        last = calendar.monthrange(year, month)[1]
        return datetime.date(year, month, min(d.day, last))
    except (ValueError, OverflowError):
        raise FormulaError("Ngày ngoài phạm vi (1..9999)", ERR_NUM)


def _fn_edate(args):
    if len(args) != 2:
        raise FormulaError("EDATE cần đúng 2 đối số")
    d = _serial_to_date(_to_number(args[0]))
    return _date_to_serial(_add_months(d, int(_to_number(args[1]))))


def _fn_eomonth(args):
    if len(args) != 2:
        raise FormulaError("EOMONTH cần đúng 2 đối số")
    d = _add_months(_serial_to_date(_to_number(args[0])), int(_to_number(args[1])))
    last = calendar.monthrange(d.year, d.month)[1]
    return _date_to_serial(datetime.date(d.year, d.month, last))


def _fn_time(args):
    if len(args) != 3:
        raise FormulaError("TIME cần đúng 3 đối số")
    total = (_to_number(args[0]) * 3600
             + _to_number(args[1]) * 60
             + _to_number(args[2]))
    return (total % 86400) / 86400.0


def _fn_second(args):
    if len(args) != 1:
        raise FormulaError("SECOND cần đúng 1 đối số")
    serial = _to_number(args[0])
    return float(int(round((serial - math.floor(serial)) * 86400)) % 60)


def _fn_days(args):
    if len(args) != 2:
        raise FormulaError("DAYS cần đúng 2 đối số")
    return float(int(_to_number(args[0])) - int(_to_number(args[1])))


def _fn_datevalue(args):
    if len(args) != 1:
        raise FormulaError("DATEVALUE cần đúng 1 đối số")
    s = _text(args[0]).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return _date_to_serial(datetime.datetime.strptime(s, fmt).date())
        except ValueError:
            continue
    raise FormulaError("DATEVALUE: không nhận dạng được ngày", ERR_VALUE)


def _week_pos(d: datetime.date, sunday_start: bool) -> int:
    """Vị trí (0..6) của ngày trong tuần. sunday_start=True: CN=0..T7=6."""
    if sunday_start:
        return d.isoweekday() % 7      # T2=1..T7=6, CN=0
    return d.isoweekday() - 1          # T2=0..CN=6


def _fn_weeknum(args):
    if len(args) not in (1, 2):
        raise FormulaError("WEEKNUM cần 1 hoặc 2 đối số")
    d = _serial_to_date(_to_number(args[0]))
    rtype = int(_to_number(args[1])) if len(args) == 2 else 1
    if rtype == 21:
        return float(d.isocalendar()[1])
    if rtype not in (1, 2):
        raise FormulaError("WEEKNUM: type chỉ hỗ trợ 1, 2, 21", ERR_NUM)
    jan1 = datetime.date(d.year, 1, 1)
    sunday_start = rtype == 1
    offset = _week_pos(jan1, sunday_start)
    return float(((d - jan1).days + offset) // 7 + 1)


def _fn_isoweeknum(args):
    if len(args) != 1:
        raise FormulaError("ISOWEEKNUM cần đúng 1 đối số")
    return float(_serial_to_date(_to_number(args[0])).isocalendar()[1])


# --- logic LƯỜI bổ sung (đối số chỉ tính khi cần) ---


def _fn_iserror_lazy(thunks):
    if len(thunks) != 1:
        raise FormulaError("ISERROR cần đúng 1 đối số")
    try:
        thunks[0]()
        return False
    except FormulaError:
        return True


def _fn_iserr_lazy(thunks):
    if len(thunks) != 1:
        raise FormulaError("ISERR cần đúng 1 đối số")
    try:
        thunks[0]()
        return False
    except FormulaError as exc:
        return getattr(exc, "etype", ERR_VALUE) != ERR_NA


def _fn_isna_lazy(thunks):
    if len(thunks) != 1:
        raise FormulaError("ISNA cần đúng 1 đối số")
    try:
        thunks[0]()
        return False
    except FormulaError as exc:
        return getattr(exc, "etype", ERR_VALUE) == ERR_NA


def _fn_ifna_lazy(thunks):
    if len(thunks) != 2:
        raise FormulaError("IFNA cần đúng 2 đối số")
    try:
        return thunks[0]()
    except FormulaError as exc:
        if getattr(exc, "etype", ERR_VALUE) == ERR_NA:
            return thunks[1]()
        raise


def _fn_switch_lazy(thunks):
    if len(thunks) < 3:
        raise FormulaError("SWITCH cần biểu_thức + ít nhất 1 cặp (giá_trị, kết_quả)")
    expr = thunks[0]()
    i = 1
    while i + 1 < len(thunks):
        if _loose_equal(expr, thunks[i]()):
            return thunks[i + 1]()
        i += 2
    if i < len(thunks):  # thunk lẻ cuối = giá trị mặc định
        return thunks[i]()
    raise FormulaError("SWITCH: không khớp và không có mặc định", ERR_NA)


_FUNCTIONS: dict[str, Callable] = {
    "SUM": _fn_sum,
    "AVERAGE": _fn_average,
    "AVG": _fn_average,
    "MIN": _fn_min,
    "MAX": _fn_max,
    "COUNT": _fn_count,
    "COUNTA": _fn_counta,
    "COUNTBLANK": _fn_countblank,
    "ABS": _fn_abs,
    "ROUND": _fn_round,
    "ROUNDUP": _fn_roundup,
    "ROUNDDOWN": _fn_rounddown,
    "SQRT": _fn_sqrt,
    "INT": _fn_int,
    "MOD": _fn_mod,
    "POWER": _fn_power,
    "CONCAT": _fn_concat,
    "CONCATENATE": _fn_concat,
    "RAND": _fn_rand,
    "RANDOM": _fn_rand,
    "RANDBETWEEN": _fn_randbetween,
    # logic
    "AND": _fn_and,
    "OR": _fn_or,
    "NOT": _fn_not,
    "TRUE": _fn_true,
    "FALSE": _fn_false,
    # thống kê có điều kiện
    "COUNTIF": _fn_countif,
    "COUNTIFS": _fn_countifs,
    "SUMIF": _fn_sumif,
    "SUMIFS": _fn_sumifs,
    "AVERAGEIF": _fn_averageif,
    # tra cứu
    "VLOOKUP": _fn_vlookup,
    "HLOOKUP": _fn_hlookup,
    "INDEX": _fn_index,
    "MATCH": _fn_match,
    "LOOKUP": _fn_lookup,
    # chuỗi
    "LEFT": _fn_left,
    "RIGHT": _fn_right,
    "MID": _fn_mid,
    "LEN": _fn_len,
    "TRIM": _fn_trim,
    "UPPER": _fn_upper,
    "LOWER": _fn_lower,
    "PROPER": _fn_proper,
    "REPT": _fn_rept,
    "REPLACE": _fn_replace,
    "SUBSTITUTE": _fn_substitute,
    "FIND": _fn_find,
    "SEARCH": _fn_search,
    "VALUE": _fn_value,
    "TEXT": _fn_text,
    # toán bổ sung
    "CEILING": _fn_ceiling,
    "FLOOR": _fn_floor,
    "TRUNC": _fn_trunc,
    "SIGN": _fn_sign,
    "PRODUCT": _fn_product,
    "SUMPRODUCT": _fn_sumproduct,
    "PI": _fn_pi,
    "EXP": _fn_exp,
    "LOG": _fn_log,
    "LN": _fn_ln,
    # ngày/giờ
    "TODAY": _fn_today,
    "NOW": _fn_now,
    "DATE": _fn_date,
    "YEAR": _fn_year,
    "MONTH": _fn_month,
    "DAY": _fn_day,
    "HOUR": _fn_hour,
    "MINUTE": _fn_minute,
    "WEEKDAY": _fn_weekday,
    "DATEDIF": _fn_datedif,
    # thống kê
    "MEDIAN": _fn_median,
    "MODE": _fn_mode,
    "STDEV": _fn_stdev,
    "VAR": _fn_var,
    "LARGE": _fn_large,
    "SMALL": _fn_small,
    "RANK": _fn_rank,
    # === v0.11.3: thông tin ===
    "ISNUMBER": _fn_isnumber,
    "ISTEXT": _fn_istext,
    "ISNONTEXT": _fn_isnontext,
    "ISBLANK": _fn_isblank,
    "ISLOGICAL": _fn_islogical,
    "ISEVEN": _fn_iseven,
    "ISODD": _fn_isodd,
    "NA": _fn_na,
    # === v0.11.3: logic ===
    "XOR": _fn_xor,
    # === v0.11.3: chuỗi ===
    "TEXTJOIN": _fn_textjoin,
    "EXACT": _fn_exact,
    "CHAR": _fn_char,
    "UNICHAR": _fn_unichar,
    "CODE": _fn_code,
    "UNICODE": _fn_unicode,
    "CLEAN": _fn_clean,
    "T": _fn_t,
    "FIXED": _fn_fixed,
    # === v0.11.3: tra cứu ===
    "CHOOSE": _fn_choose,
    "XLOOKUP": _fn_xlookup,
    # === v0.11.3: toán/lượng giác ===
    "SIN": _math1("SIN", math.sin),
    "COS": _math1("COS", math.cos),
    "TAN": _math1("TAN", math.tan),
    "ASIN": _math1("ASIN", math.asin),
    "ACOS": _math1("ACOS", math.acos),
    "ATAN": _math1("ATAN", math.atan),
    "SINH": _math1("SINH", math.sinh),
    "COSH": _math1("COSH", math.cosh),
    "TANH": _math1("TANH", math.tanh),
    "LOG10": _math1("LOG10", math.log10),
    "ATAN2": _fn_atan2,
    "DEGREES": _fn_degrees,
    "RADIANS": _fn_radians,
    "GCD": _fn_gcd,
    "LCM": _fn_lcm,
    "FACT": _fn_fact,
    "COMBIN": _fn_combin,
    "PERMUT": _fn_permut,
    "MROUND": _fn_mround,
    "EVEN": _fn_even,
    "ODD": _fn_odd,
    "QUOTIENT": _fn_quotient,
    "SUMSQ": _fn_sumsq,
    # === v0.11.3: thống kê ===
    "AVERAGEIFS": _fn_averageifs,
    "MAXIFS": _fn_maxifs,
    "MINIFS": _fn_minifs,
    "STDEVP": _fn_stdevp,
    "VARP": _fn_varp,
    "GEOMEAN": _fn_geomean,
    "HARMEAN": _fn_harmean,
    "AVERAGEA": _fn_averagea,
    # === v0.11.3: ngày/giờ ===
    "EDATE": _fn_edate,
    "EOMONTH": _fn_eomonth,
    "TIME": _fn_time,
    "SECOND": _fn_second,
    "DAYS": _fn_days,
    "DATEVALUE": _fn_datevalue,
    "WEEKNUM": _fn_weeknum,
    "ISOWEEKNUM": _fn_isoweeknum,
}

# Hàm tính lười: nhận danh sách thunk (đối số chưa tính), tự quyết định
# cái nào cần tính. Nhờ vậy IF không tính nhánh thừa, IFERROR bắt được lỗi.
_LAZY_FUNCTIONS: dict[str, Callable] = {
    "IF": _fn_if_lazy,
    "IFERROR": _fn_iferror_lazy,
    "IFS": _fn_ifs_lazy,
    # === v0.11.3: bắt lỗi (cần tính lười để bắt được FormulaError) ===
    "ISERROR": _fn_iserror_lazy,
    "ISERR": _fn_iserr_lazy,
    "ISNA": _fn_isna_lazy,
    "IFNA": _fn_ifna_lazy,
    "SWITCH": _fn_switch_lazy,
}


def _make_thunk(tokens: list, resolver):
    """Tạo hàm trì hoãn: chỉ tính biểu thức từ ``tokens`` khi được gọi."""
    def thunk():
        if not tokens:
            return ""
        return _Parser(list(tokens), resolver).parse()
    return thunk


# ---------------------------------------------------------------- parser


class _Parser:
    """Recursive-descent parser tính trực tiếp giá trị."""

    def __init__(self, tokens: list[_Token], resolver: Callable[[int, int], object]):
        self.tokens = tokens
        self.pos = 0
        self.resolver = resolver

    # --- tiện ích duyệt token ---
    def _peek(self) -> _Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> _Token:
        tok = self._peek()
        if tok is None:
            raise FormulaError("Công thức kết thúc đột ngột")
        self.pos += 1
        return tok

    def _expect_op(self, op: str):
        tok = self._peek()
        if tok is None or tok.kind != "OP" or tok.value != op:
            raise FormulaError(f"Thiếu '{op}'")
        self.pos += 1

    # --- văn phạm ---
    def parse(self):
        value = self._comparison()
        if self._peek() is not None:
            raise FormulaError(f"Token thừa: {self._peek().value!r}")
        return value

    def _comparison(self):
        value = self._expr()
        tok = self._peek()
        if tok and tok.kind == "OP" and tok.value in ("=", "<>", "<", ">", "<=", ">="):
            self.pos += 1
            rhs = self._expr()
            return _compare(value, tok.value, rhs)
        return value

    def _expr(self):
        value = self._term()
        while True:
            tok = self._peek()
            if tok and tok.kind == "OP" and tok.value in "+-":
                self.pos += 1
                rhs = self._term()
                if tok.value == "+":
                    value = _to_number(value) + _to_number(rhs)
                else:
                    value = _to_number(value) - _to_number(rhs)
            else:
                return value

    def _term(self):
        value = self._power()
        while True:
            tok = self._peek()
            if tok and tok.kind == "OP" and tok.value in "*/":
                self.pos += 1
                rhs = self._power()
                if tok.value == "*":
                    value = _to_number(value) * _to_number(rhs)
                else:
                    d = _to_number(rhs)
                    if d == 0:
                        raise FormulaError("Chia cho 0", ERR_DIV0)
                    value = _to_number(value) / d
            else:
                return value

    def _power(self):
        value = self._unary()
        tok = self._peek()
        if tok and tok.kind == "OP" and tok.value == "^":
            self.pos += 1
            rhs = self._power()  # phải-kết hợp
            return _to_number(value) ** _to_number(rhs)
        return value

    def _unary(self):
        tok = self._peek()
        if tok and tok.kind == "OP" and tok.value in "+-":
            self.pos += 1
            val = self._unary()
            return -_to_number(val) if tok.value == "-" else _to_number(val)
        return self._primary()

    def _primary(self):
        tok = self._next()
        if tok.kind == "NUMBER":
            return float(tok.value)
        if tok.kind == "STRING":
            return _unescape(tok.value)
        if tok.kind == "CELL":
            return self._cell_value(tok.value)
        if tok.kind == "SHEETCELL":
            sheet, cell = split_sheet_ref(tok.value)
            row, col = parse_cell_ref(cell)
            return self.resolver(row, col, sheet)
        if tok.kind == "IDENT":
            return self._function_call(tok.value)
        if tok.kind == "OP" and tok.value == "(":
            value = self._comparison()
            self._expect_op(")")
            return value
        raise FormulaError(f"Không mong đợi: {tok.value!r}")

    def _cell_value(self, ref: str):
        row, col = parse_cell_ref(ref)
        return self.resolver(row, col)

    def _function_call(self, name: str):
        fname = name.upper()
        self._expect_op("(")
        if fname in _LAZY_FUNCTIONS:
            thunks = self._lazy_args()
            self._expect_op(")")
            return _LAZY_FUNCTIONS[fname](thunks)
        if fname not in _FUNCTIONS:
            raise FormulaError(f"Hàm không hỗ trợ: {name}", ERR_NAME)
        args: list = []
        if not (self._peek() and self._peek().kind == "OP" and self._peek().value == ")"):
            args.extend(self._arg())
            while self._peek() and self._peek().kind == "OP" and self._peek().value == ",":
                self.pos += 1
                args.extend(self._arg())
        self._expect_op(")")
        return _FUNCTIONS[fname](args)

    def _arg(self) -> list:
        """Một đối số: có thể là vùng A1:B3 (mở rộng) hoặc một biểu thức."""
        tok = self._peek()
        nxt = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
        if tok and tok.kind == "CELL" and nxt and nxt.kind == "OP" and nxt.value == ":":
            start = tok.value
            self.pos += 2  # bỏ qua CELL và ':'
            end_tok = self._next()
            if end_tok.kind != "CELL":
                raise FormulaError("Vùng không hợp lệ")
            return [self._expand_range(start, end_tok.value)]
        # Vùng chéo sheet: Sheet1!A1:B3 (sheet áp cho cả vùng, đầu cuối cùng sheet).
        if tok and tok.kind == "SHEETCELL" and nxt and nxt.kind == "OP" and nxt.value == ":":
            sheet, start_cell = split_sheet_ref(tok.value)
            self.pos += 2
            end_tok = self._next()
            if end_tok.kind != "CELL":
                raise FormulaError("Vùng không hợp lệ")
            return [self._expand_range(start_cell, end_tok.value, sheet)]
        return [self._comparison()]

    def _expand_range(self, start: str, end: str, sheet: str | None = None) -> _Range:
        r1, c1 = parse_cell_ref(start)
        r2, c2 = parse_cell_ref(end)
        r1, r2 = sorted((r1, r2))
        c1, c2 = sorted((c1, c2))
        if sheet is None:
            rows = [[self.resolver(r, c) for c in range(c1, c2 + 1)]
                    for r in range(r1, r2 + 1)]
        else:
            rows = [[self.resolver(r, c, sheet) for c in range(c1, c2 + 1)]
                    for r in range(r1, r2 + 1)]
        return _Range(rows)

    # --- đối số tính lười (cho IF/IFERROR/IFS) ---
    def _lazy_args(self) -> list:
        """Cắt từng đối số thành thunk (chưa tính), tôn trọng ngoặc lồng nhau."""
        thunks: list = []
        if self._peek() and self._peek().kind == "OP" and self._peek().value == ")":
            return thunks
        while True:
            thunks.append(_make_thunk(self._collect_one_arg(), self.resolver))
            tok = self._peek()
            if tok and tok.kind == "OP" and tok.value == ",":
                self.pos += 1
                continue
            break
        return thunks

    def _collect_one_arg(self) -> list:
        """Gom token của một đối số tới dấu ',' hoặc ')' ở cấp ngoài cùng."""
        depth = 0
        toks: list = []
        while True:
            tok = self._peek()
            if tok is None:
                break
            if tok.kind == "OP" and tok.value == "(":
                depth += 1
            elif tok.kind == "OP" and tok.value == ")":
                if depth == 0:
                    break
                depth -= 1
            elif tok.kind == "OP" and tok.value == "," and depth == 0:
                break
            toks.append(tok)
            self.pos += 1
        return toks


def _compare(left, op: str, right) -> bool:
    """So sánh hai giá trị: ưu tiên số, nếu không thì so sánh chuỗi."""
    try:
        a, b = _to_number(left), _to_number(right)
    except FormulaError:
        a, b = str(left), str(right)
    if op == "=":
        return a == b
    if op == "<>":
        return a != b
    if op == "<":
        return a < b
    if op == ">":
        return a > b
    if op == "<=":
        return a <= b
    if op == ">=":
        return a >= b
    raise FormulaError(f"Toán tử so sánh lạ: {op}")


def _unescape(literal: str) -> str:
    return literal[1:-1].replace('\\"', '"').replace("\\\\", "\\")


# ---------------------------------------------------------------- API công khai


def is_formula(text) -> bool:
    return isinstance(text, str) and text.startswith("=") and len(text) > 1


_OFFSET_CELL_RE = re.compile(r"^(\$?)([A-Za-z]+)(\$?)(\d+)$")


def _offset_cell(ref: str, drow: int, dcol: int) -> str:
    """Dịch một tham chiếu ô theo (drow, dcol); giữ nguyên phần có dấu $."""
    m = _OFFSET_CELL_RE.match(ref)
    if not m:
        return ref
    col_abs, col_letters, row_abs, row_num = m.groups()
    col = col_letters_to_index(col_letters)
    row = int(row_num) - 1
    if not col_abs:
        col = max(0, col + dcol)
    if not row_abs:
        row = max(0, row + drow)
    return f"{col_abs}{col_index_to_letters(col)}{row_abs}{row + 1}"


def offset_formula(formula_text: str, drow: int, dcol: int) -> str:
    """Trả về công thức với mọi tham chiếu tương đối đã dịch (kiểu kéo-điền Excel).

    Tham chiếu có dấu $ (tuyệt đối) không bị dịch. Nếu không phân tích được
    thì trả về nguyên văn.
    """
    body = formula_text[1:] if formula_text.startswith("=") else formula_text
    try:
        tokens = _tokenize(body)
    except FormulaError:
        return formula_text
    parts = []
    for t in tokens:
        if t.kind == "CELL":
            parts.append(_offset_cell(t.value, drow, dcol))
        elif t.kind == "SHEETCELL":
            sheet, cell = split_sheet_ref(t.value)
            # Giữ nguyên tên sheet (kèm nháy nếu vốn có), chỉ dịch phần ô.
            prefix = t.value[: t.value.index("!") + 1]
            parts.append(prefix + _offset_cell(cell, drow, dcol))
        else:
            parts.append(t.value)
    return "=" + "".join(parts)


_BARE_SHEET_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def rename_sheet_refs(formula_str: str, old_name: str, new_name: str) -> str:
    """Đổi tên sheet trong mọi tham chiếu chéo (Sheet2!A1 -> Data!A1).

    Trả nguyên văn nếu công thức không đụng tới ``old_name`` (giữ định dạng gốc).
    """
    body = formula_str[1:] if formula_str.startswith("=") else formula_str
    try:
        tokens = _tokenize(body)
    except FormulaError:
        return formula_str
    low = old_name.strip().lower()
    quoted_new = new_name if _BARE_SHEET_RE.match(new_name) else f"'{new_name}'"
    out, changed = [], False
    for t in tokens:
        if t.kind == "SHEETCELL":
            sheet, cell = split_sheet_ref(t.value)
            if sheet.lower() == low:
                out.append(f"{quoted_new}!{cell}")
                changed = True
                continue
        out.append(t.value)
    return ("=" + "".join(out)) if changed else formula_str


def has_external_ref(formula_str: str) -> bool:
    """True nếu công thức có tham chiếu chéo sheet (Sheet1!A1)."""
    body = formula_str[1:] if formula_str.startswith("=") else formula_str
    try:
        return any(t.kind == "SHEETCELL" for t in _tokenize(body))
    except FormulaError:
        return False


def extract_refs(formula_str: str) -> set[tuple[int, int]]:
    """Quét token của công thức, trả về tập (row, col) được tham chiếu.

    Không parse đầy đủ — chỉ tìm mẫu CELL và CELL:CELL trong danh sách token.
    Công thức không hợp lệ trả về set rỗng (không raise).
    """
    body = formula_str[1:] if formula_str.startswith("=") else formula_str
    try:
        tokens = _tokenize(body)
    except FormulaError:
        return set()
    refs: set[tuple[int, int]] = set()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.kind == "CELL":
            # Kiểm tra mẫu range: CELL ':' CELL
            if (
                i + 2 < len(tokens)
                and tokens[i + 1].kind == "OP"
                and tokens[i + 1].value == ":"
                and tokens[i + 2].kind == "CELL"
            ):
                try:
                    r1, c1 = parse_cell_ref(tok.value)
                    r2, c2 = parse_cell_ref(tokens[i + 2].value)
                    r1, r2 = sorted((r1, r2))
                    c1, c2 = sorted((c1, c2))
                    for r in range(r1, r2 + 1):
                        for c in range(c1, c2 + 1):
                            refs.add((r, c))
                except FormulaError:
                    pass
                i += 3
            else:
                try:
                    refs.add(parse_cell_ref(tok.value))
                except FormulaError:
                    pass
                i += 1
        else:
            i += 1
    return refs


def _finalize(value):
    """Chuẩn hóa kết quả cuối trước khi trả cho ô.

    - Vùng 1 ô -> giá trị ô đó; vùng nhiều ô -> #VALUE! (engine scalar, chưa
      hỗ trợ spill) — tránh hiển thị repr ``<_Range object>`` (vd CHOOSE/IF).
    - Số inf/nan (tràn số, vd POWER/SUMSQ) -> #NUM! thay vì hiện 'inf'.
    """
    if isinstance(value, _Range):
        flat = value.flat()
        if len(flat) == 1:
            value = flat[0]
        else:
            raise FormulaError("Kết quả là vùng nhiều ô (chưa hỗ trợ spill)", ERR_VALUE)
    if isinstance(value, float) and not math.isfinite(value):
        raise FormulaError("Kết quả không hữu hạn", ERR_NUM)
    return value


def evaluate(formula: str, resolver: Callable[[int, int], object]):
    """Tính một công thức (đã có dấu '=') và trả về số hoặc chuỗi."""
    body = formula[1:] if formula.startswith("=") else formula
    tokens = _tokenize(body)
    if not tokens:
        raise FormulaError("Công thức rỗng")
    return _finalize(_Parser(tokens, resolver).parse())
