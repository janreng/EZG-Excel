# SPEC 32 — Find / Replace / Go To

## Mục tiêu
Find & Replace dialog đầy đủ (options panel, Find All result list); Go To + Go To Special.

## Trạng thái hiện tại
- ✓ Ctrl+F popup find (tự vòng).
- ✓ Ctrl+H Replace (có "Match case").
- ✗ Options panel: Within (Sheet/Workbook), Search (By Rows/Columns), Look in (Formulas/Values/Comments/Notes), Match entire cell, Format-based search.
- ✗ Find All → result list.
- ✗ Go To dialog (F5).
- ✗ Go To Special (F5 → Special).

## 32.1 Find & Replace Dialog (Ctrl+F / Ctrl+H)

### Layout (Find tab)
```
┌─ Find and Replace ──────────────────────────────────────┐
│ [Find] [Replace]                                         │
│ Find what: [                                          ▼] │
│            [Format... ▼] (preview swatch)               │
│                                                          │
│ [Options >>]                                             │
│  Within:        [Sheet     ▼]                            │
│  Search:        [By Rows   ▼]                            │
│  Look in:       [Formulas  ▼]                            │
│  ☐ Match case                                            │
│  ☐ Match entire cell contents                            │
│                                                          │
│       [Find All] [Find Next] [Close]                     │
│ ─────────────────────────────────────────────────────── │
│ (Find All results table:)                                │
│ Book | Sheet | Name | Cell | Value | Formula             │
│ wb1  | Sheet1|      | $A$5 | 100   | =B5*2               │
│ ...                                                      │
└──────────────────────────────────────────────────────────┘
```

### Replace tab thêm field:
- "Replace with" + dropdown history + Format
- Buttons: Replace All / Replace / Find Next / Find All

### Options
| Option | Mô tả |
|---|---|
| Within | Sheet / Workbook |
| Search | By Rows (left→right, top→bottom) / By Columns |
| Look in | Formulas (raw text) / Values (rendered) / Comments / Notes |
| Match case | Case-sensitive |
| Match entire cell contents | Exact full match |
| Format | Match cells với specific format (font/fill/border/...) |

### Format search
- Click "Format..." → mini Format Cells dialog → set criteria.
- Click "Choose Format From Cell..." → eyedropper → click cell sample.

### Wildcards (Look in = Formulas/Values)
- `?` = 1 char
- `*` = 0+ chars
- `~?`, `~*` = literal

### Find All result list
- Click row → navigate đến cell.
- Sortable columns.
- Multi-select → Replace operates on selected only.

## 32.2 Go To Dialog (F5 / Ctrl+G)

### Layout
```
┌─ Go To ─────────────────────────────────┐
│ Go to:                                  │
│  ┌──────────────────────────────────┐   │
│  │ Sheet2!A5                         │   │
│  │ DoanhThu (named range)            │   │
│  │ ...                                │   │
│  └──────────────────────────────────┘   │
│ Reference: [                          ] │
│                                          │
│ [Special...]    [OK] [Cancel]            │
└──────────────────────────────────────────┘
```

- Lịch sử Go To (max 4 gần nhất).
- Reference: gõ địa chỉ / named range / external `[File.xlsx]Sheet1!A1`.

## 32.3 Go To Special

Click Special... → dialog:

| Option | Mô tả |
|---|---|
| Comments | Cells có comment |
| Constants | Cells có giá trị hard-coded (không phải formula). Sub: Numbers / Text / Logicals / Errors. |
| Formulas | Cells có formula. Sub: Numbers / Text / Logicals / Errors. |
| Blanks | Cells trống |
| Current region | Vùng data liên tục quanh active (Ctrl+Shift+*) |
| Current array | Toàn array formula của active |
| Objects | Charts, images, shapes |
| Row differences | Cells khác giá trị so với active cell trên cùng hàng |
| Column differences | Tương tự, cùng cột |
| Precedents | Cells mà active phụ thuộc. Sub: Direct only / All levels |
| Dependents | Cells phụ thuộc active. Sub: Direct only / All levels |
| Last cell | Ô cuối cùng có data |
| Visible cells only | Bỏ qua cells ẩn (filter / hidden row) |
| Conditional formats | Cells có CF rule |
| Data validation | Cells có validation. Sub: All / Same |

OK → tất cả cells match được selected (multi-range).

## 32.4 Shortcut "Visible cells only"

Alt+; → giống Go To Special → Visible cells only. Hữu ích khi copy data đã filter — chỉ copy hàng visible.

## Implementation note

- Engine search: iterate cells trong scope (sheet / workbook); với "Look in":
  - Formulas → match raw `_data[r][c]`.
  - Values → match rendered value (number formatted, evaluated formula result).
- Wildcard → translate sang regex (`?`→`.`, `*`→`.*`, `~?`→`\?`).
- Find All result: list[(workbook, sheet, name, addr, value, formula)] → render trong `QTableView` con trong dialog.
- Go To Special "Precedents/Dependents": dùng dependency graph (đã/cần có cho formula engine).

## Acceptance criteria
1. Ctrl+F → "abc" → Find Next → cycle qua tất cả "abc" trên sheet.
2. Ctrl+F → Options → Within=Workbook → tìm xuyên toàn workbook (multi-sheet).
3. Find with wildcard `Nguyen*` → match `Nguyen Van A`, `Nguyen Thi B`.
4. Find → Match case → "ABC" không match "abc".
5. Find → Format → fill yellow → chỉ tìm cells background vàng.
6. Find All → result list 5 matches → click row 3 → cell active jump đến.
7. F5 → gõ `Z100` → Enter → jump. Reference history lưu lại.
8. F5 → Special → Blanks → tất cả ô trống trong selection (hoặc sheet) được chọn.
9. F5 → Special → Formulas → Errors → chỉ chọn cells `#VALUE!`, `#REF!`, ...
10. Filter cột → copy → paste — chỉ paste hàng visible (Alt+; logic).

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — Within=Workbook.
- [12 Formula System](12-formula-system.md) — precedents/dependents.
- [25 Data Validation](25-data-validation.md), [17 Conditional Formatting](17-conditional-formatting.md), [26 Comments](26-comments-notes.md) — Go To Special filters.

## Risk
Thấp-trung bình. Workbook-wide search trên file lớn (1M+ cells) cần stream + cancel button.
