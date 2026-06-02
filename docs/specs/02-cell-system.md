# SPEC 02 — Cell System (Địa chỉ, Trạng thái, Selection)

## Mục tiêu
Mọi cell có địa chỉ chuẩn Excel; selection hỗ trợ single / range / multi-range / row / column / select-all; trạng thái visual khớp với Excel.

## Trạng thái hiện tại
- ✓ Single, contiguous range, entire row/col, select-all.
- ✓ Shift+Arrow, Shift+Ctrl+Arrow (mở rộng đến mép data).
- ✗ **Multi-range (Ctrl+Click)** — chưa hỗ trợ; Name Box chưa parse `A1:B3,D5,F1:F10`.
- ✗ **Spill range visual** (dynamic array).
- ✗ **Tam giác đỏ comment / xanh formula error indicator** chưa có.

## Cell addressing (§2.1)

| Loại | Ký hiệu | Hành vi |
|---|---|---|
| Relative | `A1` | Đổi theo vị trí khi copy/fill |
| Absolute | `$A$1` | Cố định |
| Mixed - cố định cột | `$A1` | |
| Mixed - cố định hàng | `A$1` | |
| Whole column | `A:A` | |
| Whole row | `1:1` | |
| Named Range | `DoanhThu` | |
| Structured (Table) | `Table1[Col1]` | Phase 3 — [Table spec](16-table.md) |
| 3D Reference | `Sheet1:Sheet3!A1` | Phase 3 — [Multi-sheet](10-sheet-tabs.md) |
| External | `[File.xlsx]Sheet1!A1` | Ngoài phạm vi |

## Cell states visual (§2.2)

| State | Visual | Trigger |
|---|---|---|
| Normal | gridline | mặc định |
| Hover | nền nhạt theo theme | mouse over |
| Selected single | viền xanh 2px `#217346`, nền trắng | click trái |
| Selected range | viền bao quanh, nền xanh nhạt | drag / Shift+Arrow |
| Active trong range | viền đậm, nền trắng | ô đầu của selection |
| Edit mode | cursor nhấp nháy + viền xanh | F2 / double-click / gõ |
| Formula reference highlight | cell ref tô màu khác nhau | trong Edit + có formula |
| Error cell | tam giác xanh lá góc trên trái | #VALUE!, #REF!, #N/A... |
| Comment | tam giác đỏ góc trên phải | có comment/note |
| Overflow text | text tràn sang ô trống bên phải | text dài hơn cột |
| Spill range | viền nét đứt xanh | dynamic array |

## Selection types (§2.3)

### Single cell
- Click trái → chọn 1 ô; Name Box hiện địa chỉ; Status Bar hiện giá trị nếu là số.

### Contiguous range
- Click & drag.
- Shift + Click: từ active cell đến cell vừa click.
- Shift + Arrow: mở rộng từng ô.
- Shift + Ctrl + Arrow: đến mép data.
- Shift + Ctrl + End / Home: đến cuối / về A1.

### Non-contiguous (multi-range) — **PHẢI LÀM**
- Ctrl + Click thêm ô vào selection.
- Ctrl + Drag thêm vùng liền mạch.
- Name Box gõ `A1:B3,D5,F1:F10` → chọn nhiều vùng.
- Render: mỗi vùng tô xanh riêng, ô active trắng.
- Lưu trữ: `list[QItemSelectionRange]` — đã có sẵn trong QItemSelectionModel.

### Entire row / column
- Click row header → toàn hàng. Click col header → toàn cột.
- Shift + Click header → range hàng/cột liền.
- Ctrl + Click header → multiple không liền.
- Ctrl + Spacebar / Shift + Spacebar → entire col/row của active.

### Select all
- Ctrl + A: lần 1 chọn Table (nếu trong Table — Phase 3); lần 2 chọn toàn sheet.
- Click ô góc trên trái → toàn sheet.

## Acceptance criteria
1. Click A1, Ctrl+Click C3, Ctrl+Drag E5:F10 → Name Box hiện `A1`, viền 3 vùng riêng biệt, Status Bar hiện Sum tổng tất cả ô số.
2. Gõ `A1:B3,D5` vào Name Box + Enter → chọn 2 vùng đúng.
3. Click col header A → toàn cột A xanh; Status Bar hiện `Count: 1048576`.
4. Ctrl+A trong vùng data → chọn current region; Ctrl+A lần 2 → chọn toàn sheet.
5. Ô có comment hiện tam giác đỏ góc trên phải; hover hiện tooltip nội dung.

## Phụ thuộc
- [01 Grid Engine](01-grid-engine.md) (basic addressing).

## Liên quan
- [03 Cell Modes](03-cell-modes.md) — visual khi vào Edit
- [04 Name Box](04-name-box-formula-bar.md) — parse multi-range
