# SPEC 01 — Grid Engine (Layout & Zone Mapping)

## Mục tiêu
Render lưới 16,384 cột × 1,048,576 hàng mượt như Excel, kể cả file lớn (≥ 100k hàng).

## Trạng thái hiện tại
- ✓ QTableView render virtual (Qt tự virtualize). 
- ✓ Row/col header sticky.
- ✗ Số cột/hàng hiện vẫn theo `SpreadsheetModel.rowCount/columnCount` — nên cấp giới hạn rộng (tối thiểu 16,384 × 1,048,576).
- ✗ Hot path `paint()` còn cấp phát — xem performance plan đã viết riêng.

## Layout zones (theo doc §1.1)

| Zone | Chiều cao | Ghi chú |
|---|---|---|
| Title Bar | 32px | QMainWindow native — không tự vẽ |
| Ribbon | 110px / 22px | Toggle Ctrl+F1 hoặc double-click tab |
| Name Box + Formula Bar | 26px | Name Box rộng 80-120px, có thể kéo |
| Column Headers | 20px | A → XFD; sticky |
| Row Headers + Grid | còn lại | Row header 40px wide |
| Sheet Tabs + Scroll | 22px | Tab + nút add + scroll controls |
| Status Bar | 22px | Cell mode + thống kê + zoom |

## Grid dimensions (§1.2)
- Cột tối đa: **16,384** (A → XFD). Cột mặc định **64px** (~8.43 ký tự).
- Hàng tối đa: **1,048,576**. Hàng mặc định **20px** (15pt).
- Max ký tự / ô: 32,767 lưu; chỉ hiển thị 1,024 ký tự đầu trong cell.
- Selection border: viền 2px màu `#217346`.

## Virtual scrolling (§1.3)
- Qt đã handle. Cấm bao giờ tạo full 17 tỷ ô trong memory.
- Sparse data: `_data` hiện là `list[list[str]]` — chấp nhận chừng còn dùng nhưng phải cấp dynamically (không pre-fill).
- Header sticky thông qua `QHeaderView` (đã có).

## Acceptance criteria
1. Mở app trống → scroll Ctrl+→ tới cột cuối → Name Box hiển thị **XFD1**.
2. Ctrl+↓ tới hàng cuối → Name Box hiển thị **A1048576**.
3. Open file 50k hàng × 30 cột → scroll mượt ≥ 60 FPS trên máy dev (i7, 16GB).
4. Resize cột bằng kéo header — không lag, không repaint toàn grid (chỉ vùng visible).
5. Sticky header: scroll xuống/sang phải, A-Z và 1-N luôn nhìn thấy.

## Phụ thuộc
Không có. Nền tảng cho mọi spec khác.

## Liên quan
- [02 Cell System](02-cell-system.md) — addressing
- [11 Status Bar](11-status-bar.md) — zoom slider, view buttons
- Performance plan đã viết riêng cho hot path optimization
