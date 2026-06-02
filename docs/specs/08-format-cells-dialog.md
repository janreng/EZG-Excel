# SPEC 08 — Format Cells Dialog (6 Tabs)

## Mục tiêu
Dialog Ctrl+1 đầy đủ 6 tab: Number / Alignment / Font / Border / Fill / Protection — single source of truth cho mọi format setting.

## Trạng thái hiện tại
- ✗ Chưa có dialog gộp. Format hiện rải rác ở ribbon: font, size, bold/italic, halign/valign/wrap.
- ✗ Number format chưa có.
- ✗ Border chưa có (model `_fmt` chưa có key `border`).
- ✗ Fill color (background) chưa có (`bg` chưa).
- ✗ Strikethrough / Underline / Superscript / Subscript chưa.
- ✗ Protection tab chưa (do Sheet Protection chưa có).

## Truy cập
- Ctrl+1 (universal)
- Right-click cell → Format Cells...
- Home → Cells group → Format → Format Cells
- Dialog Box Launcher của Font / Alignment / Number group → mở đúng tab

## 8.1 Tab Number (§8.1)

| Category | Options | Ví dụ |
|---|---|---|
| General | (Excel tự quyết) | `1234` / `text` |
| Number | Decimal places (0-30), Use 1000 Separator, Negative format | `1,234.56` hoặc `(1,234.56)` đỏ |
| Currency | Decimal places, Symbol ($/€/£/₫), Negative format | `$1,234.56` |
| Accounting | Như Currency nhưng align symbol theo cột | `$    1,234.56` |
| Date | 20+ format: `3/14/01`, `March 14 2001`, `14-Mar` | `01/06/2025` |
| Time | `h:mm AM/PM`, `h:mm:ss`, `37:30:55`... | `14:30:00` |
| Percentage | Decimal places | `75.00%` |
| Fraction | 1 digit, 2 digits, halves, quarters... | `3/4` |
| Scientific | Decimal places | `1.23E+06` |
| Text | Lưu số dưới dạng text | `'0123` giữ 0 đầu |
| Special | Zip Code, Phone Number, SSN | `(012) 345-6789` |
| Custom | Format code | `#,##0.00_);[Red](#,##0.00)` |

### Custom format code grammar (cần parser tối thiểu)
- `#` digit placeholder, không pad
- `0` digit placeholder, pad 0
- `.` decimal separator
- `,` thousand separator
- `%` × 100, append %
- `_` width của char (vd `_)` reserve space cho `)`)
- `[Red]` / `[Blue]` / `[Color N]` màu chữ
- `[>1000]#,##0;[<0](0)` conditional sections
- Date: `dd/mm/yyyy`, `mmm`, `mmmm`, `dddd`, `hh:mm:ss AM/PM`

## 8.2 Tab Alignment (§8.2)

| Option | Mô tả |
|---|---|
| Horizontal | General / Left / Center / Right / Fill / Justify / Center Across Selection / Distributed |
| Vertical | Top / Center / Bottom / Justify / Distributed |
| Indent | 0-250 (chỉ tác dụng khi Horizontal = Left/Right/Distributed) |
| Orientation | -90° đến 90° hoặc Stacked (chữ dọc) |
| Wrap Text | Xuống dòng tự động, tăng row height |
| Shrink to Fit | Thu font vừa width (không wrap) |
| Merge Cells | Gộp ô (mất data ô khác) |
| Right-to-Left | Ngôn ngữ RTL |

## 8.3 Tab Font (§8.3)
- Font: dropdown với preview
- Style: Regular / Italic / Bold / Bold Italic
- Size: 1-409
- Underline: None / Single / Double / Single Accounting / Double Accounting
- Color: theme + standard + custom (RGB/HSL/Hex)
- Effects: Strikethrough, Superscript, Subscript
- Preview: `AaBbCcYyZz` với format hiện tại

## 8.4 Tab Border (§8.4)
- Presets: None / Outline / Inside
- 8 button cạnh + 2 diagonal (toggle on/off)
- Line Style: 13 kiểu (solid, dashed, dotted, double, thick...)
- Color: color picker
- Preview box: click trực tiếp vào cạnh để toggle (preferred UX)

## 8.5 Tab Fill (§8.5)
- Background Color: bảng theme + standard + More Colors
- Fill Effects: gradient 2 màu, nhiều hướng
- Pattern Style: dropdown 18 pattern (dots, stripes, crosshatch)
- Pattern Color
- More Colors → Custom: RGB / HSL / Hex

## 8.6 Tab Protection (§8.6)
- Locked: default checked. Ô bị khóa khi Sheet Protection bật.
- Hidden: khi Sheet Protection bật, formula ẩn khỏi Formula Bar.
- ⚠ Cảnh báo: Protection chỉ có tác dụng khi Review → Protect Sheet bật.

## Model changes (`table_model._fmt`)

Thêm keys (mở rộng `_FORMAT_KEYS`):
- `number_format: str` (vd `"#,##0.00"`, `"yyyy-mm-dd"`, `"0%"`)
- `bg: str` (hex `#RRGGBB`)
- `color: str` (hex chữ)
- `underline: "none"|"single"|"double"|"single_accounting"|"double_accounting"`
- `strikethrough: bool`
- `superscript`/`subscript: bool`
- `border: {top:{style,color}, bottom, left, right, diag_up, diag_down}`
- `orientation: int` (góc -90..90)
- `indent: int`
- `shrink_to_fit: bool`
- `pattern: {style, color}` (fill pattern)
- `locked: bool` (default True)
- `hidden: bool` (default False)

## Acceptance criteria
1. Ctrl+1 → dialog 6 tab. Mỗi tab chuyển nhanh, không reset selection trên grid.
2. Tab Number → chọn Currency, symbol `₫`, 0 decimals → `1234567` hiển thị `₫1,234,567`.
3. Tab Number → Custom `[Red]#,##0;[Green](#,##0)` → số âm đỏ ngoặc, số dương xanh.
4. Tab Border → click 4 cạnh ngoài trong preview → outline border áp xuống grid; undo Ctrl+Z hoàn nguyên.
5. Tab Fill → gradient 2 màu hướng dọc → ô tô đúng.
6. Apply format trên A1:B3 → đóng dialog → mở lại Ctrl+1 → hiển thị đúng state hiện tại.

## Phụ thuộc
- [09 Row/Col Operations](09-row-col-operations.md) — merge cells liên quan model.
- [17 Conditional Formatting](17-conditional-formatting.md) — tái dùng color picker.
- [Phase 3 Save format to xlsx](../roadmap.md) — `io_utils` map sang openpyxl `Font/PatternFill/Border/Alignment`.

## Risk
Trung bình-cao. Custom format code parser dễ sai; dùng openpyxl `_NumberFormat.format_value()` nếu chưa tự viết kịp.
