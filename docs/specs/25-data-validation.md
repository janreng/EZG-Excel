# SPEC 25 — Data Validation

## Mục tiêu
Validate dữ liệu nhập vào ô: list dropdown, số trong khoảng, ngày trong khoảng, length text, custom formula. Error / input message.

## Trạng thái hiện tại
- ✗ Chưa có.

## Truy cập
Data → Data Validation → Data Validation... → dialog 3 tab.

## 25.1 Tab Settings

**Allow** dropdown:

| Allow | Mô tả |
|---|---|
| Any value | Không validate |
| Whole number | Số nguyên trong điều kiện |
| Decimal | Số thập phân |
| List | Dropdown từ source (range hoặc comma-separated list) |
| Date | Ngày trong điều kiện |
| Time | Giờ trong điều kiện |
| Text length | Length text trong điều kiện |
| Custom | Formula trả TRUE/FALSE |

**Data** (cho Whole number / Decimal / Date / Time / Text length):
- between / not between / equal to / not equal to / greater than / less than / greater than or equal to / less than or equal to

**Source** (cho List):
- Range: `=$A$1:$A$10`
- Static list: `Đúng,Sai,Đang kiểm tra` (separator theo locale: comma hoặc semicolon)
- Named range: `=DanhSachSP`
- **In-cell dropdown** checkbox (default ON): hiện mũi tên ▼ bên cạnh ô khi selected.

**Ignore blank** checkbox (default ON).

**Apply these changes to all other cells with the same settings**: propagate.

## 25.2 Tab Input Message

- Hiển thị khi cell selected (tooltip-like floating box).
- **Show input message when cell is selected** checkbox.
- Title (max 32 chars).
- Input message (max 255 chars).

## 25.3 Tab Error Alert

**Show error alert after invalid data is entered** checkbox.

**Style**:
- **Stop** (red X): không cho nhập, Retry/Cancel.
- **Warning** (yellow ⚠): cảnh báo, Yes (chấp nhận)/No (sửa)/Cancel.
- **Information** (i): thông báo, OK (chấp nhận)/Cancel.

Title + Error message (max 225 chars).

## 25.4 Circle Invalid Data

Data → Data Validation → Circle Invalid Data: tô vòng tròn đỏ quanh ô không hợp lệ (đã có data từ trước hoặc paste).

Data → Data Validation → Clear Validation Circles.

## Model

```python
class DataValidationRule:
    type: "any"|"whole"|"decimal"|"list"|"date"|"time"|"text_length"|"custom"
    operator: "between"|"not_between"|"eq"|"ne"|"gt"|"lt"|"ge"|"le"
    formula1: str | float    # min / list source / formula
    formula2: str | float    # max (cho between)
    in_cell_dropdown: bool
    ignore_blank: bool
    show_input_message: bool
    input_title: str
    input_message: str
    show_error_alert: bool
    error_style: "stop"|"warning"|"information"
    error_title: str
    error_message: str
    applies_to: list[Range]
```

Sheet: `_validations: list[DataValidationRule]`.

## UX flow

### Nhập data
1. User select cell có validation.
2. Show input message tooltip (nếu bật).
3. Nếu List type + in_cell_dropdown: hiện ▼ → click → list values.
4. User gõ → khi Enter, validate:
   - Pass → commit.
   - Fail + Stop style → modal "Retry/Cancel". Retry → focus về Edit. Cancel → khôi phục.
   - Fail + Warning style → "Yes/No/Cancel". Yes → commit (chấp nhận invalid). No → focus Edit.
   - Fail + Information → "OK/Cancel". OK → commit.
5. Paste invalid → không validate paste (Excel behavior); "Circle Invalid Data" highlight sau đó.

## Implementation note

- Hook `setData` của model → check validation → return False nếu Stop, hoặc emit signal yêu cầu MainWindow show dialog.
- List dropdown UI: extend FilterHeaderView style — `QComboBox` overlay khi cell selected có validation List.
- Custom formula: reuse formula engine; resolver bind cell value.

## xlsx mapping
openpyxl: `DataValidation(type=..., operator=..., formula1=..., formula2=..., allow_blank=..., showInputMessage=..., showErrorMessage=..., errorStyle=...)` + `ws.add_data_validation(dv); dv.add(range_str)`.

## Acceptance criteria
1. Select A1:A10 → Data Validation → Allow=List, Source=`Đỏ,Vàng,Xanh` → click A1 → ▼ xuất hiện → dropdown 3 options.
2. Cùng setup → gõ "Tím" → Stop dialog "Retry/Cancel".
3. Setup Date between 2026-01-01 và 2026-12-31, Style=Warning → gõ 2025-01-01 → dialog "Yes/No/Cancel"; Yes → commit.
4. Input Message: title="Lưu ý", text="Chỉ chọn từ danh sách" → click ô → tooltip xuất hiện.
5. Paste data invalid (text vào ô number validation) → no error. Data → Circle Invalid Data → vòng đỏ.
6. Custom formula `=AND(LEN(A1)>=3, LEN(A1)<=10)` → text length 1 → error.
7. Lưu xlsx → mở Excel thật → validation còn nguyên (round-trip).

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — custom formula engine.
- [02 Cell System](02-cell-system.md) — applies_to ranges.

## Risk
Trung bình. List dropdown overlay UI cần hook QTableView selection.
