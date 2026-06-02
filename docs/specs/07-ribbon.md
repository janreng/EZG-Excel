# SPEC 07 — Ribbon (Tabs / Groups / Contextual)

## Mục tiêu
Ribbon đầy đủ tab giống Excel; có Contextual tab tự bật khi chọn object đặc biệt; có Dialog Box Launcher và Quick Access Toolbar.

## Trạng thái hiện tại
- ✓ Có một ribbon-like toolbar (`_RibbonBar`/`_RibbonSection` trong `main_window.py`) với basic format buttons.
- ✗ Chưa chia theo tab Home/Insert/Page Layout/Formulas/Data/Review/View.
- ✗ Contextual tabs chưa có (chưa có Table/Chart/PivotTable).
- ✗ Dialog Box Launcher (mũi tên góc dưới phải group) chưa có.
- ✗ Quick Access Toolbar (QAT) chưa có.
- ✗ Alt + key navigation (KeyTips) chưa có.

## Cấu trúc ribbon (§7.1)

Hai lớp: **Tabs** → **Groups** → **Controls** (button/dropdown).

| Tab | Groups | Contextual? |
|---|---|---|
| **Home** | Clipboard, Font, Alignment, Number, Styles, Cells, Editing, Ideas | Không |
| **Insert** | Tables, Illustrations, Add-ins, Charts, Tours, Sparklines, Filters, Links, Text, Symbols | Không |
| **Draw** | Drawing tools (Pen, Highlighter, Eraser) | Không |
| **Page Layout** | Themes, Page Setup, Scale to Fit, Sheet Options, Arrange | Không |
| **Formulas** | Function Library, Defined Names, Formula Auditing, Calculation | Không |
| **Data** | Get & Transform, Queries & Connections, Sort & Filter, Data Tools, Forecast, Outline | Không |
| **Review** | Proofing, Accessibility, Insights, Language, Comments, Notes, Changes, Ink | Không |
| **View** | Workbook Views, Show, Zoom, Window, Macros | Không |
| **Developer** | Code, Add-ins, Controls, XML, Modify | Không (cần bật) |
| **Help** | Help, Support, Show Training, Community | Không |
| **Table Design** | Properties, Tools, External Table Data, Table Style Options, Table Styles | ✓ khi cursor trong Table |
| **Chart Design** | Chart Layouts, Chart Styles, Data, Type, Location | ✓ khi chart selected |
| **Chart Format** | Current Selection, Insert Shapes, Shape Styles, WordArt, Arrange, Size | ✓ khi chart selected |
| **Picture Format** | Adjust, Picture Styles, Accessibility, Arrange, Size | ✓ khi image selected |
| **SmartArt Design/Format** | Layouts, SmartArt Styles, Reset | ✓ khi SmartArt selected |
| **PivotTable Analyze** | PivotTable, Active Field, Group, Filter, Data, Actions, Calculations, Tools, Show | ✓ khi PivotTable selected |

## Dialog Box Launcher (§7.2)

Mũi tên nhỏ góc dưới phải một số group → mở full dialog:

| Group | Dialog |
|---|---|
| Font | Format Cells → tab Font |
| Alignment | Format Cells → tab Alignment |
| Number | Format Cells → tab Number |
| Cells | Format Cells toàn bộ |
| Clipboard | Clipboard task pane (lịch sử 24 items) |
| Charts | Insert Chart dialog |

## Quick Access Toolbar (§7.3)
- Vị trí: trên Title Bar (mặc định) hoặc dưới Ribbon (toggle).
- Mặc định: Save, Undo, Redo + dropdown customize.
- Right-click bất kỳ control → "Add to Quick Access Toolbar".
- File → Options → Quick Access Toolbar để customize đầy đủ.
- Shortcut: **Alt + số** (Alt+1, Alt+2...) theo thứ tự trái → phải.

## Collapse/Expand ribbon
- Ctrl+F1 toggle.
- Double-click tab name toggle.
- Khi collapsed: chỉ hiện tabs; click tab → bung tạm thời.

## Implementation note

- Đề xuất: refactor `_RibbonBar` thành `QTabWidget` (mỗi tab là 1 widget chứa các `_RibbonSection` group).
- `Contextual tabs` quản lý qua `add_contextual(name, condition_callable)`; signal selection_changed → check condition → show/hide tab + auto-switch.
- Dialog Box Launcher: thêm field `launcher_callback` cho `_RibbonSection`; nếu set, render mũi tên ở corner.
- QAT: `QToolBar` riêng trên title bar.
- KeyTips: phase sau (cần infrastructure key handler tree).

## Priority phân chia phase

- **Phase 1 — Home tab đủ** (đa số đã có; rearrange theo group chuẩn).
- **Phase 2 — Insert (Tables, Charts placeholder), View (Freeze, Zoom)**.
- **Phase 3 — Formulas, Data tabs** + Function Library button (link Function Wizard).
- **Phase 5 — Contextual Table Design, Chart Design** khi có Table/Chart.
- **Phase 7 — Page Layout, Review, Draw, Developer** đầy đủ.

## Acceptance criteria
1. Ctrl+F1 → ribbon collapse; lần nữa → expand.
2. Click tab Home → group Clipboard / Font / Alignment / Number / Styles / Cells / Editing hiển thị đúng thứ tự.
3. Click mũi tên dưới phải group Font → mở Format Cells tab Font.
4. Insert Table (Ctrl+T) → tab "Table Design" tự xuất hiện cuối ribbon, được focus.
5. Right-click Bold button → context menu có "Add to Quick Access Toolbar"; sau khi add, Alt+5 (vị trí mới) toggle Bold.

## Phụ thuộc
- [08 Format Cells Dialog](08-format-cells-dialog.md).
- [16 Table](16-table.md), [19 Chart](19-chart.md), [18 PivotTable](18-pivot-table.md) cho contextual.

## Risk
Trung bình. UI refactor lớn nhưng không thay đổi data model.
