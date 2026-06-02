# SPEC 12 — Formula System (UX nâng cao)

## Mục tiêu
Formula engine không chỉ tính đúng mà còn UX đầy đủ: Function Wizard, autocomplete, ScreenTip, error smart tag, Trace Precedents/Dependents, Evaluate Formula.

## Trạng thái hiện tại
- ✓ Tokenizer + parser recursive-descent (`formula.py`).
- ✓ **~120 hàm vô hướng** (v0.11.3 thêm Information/Logical/Text/Lookup/
  Math-Trig/Stats/Date — xem CHANGELOG & `tests/test_formula_v0113.py`).
  Quyết định scope: chỉ thêm hàm vô hướng, **chưa** kèm metadata cho Function
  Wizard (nợ Phase 4) và **chưa** spill/dynamic array (Phase 6).
- ✓ **Mã lỗi kiểu Excel** (v0.11.3): engine raise & hiển thị 6 mã
  `#DIV/0! #N/A #VALUE! #NUM! #NAME? #REF!` (xem bảng §12.3).
- ✓ `offset_formula` cho fill-down/right.
- ✓ Cache `_eval_cache` per cell.
- ✗ Function Wizard (Shift+F3 / fx button) chưa.
- ✗ Formula autocomplete dropdown — [Spec 04](04-name-box-formula-bar.md).
- ✗ ScreenTip syntax tooltip chưa.
- ✗ Error smart tag (tam giác xanh + dropdown ⚠) chưa.
- ✗ Trace Precedents / Dependents (mũi tên xanh) chưa.
- ✗ Evaluate Formula step-by-step chưa.
- ✗ Watch Window chưa.
- ✗ Show Formulas toggle (Ctrl+\`) chưa.
- ✗ Named Ranges (Name Manager Ctrl+F3) chưa.
- ✗ Dynamic arrays / spill range (FILTER, SORT, UNIQUE, XLOOKUP...) chưa.

## 12.1 Formula entry flow (§12.1)

```
Bước 1: Gõ `=`              → Enter mode, Formula Bar hiện `=`, Cell hiện `=`
Bước 2: Gõ tên hàm (vd SU)  → Autocomplete dropdown xuất hiện dưới ô
Bước 3: Tab chọn SUM        → `=SUM(` tự điền, cursor sau `(`, dropdown đóng
Bước 4: Gõ A1:A10 / click+drag → Point mode khi click/drag, cell tham chiếu tô màu
Bước 5: Gõ `)`              → `=SUM(A1:A10)`
Bước 6: Enter               → Commit, kết quả hiển thị, về Ready
```

## 12.2 Function Wizard (Insert Function Dialog) (§12.2)

### Mở
- Shift+F3 / fx button trên Formula Bar / Formulas → Insert Function.

### Search panel
- "Search for a function": gõ từ khóa → Go → list match.
- "Or select a category": Math & Trig, Statistical, Lookup & Reference, Text, Date & Time, Logical, Financial, Database, Engineering, Information, Compatibility, Web, Cube, User Defined.
- "Select a function": list trong category.
- Description: mô tả ngắn dưới list.
- "Help on this function": link docs (HTML/web local).

### Function Arguments Dialog
Sau khi chọn OK:
- Mỗi argument 1 dòng: Tên + text box + nút Range Picker (↗).
- **Required** in đậm; **Optional** in nghiêng + `[...]`.
- Formula result preview phía dưới (live update).
- Range picker (↗): click → dialog thu nhỏ; chọn vùng → click lại → trở về.

### Implementation note
- Metadata mỗi hàm: name, category, args (name, required, type), description. Tách file `formula_metadata.py` hoặc decorator `@formula(...)`.
- Dialog reuse cùng infrastructure cho VBA `Application.WorksheetFunction.X` (Phase 6).

## 12.3 Error types (§12.3)

| Error | Trạng thái | Nguyên nhân | Fix |
|---|---|---|---|
| `#DIV/0!` | ✓ (v0.11.3) | Mẫu số = 0 (ô trống ở **mẫu số** coi như 0; ô trống ở tử số = 0, không lỗi) | `IF(B1=0,0,A1/B1)` hoặc `IFERROR` |
| `#VALUE!` | ✓ (v0.11.3) | Sai kiểu (số + text), giá trị không hữu hạn | `VALUE()`, check type |
| `#REF!` | ✓ (v0.11.3) | Tham chiếu/chỉ số ngoài phạm vi (vd `INDEX` quá biên) | Update formula |
| `#NAME?` | ✓ (v0.11.3) | Tên hàm không tồn tại (phần *Named Range* chờ Phase 1) | Check spelling |
| `#NULL!` | ✗ chưa | Cần toán tử giao vùng (space) — tokenizer chưa hỗ trợ | — |
| `#NUM!` | ✓ (v0.11.3) | Số không hợp lệ (`SQRT(-1)`), kết quả quá lớn (`FACT(171)`, overflow) | Check input |
| `#N/A` | ✓ (v0.11.3) | VLOOKUP/MATCH/XLOOKUP miss, `NA()` | `IFERROR` / `IFNA` |
| `#SPILL!` | ✗ chưa | Cần dynamic array / spill (Phase 6) | — |
| `#CALC!` | ✗ chưa | Cần dynamic array (Phase 6) | — |
| `#GETTING_DATA` | ✗ chưa | Cần external data | — |

> **Engine hiện raise & hiển thị 6 mã** (✓). 4 mã còn lại gắn với tính năng
> chưa làm (intersection operator / dynamic array / external). `table_model`
> hiển thị `FormulaError.etype`; mặc định `#VALUE!`.

## 12.4 Error smart tag (§12.4)
- Tam giác xanh lá góc trên trái: potential error.
- Click ô → biểu tượng ⚠ trái ô.
- Click ⚠ → dropdown: Error description / Help / Ignore Error / Edit in Formula Bar / Error Checking Options.
- **Circular Reference**: popup khi nhập; Status Bar hiện `Circular References: A5`.

### Detection
- Inconsistent formula: ô trong vùng có formula khác với ô bên cạnh cùng pattern.
- Number stored as text: leading apostrophe `'0123`.
- Formula referring to empty cell.
- Circular reference: build dep graph; nếu insert edge tạo cycle → warning.

## 12.5 Formula Auditing (§12.5)

| Tool | Phím | Mô tả |
|---|---|---|
| Trace Precedents | Formulas → Trace Precedents | Mũi tên xanh từ ô cấp vào |
| Trace Dependents | Formulas → Trace Dependents | Mũi tên xanh đến ô dùng |
| Remove Arrows | Formulas → Remove Arrows | Xóa hết arrow |
| Show Formulas | Ctrl + \` | Toggle hiện formula thay vì kết quả (toàn sheet) |
| Error Checking | Formulas → Error Checking | Duyệt tất cả lỗi |
| Evaluate Formula | Formulas → Evaluate Formula | Tính từng bước (debug) |
| Watch Window | Formulas → Watch Window | Cửa sổ theo dõi ô |

### Implementation note
- Mũi tên: vẽ overlay QGraphicsScene trên grid; start/end là cell center; arrow style chuẩn Excel.
- Evaluate Formula dialog: hiển thị formula, có nút "Step In" (eval sub-formula), "Step Out", "Evaluate", "Restart".
- Watch Window: panel `QDockWidget`; mỗi row = (workbook, sheet, name/cell, value, formula). Refresh khi `dataChanged`.

## Named Ranges (Ctrl+F3)
- Name Manager dialog: list (Name, Value, Refers To, Scope, Comment).
- New / Edit / Delete / Filter.
- Cú pháp Refers To: `=Sheet1!$A$1:$B$3` hoặc constant `=1.5`.
- Scope: Workbook / Sheet1 / Sheet2.
- Dùng trong formula: `=SUM(DoanhThu)`.

## Dynamic Arrays + Modern Functions (Phase 6)

### Core dynamic arrays (Excel 2021+)
- `FILTER(array, include, [if_empty])`
- `SORT(array, [sort_index], [sort_order], [by_col])`
- `SORTBY(array, by_array1, [order1], ...)`
- `UNIQUE(array, [by_col], [exactly_once])`
- `SEQUENCE(rows, cols, start, step)`
- `RANDARRAY(rows, cols, min, max, [whole_number])`
- `XLOOKUP(lookup_value, lookup_array, return_array, [if_not_found], [match_mode], [search_mode])`
- `XMATCH(lookup_value, lookup_array, [match_mode], [search_mode])`
- Spill range: nếu formula trả mảng, kết quả "tràn" sang ô bên cạnh; viền nét đứt xanh; chỉ ô anchor sửa được.

### Modern aggregation (Excel 365 2024)
- `GROUPBY(row_fields, values, function, [field_headers], [total_depth], [sort_order], [filter_array])` — 1-axis group-by trả mảng dynamic.
- `PIVOTBY(row_fields, col_fields, values, function, [field_headers], [row_total_depth], [row_sort_order], [col_total_depth], [col_sort_order], [filter_array])` — 2-axis pivot dynamic (alternative cho PivotTable, **never goes stale**).
- Custom aggregation lambda: cả 2 nhận function = lambda (vd `LAMBDA(x, MEDIAN(x))` để median thay sum).

### Text / Array (Excel 2022+)
- `TEXTSPLIT(text, col_delimiter, [row_delimiter], [ignore_empty], [match_mode], [pad_with])` — thay Text-to-Columns workflow.
- `TEXTBEFORE` / `TEXTAFTER` — trích substring quanh delimiter.
- `VSTACK(array1, [array2], ...)` / `HSTACK(...)` — concat arrays.
- `WRAPCOLS(vector, wrap_count, [pad_with])` / `WRAPROWS(...)` — reshape vector → matrix.
- `TOROW(array, [ignore], [scan_by_col])` / `TOCOL(...)` — flatten.
- `TAKE(array, rows, [cols])` / `DROP(array, rows, [cols])` / `CHOOSEROWS` / `CHOOSECOLS`.
- `EXPAND(array, rows, [cols], [pad_with])`.

### LAMBDA & helpers (Excel 365 2022+)
- `LAMBDA(param1, [param2], ..., body)` — anonymous function trong cell.
- `LET(name1, value1, [name2, value2], ..., result)` — local variables (clean readability).
- `MAP(array, lambda)` — element-wise transform.
- `REDUCE(initial, array, lambda(accumulator, value))` — fold.
- `SCAN(initial, array, lambda)` — fold with intermediate results.
- `BYROW(array, lambda)` / `BYCOL(array, lambda)` — apply lambda per row/col.
- `MAKEARRAY(rows, cols, lambda(row, col))` — generate array.
- `ISOMITTED(arg)` — check if optional arg passed (chỉ trong LAMBDA).

### Regex (Excel 2024)
Đã có ở [Spec 22](22-modern-features.md): `REGEXTEST`, `REGEXEXTRACT`, `REGEXREPLACE`.

### Modern array text (Excel 2025)
- `TRIMRANGE(range, [trim_rows], [trim_cols])` — bỏ trailing empty (đã có ở [Spec 22](22-modern-features.md)).
- `IMAGE(source, [alt_text], [sizing], [height], [width])` — image trong cell từ URL.
- `ARRAYTOTEXT(array, [format])` / `VALUETOTEXT(value, [format])` — array → text serialization.

### Excel 365 2025+ — AI in formula
- `COPILOT(prompt, [context_range], [model])` — LLM trong cell ([Spec 39](39-copilot-agent.md)).

### Implementation note
- LAMBDA + helpers (MAP/REDUCE/BYROW...) đòi engine first-class function values. `formula._FUNCTIONS` registry chỉ map name → callable; cần thêm Lambda value type (closures with env capture).
- GROUPBY/PIVOTBY: dùng pandas `groupby().agg(func)` / `pivot_table()` backend.
- TEXTSPLIT trả 2D array → cần Dynamic Array spill infrastructure.
- IMAGE() trả picture-in-cell — kết hợp với [Spec 34 Shapes](34-shapes-images-smartart.md) cell-anchored image.

## Acceptance criteria

### A. Đã đo được & ĐÃ ship (v0.11.3 — `tests/test_formula_v0113.py`)
Phần engine/hàm vô hướng (không UX) — chạy `python -m pytest tests/`:
- A1. `=XLOOKUP("banana",B1:B4,A1:A4)` đúng; reverse `search_mode=-1` trả match cuối; `match_mode` -1/1 (gần nhỏ/lớn hơn); miss không `if_not_found` → `#N/A`.
- A2. `=EOMONTH(DATE(2024,2,15),0)` → 29 (năm nhuận); `=EDATE(DATE(2024,1,31),1)` → 29/02.
- A3. `=MROUND(2.5,1)` → 3, `=MROUND(-2.5,-1)` → -3 (nửa-ra-xa-0); `=ATAN2(1,1)` = π/4 (thứ tự đối số kiểu Excel).
- A4. **Mã lỗi**: `=1/0`→`#DIV/0!`; `=SQRT(-1)`→`#NUM!`; `=NOTAFUNC()`→`#NAME?`; `=INDEX(A1:A2,9)`→`#REF!`; `=VALUE("x")`→`#VALUE!`; `=NA()`→`#N/A`.
- A5. **Không treo**: `=AVERAGEIFS(A1:A3,B1:B1,">0")` (vùng lệch) → `#VALUE!`; `=FACT(171)`/`=POWER(10,1000)` → `#NUM!`; `=CHOOSE(1,A1:A3)` (vùng) → `#VALUE!` (không hiện `<_Range>`).
- A6. `=ISERROR(1/0)`→TRUE; `=ISNA(NA())`→TRUE; `=ISNA(1/0)`→FALSE; `=IFNA(NA(),"x")`→"x" nhưng `=IFNA(1/0,"x")` vẫn raise `#DIV/0!`.

### B. UX chưa làm (Phase 4 — Function Wizard / Trace / smart-tag / Name Manager)
1. Shift+F3 → Function Wizard mở; search "sum" → SUM/SUMIF/SUMIFS hiện. Chọn SUM → OK → Function Arguments dialog với 1 box "Number1".
2. Trong dialog, click ↗ → dialog thu nhỏ, drag A1:A10 trên grid → quay lại, Number1 = `A1:A10`, preview hiện kết quả.
3. Gõ `=SU` trong cell → autocomplete dropdown; Tab chọn SUM; gõ `(` → tooltip syntax `SUM(`**`number1`**`, [number2], ...)`.
4. `=A1/B1` với B1=0 → #DIV/0!; tam giác xanh ở góc; click ⚠ → dropdown 5 mục.
5. Chọn `=A1+A2` ô C1 → Formulas → Trace Precedents → mũi tên xanh từ A1 và A2 đến C1.
6. `=A1` ở A2 và `=A2` ở A1 → popup "Circular Reference: A1" + Status Bar.
7. Ctrl+F3 → Name Manager; New `DoanhThu` = `=Sheet1!$A$1:$A$10`; gõ `=SUM(DoanhThu)` → đúng.
8. Ctrl+\` → toàn sheet hiện formula thay vì kết quả; lần nữa → ngược lại.

## Phụ thuộc
- [04 Name Box / Formula Bar](04-name-box-formula-bar.md) — autocomplete + ScreenTip.
- [03 Cell Modes](03-cell-modes.md) — Point mode khi click trong Function Wizard.
- [10 Sheet Tabs](10-sheet-tabs.md) — scope Named Range.

## Risk
Cao. Function Wizard + Evaluate Formula yêu cầu metadata cho mọi hàm. Dynamic array thay đổi cell model (anchor cell sở hữu vùng spill).
