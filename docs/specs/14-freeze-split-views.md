# SPEC 14 — Freeze Panes, Split, Views

## Mục tiêu
Freeze panes (cố định hàng/cột), Split view (chia 2-4 vùng cuộn độc lập), 3 view modes (Normal / Page Layout / Page Break Preview), Multiple Windows.

## Trạng thái hiện tại
- ✓ Freeze panes (3 overlay QTableView — xem `freeze.py`).
- ✗ Freeze Top Row / Freeze First Column (chỉ có Freeze Panes ở active cell).
- ✗ Split view.
- ✗ Page Layout view.
- ✗ Page Break Preview.
- ✗ Multiple Windows (View → New Window).
- ✗ Synchronous Scrolling / Side by Side.
- ✗ Custom Views.

## 14.1 Freeze Panes (§14.1)

| Option | Hành vi |
|---|---|
| Freeze Panes | Cố định MỌI thứ phía trên + bên trái active cell. Ví dụ active C3 → cột A,B + hàng 1,2 freeze |
| Freeze Top Row | Chỉ hàng 1 (bất kể active) |
| Freeze First Column | Chỉ cột A |
| Unfreeze Panes | Hủy |

Visual: đường kẻ đậm hơn gridline tại ranh giới freeze. Vùng freeze không di chuyển khi cuộn.

### Đã làm
- `freeze.py` có 3 overlay (top-left fixed, top-right cuộn ngang, bottom-left cuộn dọc).
- ⚠ Theo CLAUDE.md: `viewport().stackUnder(...)` + nền đục — nếu sửa, kiểm kỹ khi cuộn.

## 14.2 Split View (§14.2)

- View → Split tại active cell: chia worksheet thành 2 (chỉ hàng / chỉ cột) hoặc 4 vùng.
- Mỗi vùng có scroll bar riêng, cuộn độc lập.
- Kéo thanh chia để resize.
- Double-click thanh chia → xóa split.

### Implementation note
- Tương tự freeze nhưng cả 4 vùng đều cuộn được. 
- Cách 1: 4 `QTableView` cùng model, sync selection.
- Cách 2: `QSplitter` ngang + dọc.
- Lưu state per-sheet: `_split_row`, `_split_col` hoặc None.

## 14.3 View Modes (§14.3)

| Mode | Trigger | Mô tả |
|---|---|---|
| Normal | View → Normal / icon ≡ | Mặc định |
| Page Layout | View → Page Layout / icon ▤ | Margin + header/footer; WYSIWYG in ấn |
| Page Break Preview | View → Page Break Preview / icon ▦ | Đường ngắt trang xanh kéo được |
| Custom Views | View → Custom Views | Lưu/load preset (zoom, freeze, hidden rows...) |
| Full Screen | Web Excel | Out of scope |

### Page Layout
- Hiển thị page borders (giấy A4/Letter), white space giữa pages.
- Header/Footer area edit được (3 zone: left/center/right).
- Margins kéo được.
- Status Bar trái hiện "Page X of Y".

### Page Break Preview
- Zoom out 60% mặc định.
- Đường break trang màu xanh đậm; kéo để thay đổi.
- Đường tự động (Excel quyết) màu xanh nhạt.
- Right-click → Reset All Page Breaks.

### Implementation
- Page Layout là **Phase 7** (in ấn). Chỉ stub view buttons trước.
- Layout: scale page width theo cột width tổng + margin. Render rectangle xám quanh từng page.

## 14.4 Multiple Windows (§14.4)

- View → New Window: mở cửa sổ mới cùng workbook (xem 2 sheet cùng lúc, hoặc 1 sheet 2 vùng).
- View → Arrange All: Tile / Horizontal / Vertical / Cascade.
- View → Synchronous Scrolling: cuộn 2 cửa sổ cùng lúc (khi Side by Side bật).
- View → View Side by Side: so sánh 2 workbook side-by-side.

### Implementation note
- Multiple `MainWindow` share cùng `Workbook` instance.
- Title hiển thị `Workbook.xlsx:1` / `Workbook.xlsx:2`.
- Synchronous Scrolling: connect scrollbar valueChanged.
- Quan trọng: dataChanged signal phải broadcast tới tất cả windows.

## Custom Views
- Dialog: list view name + Add / Delete / Show.
- Add → snapshot: zoom, scroll position, hidden rows/cols, filter state, print settings.
- Show → áp state.

## Acceptance criteria
1. View → Freeze Top Row → hàng 1 cố định khi cuộn dọc.
2. View → Freeze First Column → cột A cố định khi cuộn ngang.
3. Active C3 → Freeze Panes → cột A,B + hàng 1,2 cố định.
4. View → Split tại D5 → grid chia 4 vùng; mỗi vùng cuộn riêng.
5. Double-click thanh chia ngang → mất split chiều ngang, còn dọc.
6. View → Page Layout → hiện page boundaries, header/footer area.
7. View → New Window → cửa sổ thứ 2 mở; gõ vào sheet ở window 1 → window 2 cập nhật ngay.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — multi-window share workbook.
- [11 Status Bar](11-status-bar.md) — view buttons.

## Risk
- Multiple windows + sync data change phải dùng signal Qt cẩn thận để tránh recursion.
- Freeze hiện đã ổn — sửa Split phải không phá freeze.
