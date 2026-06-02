# SPEC 33 — Sparklines (Mini Charts trong Cell)

## Mục tiêu
Charts nhỏ vẽ trong 1 cell, hiển thị trend của row dữ liệu.

## Trạng thái hiện tại
- ✗ Chưa có.

## 33.1 Loại Sparkline

3 loại (Insert → Sparklines):
- **Line**: line chart mini.
- **Column**: column chart mini.
- **Win/Loss**: 2 trạng thái (dương = up, âm = down) — không scale tuyến tính.

## 33.2 Tạo Sparkline

### Dialog (Insert → Sparklines → Line/Column/Win-Loss)
- **Data range**: range chứa values (vd `B2:G2`).
- **Location range**: cells chứa sparkline (vd `H2`).
- OK → sparkline render trong cell.

### Multi-row
- Data range `B2:G10` + Location range `H2:H10` → 10 sparklines, mỗi cell H tương ứng 1 hàng.

## 33.3 Sparkline Tools (Contextual Tab) — Design

Khi click cell có sparkline:

### Group: Sparkline
- Edit Data → mở dialog đổi range.
- Edit Group Location & Data: ungroup / move location.

### Group: Type
- Line / Column / Win/Loss → đổi loại.

### Group: Show
- ☐ High Point — marker đỏ tại max.
- ☐ Low Point — marker xanh tại min.
- ☐ Negative Points — color riêng cho values âm.
- ☐ First Point — marker tại đầu.
- ☐ Last Point — marker tại cuối.
- ☐ Markers (chỉ Line) — marker tại mỗi data point.

### Group: Style
- Gallery 36 styles preset (color + marker combo).
- Sparkline Color: pick.
- Marker Color: dropdown — Negative Points / Markers / High / Low / First / Last.

### Group: Group
- **Axis**:
  - Horizontal Axis Type: General / Date Axis Type (cho time series) / Show Axis (line tại 0).
  - Vertical Axis: Auto Min/Max / Same for All Sparklines / Custom.
- **Group / Ungroup**: gom multi-cell sparklines thành 1 group (chỉnh chung) hoặc tách.
- **Clear**: xóa sparkline (sparkline hoặc group).

## 33.4 Properties

- Sparkline gắn với cell — không phải shape object (khác chart embedded).
- Khi cell có text → sparkline vẽ overlay phía sau, text vẫn hiển thị foreground.
- Resize cell → sparkline auto-resize.
- Khi data đổi → sparkline auto re-render.
- Print: sparkline in được (vector).

## Model

```python
class Sparkline:
    type: "line" | "column" | "win_loss"
    data_range: Range
    location_cell: (row, col)
    group_id: int                 # cùng group → chỉnh chung
    show: {
        high: bool, low: bool, negative: bool,
        first: bool, last: bool, markers: bool
    }
    colors: {
        sparkline: str,
        markers: str, high: str, low: str,
        first: str, last: str, negative: str
    }
    axis: {
        horizontal_type: "general" | "date",
        date_axis_range: Range | None,
        show_horizontal_axis: bool,
        min: "auto" | "same_all" | float,
        max: "auto" | "same_all" | float
    }
```

Sheet: `_sparklines: list[Sparkline]`.

## Implementation note

- Render: `CellDelegate.paint()` — nếu cell có sparkline:
  - Vẽ background trước.
  - Vẽ sparkline (line/column/winloss) với painter clipped trong cell rect.
  - Vẽ text foreground.
- Hot path — cache QPainterPath / QPicture per sparkline; invalidate khi data range đổi.
- Computation: với data `[a, b, c, ...]`:
  - Line: polyline qua points (x = col_index → cell width, y = (value - min) / (max - min)).
  - Column: bar mỗi value.
  - Win/Loss: bar +0.5 (up) / -0.5 (down) / 0 (zero).
- xlsx: openpyxl `SparklineGroup` (`openpyxl.chart.sparkline`).

## Acceptance criteria
1. Data B2:G2 = [10, 20, 15, 30, 25, 35] → Insert Line Sparkline trong H2 → mini line trong H2 vẽ đúng.
2. Data B2:G10, Location H2:H10 → 10 sparklines tương ứng từng hàng.
3. Click H2 → Sparkline contextual tab xuất hiện. Show High Point → marker đỏ tại 35.
4. Đổi B5 = 100 → sparkline H5 update.
5. Type → Column → đổi sang column chart.
6. Type → Win/Loss với data có values âm → bar above/below baseline.
7. Group H2:H10 → chỉnh Style → tất cả 9 cells update.
8. Ungroup H5 → chỉnh riêng style H5 → các cell khác không đổi.
9. Save xlsx → mở lại → sparklines còn nguyên.

## Phụ thuộc
- [01 Grid Engine](01-grid-engine.md) — paint pipeline.
- [07 Ribbon](07-ribbon.md) — Sparkline contextual tab.

## Risk
Thấp-trung bình. Render trong cell nhanh nếu cache path. Win/Loss layout cần test với mix dữ liệu.
