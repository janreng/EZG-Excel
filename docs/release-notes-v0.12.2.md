# Ezcel v0.12.2 — Cell Mode indicator

**Ngày:** 2026-06-03
**Loại:** Tính năng (Phase 1 — Core UX gap-close, Spec 03)

## Có gì mới

Thanh trạng thái (góc dưới-trái) giờ hiển thị **mode hiện tại của ô** như Excel:

| Mode | Khi nào | Nhãn (VI / EN) |
|---|---|---|
| Ready | Không sửa, đang điều hướng | Sẵn sàng / Ready |
| Enter | Vừa gõ ký tự vào ô (nhập mới) | Nhập / Enter |
| Edit  | F2 / double-click ô có data / soạn trên Formula Bar | Chỉnh sửa / Edit |
| Point | Chọn ô làm tham chiếu khi đang soạn công thức | Trỏ / Point |

> *"Đây là gốc rễ của mọi keyboard behavior"* (Spec 03) — bản này đặt nền: tách
> state machine + hiện indicator để các bản sau gắn hành vi phím theo từng mode.

## Kỹ thuật & chất lượng

- State machine tách **module thuần** `cell_mode.py` (`CellMode` enum + `transition()`)
  — không phụ thuộc Qt, kiểm thử headless. **19 unit test** bám đúng bảng chuyển
  trạng thái Spec 03 (gồm: F2 cycle Edit↔Point, hành trình soạn công thức, Esc 1
  lần về Ready).
- Qt wiring: override `SpreadsheetView.edit()` để phân biệt Enter (gõ) vs Edit
  (F2/double-click); hook `closeEditor` / commit / Esc / đổi ô → Ready; `cellPicked`
  → Point. Smoke test offscreen xác nhận đủ 4 mode đổi đúng.

## Hoãn sang bản sau

- **Point mode bằng phím mũi tên**: gõ `=` rồi ↑↓ để chọn/mở rộng tham chiếu (thay
  vì commit + di chuyển ô). Đây là phần xâm lấn nhất (hook key cấp thấp, dễ xung đột
  QTableView) — tách riêng để bản này an toàn. Hiện Point kích hoạt qua **click ô**.

## Cài đặt

Tải `Ezcel-Setup-0.12.2.exe` ở phần Assets. Bản đang dùng sẽ tự đề nghị cập nhật.
