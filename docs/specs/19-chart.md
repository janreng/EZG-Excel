# SPEC 19 — Chart (Biểu đồ)

## Mục tiêu
Insert chart từ data range; embedded hoặc full chart sheet; 4 selection states; Format pane.

## Trạng thái hiện tại
- ✗ Chưa có chart engine.

## 19.1 Insert Chart Flow (§19.1)

- Chọn data range (gồm header) → Insert → Charts → chọn loại.
- Hoặc Insert → Recommended Charts (Excel gợi ý).
- Chart float trên sheet (Embedded Chart Object).
- F11: tạo Chart Sheet riêng.

### Chart types (Phase đầu cover 5 loại; full 17 loại sau)
- **Column** (Clustered / Stacked / 100% Stacked / 3D variants)
- **Bar**
- **Line** (Line / Stacked / 100% / with Markers)
- **Pie** (Pie / 3D Pie / Doughnut / Pie of Pie / Bar of Pie)
- **Scatter (XY)**
- Area / Stock / Surface / Radar / TreeMap / Sunburst / Histogram / Box & Whisker / Waterfall / Funnel / Combo / Map — Phase sau.

## 19.2 Selection States (§19.2)

| State | Visual | Hành vi |
|---|---|---|
| Không chọn | Chart bình thường | Click 1 lần → Object mode |
| Object mode | 8 handle resize ở góc + cạnh | Click ngoài → deselect. Click 2 lần → Edit mode |
| Edit mode | Viền khác | Click element trong chart → chọn element |
| Element selected | Element có handle riêng | Right-click → Format. Delete → xóa |

## 19.3 Chart Design Contextual Tab (§19.3)

- Chart Layouts: Quick Layout presets.
- Add Chart Element: Axes / Axis Titles / Chart Title / Data Labels / Data Table / Error Bars / Gridlines / Legend / Lines / Trendline / Up-Down Bars.
- Chart Styles: gallery color scheme.
- Switch Row/Column: đảo data series ↔ category.
- Select Data: dialog edit range / series name / axis labels.
- Change Chart Type: đổi loại biểu đồ.
- Move Chart: Embedded ↔ Chart Sheet.

## 19.4 Format Chart Elements (§19.4)

- Double-click element → Format pane bên phải.
- Tabs:
  - **Fill & Line**: color, line style, width, gradient.
  - **Effects**: shadow, glow, soft edges, 3D format.
  - **Size & Properties**: width, height, lock aspect ratio.
  - (Element-specific): scale (axis), gap width (bar), markers (line).
- Format Axis: scale (min/max/units), number format, tick marks, labels.
- Format Data Series: fill, border, markers, gap width, overlap.

## Implementation note

### Engine
- Dùng `matplotlib` (đã có pandas, có thể thêm). Render chart sang PNG → embed vào sheet với position/size.
- Hoặc `QChart` (Qt Charts module) cho interactive (chart sống). Phase đầu matplotlib PNG đủ.

### Model
```python
class Chart:
    type: str             # "column", "line", "pie", "scatter", ...
    subtype: str          # "clustered", "stacked", ...
    data_range: Range
    title: str
    legend: bool
    legend_position: str  # "top", "bottom", "left", "right"
    series: list[Series]  # name + range + color override
    axes: dict            # x_axis, y_axis: title, min, max, format
    style: int            # preset 1-16
    location: (sheet, anchor_row, anchor_col, width_px, height_px)
```

Sheet: `_charts: list[Chart]`.

### Render
- Khi data đổi: chart marked dirty; re-render trên `dataChanged`.
- Embedded: chart là widget overlay trên grid; z-order cao hơn cell.
- Chart Sheet: sheet kiểu khác, chỉ chứa 1 chart full size; toggle qua Move Chart dialog.

### Format pane
- `QDockWidget` right side; lazy-load tabs.

## Acceptance criteria
1. Chọn A1:B10 (header + 10 data points) → Insert → Column → 2D Clustered → chart embedded, anchor F2.
2. Click chart → 8 handle resize; drag góc → resize chart.
3. Double-click chart → Edit mode; click bar → series selected; Delete → xóa series.
4. Change Chart Type → Line → chart đổi sang line, giữ data.
5. Đổi data trong B5 → chart auto re-render đúng giá trị mới.
6. F11 → Chart Sheet mới full size.
7. Double-click axis → Format Axis pane; đổi min 0, max 100 → axis update.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — Chart Sheet là loại sheet đặc biệt.
- matplotlib (cần thêm dependency — đánh giá so với QtCharts).

## Risk
Cao. UI Edit mode (click vào element con) phức tạp; matplotlib chart không click-element được nên cần overlay logic.
