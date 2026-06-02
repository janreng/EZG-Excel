# SPEC 21 — VBA / Macro

## Mục tiêu
Recording + Editor + debug. Excel có VBA chuẩn — clone cần ngôn ngữ scripting tương đương; pragmatic là **Python** (Excel 2024 cũng có Python in Excel).

## Trạng thái hiện tại
- ✗ Chưa có.

## Đề xuất Ezcel
Thay vì VBA, **dùng Python làm macro language** (đã có Python runtime sẵn — không thêm dependency):
- Macro script là `.py` lưu trong workbook (xlsx + extra zip entry, hoặc folder bên ngoài).
- API tương tự `xlwings`: `wb.sheets["Sheet1"].range("A1").value = 5`.

Lý do:
- Tránh implement VBA parser + interpreter (cực lớn).
- Python user-base lớn hơn VBA hiện nay.
- Spec doc §22.3 cho thấy Excel cũng đang push Python in Excel.

⚠ Trade-off: file `.xlsm` của Excel sẽ KHÔNG chạy được trên Ezcel (VBA code không decode). Document rõ.

## 21.1 Truy cập

- Alt+F11: mở/đóng Macro Editor.
- Developer tab → Visual Basic (rename → "Python").
- Alt+F8: mở Macro list dialog (không cần mở editor).

## 21.2 Editor Layout (§21.2)

Editor riêng (`QMainWindow` con hoặc `QDialog`):

```
┌─ Macro Editor ───────────────────────────────────────────────┐
│ File  Edit  View  Insert  Format  Debug  Run  Tools  Help    │
│ ────────────────────────────────────────────────────────────│
│ Project Explorer    │ Code Window                             │
│ ┌─────────────────┐ │ ┌─────────────────────────────────────┐│
│ │ Workbook        │ │ │ def my_macro(app):                  ││
│ │  Sheet1         │ │ │     ws = app.active_sheet           ││
│ │  Sheet2         │ │ │     ws.range("A1").value = 5        ││
│ │  Modules        │ │ │                                     ││
│ │   Module1       │ │ └─────────────────────────────────────┘│
│ │   Module2       │ │ Immediate                               │
│ │  Forms (sau)    │ │ >>> ws.range("B1").value               │
│ └─────────────────┘ │ 10                                      │
│ Properties (F4)     │                                         │
│  Name: Module1      │                                         │
└──────────────────────────────────────────────────────────────┘
```

- **Project Explorer** (Ctrl+R): tree Workbook → Sheets → Modules → Class Modules → Forms (sau).
- **Code Window**: editor cho module đang chọn. Highlight syntax Python.
- **Immediate Window** (Ctrl+G): REPL — gõ Python, Enter run, output Debug.Print → tương đương `print(...)`.
- **Properties Window** (F4): module name, options.
- **Locals Window**, **Watch Window**: khi debug.

## 21.3 Debug (§21.3)

| Phím | Hành vi |
|---|---|
| F5 | Run macro từ đầu |
| F8 | Step Into |
| Shift+F8 | Step Over |
| F9 | Toggle Breakpoint |
| Ctrl+Break | Dừng macro đang chạy |

Implementation: dùng `pdb` Python (programmatic) hoặc `bdb` cho custom hook.

## Macro Recording

- Developer → Record Macro → dialog (name, shortcut, store in: Workbook / Personal / New Workbook).
- Status Bar hiện ■ recording.
- Mọi UI action → ghi thành Python code:
  - Click cell A1 → `ws.range("A1").select()`
  - Gõ "hello" → `ws.range("A1").value = "hello"`
  - Format Bold → `ws.range("A1").font.bold = True`
  - Insert row → `ws.rows(5).insert()`
- Developer → Stop Recording → save module.

## API surface (Pythonic, similar to xlwings)

```python
app                            # current app
app.books                      # list[Workbook]
app.active_book                
app.active_sheet               

wb.sheets                      # list
wb.sheets["Sheet1"]
wb.sheets.add(name="New")

ws.range("A1")
ws.range("A1:B3")
ws.cells(1, 1)                 # row, col 1-indexed
ws.rows(5)                     # entire row
ws.columns("A")

range.value                    # get/set scalar or 2D list
range.formula
range.font.bold = True
range.font.color = "#FF0000"
range.fill.color = "#FFFF00"
range.number_format = "0.00"
range.merge()
range.unmerge()
range.copy()
range.paste()
range.clear()
range.clear_contents()
range.autofit()

ws.insert_row(at=5)
ws.delete_row(5)
ws.freeze(row=2, col=1)

wb.save()
wb.save_as(path)
wb.close()
```

## Workbook events
- `workbook_open(wb)`, `workbook_close(wb)`, `sheet_change(sheet, range)`, `selection_change(sheet, range)`.
- Register: decorator `@on_event("sheet_change")` trong module.

## Acceptance criteria
1. Alt+F11 → editor mở; Project Explorer hiện tree.
2. Insert → Module → tab editor mới `Module1.py`.
3. Gõ `def hello(app): app.active_sheet.range("A1").value = "Hi"` → save → Alt+F8 → list macro có "hello" → Run → A1 = "Hi".
4. Developer → Record Macro → Click B1, gõ 5, Bold → Stop Recording → module sinh code tương ứng.
5. F9 trên dòng code → breakpoint đỏ; F5 chạy → dừng tại dòng đó; F8 step.
6. Immediate Window: gõ `app.active_sheet.range("C1").value` → Enter → in giá trị.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — multi-sheet API.
- [16 Table](16-table.md) — `wb.tables` API.

## Risk
**Cao.** Macro Recording chuyển UI action sang code — phải hook mọi command. Debug với breakpoint cần bdb integration cẩn thận để không freeze UI thread (chạy macro trong thread khác).
