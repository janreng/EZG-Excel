# SPEC 04 — Name Box & Formula Bar

## Mục tiêu
Name Box và Formula Bar hành xử đúng Excel: navigate, hiển thị state đúng, có Function Wizard, expand button.

## Trạng thái hiện tại
- ✓ Có Formula Bar text editable.
- ✓ Có Name Box hiển thị địa chỉ active.
- ✗ Name Box gõ địa chỉ + Enter chưa nhảy đến.
- ✗ Name Box dropdown Named Ranges chưa có.
- ✗ Formula Bar expand button (Ctrl+Shift+U) chưa có.
- ✗ Confirm (✓) / Cancel (✗) button khi edit chưa có.
- ✗ fx button chưa mở Function Wizard.
- ✗ Autocomplete dropdown khi gõ `=SU...` chưa có.

## Name Box (§4.1)

### Vị trí
Trái Formula Bar, rộng 80-120px, có thể kéo edge phải để resize.

### Trạng thái hiển thị

| Trạng thái | Hiển thị | Click/type behavior |
|---|---|---|
| Cell đơn selected | `A1`, `B5`... | Click → highlight địa chỉ; gõ địa chỉ mới + Enter → navigate |
| Range selected | `A1:C5` | Gõ range mới → chọn range đó |
| Multi-range selected | Địa chỉ range đầu (`A1:C5`) | — |
| Named Range | Tên range (vd `DoanhThu`) | Hiện tên nếu match cell/range |
| Entire row | `1:1` hoặc `3:5` | — |
| Entire col | `A:A` hoặc `B:D` | — |
| Trong Edit/Enter mode | Vẫn hiển thị địa chỉ active | Click → thoát Edit, navigate |
| Dropdown | Mũi tên hover phải | Click → list Named Ranges trong workbook |

### Navigate by typing
- Click Name Box (hoặc Ctrl+G / F5) → highlight content.
- Gõ địa chỉ: `A1` / `B100` / `Sheet2!D5` (multi-sheet — Phase 3) / `DoanhThu` (named range — Phase 4+) / `A1:C5,E5,F1:F10` (multi-range).
- Enter → navigate.
- Esc → khôi phục địa chỉ cũ.

## Formula Bar (§4.2)

### Thành phần (trái → phải)
1. **fx button** — click mở Function Wizard (Shift+F3). [Spec 12](12-formula-system.md).
2. **Text area** — hiển thị/edit nội dung **gốc** (formula `=SUM(A1)`, không phải kết quả).
3. **Expand button (▼)** — click hoặc Ctrl+Shift+U → toggle nhiều dòng.
4. **Confirm (✓)** — xuất hiện khi edit. Click = Enter.
5. **Cancel (✗)** — xuất hiện khi edit. Click = Escape.

### Trạng thái

| Trạng thái | Hiển thị |
|---|---|
| Ô trống | rỗng |
| Ô số/text | giá trị raw |
| Ô có công thức | `=SUM(A1:A10)` (Ctrl+` toggle hiện formula trong cell luôn) |
| Ô protected & hidden | rỗng (cần Sheet Protection bật) |
| Đang Edit | cursor nhấp nháy, ✓ và ✗ xuất hiện |
| Multi-cell (khác giá trị) | rỗng — gõ + Ctrl+Enter điền tất cả |

## Formula autocomplete dropdown (§4.3)

- Trigger: trong Enter mode, sau `=` + ≥ 1 ký tự (vd `=SU` → SUM, SUBSTITUTE, SUMIF...).
- Hiển thị: tên hàm + icon (fx vàng), kèm Named Ranges, Table names, Sheet names.
- Arrow Up/Down → navigate.
- **Tab → insert vào formula** (không phải Enter — Enter sẽ commit cell).
- Escape → đóng dropdown.
- Sau khi chọn hàm và gõ `(` → ScreenTip tooltip hiện dưới ô: `=VLOOKUP(`**`lookup_value`**`, table_array, col_index_num, [range_lookup])` (bold arg đang nhập).

## Acceptance criteria
1. Click Name Box, gõ `Z100` + Enter → active cell jump đến Z100.
2. Chọn A1:B3, Name Box hiển thị `A1:B3`. Chọn entire col C → hiển thị `C:C`.
3. F2 vào ô có `=SUM(A1:A10)`; Formula Bar hiện `=SUM(A1:A10)`, ✓ và ✗ xuất hiện. Click ✗ → Esc, khôi phục.
4. Gõ `=SU` vào A1 → dropdown hiện ≥ SUM/SUMIF/SUBSTITUTE; Tab chọn SUM → text thành `=SUM(`; tooltip hiện syntax.
5. Click fx button → mở Function Wizard dialog ([Spec 12](12-formula-system.md)).
6. Ctrl+Shift+U → Formula Bar expand 3-5 dòng; lần nữa → collapse.

## Phụ thuộc
- [03 Cell Modes](03-cell-modes.md) — Edit/Enter mode chuẩn.
- [12 Formula System](12-formula-system.md) — Function Wizard, ScreenTip.
- [02 Cell System](02-cell-system.md) — parse multi-range string.

## Risk
Trung bình. Autocomplete dropdown phải bám theo cell position khi scroll.
