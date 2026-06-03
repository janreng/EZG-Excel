# Ezcel v0.12.1 — Name Box "Go To"

**Ngày:** 2026-06-03
**Loại:** Tính năng (Phase 1 — Core UX gap-close, Spec 04)

## Có gì mới

Thanh **Name Box** (ô địa chỉ góc trái thanh công thức) giờ điều hướng đúng kiểu Excel:

| Gõ vào Name Box | Kết quả |
|---|---|
| `A1`, `$A$1`, `z50` | Nhảy & chọn ô đó (không phân biệt hoa thường) |
| `A1:C5`, `C5:A1` | Chọn vùng (tự chuẩn hóa nếu gõ ngược) |
| `A:A`, `A:C` | Chọn cả cột / dải cột |
| `1:1`, `2:5` | Chọn cả hàng / dải hàng |

- **F5** hoặc **Ctrl+G** → Go To: nhảy con trỏ vào Name Box, bôi đen sẵn để gõ.
- **Esc** trong Name Box → hủy, khôi phục địa chỉ ô đang chọn, trả focus về lưới.
- Tham chiếu vượt biên lưới được **kẹp về biên**; cú pháp sai hoặc ngoài lưới hẳn
  → hộp thoại **"Tham chiếu không hợp lệ."**, không đổi vùng chọn.

## Kỹ thuật & chất lượng

- Lõi phân tích tách thành hàm thuần `formula.parse_grid_reference(text, n_rows, n_cols)`
  — kiểm thử headless, không phụ thuộc Qt. **25 unit test** (gồm các ca biên do review chỉ ra:
  `$` trên dải cột/hàng, hàng 0/0x, range trộn cột-hàng, số hàng khổng lồ không tràn int).
- Regex **compile-once** ở cấp module — không cấp phát thừa trên hot path (chạy mỗi lần Enter).
- Đã qua 2 vòng review sub-agent: (1) code + research chuẩn Excel Go To trên web,
  (2) rà soát bộ tài liệu UX flow.

## Hoãn sang Phase sau (hiện hiển thị hộp thoại lỗi, không crash)

- Named range trong Name Box (cần Spec 31 — Name Manager).
- Vùng rời rạc `A1:B3,D5` (cần lớp vẽ đa vùng).
- Tham chiếu chéo sheet `Sheet2!A1` (cần multi-sheet — Phase 3).

## Cài đặt

Tải `Ezcel-Setup-0.12.1.exe` ở phần Assets. Bản đang dùng sẽ tự đề nghị cập nhật.
