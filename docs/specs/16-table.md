# SPEC 16 — Table (Ctrl+T) — Structured References

## Mục tiêu
Excel Table = container đặc biệt: filter tự động, table styles, structured references, total row, auto-extend.

## Trạng thái hiện tại
- ✗ Chưa có khái niệm Table.
- Filter hiện ở sheet level — Table sẽ là container có filter riêng.

## 16.1 Tạo Table (§16.1)

- Ctrl+T / Insert → Table.
- Dialog: "Where is data?" range (auto-detect) + checkbox "My table has headers".
- Output: vùng tô màu theo Table Style; filter dropdown trên header; Total Row option.

## 16.2 Features (§16.2)

| Feature | Behavior |
|---|---|
| AutoFilter | Tự động ở header (không tắt riêng được, chỉ tắt qua Table Design) |
| Total Row | Toggle ở Table Design tab; click cell trong total → dropdown (Sum / Avg / Count / Max / Min / StdDev / Var / Custom) |
| Resize Handle | Góc dưới phải có handle nhỏ → kéo extend/shrink |
| Append Data | Gõ vào hàng/cột ngay sát → auto extend table |
| Column Formula | Nhập formula 1 ô → auto fill cả cột (calculated column) |
| Structured Reference | Formula Bar: `=Table1[@Doanh_thu]` thay vì `=C2` |
| Table Name | Đặt ở Table Design; dùng: `=SUM(DoanhThu[Q1])` |
| Slicer | Insert → Slicer: filter button trực quan |
| Export to Range | Table Design → Convert to Range: bỏ table, giữ format |
| Duplicate Check | Không auto-warn duplicates |

## Structured References

Syntax:
- `TableName` → toàn bộ table không header
- `TableName[Column]` → toàn cột (không header)
- `TableName[@Column]` → ô cùng hàng trong cột (chỉ trong table)
- `TableName[#Headers]` → header row
- `TableName[#Totals]` → total row
- `TableName[#All]` → toàn bộ kể cả header + total
- `TableName[[#Data],[ColA]:[ColB]]` → range nhiều cột data

### Implementation note
- Class `Table` lưu: name, range (anchor row/col + size), columns (list[str]), has_total, has_header, style_name.
- `Workbook` (hoặc per-sheet) giữ `list[Table]`.
- Formula parser: token TABLE_REF = `r'[A-Za-z_]\w*\[[^\]]*\]'`; resolver map sang absolute range.
- Auto-extend: hook `dataChanged` ở model — nếu ô bên dưới/phải table có data và data không trống, mở rộng table range.
- Calculated column: khi nhập formula vào 1 ô trong cột table, broadcast `offset_formula` xuống toàn cột.

## Table Design contextual tab (theo §7.1)
- Properties: Table Name input.
- Tools: Summarize with PivotTable, Remove Duplicates, Convert to Range, Insert Slicer.
- External Table Data: Export, Refresh, Unlink.
- Table Style Options: Header Row, Total Row, Banded Rows, First Column, Last Column, Banded Columns, Filter Button.
- Table Styles: Gallery preset (Light/Medium/Dark theme variations).

## Acceptance criteria
1. Chọn data có header → Ctrl+T → dialog hiện range + checkbox "My table has headers" → OK.
2. Table tô màu zebra; mỗi header có filter ▼; Table Design tab xuất hiện ribbon.
3. Gõ formula `=A2*1.1` vào ô đầu cột mới (cột E của table) → auto fill toàn cột.
4. Trong cột "DoanhThu" total row dropdown → chọn Sum → ô total = `=SUBTOTAL(109,Table1[DoanhThu])` = tổng cột.
5. Gõ data vào hàng sát dưới table → table tự extend (range + style + filter mới).
6. Trong ô ngoài table: `=SUM(Table1[Q1])` → ra tổng cột Q1.
7. Convert to Range → table style giữ; filter mất; reference structured biến thành absolute.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — Workbook chứa list Tables.
- [12 Formula System](12-formula-system.md) — parser hỗ trợ `Table1[Col]`.
- [15 Filter/Sort](15-filter-sort.md) — Table filter dùng cùng UI.
- [07 Ribbon](07-ribbon.md) — Table Design contextual.

## Risk
Cao. Auto-extend + structured reference + calculated column liên quan nhiều module.
