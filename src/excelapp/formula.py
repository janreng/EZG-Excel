"""Một engine công thức nhỏ kiểu Excel.

Hỗ trợ:
  - Số, chuỗi ("..."), toán tử + - * / ^ và ngoặc ().
  - Tham chiếu ô kiểu A1 và vùng A1:B3 (vùng 2 chiều cho VLOOKUP/INDEX...).
  - ~60 hàm: gộp (SUM, AVERAGE, MIN, MAX, COUNT...), logic (IF, AND, OR,
    NOT, IFERROR, IFS), điều kiện (COUNTIF, SUMIF, COUNTIFS, SUMIFS...),
    tra cứu (VLOOKUP, HLOOKUP, INDEX, MATCH, LOOKUP), chuỗi (LEFT, RIGHT,
    MID, LEN, TRIM, UPPER, LOWER, SUBSTITUTE...), toán (CEILING, FLOOR,
    PRODUCT, SUMPRODUCT, LOG...), ngày/giờ (TODAY, NOW, DATE, YEAR...),
    thống kê (MEDIAN, STDEV, LARGE, SMALL, RANK...).

Công thức là chuỗi bắt đầu bằng dấu '='. Việc lấy giá trị ô do
``resolver(row, col)`` đảm nhiệm (trả về số/chuỗi đã tính xong).
"""

from __future__ import annotations

import datetime
import fnmatch
import math
import random
import re
import statistics
from typing import Callable

# ---------------------------------------------------------------- lỗi


class FormulaError(Exception):
    """Lỗi khi phân tích hoặc tính công thức."""


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


# ---------------------------------------------------------------- tokenizer

_TOKEN_RE = re.compile(
    r"""
      (?P<NUMBER>\d+\.\d+|\d+|\.\d+)
    | (?P<STRING>"(?:[^"\\]|\\.)*")
    | (?P<CELL>\$?[A-Za-z]+\$?\d+)
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
        return float(value)
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        raise FormulaError(f"Không phải số: {value!r}")


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


def _match_criteria(value, criteria) -> bool:
    """So khớp giá trị với tiêu chí kiểu Excel: số, ">5", "<=3", "<>x", "ab*"."""
    if isinstance(criteria, bool):
        return _to_bool(value) == criteria
    if isinstance(criteria, (int, float)):
        try:
            return _to_number(value) == float(criteria)
        except FormulaError:
            return False
    crit = str(criteria)
    op = None
    for o in (">=", "<=", "<>", ">", "<", "="):
        if crit.startswith(o):
            op, crit = o, crit[len(o):]
            break
    try:
        crit_num = float(crit)
    except ValueError:
        crit_num = None
    if op in (">", "<", ">=", "<="):
        if crit_num is None:
            return False
        try:
            v = _to_number(value)
        except FormulaError:
            return False
        return {">": v > crit_num, "<": v < crit_num,
                ">=": v >= crit_num, "<=": v <= crit_num}[op]
    if crit_num is not None:
        try:
            eq = _to_number(value) == crit_num
        except FormulaError:
            eq = False
    else:
        eq = fnmatch.fnmatch(_text(value).lower(), crit.lower())
    return (not eq) if op == "<>" else eq


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
        raise FormulaError("SQRT của số âm")
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
        raise FormulaError("MOD chia cho 0")
    return _to_number(args[0]) % b


def _fn_power(args):
    if len(args) != 2:
        raise FormulaError("POWER cần đúng 2 đối số")
    return _to_number(args[0]) ** _to_number(args[1])


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
    return float(sum(1 for v in _crit_values(args[0]) if _match_criteria(v, args[1])))


def _fn_sumif(args):
    if len(args) not in (2, 3):
        raise FormulaError("SUMIF cần 2 hoặc 3 đối số")
    crit_vals = _crit_values(args[0])
    sum_vals = _crit_values(args[2]) if len(args) == 3 else crit_vals
    total = 0.0
    for cv, sv in zip(crit_vals, sum_vals):
        if _match_criteria(cv, args[1]):
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
    picked = []
    for cv, av in zip(crit_vals, avg_vals):
        if _match_criteria(cv, args[1]):
            try:
                picked.append(_to_number(av))
            except FormulaError:
                pass
    if not picked:
        raise FormulaError("AVERAGEIF: không có ô khớp")
    return sum(picked) / len(picked)


def _fn_countifs(args):
    if len(args) < 2 or len(args) % 2 != 0:
        raise FormulaError("COUNTIFS cần các cặp (vùng, tiêu_chí)")
    ranges = [_crit_values(args[i]) for i in range(0, len(args), 2)]
    crits = [args[i + 1] for i in range(0, len(args), 2)]
    n = len(ranges[0])
    return float(sum(
        1 for i in range(n)
        if all(_match_criteria(ranges[k][i], crits[k]) for k in range(len(crits)))
    ))


def _fn_sumifs(args):
    if len(args) < 3 or len(args) % 2 == 0:
        raise FormulaError("SUMIFS cần vùng_tổng + các cặp (vùng, tiêu_chí)")
    sum_vals = _crit_values(args[0])
    ranges = [_crit_values(args[i]) for i in range(1, len(args), 2)]
    crits = [args[i + 1] for i in range(1, len(args), 2)]
    total = 0.0
    for i in range(len(sum_vals)):
        if all(_match_criteria(ranges[k][i], crits[k]) for k in range(len(crits))):
            try:
                total += _to_number(sum_vals[i])
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
            raise FormulaError("VLOOKUP: không tìm thấy")
        return table.rows[best][col_idx - 1]
    for i, v in enumerate(first):
        if _loose_equal(v, key):
            return table.rows[i][col_idx - 1]
    raise FormulaError("VLOOKUP: không tìm thấy")


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
            raise FormulaError("HLOOKUP: không tìm thấy")
        return table.rows[row_idx - 1][best]
    for i, v in enumerate(first):
        if _loose_equal(v, key):
            return table.rows[row_idx - 1][i]
    raise FormulaError("HLOOKUP: không tìm thấy")


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
        raise FormulaError("INDEX: chỉ số vượt phạm vi")
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
        raise FormulaError("MATCH: không tìm thấy")
    best = None
    for i, v in enumerate(vals):
        if (mtype == 1 and _cmp(v, key) <= 0) or (mtype != 1 and _cmp(v, key) >= 0):
            best = i
    if best is None:
        raise FormulaError("MATCH: không tìm thấy")
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
        raise FormulaError("LOOKUP: không tìm thấy")
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
    return _EXCEL_EPOCH + datetime.timedelta(days=int(n))


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
}

# Hàm tính lười: nhận danh sách thunk (đối số chưa tính), tự quyết định
# cái nào cần tính. Nhờ vậy IF không tính nhánh thừa, IFERROR bắt được lỗi.
_LAZY_FUNCTIONS: dict[str, Callable] = {
    "IF": _fn_if_lazy,
    "IFERROR": _fn_iferror_lazy,
    "IFS": _fn_ifs_lazy,
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
                        raise FormulaError("Chia cho 0")
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
            raise FormulaError(f"Hàm không hỗ trợ: {name}")
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
        return [self._comparison()]

    def _expand_range(self, start: str, end: str) -> _Range:
        r1, c1 = parse_cell_ref(start)
        r2, c2 = parse_cell_ref(end)
        r1, r2 = sorted((r1, r2))
        c1, c2 = sorted((c1, c2))
        rows = [[self.resolver(r, c) for c in range(c1, c2 + 1)]
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
    parts = [
        _offset_cell(t.value, drow, dcol) if t.kind == "CELL" else t.value
        for t in tokens
    ]
    return "=" + "".join(parts)


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


def evaluate(formula: str, resolver: Callable[[int, int], object]):
    """Tính một công thức (đã có dấu '=') và trả về số hoặc chuỗi."""
    body = formula[1:] if formula.startswith("=") else formula
    tokens = _tokenize(body)
    if not tokens:
        raise FormulaError("Công thức rỗng")
    return _Parser(tokens, resolver).parse()
