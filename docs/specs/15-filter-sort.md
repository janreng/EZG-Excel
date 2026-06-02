# SPEC 15 — Filter & Sort

## Mục tiêu
AutoFilter dropdown đầy đủ (search box, sort, sub-menu Text/Number/Date filters); Sort dialog multi-level.

## Trạng thái hiện tại
- ✓ AutoFilter có (ô header → nút phễu, list checkbox).
- ✓ Sort by column (menu Data, hoặc double-click header).
- ✗ Search box trong dropdown filter — cần verify.
- ✗ Sort A→Z / Z→A trong dropdown filter — cần verify.
- ✗ Sort by Color, Sort by Font Color.
- ✗ Text Filters / Number Filters / Date Filters sub-menu (Top 10, Above Average, Between...).
- ✗ Sort dialog multi-level (Add Level, Then By, Custom List).
- ✗ Custom AutoFilter (2 điều kiện AND/OR).

## 15.1 AutoFilter UX (§15.1)

### Bật/tắt
- Ctrl+Shift+L / Data → Filter / Home → Sort & Filter → Filter.
- Mỗi cell header xuất hiện nút dropdown (▼).
- Khi filter active: ▼ → biểu tượng phễu; row numbers cột số tô xanh.
- Rows bị filter: số hàng nhảy (vd 1, 3, 7 → ẩn 2, 4, 5, 6).

## Filter Dropdown UX

```
┌─ Filter ────────────────────┐
│ Sort A→Z                    │
│ Sort Z→A                    │
│ Sort by Color           ►   │
│ ──────────────────────────  │
│ Filter by Color         ►   │
│ Text Filters            ►   │
│ Clear Filter from "Tên cột" │
│ ──────────────────────────  │
│ [🔍 Search...]              │
│ ☑ (Select All)              │
│ ☑ value 1                   │
│ ☑ value 2                   │
│ ☐ value 3                   │
│ ...                         │
│         [ OK ] [ Cancel ]   │
└─────────────────────────────┘
```

- **Search box**: gõ filter list checkbox nhanh.
- **Select All**: toggle tất cả.
- **Sort A→Z / Z→A** đầu dropdown.
- **Sort by Color** sub-menu nếu cột có cell màu.
- **Text/Number/Date Filters** sub-menu (bộ điều kiện).
- Danh sách checkbox = unique values cột.
- OK apply; Cancel hủy.

## 15.2 Filter conditions (§15.2)

### Text Filters
- Equals
- Does Not Equal
- Begins With
- Ends With
- Contains
- Does Not Contain
- Custom Filter... (AND/OR 2 điều kiện)

### Number Filters
| Condition | Mô tả |
|---|---|
| Equals / Does Not Equal | So sánh |
| Greater Than / Less Than / Greater Or Equal / Less Or Equal | |
| Between | Khoảng (min, max) |
| Top 10... | n top/bottom theo số hoặc % |
| Above Average / Below Average | So với trung bình cột |
| Custom Filter... | Dialog 2 điều kiện AND/OR |

### Date Filters
- Equals / Before / After / Between
- Tomorrow / Today / Yesterday
- Next/This/Last Week / Month / Quarter / Year
- Year to Date
- All Dates in the Period → list tháng / quý

### Custom AutoFilter Dialog
- Row 1: dropdown condition + value input.
- Radio: ⦿ AND ⦾ OR.
- Row 2: dropdown condition + value input.
- OK / Cancel.

## 15.3 Sort Dialog (Data → Sort) (§15.3)

```
┌─ Sort ─────────────────────────────────────────┐
│ [+ Add Level] [- Delete] [📋 Copy] [⬆][⬇]      │
│ ☑ My data has headers                          │
│ ──────────────────────────────────────────────  │
│ Column        Sort On       Order              │
│ [Sort By  ▼] [Values   ▼]  [A → Z          ▼] │
│ [Then By  ▼] [Values   ▼]  [Smallest to L ▼] │
│ [Then By  ▼] [Cell Color▼] [Red on top    ▼] │
│                                  [ OK ] [Cancel]│
└────────────────────────────────────────────────┘
```

- **Sort By / Then By / Then By...**: multi-level.
- **Sort On**: Values / Cell Color / Font Color / Conditional Formatting Icon.
- **Order**:
  - Values: A→Z, Z→A, Smallest→Largest, Largest→Smallest
  - Color: Red on top / Bottom...
  - Custom List...: Mon,Tue,Wed... / Q1,Q2... / user-defined
- **Add Level / Delete Level / Copy Level**: max 64 levels.
- **My data has headers**: checkbox; bỏ tick = không có header.
- **Move Up / Down** thay đổi priority.

### Implementation note
- Hiện sort ở model `_data` đảo hàng. Multi-level: dùng stable sort, lặp ngược từ level cuối → đầu (Python `sorted` stable).
- Sort on Color: cần key = mã màu trong `_fmt`.
- Custom List: lưu QSettings, dialog edit list.

## Acceptance criteria
1. Ctrl+Shift+L bật filter → mỗi header có nút ▼.
2. Click ▼ cột A → search box hiện. Gõ "abc" → list checkbox chỉ hiện values chứa "abc".
3. Number Filters → Top 10 → dialog "Top [10] [Items/Percent] from [Top/Bottom]".
4. Number Filters → Between → 2 textbox (min, max) → apply giữ hàng trong khoảng.
5. Data → Sort → Add Level 3 cấp → sort multi-level đúng.
6. Sort by Cell Color: chọn "Red on top" → hàng có ô màu đỏ lên đầu.
7. Filter trên cột A active → row header 1,3,7,... xanh; row 2,4,5,6 ẩn.

## Phụ thuộc
- [08 Format Cells](08-format-cells-dialog.md) — cell color cho Sort by Color.
- Hiện tại `view.FilterHeaderView` đã có — extend.

## Risk
Trung bình. UI dropdown lớn; cẩn thận perf khi có 100k+ unique values.
