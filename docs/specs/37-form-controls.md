# SPEC 37 — Form Controls (Developer tab)

## Mục tiêu
Form Controls cell-linked (modern Excel): Button, Check Box, List Box, Combo Box, Scroll Bar, Spin Button, Group Box, Label, Option Button.

> **Ưu tiên thấp.** Modern Excel khuyến nghị **Checkbox cell-native** ([Spec 22](22-modern-features.md)) thay cho legacy Form Controls. Spec này giữ để compat khi load file Excel cũ.

## Trạng thái hiện tại
- ✗ Chưa có.

## 37.1 Truy cập

Developer tab (cần bật trong File → Options → Customize Ribbon → ☑ Developer) → Controls group → Insert dropdown.

Hai loại:
- **Form Controls** (legacy nhưng vẫn dùng tốt, không cần VBA): Button, Check Box, List Box, Combo Box, Scroll Bar, Spin Button, Label, Group Box, Option Button.
- **ActiveX Controls** (cần VBA, Windows-only): TextBox, ComboBox, CheckBox, ListBox, CommandButton, OptionButton, ToggleButton, SpinButton, ScrollBar, Label, Image, More Controls.

⚠ **Ezcel chỉ implement Form Controls** (cell-linked, đơn giản, không phụ thuộc VBA). ActiveX **bỏ qua**.

## 37.2 Form Controls

### Check Box
- Insert → Check Box → drag tạo.
- Right-click → Format Control:
  - Value: Unchecked / Checked / Mixed.
  - **Cell link**: ô lưu TRUE/FALSE.
  - 3-D shading.
- Click → toggle; cell link update.

### Option Button (Radio)
- Insert → Option Button → drag.
- Format Control:
  - Cell link: ô lưu số ordinal của option được chọn (1, 2, 3...).
  - Group Box: option buttons trong cùng group box mutex.

### List Box
- Insert → List Box → drag.
- Format Control:
  - **Input range**: range chứa items hiển thị (vd `A1:A10`).
  - **Cell link**: ô lưu index của item được chọn.
  - Selection type: Single / Multi / Extend.

### Combo Box
- Insert → Combo Box → drag.
- Format Control: tương tự List Box.
- Drop down lines: số dòng hiển thị khi drop.

### Scroll Bar
- Insert → Scroll Bar → drag.
- Format Control:
  - Min / Max value.
  - Incremental change (small step), Page change (large step).
  - Cell link: ô lưu current value.

### Spin Button
- Insert → Spin Button → drag (2 button up/down).
- Format Control: Min / Max / Step / Cell link.

### Button (Form Control)
- Insert → Button → drag → dialog "Assign Macro".
- Trong Ezcel: assign Python function ([Spec 21](21-vba-macro.md)).
- Right-click → Edit Text → đổi label.

### Group Box
- Container visual cho Option Buttons. Mutex group.

### Label
- Static text — không có cell link.

## 37.3 Format Control Dialog (Right-click → Format Control)

3 tab:
- **Size**: width, height, lock aspect, scale.
- **Protection**: locked, lock text (when sheet protected).
- **Properties**:
  - Move and size with cells / Move but don't size / Don't move or size.
  - Print object ✓.
  - Locked ✓.
- **Web** (deprecated).
- **Alt Text**.
- **Control** (loại-specific options như trên).

## 37.4 Common properties

- All Form Controls render bằng vector (anchor + size).
- Anchored to cell → di chuyển/resize cùng cell theo option Properties.
- Print: in được (option Print object).
- Accessible: alt text cho screen reader.

## Model

```python
class FormControl:
    type: "checkbox"|"option"|"listbox"|"combobox"|"scrollbar"|"spinner"|"button"|"groupbox"|"label"
    cell_link: (sheet_id, row, col) | None
    input_range: Range | None         # listbox/combobox
    min_value: float | None
    max_value: float | None
    step: float | None
    page_step: float | None
    value: Any                        # current state
    text: str                         # label
    position: (x, y, w, h)
    anchor: "move_size"|"move_only"|"fixed"
    macro_id: str | None              # python function id for Button
    selection_type: "single"|"multi"|"extend"
```

Sheet: `_form_controls: list[FormControl]`.

## Implementation note

- Render: `QWidget` subclass cho mỗi type, overlay trên grid (như Shapes [Spec 34](34-shapes-images-smartart.md)).
- Hook value change → update cell link via model `setData`.
- Hook cell link change (data change → reflect to control state).

## xlsx mapping
openpyxl: Form Controls lưu trong `xl/drawings/drawing1.xml` + `xl/ctrlProps/ctrlProp1.xml`. openpyxl support read; write hạn chế.

## Acceptance criteria
1. Developer → Insert → Check Box → drag → checkbox với label "Check Box 1".
2. Right-click → Format Control → Cell link `$D$1` → click → D1 = TRUE.
3. Option Button x3 trong Group Box → click 1 cái → 2 cái còn lại tự unselect → cell link = 1/2/3.
4. List Box input range `A1:A10` → render list; click item 3 → cell link = 3.
5. Scroll Bar min=0, max=100, cell link D5 → drag → D5 update từ 0-100.
6. Button → Assign Macro → "hello" Python function → click → run function.

## Phụ thuộc
- [21 VBA / Macro](21-vba-macro.md) — Button assign Python function.
- [34 Shapes & Images](34-shapes-images-smartart.md) — overlay rendering.

## Risk
**Thấp ưu tiên.** Modern Excel push cell-native ([Spec 22](22-modern-features.md)). Implement chỉ khi cần compat với file Excel cũ có Form Controls.
