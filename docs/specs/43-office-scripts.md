# SPEC 43 — Office Scripts (TypeScript Automation)

## Mục tiêu
Office Scripts — TypeScript runtime cho Excel Web, replay-able, share-able. **Ezcel desktop: ưu tiên thấp — đề xuất bỏ qua hoặc fallback sang Python ([Spec 21](21-vba-macro.md)).**

## Trạng thái hiện tại
- ✗ Chưa có.

## 43.1 Office Scripts là gì

- Modern alternative cho VBA, **chỉ chạy trên Excel for Web** (browser).
- Ngôn ngữ: TypeScript subset (built on Office.js).
- Lưu trong OneDrive (`.osts` files).
- Có thể trigger từ Power Automate / Power Apps.
- Use case: automation workflow cloud-native.

## 43.2 Office Script Editor

### Truy cập (Web Excel)
- Automate tab → New Script / Record Actions / Code Editor.

### Layout
```
┌─ Code Editor pane ──────────────────────────────────────┐
│ [▶ Run] [Save] [Refresh]                                 │
│ ──────────────────────────────────────────────────────  │
│ function main(workbook: ExcelScript.Workbook) {          │
│   let sheet = workbook.getActiveWorksheet();             │
│   let range = sheet.getRange("A1:B10");                  │
│   range.setValue(0);                                     │
│ }                                                         │
│ ──────────────────────────────────────────────────────  │
│ Console: [output]                                        │
└──────────────────────────────────────────────────────────┘
```

### API (Office.js / ExcelScript)
- `workbook.getActiveWorksheet()`
- `workbook.getWorksheets()`
- `workbook.addWorksheet(name)`
- `sheet.getRange(addressOrName)`
- `range.getValue()`, `setValue(value)`, `getValues()`, `setValues(matrix)`
- `range.getFormat().getFill().setColor("#FF0000")`
- `range.getFormat().getFont().setBold(true)`
- `sheet.addTable(range, hasHeaders)`
- `workbook.addChart(type, sourceRange)`
- ... (hundreds of methods)

### Record Actions
- Click record → mọi UI action → TypeScript code sinh ra (như macro recording).
- Stop → save script.

### Run from Power Automate
- Flow trigger (schedule / button / HTTP) → call Office Script → automate Excel cloud workflow.

## 43.3 Ezcel Decision

**Khuyến nghị: BỎ QUA Office Scripts.** Lý do:
- Office Scripts là cloud-Excel-only; Ezcel desktop standalone không có infra Office.js runtime.
- Implement TypeScript runtime + full API surface = effort khổng lồ.
- Python macro ([Spec 21](21-vba-macro.md)) đã cover gần hết use case automation.

### Fallback: Python equivalent
- Provide tài liệu mapping Office Script → Ezcel Python API.
- Vd: `workbook.getActiveWorksheet().getRange("A1").setValue(5)` → `app.active_sheet.range("A1").value = 5`.

## 43.4 Office.js Add-ins (riêng biệt)

- Office.js Add-ins khác Office Scripts: là *task pane HTML+JS plugin* embed vào Excel.
- Distributed via AppSource hoặc sideload.
- Cũng cloud/cross-platform.

### Ezcel approach
- Plugin system Python-based ([Spec 21](21-vba-macro.md) extension).
- Plugin = Python module + ribbon entry + task pane (Qt widget).
- Không tương thích với Office.js add-ins ecosystem.

## Acceptance criteria
N/A — spec này là **decision record** giải thích lý do không implement.

## Phụ thuộc
- [21 Macro (Python)](21-vba-macro.md) — alternative.

## Risk
Không. Quyết định bỏ qua giảm scope.

## Phase
Out of scope. Re-evaluate khi Ezcel có web version.
