# SPEC 17 — Conditional Formatting

## Mục tiêu
Quy tắc format theo điều kiện: 5 loại preset + custom formula; Manage Rules dialog với priority + Stop If True.

## Trạng thái hiện tại
- ✗ Chưa có UI.
- ✓ Đã có chỗ trong undo snapshot (`("snapshot", data, fmt, merges, cond)` — theo CLAUDE.md). Cấu trúc `cond` chưa định nghĩa.

## 17.1 Loại rule

### Preset (Home → Conditional Formatting)
1. **Highlight Cells Rules**
   - Greater Than
   - Less Than
   - Between
   - Equal To
   - Text that Contains
   - A Date Occurring (Today, Yesterday, This Week, Last Month...)
   - Duplicate Values

2. **Top/Bottom Rules**
   - Top 10 Items / Bottom 10 Items
   - Top 10% / Bottom 10%
   - Above Average / Below Average

3. **Data Bars** — bar trong cell, length theo value
   - Gradient fill (Blue/Green/Red/Orange/Light Blue/Purple)
   - Solid fill

4. **Color Scales** — 2 màu / 3 màu gradient theo value
   - Green-Yellow-Red
   - Red-Yellow-Green
   - Blue-White-Red
   - ...

5. **Icon Sets** — icon nhỏ trong cell
   - 3 arrows (up/flat/down)
   - 3 traffic lights
   - 5 stars
   - 4 ratings
   - ...

### Custom — Use Formula
- Quan trọng nhất khi implement.
- Formula trả về TRUE/FALSE.
- Reference cần là ô ĐẦU TIÊN của vùng applies-to.
- Ví dụ:
  - Applies to `$A$1:$D$10`, formula `=MOD(ROW(),2)=0` → tô hàng chẵn.
  - Applies to `$B$2:$B$100`, formula `=$B2>1000000` → đánh dấu doanh thu cao.

## 17.2 Manage Rules dialog

Home → Conditional Formatting → Manage Rules.

```
┌─ Conditional Formatting Rules Manager ──────────────┐
│ Show formatting rules for: [This Worksheet     ▼]  │
│ ──────────────────────────────────────────────────  │
│ [+ New Rule] [Edit Rule] [- Delete] [⬆][⬇]         │
│ ──────────────────────────────────────────────────  │
│ Rule (preview) | Format | Applies to     | Stop If  │
│ Cell > 100     | red bg | $A$1:$A$100    │ ☐        │
│ Top 10 items   | yellow | $B$1:$B$100    │ ☐        │
│ ...                                                  │
│                          [Apply] [OK] [Cancel]      │
└─────────────────────────────────────────────────────┘
```

- Show for: This Selection / This Worksheet / This Table.
- Mỗi rule: Preview, Rule type, Format, Applies to range, Stop If True checkbox.
- **Priority**: rule trên cùng cao nhất; drag-reorder.
- **Stop If True**: rule này match → skip các rule dưới.

## Model

```python
class CondFormatRule:
    type: str          # "cell_value" / "formula" / "top_n" / "data_bar" / "color_scale" / "icon_set" / "above_average" / "duplicate" / ...
    applies_to: list[Range]
    formula: str       # nếu type = "formula"
    operator: str      # ">", "<", "between", "contains", "duplicate", ...
    values: list       # threshold / 2 values for between
    format: dict       # fmt dict (bg, color, font, border) — phần áp dụng
    stop_if_true: bool
    priority: int      # 0 = highest
```

Sheet: `_cond_rules: list[CondFormatRule]`.

## Render
- `delegate.paint()` → trước khi vẽ cell, evaluate rules:
  - Lặp rules priority ascending.
  - Match → áp format (merge với base `_fmt`).
  - Stop If True → break.
- **Hot path** — cache evaluation:
  - Khi data đổi: invalidate cell ảnh hưởng (precedents/dependents tương tự formula).
  - Khi rule đổi: invalidate range applies_to.
- Data bar / Color scale / Icon set: cần value range của toàn vùng applies_to (min/max) → cache; recalc khi data đổi.

## Formula reference trong rule
- Reuse formula engine (`evaluate(formula, resolver)`).
- Resolver: với mỗi cell `(r,c)` trong applies_to → translate formula bằng `offset_formula(formula, r-anchor_r, c-anchor_c)`.

## Acceptance criteria
1. Chọn A1:A10 → CF → Highlight Cells → Greater Than → 100 → red bg → các ô >100 đỏ.
2. Chọn B1:B100 → CF → Top/Bottom → Top 10 Items → 10 ô lớn nhất tô vàng.
3. Chọn C1:C20 → CF → Data Bars → Blue gradient → mỗi cell có bar dài theo giá trị.
4. Chọn D1:D10 → CF → Color Scales → Green-Yellow-Red → giá trị nhỏ xanh, lớn đỏ.
5. Chọn E1:E50 → CF → New Rule → Use Formula `=MOD(ROW(),2)=0` → hàng chẵn tô xám.
6. Manage Rules → đổi priority rule 2 lên trên rule 1 → render đúng theo priority mới.
7. Set Stop If True trên rule 1 → ô match rule 1 không apply rule 2.
8. Đổi data → CF auto re-evaluate (vd Top 10 Items dynamic).

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — engine evaluate.
- [08 Format Cells](08-format-cells-dialog.md) — format dict.
- Performance plan — hot path render.

## Risk
Cao. Data bar / Color scale / Icon set vẽ trực tiếp trong cell phải nhanh; cache toàn vùng applies_to thay vì tính lại mỗi paint.

## Lưu file (Phase 3 io_utils)
- Map sang openpyxl `ConditionalFormattingList`:
  - `CellIsRule` cho cell_value
  - `FormulaRule` cho formula
  - `Top10Rule` cho top/bottom
  - `DataBarRule`, `ColorScaleRule`, `IconSetRule`
