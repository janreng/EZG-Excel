# Ezcel v0.12.3 — Status Bar statistics + customize

**Ngày:** 2026-06-03
**Loại:** Tính năng (Phase 1 — Core UX gap-close, Spec 11.2)

## Có gì mới

Phần thống kê ở thanh trạng thái (giữa) giờ đầy đủ như Excel:

| Item | Mặc định | Tính trên |
|---|---|---|
| Trung bình / Average | ✓ | ô số |
| Đếm / Count | ✓ | ô không rỗng (gồm chữ, TRUE/FALSE) |
| Đếm số / Numerical Count | — | ô số |
| Nhỏ nhất / Min | — | ô số |
| Lớn nhất / Max | — | ô số |
| Tổng / Sum | ✓ | ô số |

- **Chuột phải vào thanh trạng thái** → menu bật/tắt từng item, **lưu lại** (mở lại
  app vẫn nhớ — QSettings). Mặc định Trung bình / Đếm / Tổng như Excel.
- Quy ước Excel chuẩn: **Đếm** gồm cả ô chữ & TRUE/FALSE; còn **Tổng / Trung bình /
  Min / Max / Đếm số** chỉ tính ô SỐ (TRUE/FALSE không cộng vào).

## Sửa (từ review)

- **Đa vùng chọn (Ctrl+Click)** giờ tính đúng các ô được chọn — trước đây gộp cả
  bounding box nên đếm lẫn ô không chọn.
- **Số lớn** không còn hiện ký hiệu khoa học: `1234567` thay vì `1.23457e+06`.

## Kỹ thuật & chất lượng

- Logic tách **module thuần** `statusbar_stats.py` (`compute_stats` + `format_stat_value`)
  — kiểm thử headless. Duyệt **một lượt theo từng range** (không cấp phát list, không
  quét ô ngoài vùng chọn) → giữ hot path nhẹ đúng yêu cầu Spec 11.2.
- Thêm public `model.cell_value()` (thay vì gọi `_cell_value` xuyên module).
- **16 test mới** (9 unit + 7 integration). Review sub-agent (perf + web): *ship*;
  đã vá 2 ý review chỉ ra (đa vùng + format số). Toàn bộ **141/141 test pass**.

## Cài đặt

Tải `Ezcel-Setup-0.12.3.exe` ở phần Assets. Bản đang dùng sẽ tự đề nghị cập nhật.
