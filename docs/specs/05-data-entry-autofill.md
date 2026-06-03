# SPEC 05 — Data Entry, AutoFill, AutoComplete, Flash Fill

## Mục tiêu
Bốn cơ chế điền dữ liệu của Excel: nhập tay, AutoFill (fill handle), AutoComplete (text column), Flash Fill (Ctrl+E).

## Trạng thái hiện tại
- ✓ AutoFill có (núm xanh, drag, Ctrl+D / Ctrl+R, recognize số đơn / series 1,2 / text+số `Item1`).
- ✓ Công thức autofill dịch tham chiếu tương đối, giữ `$`.
- ✗ AutoComplete cột text chưa có.
- ✗ Pick From Dropdown List chưa có.
- ✗ Flash Fill (Ctrl+E) chưa có.
- ✗ Auto Fill Options button (icon ở cuối fill) chưa có.
- ✗ Drag & drop cells (move/copy vùng) chưa có.
- ✗ Right-click drag → menu chưa có.
- ✗ Pattern day/month/quarter chưa có (đã có ordinal? — chưa).

## Confirm key (§5.1)
Xem [03 Cell Modes](03-cell-modes.md).

## AutoComplete (§5.2)
- **Chỉ với text**, **chỉ trong cùng cột**.
- Khi gõ trong cột đã có text: scan từ đầu cột → tìm match theo prefix.
- 1 match duy nhất → hiện inline suggestion (text màu xám).
- Nhiều match → không hiện (Excel mới hơn hiện dropdown).
- Accept: Enter / Tab. Reject: tiếp tục gõ / Delete.
- Setting: File → Options → Advanced → "Enable AutoComplete for cell values".
- Pick From Dropdown List (right-click hoặc Alt+↓): list unique text trong cột.

## Fill Handle / AutoFill (§5.3)

### Mouse
| Thao tác | Kết quả |
|---|---|
| Hover góc dưới phải selection | Con trỏ thành `+` (crosshair đen) |
| Drag | AutoFill theo pattern |
| Double-click | Fill xuống đến cuối data liền kề (cột bên cạnh phải có data) |
| Right-click + drag | Menu sau khi thả: Copy Cells / Fill Series / Fill Formatting Only / Fill Without Formatting / Fill Days/Weekdays/Months/Years |
| Ctrl + drag (fill handle) | **Đảo** hành vi mặc định theo loại seed: số đơn (vd `1`) → **tạo series** 1,2,3…; seed kiểu series (ngày, "Mon", "Q1") → **ép copy**. (Khác với Ctrl+drag trên *viền* selection = copy khối — xem dòng dưới.) |

### Pattern recognition
| Input | Pattern | Fill |
|---|---|---|
| `1` | Số đơn | Copy 1,1,1... |
| `1, 2` | Bước 1 | 3,4,5... |
| `1, 3` | Bước 2 | 5,7,9... |
| `Mon` | Day viết tắt | Tue,Wed... |
| `Monday` | Day đầy đủ | Tuesday,Wednesday... |
| `Jan` / `January` | Tháng | Feb / February... |
| `Q1` | Quarter | Q2,Q3,Q4,Q1... |
| `01/01/2024` | Date | 02/01/2024... |
| `1st, 2nd` | Ordinal | 3rd, 4th... |
| `Product1` | Text + số | Product2,Product3... |
| `=A1` | Formula | =A2,=A3 (relative) |
| `=$A$1` | Absolute | =$A$1,=$A$1 (copy y hệt) |

### Auto Fill Options button
- Sau fill, icon nhỏ xuất hiện ở cuối vùng fill.
- Click → menu:
  - Copy Cells
  - Fill Series
  - Fill Formatting Only
  - Fill Without Formatting
  - Flash Fill

## Flash Fill (§5.4) — Ctrl+E

### Flow
1. User nhập 1-2 ví dụ trong cột bên cạnh data nguồn.
2. Ctrl+E hoặc Data → Flash Fill.
3. Engine phân tích pattern (regex/sub-string/split) → điền các ô còn lại.
4. Trigger tự động: khi gõ ô kế tiếp, Excel có thể gợi ý Flash Fill (text mờ) → Enter accept.

### Ví dụ
- A: `Nguyen Van A` → B: gõ `Nguyen` → Flash Fill hiểu lấy họ → fill toàn cột.
- A: `user@gmail.com` → B: gõ `gmail.com` → Flash Fill tách domain.
- A: `0901234567` → B: gõ `090-123-4567` → format số.

### Implementation note
- Pattern recognition khó — bắt đầu với rules đơn giản (split by space/comma, take token N, lower/upper case, concat). Không cần ML.
- Phase 4 — sau khi formula system stable.

## Drag & Drop cells (§5.5)
- Hover cạnh viền selection → con trỏ thành mũi tên 4 chiều.
- Drag → di chuyển vùng.
- Ctrl + Drag → copy.
- Shift + Drag → insert (chèn vào đích, đẩy cell khác).
- Khi thả lên data: dialog "Replace the contents?" OK/Cancel.
- Drag sang Sheet khác: kéo đến tab Sheet (Phase 3).

## Acceptance criteria
1. Cột A có "An", "Anh", "Ánh"; gõ "A" vào A4 → suggestion mờ "An"; Enter accept → A4 = "An".
2. A1=1, A2=2, fill handle drag tới A10 → 1..10. Right-click drag thay vì left → menu hiện 5 options.
3. A1=`Nguyen Van A`, A2=`Tran Van B`, A3=`Le Thi C`; B1=`A` → Ctrl+E → B2=`B`, B3=`C`.
4. Chọn A1=Jan → double-click núm xanh → fill xuống đến hàng cuối có data ở cột B (vd 12 hàng → Jan..Dec).
5. Sau fill, icon Auto Fill Options xuất hiện cuối vùng → click → menu 5 options.
6. Chọn A1:B3 → hover viền (cursor 4-chiều) → drag sang D1 → A1:B3 di chuyển đến D1:E3. Ctrl+drag → copy.

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — `offset_formula` đã có.
- [03 Cell Modes](03-cell-modes.md) — confirm key behavior.

## Risk
- AutoComplete inline suggestion phải vẽ overlay trong cell delegate (paint sub-text màu xám) — hot path.
- Flash Fill engine: bắt đầu rule-based; ML-based ngoài phạm vi.
