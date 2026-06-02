# SPEC 27 — Data Tools (Text to Columns / Remove Duplicates / Consolidate / Subtotal / Forecast Sheet)

## Mục tiêu
Gom các công cụ data manipulation trong tab Data → Data Tools / Forecast / Outline.

## Trạng thái hiện tại
- ✗ Chưa có (toàn bộ).

## 27.1 Text to Columns (Data → Text to Columns)

3-step wizard tách 1 cột text thành nhiều cột.

### Step 1
- **Delimited**: tách theo ký tự (Tab/Semicolon/Comma/Space/Other).
- **Fixed width**: tách theo độ rộng ký tự cố định.

### Step 2 (Delimited)
- Check delimiters: ☑ Tab ☑ Semicolon ☑ Comma ☑ Space ☐ Other:[ ]
- "Treat consecutive delimiters as one" checkbox.
- Text qualifier: " / ' / {none}
- Preview live.

### Step 2 (Fixed width)
- Preview với ruler; click để add break line; double-click để remove; drag để move.

### Step 3
- Cho mỗi cột: data type (General / Text / Date / Skip column) + Destination cell.
- Advanced: Decimal separator, Thousands separator.

## 27.2 Flash Fill (Ctrl+E)
Xem [Spec 05](05-data-entry-autofill.md).

## 27.3 Remove Duplicates (Data → Remove Duplicates)

- Dialog: "My data has headers" checkbox.
- Checkbox list của columns; chọn cột nào dùng để xác định duplicate (default: tất cả).
- OK → xóa hàng duplicate, giữ first occurrence.
- Message sau: "X duplicates found and removed. Y unique values remain."

### Implementation
- Hash tuple values của các cột chọn; giữ first.

## 27.4 Data Validation
Xem [Spec 25](25-data-validation.md).

## 27.5 Consolidate (Data → Consolidate)

Gộp data từ nhiều range / sheets thành summary.

- **Function** dropdown: Sum / Count / Average / Max / Min / Product / Count Numbers / StdDev / StdDevp / Var / Varp.
- **References**: list các source range. Add / Delete.
  - Source có thể là sheet khác cùng workbook, hoặc workbook khác (external).
- **Use labels in**: Top row / Left column / Both.
- **Create links to source data** checkbox: tạo formula thay vì hardcode values.
- OK → render kết quả vào active cell.

## 27.6 Group / Outline / Subtotal (§9.4 + Data → Subtotal)

### Subtotal dialog
- "At each change in" dropdown (cột grouping).
- "Use function" dropdown.
- "Add subtotal to" checkbox list (cột cần aggregate).
- "Replace current subtotals" checkbox.
- "Page break between groups" checkbox.
- "Summary below data" checkbox.
- Insert: tự thêm hàng "Subtotal X" sau mỗi nhóm + outline level.

**Lưu ý**: data phải sort theo cột grouping trước. Excel khuyên warn nếu chưa.

### Group/Outline UI
Xem [Spec 09](09-row-col-operations.md).

## 27.7 What-If Analysis
Xem [Spec 28](28-what-if-analysis.md).

## 27.8 Forecast Sheet (Data → Forecast → Forecast Sheet)

- Chọn 2 cột: date/time + values.
- Dialog: Create Forecast Worksheet.
- Forecast end: date.
- Options:
  - Forecast Start: tự / chọn.
  - Confidence Interval: 95% (default), tùy chỉnh.
  - Seasonality: Auto / Manually (number).
  - Fill missing points: Interpolation / Zeros.
  - Aggregate duplicates: Average / Count / Max / Min / Sum / Median.
  - Include forecast statistics (alpha, beta, gamma, MASE, SMAPE, MAE, RMSE).
- OK → sheet mới với chart (Line) + bảng dữ liệu (historical + forecast + upper/lower bound).
- Engine: triple exponential smoothing (ETS) algorithm.

### Implementation
- Phase muộn. Có thể dùng `statsmodels.tsa.holtwinters.ExponentialSmoothing` (cần add dependency) hoặc tự viết.

## 27.9 Relationships (Data → Relationships)
- Quản lý quan hệ giữa Tables ([Spec 16](16-table.md)) trong workbook.
- Dialog: New / Edit / Delete relationship.
- Một quan hệ: Table A column → Table B column.
- Phục vụ PivotTable từ Data Model ([Spec 18](18-pivot-table.md)).

## Acceptance criteria

### Text to Columns
1. Cột A có "Nguyen, Van A", chọn A1:A100 → Data → Text to Columns → Delimited → Comma → cột mới B="Nguyen", C=" Van A".
2. Fixed width: cột A có "John  25M", chia tại pos 5 và 8 → B=John, C=25, D=M.

### Remove Duplicates
3. Cột A có 1,2,3,2,1,4 → Remove Duplicates → còn 1,2,3,4 (4 rows).

### Consolidate
4. Sheet1 A1:B5 + Sheet2 A1:B5 (cùng layout) → Consolidate Sum → kết quả là tổng từng ô tương ứng.

### Subtotal
5. Data sort theo Region; Subtotal "At each change in Region" Sum Sales → mỗi vùng region có hàng "Region X Total" + Grand Total cuối.

### Forecast
6. Date column 12 tháng + Value column → Forecast 6 tháng tiếp → sheet mới có chart line + table forecast + upper/lower bounds.

## Phụ thuộc
- [09 Row/Col Operations](09-row-col-operations.md) — Group/Outline UI.
- [12 Formula System](12-formula-system.md) — Consolidate "Create links" tạo formula.
- [16 Table](16-table.md), [18 PivotTable](18-pivot-table.md) — Relationships.

## Risk
- Forecast Sheet: ETS algorithm phức tạp; có thể fallback dùng statsmodels.
- Consolidate cross-sheet/cross-workbook: external workbook reference khó.
