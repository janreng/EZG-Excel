# SPEC 10 — Sheet Tabs (Multi-sheet Workbook)

## Mục tiêu
Một file chứa nhiều sheet; thanh tab dưới cùng; tham chiếu chéo sheet trong formula.

## Trạng thái hiện tại
- ✗ Một sheet/file. Toàn bộ `MainWindow` giữ MỘT `SpreadsheetModel`.
- ✗ Chưa có tab bar.
- ✗ Chưa có khái niệm `Workbook`.

## Kiến trúc refactor

### Class mới
```python
class Workbook:
    sheets: list[SpreadsheetModel]
    names: list[str]               # tên sheet
    active: int                    # index sheet đang xem
    tab_colors: dict[int, str]     # hex màu tab
    hidden: set[int]               # sheet ẩn
```

### Refactor `MainWindow`
- `self.model` → `self.workbook` + `self.workbook.active_sheet()`.
- Đổi tab: `view.setModel(workbook.sheets[i])` + update Formula Bar / Name Box / Status Bar binding.
- **Per-sheet state**: freeze config, filters, undo history phải di chuyển từ MainWindow vào model (đã có một phần).

### UI tab bar
- `QTabBar` dưới cùng cuối main window (trên Status Bar).
- Left: scroll buttons `◄ ►` (right-click hiện list sheets).
- Mid: tabs (tên, current highlight).
- Right: nút `+` add sheet.

## Sheet operations (§10 + §6.4)

| Thao tác | Cách |
|---|---|
| Tạo sheet | Click `+` / Right-click → Insert / Shift+F11 |
| Rename | Double-click tab → text editable / Right-click → Rename |
| Xóa | Right-click → Delete (warning: KHÔNG undo) |
| Move | Drag tab trái/phải (line guide khi drag) |
| Copy | Ctrl + Drag tab / Right-click → Move or Copy → check "Create a copy" |
| Tab Color | Right-click → Tab Color → color picker |
| Hide | Right-click → Hide |
| Unhide | Right-click → Unhide... → dialog chọn sheet ẩn |
| Navigate | Ctrl+Page Down (next) / Ctrl+Page Up (prev) |
| List sheets | Right-click nút scroll ◄ ► trái tabs |
| Group sheets | Shift+Click (liền) / Ctrl+Click (không liền). Title hiện `[Group]` |
| Ungroup | Click tab ngoài group / Right-click → Ungroup Sheets |

⚠ **Group mode nguy hiểm**: thao tác trên 1 sheet áp dụng tất cả sheet trong group.

## Tham chiếu chéo sheet trong formula

- Cú pháp: `Sheet1!A1`, `'Sheet With Space'!A1` (quote nếu có space).
- 3D Reference: `Sheet1:Sheet3!A1` — cùng ô trên nhiều sheet liên tiếp.
- External: `[File.xlsx]Sheet1!A1` — Out of scope.

### Implementation
- `formula.py`: token CELL mở rộng regex để match `(?:'[^']+'|[A-Za-z_]\w*)!([A-Z]+\d+)`.
- Resolver: hiện `resolver(row, col) → value`; mở rộng `resolver(sheet_id, row, col)`. Workbook-aware.
- Range trên cùng sheet vẫn `A1:B3`; chéo sheet `Sheet1!A1:B3`.

## File I/O đa sheet

- `load_xlsx`: lặp `wb.worksheets` → tạo `SpreadsheetModel` cho mỗi sheet.
- `save_xlsx`: tạo nhiều `wb.create_sheet(name)`, ghi data + format từng sheet.
- CSV: chỉ 1 sheet — khi lưu workbook có >1 sheet, cảnh báo "Chỉ lưu sheet active".

## Acceptance criteria
1. Click `+` → sheet mới `Sheet2`; active chuyển sang.
2. Double-click `Sheet2` tab → editable; gõ `Doanh thu` + Enter → tên đổi.
3. Right-click tab → Tab Color → đỏ → tab có vạch đỏ.
4. Trong `Sheet2!A1` gõ `=Sheet1!A1+10` → kết quả = giá trị Sheet1!A1 + 10.
5. Ctrl+Page Down → chuyển sang sheet sau.
6. Shift+Click tab 1 và 3 → title hiện `[Group]`; gõ `hello` vào A1 → cả 3 sheet đều `hello` ở A1.
7. Lưu .xlsx (3 sheet) → đóng → mở lại → cả 3 sheet còn nguyên data + tên + màu.

## Phụ thuộc
- [01 Grid Engine](01-grid-engine.md), [02 Cell System](02-cell-system.md) — base.
- [12 Formula System](12-formula-system.md) — parser mở rộng.

## Risk
**Cao.** Refactor kiến trúc lớn. Per-sheet state (freeze, filter, undo) phải được di chuyển hết về model — nếu sót thì state nhầm giữa các sheet.
