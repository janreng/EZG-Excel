"""Một engine công thức nhỏ kiểu Excel.

Hỗ trợ:
  - Số, chuỗi ("..."), toán tử + - * / ^ và ngoặc ().
  - Tham chiếu ô kiểu A1 và vùng A1:B3.
  - Các hàm: SUM, AVERAGE/AVG, MIN, MAX, COUNT, ABS, ROUND,
             SQRT, INT, MOD, POWER, IF, CONCAT/CONCATENATE,
             RAND/RANDOM, RANDBETWEEN.

Công thức là chuỗi bắt đầu bằng dấu '='. Việc lấy giá trị ô do
``resolver(row, col)`` đảm nhiệm (trả về số/chuỗi đã tính xong).
"""

from __future__ import annotations

import random
import re
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


def _numbers(args) -> list[float]:
    """Lấy các giá trị số, bỏ qua ô rỗng / không phải số."""
    out = []
    for a in args:
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


def _fn_if(args):
    if len(args) != 3:
        raise FormulaError("IF cần đúng 3 đối số: IF(điều_kiện, đúng, sai)")
    cond = args[0]
    truthy = _to_number(cond) != 0 if not isinstance(cond, str) else cond.strip() != ""
    return args[1] if truthy else args[2]


def _fn_concat(args):
    def s(v):
        if v is None:
            return ""
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    return "".join(s(a) for a in args)


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


_FUNCTIONS: dict[str, Callable] = {
    "SUM": _fn_sum,
    "AVERAGE": _fn_average,
    "AVG": _fn_average,
    "MIN": _fn_min,
    "MAX": _fn_max,
    "COUNT": _fn_count,
    "ABS": _fn_abs,
    "ROUND": _fn_round,
    "SQRT": _fn_sqrt,
    "INT": _fn_int,
    "MOD": _fn_mod,
    "POWER": _fn_power,
    "IF": _fn_if,
    "CONCAT": _fn_concat,
    "CONCATENATE": _fn_concat,
    "RAND": _fn_rand,
    "RANDOM": _fn_rand,
    "RANDBETWEEN": _fn_randbetween,
}


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
        if fname not in _FUNCTIONS:
            raise FormulaError(f"Hàm không hỗ trợ: {name}")
        self._expect_op("(")
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
            return self._expand_range(start, end_tok.value)
        return [self._comparison()]

    def _expand_range(self, start: str, end: str) -> list:
        r1, c1 = parse_cell_ref(start)
        r2, c2 = parse_cell_ref(end)
        r1, r2 = sorted((r1, r2))
        c1, c2 = sorted((c1, c2))
        values = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                values.append(self.resolver(r, c))
        return values


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
