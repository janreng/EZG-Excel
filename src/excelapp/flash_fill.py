"""Flash Fill (Ctrl+E): suy ra phép biến đổi từ ví dụ người dùng gõ rồi điền nốt.

Thuần (không Qt) nên kiểm thử headless được. An toàn: nếu chương trình suy ra
KHÔNG tái tạo đúng MỌI ví dụ đã cho thì trả None (không điền bừa).

Hỗ trợ:
- Biến đổi cả chuỗi: in hoa / in thường / viết hoa đầu từ / cắt khoảng trắng / nguyên.
- Ghép lại theo token: tách nguồn theo khoảng trắng, sắp xếp lại token + chèn chữ
  cố định (vd "John Smith" -> "Smith, John", lấy token, thêm hậu tố...).
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def _tokens(s: str) -> list[str]:
    return [t for t in _WS.split(s.strip()) if t]


def _decompose(tokens: list[str], out: str):
    """Phân rã ``out`` thành chuỗi mảnh ('tok', idx) | ('lit', text) từ token nguồn."""
    by_len = sorted({t for t in tokens if t}, key=len, reverse=True)
    prog: list[tuple] = []
    lit: list[str] = []
    pos = 0
    while pos < len(out):
        match = next((t for t in by_len if out.startswith(t, pos)), None)
        if match is not None:
            if lit:
                prog.append(("lit", "".join(lit)))
                lit = []
            prog.append(("tok", tokens.index(match)))
            pos += len(match)
        else:
            lit.append(out[pos])
            pos += 1
    if lit:
        prog.append(("lit", "".join(lit)))
    return prog or None


def _apply(prog, tokens: list[str]):
    parts = []
    for kind, v in prog:
        if kind == "lit":
            parts.append(v)
        else:
            if v >= len(tokens):
                return None
            parts.append(tokens[v])
    return "".join(parts)


_WHOLE = (
    lambda s: s,
    lambda s: s.upper(),
    lambda s: s.lower(),
    lambda s: s.title(),
    lambda s: s.strip(),
)


def infer_and_fill(sources: list[str], examples: dict[int, str]):
    """Suy phép biến đổi từ ``examples`` (row -> output) rồi áp cho mọi ``sources``.

    Trả danh sách output cùng độ dài ``sources``, hoặc None nếu không suy được /
    không nhất quán với mọi ví dụ.
    """
    items = [(i, out) for i, out in examples.items() if 0 <= i < len(sources)]
    if not items:
        return None

    # 1) Biến đổi cả chuỗi.
    for f in _WHOLE:
        if all(f(sources[i]) == out for i, out in items):
            return [f(s) for s in sources]

    # 2) Ghép token + chữ cố định, suy từ ví dụ đầu, KIỂM CHỨNG trên mọi ví dụ.
    i0, out0 = items[0]
    prog = _decompose(_tokens(sources[i0]), out0)
    if prog is None:
        return None
    for i, out in items:
        if _apply(prog, _tokens(sources[i])) != out:
            return None
    result = []
    for s in sources:
        v = _apply(prog, _tokens(s))
        if v is None:
            return None
        result.append(v)
    return result
