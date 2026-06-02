"""Đọc/ghi file CSV và XLSX về dạng lưới (list[list[str]])."""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl


def _normalize(rows: list[list], min_cols: int = 1) -> list[list[str]]:
    """Chuẩn hóa thành ma trận chữ nhật toàn chuỗi."""
    rows = [[("" if v is None else str(v)) for v in row] for row in rows]
    width = max([len(r) for r in rows] + [min_cols])
    for r in rows:
        r.extend([""] * (width - len(r)))
    if not rows:
        rows = [[""] * width]
    return rows


def load_csv(path: str | Path) -> list[list[str]]:
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(f, dialect))
    return _normalize(rows)


def save_csv(path: str | Path, rows: list[list[str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(rows)


def load_xlsx(path: str | Path) -> list[list[str]]:
    # data_only=False để giữ nguyên công thức (=...) — app tự tính lại.
    wb = openpyxl.load_workbook(path, data_only=False, read_only=True)
    ws = wb.active
    rows = [list(row) for row in ws.iter_rows(values_only=True)]
    wb.close()
    return _normalize(rows)


def save_xlsx(path: str | Path, rows: list[list[str]]) -> None:
    from .formula import is_formula

    wb = openpyxl.Workbook()
    ws = wb.active
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row, start=1):
            if value == "":
                continue
            cell = ws.cell(row=r, column=c)
            # Công thức của app dùng cú pháp tương thích Excel -> ghi thẳng.
            if is_formula(value):
                cell.value = value
            else:
                num = _try_number(value)
                cell.value = num if num is not None else value
    wb.save(path)


def _try_number(text: str):
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except (ValueError, TypeError):
        return None


def load_file(path: str | Path) -> list[list[str]]:
    """Tự nhận định dạng theo phần mở rộng."""
    suffix = Path(path).suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        return load_xlsx(path)
    if suffix in (".csv", ".txt", ".tsv"):
        return load_csv(path)
    raise ValueError(f"Định dạng không hỗ trợ: {suffix}")


def save_file(path: str | Path, rows: list[list[str]]) -> None:
    suffix = Path(path).suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        save_xlsx(path, rows)
    elif suffix in (".csv", ".txt", ".tsv"):
        save_csv(path, rows)
    else:
        raise ValueError(f"Định dạng không hỗ trợ: {suffix}")
