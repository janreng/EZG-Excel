# SPEC 45 — Power Pivot, Data Model, DAX

## Mục tiêu
Multi-table analysis trong workbook: Data Model gộp nhiều tables + relationships; DAX measures cho calculations reusable; PivotTable nguồn từ Data Model.

## Trạng thái hiện tại
- ✗ Chưa có.

## 45.1 Data Model

### Khái niệm
- "In-memory database" trong workbook (xVelocity engine).
- Chứa multiple tables + relationships giữa chúng.
- Powers PivotTable / PivotChart / Power View (deprecated).
- Format: nén columnar (vd 100M rows fit trong 1GB RAM).

### Add to Data Model
- Khi tạo PivotTable: dialog có checkbox "Add this data to the Data Model" ([Spec 18](18-pivot-table.md)).
- Power Query: Close & Load To → "Add to Data Model".
- Insert → PivotTable from External Data Source.

### Manage Data Model
- Power Pivot tab → Manage → mở Power Pivot window (separate window).

## 45.2 Power Pivot Window

Cửa sổ riêng (như Power Query Editor).

```
┌─ Power Pivot ──────────────────────────────────────────┐
│ Home  Design  Advanced                                  │
│ ──────────────────────────────────────────────────────│
│ [Tab Sales] [Tab Products] [Tab Customers]              │
│ ──────────────────────────────────────────────────────│
│ Data Grid View (table)                                  │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Date     | Product | Region | Sales | TotalCol      ││
│ │ 2026-01-01| P1      | North  | 100   | =SUM(...)    ││
│ │ ...                                                  ││
│ └─────────────────────────────────────────────────────┘│
│ ──────────────────────────────────────────────────────│
│ Measures (DAX):                                         │
│ TotalSales := SUM(Sales[Sales])                         │
│ YoY% := DIVIDE([TotalSales]-[LastYearSales], ...)       │
│ ──────────────────────────────────────────────────────│
│ View modes: [Data View] [Diagram View]                  │
└─────────────────────────────────────────────────────────┘
```

### Diagram View
- Visual: tables = boxes; relationships = lines giữa columns.
- Drag column từ table A đến column table B → tạo relationship.
- Relationship cardinality: 1:1, 1:Many, Many:Many.
- Relationship direction: Single / Both.

## 45.3 DAX (Data Analysis Expressions)

Ngôn ngữ formula riêng cho Data Model.

### Khác công thức Excel
- DAX không reference cell. Reference **column** (`Table[Column]`) hoặc **measure** (`[Measure]`).
- 2 loại evaluation: **row context** (per row) vs **filter context** (aggregation).
- Hàng trăm hàm: SUMX, COUNTX, FILTER, CALCULATE, RELATED, ALL, EARLIER, DATEADD, ...

### Calculated Column
- Trong Power Pivot, thêm cột mới với DAX: `=Sales[Quantity] * Sales[Price]` → tính per-row.

### Measure
- Aggregation reusable. Define ở Power Pivot Measures area:
  ```
  TotalRevenue := SUM(Sales[Revenue])
  AvgRevenue := AVERAGE(Sales[Revenue])
  TopCustomerRevenue := CALCULATE([TotalRevenue], TOPN(1, Customers, [TotalRevenue]))
  ```
- Dùng trong PivotTable Values.

### Key DAX functions
| Hàm | Mục đích |
|---|---|
| SUM / AVERAGE / COUNT / MAX / MIN | Aggregations cơ bản |
| SUMX / AVERAGEX / COUNTX | Iterator versions (row context) |
| CALCULATE(expr, filter1, filter2, ...) | Override filter context |
| FILTER(table, condition) | Filtered table |
| ALL(table_or_col) | Remove filter |
| ALLSELECTED / ALLEXCEPT | Selective filter |
| RELATED(column) | Get value from related table |
| RELATEDTABLE(table) | Get filtered related table |
| EARLIER / EARLIEST | Outer row context (advanced) |
| TOPN / RANKX | Ranking |
| DATEADD / DATESYTD / DATESBETWEEN | Time intelligence |
| SAMEPERIODLASTYEAR | YoY |
| SWITCH(expression, val1, result1, ..., else) | Conditional |
| VAR ... RETURN | Variables |
| TREATAS / USERELATIONSHIP / CROSSFILTER | Relationship manipulation |

### DAX vs Formula Excel
| Excel | DAX |
|---|---|
| `=SUM(A1:A10)` | `=SUM(Sales[Amount])` |
| `=AVERAGEIF(A:A, ">100", B:B)` | `=CALCULATE(AVERAGE(Sales[Amount]), Sales[Amount]>100)` |
| `=VLOOKUP(A1, Table2!A:B, 2)` | `=RELATED(Products[Price])` |

## 45.4 KPIs

Power Pivot → Measures → click measure → Create KPI:
- Target value (absolute hoặc measure).
- Status thresholds (Red / Yellow / Green).
- Icon style (smiley / arrows / traffic light).

Hiển thị trong PivotTable: icon next to value.

## 45.5 Hierarchies

Power Pivot Diagram View → drag fields lên 1 column → tạo hierarchy (vd Year → Quarter → Month → Day).

PivotTable drag entire hierarchy → expand/collapse một thao tác.

## Implementation note

**Phase rất muộn / Out of scope.** Reasons:
- DAX engine = nguyên 1 project (hundreds of functions, complex semantics).
- Columnar in-memory store khác data model hiện tại (`list[list[str]]`).
- Power Pivot tab = entirely new UI.

### Pragmatic alternative cho Ezcel
1. **Use pandas** as data model backend (đã có dependency).
2. **Multi-table relationships**: dict `relationships: list[(table_a, col_a, table_b, col_b)]`.
3. **Measure**: Python lambda hoặc subset of formula engine extended với:
   - `SUMX(Sales, [Quantity] * [Price])` → translate to `sum(row.Quantity * row.Price for row in Sales)`.
   - `CALCULATE`, `FILTER`, `RELATED` → pandas operations.
4. **PivotTable with measures**: PivotTable Values cell có thể là DAX measure thay vì raw column aggregation.

### Scope reduction
Phase 6+:
- Implement subset DAX: SUM, AVERAGE, COUNT, CALCULATE, FILTER, RELATED, ALL.
- No iterator functions (SUMX/AVERAGEX) — bỏ.
- No time intelligence — user dùng formula tính trước.
- No hierarchies.

## Acceptance criteria (minimal viable)
1. Insert PivotTable → checkbox "Add to Data Model" → workbook có Data Model.
2. Power Pivot → Manage → Diagram View hiện tables.
3. Drag Sales[ProductID] đến Products[ProductID] → relationship line xuất hiện.
4. Create Measure: `TotalSales := SUM(Sales[Amount])` → PivotTable Values dropdown hiện `TotalSales`.
5. PivotTable filter Region=North → measure `TotalSales` recompute under filter.

## Phụ thuộc
- [16 Table](16-table.md) — tables as Data Model source.
- [18 PivotTable](18-pivot-table.md) — consumer.
- [20 Power Query](20-power-query.md) — load data → Model.
- [27 Data Tools](27-data-tools.md) — Relationships dialog.

## Risk
**Rất cao.** DAX implementation = ngang một project khác. Khuyến nghị **out of scope** MVP và mid-term roadmap. Long-term có thể implement subset.
