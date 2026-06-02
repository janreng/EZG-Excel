# SPEC 40 — Quick Analysis & Recommended Charts/PivotTables

## Mục tiêu
Trải nghiệm "1-click" để áp visualize/format/sort thường gặp: Quick Analysis button + Recommended Charts/PivotTables/Insights.

## Trạng thái hiện tại
- ✗ Chưa có.

## 40.1 Quick Analysis Button (Ctrl+Q)

### Trigger
- Chọn data range (>1 ô) → icon nhỏ ⚡ xuất hiện góc dưới phải selection.
- Hoặc Ctrl+Q.
- Hoặc right-click → Quick Analysis.

### Popup menu — 5 tab

```
┌─ Quick Analysis ────────────────────────────────────────┐
│ [Formatting] [Charts] [Totals] [Tables] [Sparklines]    │
│ ────────────────────────────────────────────────────── │
│ (Tab content with preset buttons; hover = live preview) │
└─────────────────────────────────────────────────────────┘
```

### Tab Formatting
- Data Bars, Color Scale, Icon Set, Greater Than (>), Top 10%, Clear Format.

### Tab Charts
- Recommended chart presets (Column/Line/Pie/Bar/Scatter — chọn dựa trên loại data).
- More Charts... → Recommended Charts dialog.

### Tab Totals
- Sum (Row totals + Column totals)
- Average
- Count
- % Total
- Running Total
- Buttons riêng cho "Sum row at bottom" vs "Sum column at right".

### Tab Tables
- Table → convert to Table (Ctrl+T).
- PivotTable variations: 5-6 layout gợi ý.

### Tab Sparklines
- Line / Column / Win/Loss → insert sparkline column bên phải selection.

### Live Preview
- Hover button → preview áp lên grid (chưa commit).
- Click → commit + close popup.
- Click ngoài → cancel.

## 40.2 Recommended Charts (Insert → Recommended Charts)

### Dialog
```
┌─ Insert Chart ──────────────────────────────────────────┐
│ [Recommended Charts] [All Charts]                        │
│ ───────────────────────────────────────────────────────  │
│ Recommended:                       Preview:              │
│  ┌─────────────┐                  ┌───────────────────┐ │
│  │ ▣ Clustered │                  │                   │ │
│  │   Column    │                  │   [Chart preview] │ │
│  │             │                  │                   │ │
│  ├─────────────┤                  │                   │ │
│  │ ▤ Line      │                  └───────────────────┘ │
│  │   ...       │   Note: This chart is ideal because... │
│  │             │                                          │
│  └─────────────┘                              [OK] [Cancel]│
└─────────────────────────────────────────────────────────┘
```

### Engine
- Analyze data shape:
  - 1 categorical + 1 numerical → Column/Bar.
  - 2 numerical → Scatter.
  - Time series → Line / Area.
  - Parts of whole → Pie/Doughnut.
  - Many categories → Bar (horizontal).
  - High variance → Box-Whisker.

Auto-pick top 5-7 recommendations với explanation.

## 40.3 Recommended PivotTables (Insert → Recommended PivotTables)

Tương tự — engine analyze data + suggest pivot layouts (Region × Product, Date × Sum, ...).

### Dialog
List 5-6 pivot configurations với mini preview render.

Click → tạo PivotTable theo config + sheet mới.

## 40.4 Analyze Data / Ideas (Home → Analyze Data — formerly "Ideas")

AI-driven insights:
- Trends
- Outliers
- Rank
- Majority categories
- Correlations

### UX
- Click → pane bên phải hiện multiple "Insight cards":
  - "Sales are highest in Q3"
  - "Region North accounts for 45% of total"
  - "Product A correlates strongly with Region East"
  - Each card có icon chart preview + "Insert PivotTable" button.

Click card → insert pivot/chart vào sheet.

Phase 6 (cần engine analysis).

## Implementation note

### Quick Analysis button
- Render icon ⚡ overlay khi selection.size() > 1.
- Click → popup `QWidget` floating + tab widget.
- Hover preview: tạm thời apply CF/sort/etc với rollback khả thi (snapshot before, restore on cancel).

### Recommended Charts engine
- Function `recommend_charts(data) → list[ChartConfig]`:
  - Detect columns: text / number / date.
  - Rule-based: nếu (1 text + 1 number) → Column.
  - Sort by relevance.
- Render preview = matplotlib mini.

### Recommended PivotTable engine
- `recommend_pivots(data) → list[PivotConfig]`:
  - Heuristics: text col → Rows; date col → Rows (with group); number col → Values (Sum default).
  - Generate 5-6 variations.

### Analyze Data
- Phase 6 với Copilot ([Spec 39](39-copilot-agent.md)) — overlap.
- Statistical: anomaly detection (z-score), correlation (Pearson), trend (linear regression slope).

## Acceptance criteria
1. Chọn data A1:C10 → icon ⚡ xuất hiện góc dưới phải. Click → popup 5 tab.
2. Tab Formatting → hover Data Bars → grid preview xanh; click → commit, popup close.
3. Tab Charts → hover Column → mini chart preview floating; click → chart insert.
4. Tab Totals → click "Sum row at bottom" → hàng 11 = sum cột A, B, C.
5. Tab Sparklines → Line → cột D có sparkline cho từng hàng.
6. Insert → Recommended Charts → dialog hiện 5 chart presets cùng explanation.
7. Insert → Recommended PivotTables → dialog hiện 5 pivot config; click → tạo pivot.

## Phụ thuộc
- [17 Conditional Formatting](17-conditional-formatting.md), [19 Chart](19-chart.md), [18 PivotTable](18-pivot-table.md), [33 Sparklines](33-sparklines.md), [16 Table](16-table.md) — tất cả đều phải có trước.
- [39 Copilot](39-copilot-agent.md) — overlap với Analyze Data.

## Risk
- Live preview: phải rollback hoàn hảo nếu user cancel → snapshot/restore mechanism.
- Recommended engine: rule-based đơn giản, đủ; ML-based ngoài scope.
