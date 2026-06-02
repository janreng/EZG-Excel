# SPEC 48 — Touch Mode / Pen / Ink

## Mục tiêu
Touch-optimized UI mode; Pen/stylus input cho annotation, sign, draw chart; Ink to Math, Ink to Shape.

## Trạng thái hiện tại
- ✗ Chưa có.

## 48.1 Touch Mode

### Truy cập
- Quick Access Toolbar dropdown → ☑ Touch/Mouse Mode → button toggle.
- Auto-enable trên thiết bị touch (Surface, tablet).

### Differences khi Touch mode bật
- Ribbon buttons lớn hơn (~1.4×).
- Spacing rộng hơn.
- Long-press = right-click.
- Pinch zoom: hai-finger trên grid → zoom slider.
- Two-finger pan: scroll.
- Tap đôi nhanh: edit cell.

## 48.2 Pen / Stylus

### Draw Tab (Excel 2019+)
- Pen / Highlighter / Pencil tools (3 loại pen).
- Color picker per tool.
- Thickness slider.
- Eraser (Object eraser / Stroke eraser).
- Lasso Select: vẽ vòng quanh ink → chọn.

### Modes
- **Inking on cell**: vẽ trực tiếp trên grid → stroke trở thành object overlay.
- **Inking on shape**: vẽ trên shape (tương tự Word).

## 48.3 Ink to Math

Draw → Ink to Math → mở Equation Editor:
- Vẽ công thức bằng pen → ML recognize → convert sang typeset equation.
- Insert vào cell hoặc shape.

## 48.4 Ink to Shape

Vẽ shape rough (rectangle, circle, triangle, arrow) → Excel detect → convert sang shape chuẩn (clean lines).

## 48.5 Ink Replay

Draw → Ink Replay: animate strokes theo thứ tự được vẽ (như slideshow).

Use case: present quá trình giải bài.

## Implementation note

### PySide6 input
- `QTouchEvent`: touch points.
- `QTabletEvent`: pen (pressure, tilt, twist).
- `QGesture`: pinch, swipe.

### Touch mode toggle
- Settings → Touch mode → CSS-like override:
  - Button min size 44×44 (target WCAG touch target).
  - Spacing 1.4× normal.

### Ink storage
- Strokes = list[(x, y, pressure)]; stored as objects per sheet (like Shapes).
- Render: `QPainter.drawPolyline` với pen có pressure → variable width.

### Ink to Math / Shape
- Recognition engine: MyScript SDK (proprietary) hoặc open-source HMM model. Phase rất muộn.
- Bắt đầu: chỉ Ink to Shape với basic rules (vẽ kín hình → detect ellipse/rect/triangle theo aspect + closure).

## Acceptance criteria
1. QAT → Touch Mode toggle → ribbon button lớn hơn; row height auto increase.
2. Pinch zoom trên grid → zoom slider sync.
3. Draw tab → Pen → vẽ trên grid → stroke đỏ.
4. Eraser → click stroke → xóa.
5. Lasso → vẽ vòng quanh strokes → select all in lasso.
6. Vẽ hình tam giác rough → Ink to Shape → chuyển thành triangle chuẩn.
7. Lưu xlsx → reopen → ink strokes còn nguyên.

## Phụ thuộc
- [34 Shapes / Images](34-shapes-images-smartart.md) — ink objects = subset shape.
- [07 Ribbon](07-ribbon.md) — Draw tab.

## Risk
- Touch mode: chỉ là styling CSS — dễ.
- Pen pressure: cần hardware support; thiếu sẽ degrade gracefully.
- Ink to Math / Shape: ML, phase rất xa.

## Phase
Touch mode: Phase 5+. Pen/Ink: Phase 7+. Ink to Math: out of scope (rất xa).
