# SPEC 34 — Shapes / Images / SmartArt / Hyperlinks / Symbols / Header & Footer

## Mục tiêu
Insert tab — toàn bộ objects nhúng vào sheet: Pictures, Icons, 3D Models, SmartArt, Shapes, Text Box, WordArt, Symbol, Equation, Hyperlink, Screenshot, Header & Footer (Page Layout view).

## Trạng thái hiện tại
- ✗ Chưa có (toàn bộ).

## 34.1 Pictures (Insert → Pictures)

### Sources
- **From This Device**: file picker.
- **Stock Images**: catalog (Excel 365 — out of scope cho Ezcel; có thể stub).
- **Online Pictures**: Bing search.
- **From URL**: nhập URL.

### Insert result
- Image floating trên sheet (Object mode), 8 handle resize.
- Default position: cùng vị trí với active cell, default size = natural size scaled fit.
- Anchor option: Move and size with cells / Move but don't size / Don't move or size with cells.

### Picture Format contextual tab (§7.1)
- Remove Background (auto-detect)
- Corrections: Sharpen/Soften, Brightness/Contrast presets
- Color: Saturation, Tone, Recolor (preset filter)
- Artistic Effects: 23 preset (pencil sketch, paint brushstrokes...)
- Compress Pictures (giảm DPI)
- Change Picture (giữ size/position)
- Reset Picture
- Picture Styles gallery (frame/shadow/border presets)
- Picture Border, Picture Effects (shadow/glow/soft edges/bevel/3D), Picture Layout (SmartArt convert)
- Alt Text (accessibility)
- Arrange (Bring to Front/Back, Selection Pane, Align, Group, Rotate, Crop)
- Size (Height, Width, lock aspect)

## 34.2 Shapes (Insert → Shapes)

### Categories
Recently Used, Lines (12), Rectangles (10), Basic Shapes (32), Block Arrows (28), Equation Shapes (6), Flowchart (28), Stars and Banners (16), Callouts (20), Action Buttons (12).

### Insert
- Click shape → cursor crosshair → drag trên sheet.
- Hold Shift khi drag → giữ proportions.
- Hold Ctrl → resize từ tâm.

### Shape Format contextual tab
- Insert Shapes (mini shape list)
- Change Shape
- Edit Points (polyline)
- Shape Styles gallery + Fill/Outline/Effects
- WordArt Styles (text trong shape)
- Arrange + Size groups

## 34.3 Icons (Insert → Icons)

- Stock icon library (10,000+ vector SVG).
- Categorized: Accessibility, Analytics, Animals, Apparel, ...
- Recolor, resize.
- Convert to Shape (chỉnh per-path).

## 34.4 3D Models (Insert → 3D Models)

- From This Device / Stock 3D Models / Online 3D Models.
- Rotate 3D control: drag để rotate trong viewport.
- 3D Model Views gallery (preset angles).
- Out of scope cho Ezcel phase đầu — stub disabled.

## 34.5 SmartArt (Insert → SmartArt)

### Categories
List, Process, Cycle, Hierarchy, Relationship, Matrix, Pyramid, Picture.

### Dialog
- Chọn template → OK → SmartArt object floating + Text Pane.
- **Text Pane** (toggle bằng arrow trái object): nhập bullet points → SmartArt auto-render shapes.
- Promote/Demote bullet → đổi level.

### SmartArt Design tab
- Layouts gallery
- Change Colors
- SmartArt Styles
- Reset Graphic
- Convert to Shapes / Text

## 34.6 Text Box (Insert → Text Box)

- Drag tạo text box (rectangle với text editable).
- Vertical Text Box: text dọc.
- Khác Shape: anchor mặc định "Move and size with cells"? No — text box mặc định float free.

## 34.7 WordArt (Insert → WordArt)

- Gallery 15 styles → click → text "Your text here" → edit.
- Properties tương tự shape + text style đặc biệt (gradient, outline, transform: arch, circle, wave, ...).

## 34.8 Symbol / Equation (Insert → Symbols)

### Symbol dialog
- Font dropdown (system fonts).
- Subset dropdown (Latin, Greek, Currency, Arrows, Math Operators, ...).
- Grid hiển thị characters → double-click insert.
- Character code (Unicode/ASCII) input.
- Recently used symbols.
- AutoCorrect option (vd `(c)` → `©`).

### Equation
- Insert → Equation: math editor (chèn LaTeX-style expression).
- Equation Tools tab: Structures (Fraction, Script, Radical, Integral, Function, Bracket, Matrix, ...), Symbols.
- Render dạng object floating.

## 34.9 Hyperlink (Insert → Link / Ctrl+K)

### Dialog
- Link to:
  - **Existing File or Web Page**: browse / URL.
  - **Place in This Document**: list cells / named ranges / sheets.
  - **Create New Document**: tạo file mới + link.
  - **E-mail Address**: `mailto:` + subject.
- Text to display.
- ScreenTip... button → tooltip khi hover link.

### Behavior
- Cell có hyperlink: text underlined + blue color (theme).
- Ctrl+Click → mở (browser/email/jump).
- Right-click → Edit Hyperlink / Open / Copy / Remove.

## 34.10 Screenshot (Insert → Screenshot)

- Dropdown:
  - Available Windows (thumbnail của all open windows) → click insert toàn cửa sổ.
  - Screen Clipping → screen mờ → drag rectangle → screenshot vùng đó.

## 34.11 Header & Footer (Insert → Header & Footer)

Mở view Page Layout với header/footer area editable. Xem [Spec 24 Print](24-print-page-setup.md) §24.2 tab Header/Footer.

## 34.12 Selection Pane

Home → Find & Select → Selection Pane (Phase muộn).

- Pane bên phải list tất cả objects trên sheet.
- Show/Hide từng object (eye icon).
- Reorder (z-order).
- Rename.

## Model

```python
class Shape:
    type: "picture" | "shape" | "icon" | "smartart" | "text_box" | "wordart" | "symbol" | "equation" | "chart"
    id: int
    sheet_id: int
    position: (x, y, w, h)        # pixel hoặc EMU
    anchor: "move_size" | "move_only" | "fixed"
    anchor_cell: (row, col)       # cho move_size / move_only
    z_order: int
    locked: bool
    alt_text: str
    rotation: float
    # type-specific data
    image_path: str | None
    shape_geometry: str | None    # "rect", "ellipse", "line", "arrow", ...
    fill: dict
    outline: dict
    text: str | None
    text_format: dict
    hyperlink: str | None
```

Sheet: `_shapes: list[Shape]`.

## Implementation note

- Phase 7 (sau cùng) — không critical cho spreadsheet UX.
- Shape rendering: overlay `QGraphicsView` trên grid hoặc `QWidget` floating với `paintEvent` custom.
- Image: `QPixmap` cache (giảm decode mỗi paint).
- SmartArt: tự render từ template (engine layout) hoặc convert sang group of shapes.
- Equation: parse LaTeX/MathML → render bằng `QGraphicsTextItem` với HTML/SVG.

## Acceptance criteria
1. Insert → Pictures → chọn `logo.png` → image floating cạnh active cell, 8 handle.
2. Right-click image → Size and Properties → anchor "Move but don't size with cells".
3. Insert → Shapes → Rectangle → drag → rectangle xanh. Double-click → text edit mode.
4. Insert → Icons → "User" icon → vector chèn vào.
5. Insert → SmartArt → Process → Basic Process → 3 shape arrows; Text Pane: gõ 3 bullet → 3 shape có text.
6. Ctrl+K trên A1 → Hyperlink dialog → URL `https://example.com` → Text "Click me" → A1 = "Click me" underlined blue. Ctrl+Click → browser mở.
7. Insert → Symbol → Greek subset → `α` insert vào cell active.

## Phụ thuộc
- [07 Ribbon](07-ribbon.md) — contextual Picture Format / Shape Format / SmartArt Design.
- [24 Print](24-print-page-setup.md) — Header & Footer.

## Risk
- SmartArt + Equation: complex; có thể stub rồi mở rộng dần.
- 3D Models: rất phức tạp; stub disable hợp lý.
- Image manipulation (background remove, artistic effects): Pillow + filter — nặng. Phase rất muộn.
