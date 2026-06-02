# SPEC 30 — Themes, Cell Styles, Table Styles, Custom Lists

## Mục tiêu
Hệ thống style hierarchy: Theme (font + color palette) → Cell Styles gallery → áp dụng nhanh + auto-update khi đổi theme.

## Trạng thái hiện tại
- ✗ Chưa có.

## 30.1 Themes (Page Layout → Themes)

Theme = bộ (Colors palette + Fonts heading/body + Effects).

### Built-in themes
Office, Aspect, Banded, Basic, Berlin, Celestial, Circuit, Damask, Depth, Dividend, Droplet, Facet, Frame, Gallery, Headlines, Integral, Ion, Ion Boardroom, Madison, Main Event, Mesh, Metropolitan, Office 2007-2010, Organic, Parallax, Quotable, Retrospect, Savon, Slate, Slice, Vapor Trail, View, Wisp, Wood Type.

### Components
- **Colors**: 12 màu (background 1-2, text 1-2, accent 1-6, hyperlink, followed hyperlink). Page Layout → Colors → preset hoặc Customize Colors.
- **Fonts**: heading + body. Page Layout → Fonts → preset hoặc Customize Fonts.
- **Effects**: line, fill, effect style (matte/glass/...). Page Layout → Effects.

### Khi đổi theme
- Mọi cell dùng theme color (Accent 1...) → đổi màu theo.
- Cell dùng custom color (RGB cụ thể) → giữ nguyên.
- Heading/body font đổi.
- Charts, SmartArt, Shapes update.

## 30.2 Cell Styles (Home → Cell Styles)

Gallery preset styles, mỗi cái = bundle format (font + color + bg + border + number format).

### Built-in
**Good, Bad, Neutral**
- Good (green bg)
- Bad (red bg)
- Neutral (yellow bg)

**Data and Model**
- Calculation
- Check Cell
- Explanatory Text
- Input
- Linked Cell
- Note
- Output
- Warning Text

**Titles and Headings**
- Heading 1 / 2 / 3 / 4
- Title
- Total

**Themed Cell Styles**
- 20% / 40% / 60% — Accent 1...6
- Accent 1 / 2 / 3 / 4 / 5 / 6

**Number Format**
- Comma, Comma [0], Currency, Currency [0], Percent

### Custom Cell Style
- Home → Cell Styles → New Cell Style → dialog:
  - Style name
  - Style includes (checkbox): Number / Alignment / Font / Border / Fill / Protection
  - Format → mở Format Cells dialog để cấu hình từng aspect.
- "Modify" để sửa style cũ; mọi cell dùng style auto-update.

### Merge Styles
- From workbook khác → copy styles.

## 30.3 Format as Table — Table Styles (Home → Format as Table)

Gallery 60+ table styles:
- **Light** (Light 1-21): nhẹ
- **Medium** (Medium 1-28): trung bình, default
- **Dark** (Dark 1-11): đậm

Mỗi style định nghĩa:
- Header row format
- Banded rows (alternate color)
- Banded columns
- First column highlight
- Last column highlight
- Total row format
- Filter button visibility

Áp vào Table ([Spec 16](16-table.md)).

Custom Table Style: dialog cho phép define từng element.

## 30.4 PivotTable Styles (PivotTable Analyze → ...)

Tương tự Table Styles nhưng cho PivotTable. Phase 6.

## 30.5 Custom Lists (File → Options → Advanced → Edit Custom Lists)

Lists dùng cho:
- AutoFill: gõ "Mon" + fill → "Tue, Wed, ...".
- Sort by Custom List ([Spec 15](15-filter-sort.md)).

### Built-in lists
- Sun, Mon, Tue, Wed, Thu, Fri, Sat
- Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday
- Jan, Feb, Mar...
- January, February...

### Custom
- Dialog Custom Lists: list của lists.
- Add new: gõ items separate by Enter, hoặc import from range.

### Tiếng Việt
Có thể thêm: "T2, T3, T4, T5, T6, T7, CN" / "Thứ hai, Thứ ba, ..." / "Tháng 1, Tháng 2, ..."

## Implementation note

### Theme model
```python
class Theme:
    name: str
    colors: dict[str, str]      # "accent1": "#5B9BD5", ...
    fonts: {heading: str, body: str}
    effects: str                # preset id
```

Workbook giữ active theme.

### Cell Style model
```python
class CellStyle:
    name: str
    builtin_id: int | None      # 0=Normal, 1=Comma, ...
    fmt: dict                   # full format dict (theo [Spec 08])
    includes: set[str]          # {"number","alignment","font","border","fill","protection"}
```

Workbook: `_styles: dict[str, CellStyle]`. Cell có `_fmt["style"] = "Heading 1"` → resolve cascade.

### Resolve order
1. Cell explicit `_fmt[(r,c)]` (highest)
2. Cell style (cascade từ `_fmt["style"]`)
3. Default "Normal" style
4. Theme defaults

## Acceptance criteria
1. Page Layout → Themes → Aspect → mọi cell dùng theme color đổi sang palette mới; font heading/body đổi.
2. Home → Cell Styles → click "Heading 1" trên A1 → A1 = font 18 / bold / màu accent1.
3. Cell Styles → New Cell Style → "ImportantInput" → bg vàng, font bold red → save. Apply lên B1:B5.
4. Modify "ImportantInput" → bg orange → B1:B5 tự cập nhật.
5. Format as Table → Medium 9 → table tô màu theo style. Đổi Table Style → Light 1 → bảng đổi.
6. File → Options → Edit Custom Lists → add "Q1,Q2,Q3,Q4 VN" → AutoFill type "Q1" → drag → "Q2","Q3","Q4","Q1 VN"... Sort dialog có option Custom List này.

## Phụ thuộc
- [08 Format Cells](08-format-cells-dialog.md) — format dict.
- [16 Table](16-table.md) — Table Styles.
- [05 AutoFill](05-data-entry-autofill.md), [15 Filter/Sort](15-filter-sort.md) — Custom Lists.

## Risk
Trung bình. Theme cascade phức tạp; cẩn thận distinguish theme color (cascade) vs custom color (fixed).
