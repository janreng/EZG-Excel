# SPEC 18 — PivotTable

## Mục tiêu
Tổng hợp dữ liệu thành báo cáo: drag-drop fields vào 4 zone (Filters / Columns / Rows / Values), drill-down, group, Slicer, Timeline, refresh.

## Trạng thái hiện tại
- ✗ Chưa có. Phase 6 (sau khi Multi-sheet + Table xong).

## 18.1 Tạo PivotTable (§18.1)

- Insert → PivotTable.
- Dialog:
  - Source range (auto-detect bao trùm vùng data).
  - "New worksheet" / "Existing worksheet" (location).
  - "Add this data to the Data Model" — Phase sau (multi-table / DAX).
- OK → Sheet mới (hoặc location chọn) với placeholder + Field List pane.

## 18.2 Field List Pane (§18.2)

Pane bên phải màn hình:

```
┌─ PivotTable Fields ─────────┐
│ Choose fields to add:        │
│  ☐ Region                   │
│  ☐ Product                  │
│  ☐ Year                     │
│  ☐ Sales                    │
│ ──────────────────────────── │
│ Drag fields between areas:   │
│                              │
│  ▼ Filters    │  ▼ Columns   │
│  [          ] │  [         ] │
│  ────────────┼─────────────  │
│  ▼ Rows       │  ▼ Values    │
│  [          ] │  [         ] │
└─────────────────────────────┘
```

- Check field → tự thêm vào zone phù hợp (text → Rows; số → Values với SUM).
- Drag field giữa 4 zone.
- Click ▼ trong Values → Field Settings: đổi aggregation (Sum / Count / Average / Max / Min / Product / Count Numbers / StdDev / StdDevp / Var / Varp), number format, name.

## 18.3 Interaction (§18.3)

- Click field trong Values → Field Settings dialog.
- Double-click giá trị → Drill down: tạo sheet mới với detail rows.
- Click ▼ trong Row/Column header → Filter/Sort nhanh.
- Right-click → Group: nhóm date theo Month / Quarter / Year; nhóm số theo khoảng.
- **Refresh**: PivotTable Analyze → Refresh / Alt+F5 — bắt buộc khi data nguồn đổi (Pivot không auto-refresh).
- **Slicer**: PivotTable Analyze → Insert Slicer → chọn field → button filter trực quan.
- **Timeline**: PivotTable Analyze → Insert Timeline → chọn date field → slider thời gian.

## Implementation note

### Data model
```python
class PivotTable:
    source: Range | TableRef    # data nguồn
    location: (sheet, anchor_row, anchor_col)
    filters: list[FieldConfig]
    rows: list[FieldConfig]
    columns: list[FieldConfig]
    values: list[ValueFieldConfig]  # field + aggregation + format
    grand_total_rows: bool
    grand_total_cols: bool
    style: str
    slicers: list[Slicer]
    timelines: list[Timeline]
```

### Compute engine
- Group by rows × columns; aggregate values per cell theo function.
- Implement bằng `dict[(row_key, col_key)] → aggregator`.
- pandas có thể dùng: `pd.pivot_table(df, index=rows, columns=cols, values=val, aggfunc=agg)` — Ezcel đã có pandas dependency.

### Render
- PivotTable render là một **block trong sheet** chứa cells với formula `=GETPIVOTDATA(...)`.
- Có anchor cell; size = số row groups + total × số col groups + total.
- Cells trong vùng pivot: read-only (sửa ngoài Field List/Slicer không hợp lệ).

### Slicer
- Float widget hoặc embedded shape trong sheet.
- Button list = unique values của field.
- Click button → filter pivot (set filter field).
- Multi-select: Ctrl+Click / Shift+Click.

### Timeline
- Slider horizontal: range date.
- Drag 2 handle → set date range filter.
- Granularity dropdown: Years / Quarters / Months / Days.

## Acceptance criteria
1. Insert PivotTable trên data 100 rows × 4 cols (Region, Product, Year, Sales) → sheet mới + Field List pane.
2. Drag Region → Rows; Product → Columns; Sales → Values (SUM mặc định) → pivot matrix đúng SUM(Sales) by region × product.
3. Right-click date field trong Rows → Group → Months → pivot group theo tháng.
4. Đổi data nguồn → Alt+F5 → pivot cập nhật.
5. Insert Slicer → chọn Region → slicer hiện 4 button (Bắc/Trung/Nam/...). Click "Bắc" → pivot filter.
6. Double-click cell trong pivot → sheet mới với detail rows tương ứng.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — pivot ở sheet khác.
- [16 Table](16-table.md) — source có thể là Table.
- [12 Formula System](12-formula-system.md) — GETPIVOTDATA function.
- pandas (đã có).

## Risk
**Rất cao.** Pivot là module lớn. Slicer/Timeline là widget riêng. Refresh khi source đổi cần dependency tracking.
