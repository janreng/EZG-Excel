# SPEC 31 — Named Ranges (Name Manager)

## Mục tiêu
Đặt tên cho ô / range / constant / formula → dùng trong formula thay địa chỉ. Quản lý qua Name Manager.

## Trạng thái hiện tại
- ✗ Chưa có (Name Box hiện chỉ navigate, không show named ranges dropdown).
- [Spec 04](04-name-box-formula-bar.md) đề cập dropdown Name Box list named ranges.
- [Spec 12](12-formula-system.md) mention `=SUM(DoanhThu)`.

## 31.1 Tạo Named Range

### Cách 1: Name Box
- Chọn range → click Name Box → gõ tên (vd `DoanhThu`) → Enter.
- ⚠ Phải Enter, không phải click ngoài.

### Cách 2: Formulas → Define Name
- Formulas → Defined Names → Define Name → dialog:
  - Name
  - Scope: Workbook / Sheet1 / Sheet2 (sheet-scope vs global)
  - Comment
  - Refers to: range / constant / formula

### Cách 3: Create from Selection (Ctrl+Shift+F3)
- Chọn range gồm header + data (vd A1:B10 với header A1, B1).
- Ctrl+Shift+F3 → dialog "Create names from values in":
  - Top row ✓ / Bottom row / Left column / Right column
- OK → tạo named ranges dựa trên header.

## 31.2 Name Manager (Ctrl+F3)

Dialog list tất cả names:

```
┌─ Name Manager ─────────────────────────────────────────────┐
│ [New...] [Edit...] [Delete]   Filter: [All Names      ▼]  │
│ ─────────────────────────────────────────────────────────  │
│ Name      | Value          | Refers To                 | Scope    | Comment │
│ DoanhThu  | {100;200;300}  | =Sheet1!$A$1:$A$10        | Workbook | ...    │
│ Tax_Rate  | 0.1            | =0.1                       | Workbook |        │
│ SubTotal  | #VALUE!        | =SUM(DoanhThu)*0.9        | Workbook |        │
│ ─────────────────────────────────────────────────────────  │
│ Refers to:                                                  │
│ [=Sheet1!$A$1:$A$10                                      ] │
│                                            [Close]          │
└────────────────────────────────────────────────────────────┘
```

- Filter dropdown: All Names / Names Scoped to Worksheet / Names Scoped to Workbook / Names with Errors / Names without Errors / Defined Names / Table Names.
- Sortable columns.
- Edit/Delete inline.
- "Refers to" textbox edit at bottom với commit ✓/cancel ✗ buttons.

## 31.3 Name rules

- Đầu = letter, underscore `_`, hoặc backslash `\`.
- Sau = letter, digit, `.`, `_`, `?`.
- KHÔNG được: space (dùng `_`), cell reference syntax (`A1`, `R1C1`), single letter `C`, `c`, `R`, `r`.
- Max 255 chars.
- Case-insensitive (`DoanhThu` = `DOANHTHU` = `doanhthu`).
- Trùng tên + cùng scope → error.

## 31.4 Refers to syntax

| Loại | Ví dụ |
|---|---|
| Cell | `=Sheet1!$A$1` |
| Range | `=Sheet1!$A$1:$B$10` |
| Multi-range | `=Sheet1!$A$1,Sheet1!$C$1:$D$5` |
| Constant | `=0.1` / `="VAT"` / `={1,2,3}` |
| Formula | `=OFFSET(Sheet1!$A$1,0,0,COUNTA(Sheet1!$A:$A),1)` (dynamic) |
| Cross-sheet | `=Sheet2!$A$1` |
| Table reference | `=Table1[Col1]` |
| 3D | `=Sheet1:Sheet3!$A$1` |

## 31.5 Dùng trong formula

- `=SUM(DoanhThu)` thay `=SUM(Sheet1!$A$1:$A$10)`.
- Autocomplete: gõ `=DOAN` → dropdown gợi ý `DoanhThu` cùng functions ([Spec 04](04-name-box-formula-bar.md)).
- Trong Name Box: gõ `DoanhThu` + Enter → navigate đến range.

## 31.6 Paste List (Formulas → Use in Formula → Paste Names → Paste List)

Paste bảng list các names vào sheet (cột Name, cột Refers To).

## 31.7 Apply Names

Formulas → Defined Names → dropdown → Apply Names: convert references trong existing formulas thành named ranges nếu match.

## Model

```python
class NamedRange:
    name: str
    refers_to: str          # raw formula string
    scope: "workbook" | sheet_id
    comment: str
    hidden: bool            # true → không hiển thị trong Name Manager (system names)
```

Workbook: `_names: list[NamedRange]`.
Sheet: subset của workbook names + sheet-scoped.

## Resolver

- Formula engine: trước khi parse cell ref, check named ranges:
  - Token IDENT → look up in `(sheet_id, name)` rồi `("workbook", name)` → resolve to refers_to → evaluate.
  - Cache resolved range (invalidate khi name đổi).
- Circular: name A refers to formula chứa name A → error.

## Acceptance criteria
1. Chọn A1:A10, Name Box gõ `DoanhThu` + Enter → tạo named range.
2. Ctrl+F3 → Name Manager hiện `DoanhThu` với Refers to `=Sheet1!$A$1:$A$10`.
3. Trong B1 gõ `=SUM(DoanhThu)` → ra tổng đúng.
4. Edit DoanhThu → đổi sang `=Sheet1!$A$1:$A$5` → B1 recompute.
5. Define Name `VAT` = `=0.1` (constant) → `=A1*VAT` ra A1 * 0.1.
6. Ctrl+Shift+F3 trên A1:C10 (row 1 = headers Q1, Q2, Q3) → 3 names tạo: `Q1`=A2:A10, `Q2`=B2:B10, `Q3`=C2:C10.
7. Tên invalid `1Name` (bắt đầu số) → error message.
8. Trong Name Box gõ `DoanhThu` + Enter → navigate đến A1:A10.
9. Paste List vào D1 → bảng 2 cột (Name, Refers To).

## Phụ thuộc
- [04 Name Box / Formula Bar](04-name-box-formula-bar.md) — Name Box dropdown.
- [12 Formula System](12-formula-system.md) — resolver.
- [10 Sheet Tabs](10-sheet-tabs.md) — sheet-scoped names.

## Risk
Trung bình. Edge case: name shadow cell reference (vd ai đó đặt name = `A1`); name circular reference.
