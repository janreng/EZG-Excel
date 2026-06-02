# SPEC 29 — Protection (Sheet / Workbook / Range / Encryption)

## Mục tiêu
Bảo vệ data: protect sheet, protect workbook structure, allow edit ranges, encryption (password to open).

## Trạng thái hiện tại
- ✗ Chưa có.

## 29.1 Protect Sheet (Review → Protect Sheet)

### Dialog
- Password to unprotect (optional).
- "Allow all users of this worksheet to:" checkbox list:
  - Select locked cells (default ✓)
  - Select unlocked cells (default ✓)
  - Format cells
  - Format columns
  - Format rows
  - Insert columns
  - Insert rows
  - Insert hyperlinks
  - Delete columns
  - Delete rows
  - Sort
  - Use AutoFilter
  - Use PivotTable & PivotChart
  - Edit objects
  - Edit scenarios

### Hành vi
- Cell có `_fmt.locked = True` (default) → không edit được.
- Cell có `_fmt.locked = False` → editable kể cả sheet protected (cần set trước khi protect: Format Cells → Protection tab → bỏ Locked).
- Cell có `_fmt.hidden = True` → formula ẩn khỏi Formula Bar (chỉ thấy result).

## 29.2 Protect Workbook (Review → Protect Workbook)

- Structure: chặn thêm/xóa/đổi tên/move sheet, hide/unhide sheet.
- Windows: chặn resize/move window (Excel cũ).
- Password.

## 29.3 Allow Edit Ranges (Review → Allow Edit Ranges)

Cho phép sửa vùng cụ thể ngay cả khi sheet protected — tùy thuộc password riêng / user permission.

### Dialog
- New Range:
  - Title
  - Refers to cells (range)
  - Range password (optional)
  - Permissions (Domain user list — bỏ qua nếu standalone)

## 29.4 Mark as Final (File → Info → Protect Workbook → Mark as Final)

- Workbook read-only, edit cảnh báo "marked as final".
- Không phải bảo mật, chỉ là hint.

## 29.5 Encrypt with Password

- File → Info → Protect Workbook → Encrypt with Password.
- Password required to **open** file.
- Algorithm: AES-256 (.xlsx hiện đại). Workbook structure + content được encrypt.

### Implementation note
- openpyxl chỉ đọc/ghi file không protected. Encrypted xlsx cần `msoffcrypto-tool` library (Python) để decrypt/encrypt → handle separately trong `io_utils`.
- UI: dialog "Workbook is encrypted, enter password" khi mở.

## 29.6 Digital Signature

- File → Info → Protect Workbook → Add a Digital Signature.
- Cần certificate.
- Phase rất muộn / out of scope.

## Implementation note (Sheet Protection)

### Model
```python
class SheetProtection:
    enabled: bool
    password_hash: str | None     # SHA-1 với salt (theo openpyxl)
    allow: dict[str, bool]        # checkbox list state
    edit_ranges: list[EditRange]  # title, range, password_hash, users
```

### Hook
- Trong `setData`: check `_protection.enabled` → check cell's `_fmt.locked` → check `edit_ranges` matching → reject + dialog "Cell is protected" hoặc prompt password.
- `delegate.paint()`: cell hidden + formula → hiển thị value, formula bar empty.
- Disable ribbon buttons theo `allow` flags (Format Cells / Insert Row / ...).

### Password hashing
- openpyxl dùng PasswordHasher (xlsx legacy hash). Match để compatible Excel.

## Acceptance criteria
1. Cells A1:B3 chọn → Format Cells → Protection → bỏ Locked → OK. Review → Protect Sheet → password "abc" → OK.
2. Click cell C5 (locked) → gõ → dialog "Cell is protected".
3. Click A1 (unlocked) → gõ "hi" → OK.
4. Review → Unprotect Sheet → enter "abc" → unlocked.
5. Encrypt with Password "xyz" → save → close → open → dialog password → enter "xyz" → mở được.
6. Protect Workbook → Structure → user không thể add/delete/rename sheet (menu disabled).
7. Allow Edit Ranges → range D1:E5 password "qwe" → sheet protected → click D1 → dialog "Enter password for range: Range1" → "qwe" → unlock cho session.

## Phụ thuộc
- [08 Format Cells](08-format-cells-dialog.md) — Protection tab.
- `msoffcrypto-tool` (optional) — encryption.

## Risk
- Encryption: dependency lớn (`cryptography` underlying). Phase muộn.
- Password hashing phải match Excel legacy để file mở qua lại.
