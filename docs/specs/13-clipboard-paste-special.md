# SPEC 13 — Clipboard & Paste Special

## Mục tiêu
Clipboard có history 24 items; Paste Options icon-bar sau paste; Paste Special dialog đầy đủ.

## Trạng thái hiện tại
- ✓ Ctrl+C / Ctrl+X / Ctrl+V cơ bản.
- ✓ Ctrl+Shift+V (paste plain text — đã có).
- ✗ Clipboard history (24 items).
- ✗ Paste Options icon-bar sau paste.
- ✗ Paste Special dialog (Ctrl+Alt+V).
- ✗ Marching ants animation cho cut/copy source.

## 13.1 Clipboard history (§13.1)
- Ctrl+C lần 1: copy vào clipboard.
- Ctrl+C 2 lần liên tiếp: mở Clipboard task pane (24 items gần nhất).
- Home → Clipboard launcher: mở pane.
- Paste All: dán tất cả lần lượt.
- Clear All: xóa.

### Implementation note
- `ClipboardHistory` class giữ deque max 24.
- Mỗi item: (text/html, format dict, source ref, timestamp).
- Listen `QApplication.clipboard().dataChanged` để push entry.

## 13.2 Paste Options icon-bar (§13.2)

Sau Ctrl+V, icon nhỏ xuất hiện góc dưới phải vùng dán. Nhấn Ctrl để xem options (tooltip + access key trong ngoặc):

| Icon / Option | Phím (sau Ctrl) | Mô tả |
|---|---|---|
| Keep Source Formatting | K | Paste với format gốc |
| Values (V) | V | Chỉ giá trị, không formula/format |
| Formulas (F) | F | Formula, không format |
| Formatting (T) | T | Chỉ format |
| Values & Source Formatting | A | Giá trị + format gốc, không formula |
| Transpose (E) | E | Hàng ↔ cột |
| Link (N) | N | Tạo link đến source |
| Picture | (qua Paste Special) | Ảnh tĩnh |
| Linked Picture | (qua Paste Special) | Ảnh động (update khi source đổi) |

## 13.3 Paste Special Dialog (Ctrl+Alt+V) (§13.3)

| Nhóm | Tùy chọn |
|---|---|
| Paste | All / Formulas / Values / Formats / Comments and Notes / Validation / All using Source theme / All except borders / Column widths / Formulas and number formats / Values and number formats |
| Operation | None / **Add / Subtract / Multiply / Divide** (thực hiện phép tính giữa source và đích khi paste) |
| Special | **Skip Blanks** (không ghi đè ô có giá trị bằng ô trống nguồn) |
| Transpose | Đổi hàng/cột |

Buttons: OK / Cancel / **Paste Link** (như "Link" option).

### Implementation note
- Dialog QWidget với 3 group (Paste, Operation) radio buttons + 2 checkbox (Skip Blanks, Transpose).
- Apply: map vào `model.paste(rows, fmt, options)` — extend hàm paste hiện có.

## Marching ants animation
- Sau Ctrl+C/Ctrl+X, source range có viền nét đứt animated.
- Esc → tắt; sau khi paste (Ctrl+V cho Cut) → tự tắt; data change → tắt.
- Implementation: QTimer 200ms toggle dash offset, redraw selection range delegate.

## Drag clipboard data ngoài app
- Copy từ Excel → clipboard có HTML + plain text. Paste vào Ezcel phải parse HTML để giữ format (Phase sau khi có format model đầy đủ).
- Copy từ Ezcel → ra clipboard plain text (TSV) + HTML — paste sang Excel giữ format.

## Acceptance criteria
1. Ctrl+C trên A1:B3 → viền marching ants quanh A1:B3. Esc → tắt.
2. Ctrl+C lần 2 liền → Clipboard pane mở bên phải; có 1 item gần nhất.
3. Copy A1=`=B1+1`, B1=`10`. Paste vào D1 → Paste Options icon xuất hiện cuối D1. Click → menu. Chọn "Values" → D1 = 11 (không phải `=E1+1`).
4. Ctrl+Alt+V → Paste Special dialog. Chọn Values + Operation=Add → D1 cộng thêm 11 (assuming D1 đang là 5, sau = 16).
5. Copy 1 hàng → chọn 5 hàng đích → Ctrl+Alt+V + Transpose → 1 hàng thành 1 cột 5 ô.
6. Chọn vùng có ô trống xen kẽ → copy → paste với Skip Blanks → ô đích trùng vị trí trống không bị ghi đè.

## Phụ thuộc
- [08 Format Cells Dialog](08-format-cells-dialog.md) — format model đầy đủ.
- [02 Cell System](02-cell-system.md) — multi-range copy.

## Risk
Trung bình. Marching ants animation tốn paint event; throttle với QTimer.
