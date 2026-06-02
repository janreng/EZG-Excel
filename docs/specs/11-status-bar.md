# SPEC 11 — Status Bar (Toàn bộ Indicators)

## Mục tiêu
Status Bar 3 vùng: Cell Mode + thông tin (trái), Statistics (giữa), View + Zoom (phải). Right-click customize items.

## Trạng thái hiện tại
- ✓ Có Sum / Avg / Count ở giữa (cơ bản).
- ✗ Cell Mode label (Ready/Enter/Edit/Point) — chưa.
- ✗ Macro Recording indicator, Accessibility indicator — chưa.
- ✗ View buttons (Normal / Page Layout / Page Break Preview) — chưa.
- ✗ Zoom slider (10%-400%) + zoom level button — chưa (chỉ có menu Zoom).
- ✗ Right-click customize — chưa.
- ✗ Numerical Count, Min, Max items — chưa.

## 11.1 Phần trái

| Indicator | Mô tả |
|---|---|
| **Cell Mode** | `Ready` / `Enter` / `Edit` / `Point` — bám sát [03 Cell Modes](03-cell-modes.md) |
| Macro Recording | Biểu tượng `■` khi đang record — Phase VBA |
| Accessibility Checker | Biểu tượng xe lăn nếu có issue — Out of scope |
| Save state | "Saved" / "Saving..." nhỏ (optional) |

## 11.2 Phần giữa — Statistics

Khi chọn nhiều ô số:

| Item | Default | Mô tả |
|---|---|---|
| Average | ✓ | Trung bình các ô số |
| Count | ✓ | Đếm ô không trống (bao gồm text) |
| Numerical Count | ✗ | Đếm ô có số |
| Min | ✗ | Giá trị nhỏ nhất |
| Max | ✗ | Giá trị lớn nhất |
| Sum | ✓ | **Quan trọng nhất** |

Right-click Status Bar → checklist bật/tắt từng item.

### Implementation note
- Hot path: tính khi selection đổi (`selectionChanged`). Không duyệt từng `QModelIndex` — phá hot path khi chọn cả cột (1M cells). Lấy bounding box từ `selectionModel().selection()` ranges (O(số vùng)).
- Cache: nếu selection không đổi data, không tính lại.

## 11.3 Phần phải — View & Zoom

### View buttons (theo §14.3)

| Mode | Phím / Menu | Mô tả |
|---|---|---|
| Normal | icon "≡" | Mặc định |
| Page Layout | icon "▤" | Hiện margin, header/footer; WYSIWYG in ấn |
| Page Break Preview | icon "▦" | Đường ngắt trang xanh (kéo được) |

### Zoom slider
- Trái nút `-` → zoom -10%.
- Slider 10% → 400%.
- Phải nút `+` → zoom +10%.
- Click số % → mở Zoom dialog (75, 100, 150, Fit selection, Custom).

### Implementation note
- Zoom level lưu ở `_zoom` (workbook hoặc per-sheet). 
- Apply: scale `QTableView.setStyleSheet()` font + row/col size — hoặc transform painter trong delegate (phức tạp).
- Ctrl+Scroll wheel: trigger zoom (Excel cũng vậy).

## Right-click customize Status Bar

Menu hiện checklist:
- Cell Mode ✓
- Flash Fill suggestions
- Average ✓
- Count ✓
- Numerical Count
- Min
- Max
- Sum ✓
- View Shortcuts ✓
- Zoom Slider ✓
- Zoom ✓
- ...

QSettings lưu state.

## Acceptance criteria
1. Click 1 ô trống → Status Bar trái = `Ready`. Bắt đầu gõ → `Enter`. Esc → `Ready`.
2. Chọn 5 ô số (1,2,3,4,5) → Status Bar giữa hiện `Average: 3   Count: 5   Sum: 15`.
3. Right-click Status Bar → bật Min/Max → 5 ô trên hiện thêm `Min: 1   Max: 5`.
4. Click icon Page Layout → grid chuyển sang view margin + header/footer (Phase sau cùng OK nếu chỉ stub).
5. Ctrl + scroll wheel → zoom level đổi; slider update; số % update.
6. Restart app → custom items (Min/Max bật) vẫn còn nhờ QSettings.

## Phụ thuộc
- [03 Cell Modes](03-cell-modes.md) — Cell Mode label.
- [14 Freeze/Split/Views](14-freeze-split-views.md) — Page Layout, Page Break Preview.

## Risk
Thấp-trung bình. Stats hot path quan trọng (đã có lesson trong performance plan).
