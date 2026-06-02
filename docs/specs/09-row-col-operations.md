# SPEC 09 — Row / Column / Cell Operations

## Mục tiêu
Resize, insert, delete, hide/unhide, group/outline đầy đủ kiểu Excel.

## Trạng thái hiện tại
- ✓ Resize cột/hàng bằng kéo header.
- ✓ Insert/Delete row/col (cell-level chưa rõ).
- ✓ Hide row/col (Ctrl+9 / Ctrl+0 — cần verify shortcuts).
- ✗ Row Height / Column Width dialog (nhập số chính xác).
- ✗ AutoFit Default Width.
- ✗ Group / Outline (Data → Group).
- ✗ Insert/Delete cell với dialog Shift right/down/up/left.
- ✗ Clear Formats / Clear Comments riêng (chỉ có Clear Contents).

## 9.1 Resize (§9.1)

### Mouse
- Hover ranh giới 2 cột header → cursor `↔`.
- Drag → resize. Drag phải = tăng. Trái = giảm.
- Double-click → AutoFit theo nội dung rộng/cao nhất.
- Nếu nhiều cột đang chọn → resize tất cả cùng lúc cùng width.

### Dialog chính xác
- Right-click header → Column Width... / Row Height...
- Nhập số: column theo **characters** (mặc định 8.43); row theo **points** (mặc định 15).
- Home → Format → Column Width / Row Height / AutoFit / Default Width.

## 9.2 Insert & Delete (§9.2)

| Thao tác | Phím | Hành vi |
|---|---|---|
| Insert Row | Ctrl + Shift + + | Chèn **phía trên** hàng chọn |
| Insert Column | Ctrl + Shift + + | Chèn **phía trái** cột chọn |
| Insert Cell | Ctrl + Shift + + | Dialog: Shift right / down / Insert row / Insert col |
| Delete Row | Ctrl + - | Xóa hàng, kéo lên |
| Delete Column | Ctrl + - | Xóa cột, kéo trái |
| Delete Cell | Ctrl + - | Dialog: Shift left / up / Delete row / col |
| Clear Contents | Delete | Xóa nội dung, giữ format/comment |
| Clear All | Home → Clear → All | Xóa data + format + comments + hyperlinks |
| Clear Formats | Home → Clear → Formats | Xóa format, giữ data |
| Clear Comments | Home → Clear → Comments & Notes | Xóa comments |

## 9.3 Hide & Unhide (§9.3)
- Hide Row: Ctrl+9 hoặc right-click → Hide.
- Hide Col: Ctrl+0 hoặc right-click → Hide.
- Unhide Row: chọn hàng XUNG QUANH hàng ẩn → Ctrl+Shift+9 hoặc right-click → Unhide.
- Unhide Col: tương tự, Ctrl+Shift+0.
- Visual: header bỏ nhảy (vd 4,5,8 → ẩn 6,7).
- Double-click ranh giới ẩn trong header: unhide nhanh.

## 9.4 Group / Outline (§9.4)

### Tạo group
- Chọn hàng/cột → Data → Group → Group.
- Hoặc Alt+Shift+→ (Group) / Alt+Shift+← (Ungroup).
- Auto Outline: Data → Group → Auto Outline (Excel tự detect cấu trúc).

### Visual
- Outline bar bên trái row headers (hoặc trên cùng col headers).
- Dấu `[-]` (expand) / `[+]` (collapse) tại từng group.
- Level buttons `1, 2, 3` góc trên trái: click để collapse/expand đến level N.

### Implementation note
- Cần widget mới bên trái row header (panel outline ~24px). 
- Model: thêm `_outline: dict[int, int]` (row → level), `_outline_col: dict[int, int]`.
- Khi collapse: set row hidden cho range của group.

## Implementation note (model)

- Row Height dialog: ngoài resize trong view, lưu state `_row_heights: dict[int, int]` (đã có dạng nào tương đương?). 
- Insert Cell với shift right: tạo gap → khó hơn insert full row. Cần `_data[row].insert(col, "")` cho 1 hàng; cập nhật `_fmt` shift keys phù hợp.

## Acceptance criteria
1. Right-click row header → Row Height... → nhập 30 → hàng đó cao 30 points.
2. Chọn cột B, C; double-click ranh giới C/D → cả B và C autofit cùng width nội dung dài nhất của mỗi cột (riêng từng cột).
3. Ctrl+9 ẩn hàng 5; chọn hàng 4-6 → Ctrl+Shift+9 → hàng 5 hiện lại.
4. Chọn cells A1:B3 → Ctrl + - → dialog hiện 4 option; chọn "Shift cells left" → A1:B3 mất, C1:D3 dịch trái.
5. Chọn hàng 5-10 → Alt+Shift+→ → outline bar xuất hiện bên trái, dấu `[-]` ở hàng 11; click → collapse 5-10 ẩn.

## Phụ thuộc
- [02 Cell System](02-cell-system.md) — selection range.
- [06 Context Menus](06-context-menus.md).

## Risk
- Group/Outline cần widget bên trái — phá layout hiện tại. 
- Insert cell với shift partial nguy hiểm: dễ vỡ `_fmt` keys.
