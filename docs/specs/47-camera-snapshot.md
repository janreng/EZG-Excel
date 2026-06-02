# SPEC 47 — Camera Tool (Live Picture Linked to Range)

## Mục tiêu
Snapshot vùng cells, paste như **picture sống** (cập nhật khi source data đổi). Khác từ chụp screenshot tĩnh.

## Trạng thái hiện tại
- ✗ Chưa có.

## 47.1 Camera Tool

### Truy cập
- Mặc định ẨN trong Excel 365. User phải add manual vào QAT:
  - File → Options → Quick Access Toolbar → All Commands → "Camera" → Add.
- Hoặc ribbon customize: add Camera button.

### Flow
1. Chọn range (vd A1:D10).
2. Click Camera button.
3. Cursor đổi thành crosshair.
4. Click bất kỳ đâu trong sheet (cùng hoặc sheet khác).
5. **Live picture** xuất hiện = render của A1:D10. Resize/move như shape.

### Properties
- Linked: data trong A1:D10 đổi → picture auto-update (re-render).
- Formula picture: `=A1:D10` trong Formula Bar khi click picture.
- Format: Picture Format tab áp dụng (border, shadow, etc.).
- Print: in được.

## 47.2 Paste As Linked Picture

Alternative: Copy range → Right-click → Paste Special → **Linked Picture** (icon eyedropper-like).
- Same effect: live picture.

## 47.3 Use cases

- Dashboard: gộp nhiều bảng từ nhiều sheets vào 1 dashboard sheet.
- Cross-sheet preview: thấy data sheet khác mà không cần switch.
- Print: arrange flexibly trên trang.

## Implementation note

### Model
```python
class LinkedPicture(Shape):  # extends Shape from [Spec 34]
    type = "linked_picture"
    source_range: Range            # vd Sheet1!A1:D10
    position: (x, y, w, h)
    rendered_image: QPixmap | None # cache
    last_render_hash: int          # detect when source changes
```

### Render
- `delegate.paint()` cho cell chứa LinkedPicture: render `rendered_image` vào cell rect.
- Hoặc overlay `QGraphicsView` (như Shapes).
- Invalidate cache khi source range data hoặc format thay đổi.
- Re-render bằng cách `QTableView.render(painter, rect, source_rect)` của source range.

### Performance
- Hot path: nếu source range thay đổi nhiều ô, không re-render mỗi cell change → dùng `QTimer.singleShot(100, render)` debounce.
- Cache rendered QPixmap; chỉ re-render khi `source_range_hash` thay đổi.

## Acceptance criteria
1. Chọn A1:D10 (có data + format) → Camera button → click vào F2 → picture xuất hiện hiển thị nội dung A1:D10.
2. Đổi A1 = 100 → picture auto-update.
3. Đổi background A2 = vàng → picture update.
4. Click picture → Formula Bar hiện `=Sheet1!$A$1:$D$10`.
5. Move picture → giữ link nguyên.
6. Resize picture → content scale (giữ proportion theo source).
7. Save xlsx → reopen → picture còn link + content render.

## Phụ thuộc
- [34 Shapes / Images](34-shapes-images-smartart.md) — overlay shape infrastructure.
- [01 Grid Engine](01-grid-engine.md) — render source range.

## Risk
Trung bình. Re-render trên data change: cần debounce + hash check để tránh perf hit.

## Phase
Phase 7+. Sau khi Shapes ([Spec 34]) ổn.
