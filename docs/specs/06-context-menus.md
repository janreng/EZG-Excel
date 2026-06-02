# SPEC 06 — Context Menus + Mini Toolbar

## Mục tiêu
Right-click bốn loại object đều bật menu đúng kiểu Excel; kèm Mini Toolbar floating.

## Trạng thái hiện tại
- ✓ Cell right-click có menu cơ bản (copy/cut/paste/insert/delete/clear).
- ✗ Row header right-click thiếu nhiều mục (Row Height dialog, AutoFit, Unhide).
- ✗ Col header right-click tương tự.
- ✗ Sheet tab right-click chưa có (do chưa multi-sheet).
- ✗ Mini Toolbar floating chưa có.
- ✗ Smart Lookup, Quick Analysis, Get Data from Table chưa có (out of scope phase đầu).

## 6.1 Cell right-click (§6.1)

| Mục | Hành vi |
|---|---|
| Cut (Ctrl+X) | Cắt, marching ants |
| Copy (Ctrl+C) | Copy, marching ants |
| Paste Options | Icon bar: Values / Formulas / Formatting / Transpose / Link |
| Paste Special... (Ctrl+Alt+V) | Dialog đầy đủ — [Spec 13](13-clipboard-paste-special.md) |
| Smart Lookup | Bing search — out of scope |
| Insert... | Dialog: shift right/down / insert row/col |
| Delete... | Dialog: shift left/up / delete row/col |
| Clear Contents (Del) | Xóa nội dung, giữ format |
| Quick Analysis (Ctrl+Q) | Out of scope phase đầu |
| Filter | Sub: by selected value/color/font color |
| Sort | Sub: ascending / descending / custom |
| Get Data from Table/Range | Power Query — [Spec 20](20-power-query.md) |
| New Comment / Edit Comment | Phase sau |
| New Note / Edit Note | Phase sau |
| Format Cells... (Ctrl+1) | Mở dialog 6 tab — [Spec 08](08-format-cells-dialog.md) |
| Pick From Dropdown List | List unique text trong cột — [Spec 05](05-data-entry-autofill.md) |
| Define Name... | Phase sau |
| Link (Hyperlink) | Phase sau |

## 6.2 Row header right-click (§6.2)
- Insert (chèn phía trên)
- Delete
- Clear Contents
- Format Cells (toàn hàng)
- Row Height... — dialog nhập số (points)
- AutoFit Row Height — đã có (double-click border)
- Hide / Unhide (Unhide chỉ enable khi có hàng ẩn liền kề trong selection)

## 6.3 Col header right-click (§6.3)
- Insert (chèn phía trước)
- Delete
- Column Width... — dialog nhập số (characters)
- AutoFit Column Width
- Hide / Unhide

## 6.4 Sheet tab right-click (§6.4) — Phase 3
- Insert... (dialog chọn loại: Worksheet/Chart/Macro)
- Delete (warning: không undo)
- Rename
- Move or Copy... (dialog: vị trí + checkbox Create a Copy)
- View Code (VBA — Phase 6)
- Protect Sheet... (Phase sau)
- Tab Color (color picker)
- Hide / Unhide... (dialog chọn sheet)
- Select All Sheets (group mode — thao tác đồng thời trên nhiều sheet)

## 6.5 Mini Toolbar (Floating Format Bar) (§6.5)

### Trigger
- Right-click cell → mini toolbar xuất hiện **phía trên** context menu (mờ dần sau ~2s nếu không hover).
- Select text trong Edit mode (như Word) → cũng xuất hiện.

### Layout
- Font dropdown, Size dropdown
- Bold, Italic, Underline
- Decrease/Increase Font Size (A-, A+)
- Highlight Color (fill), Font Color
- Comma Style, Currency, Percent
- Increase/Decrease Decimal
- Merge & Center
- Borders dropdown

### Implementation note
- `QToolBar` floating, parent là `QWidget` top-level, position theo cursor.
- Auto-hide bằng `QTimer.singleShot(2000, ...)` reset khi mouse enter.

## Acceptance criteria
1. Right-click cell → menu hiện Mini Toolbar phía trên + main menu phía dưới. Không hover 2s → Mini Toolbar mờ.
2. Right-click row header → menu có "Row Height..." (dialog) và "AutoFit Row Height".
3. Right-click col header với selection nhiều cột (B+D) trong đó cột C ẩn → "Unhide" enable.
4. Trong Edit mode, select text "abc" → Mini Toolbar floating xuất hiện cạnh selection.

## Phụ thuộc
- [08 Format Cells Dialog](08-format-cells-dialog.md) — Mini Toolbar buttons mở dialog.
- [09 Row/Col Operations](09-row-col-operations.md) — Row Height dialog, AutoFit.

## Risk
Thấp. UI thuần.
