# PLAN — Ezcel tiến gần Microsoft Excel

> Master plan đồng bộ với `Excel_UX_Spec_Clone_Guide.docx` (Microsoft 365 / 2021 / 2024) **+ research mở rộng tới Excel 2024-2025**. Lấy spec làm chuẩn UX; mỗi tính năng có file riêng trong `docs/specs/`.

## Nguyên tắc

- **Theo Excel bản hiện đại (Microsoft 365 / 2024-2025).** Tính năng legacy (VBA, Notes cũ, Form Controls cũ, ActiveX, BIFF .xls write) chỉ giữ làm tham khảo compat — KHÔNG ưu tiên implement.
- **Spec là chuẩn UX, không phải lịch giao.** Tính năng nào đã có một phần thì spec ghi rõ "đã có" / "thiếu" / "khác Excel".
- **Phase chia theo phụ thuộc kỹ thuật**, không theo độ "đẹp". Sửa cấu trúc dữ liệu trước, UI sau, file format sau cùng.
- **Mỗi spec phải có acceptance criteria đo được** (gõ phím gì → thấy gì). Không acceptance criteria → không thể gọi là xong.
- **Tôn trọng ranh giới module** đã định trong `CLAUDE.md` (model / view / main_window / formula / io_utils).
- **Hot path** (paint, data(), selectionChanged) cấm cấp phát thừa — xem `docs/plans/2026-06-02-performance-optimization.md`.

## Trạng thái Ezcel hiện tại (chốt ngày 2026-06-02)

| Mảng | Ezcel | Excel | Spec |
|---|---|---|---|
| Grid + virtual scroll | ✓ (QTableView) | ✓ | [01](01-grid-engine.md) |
| Cell addressing A1:XFD | một phần (giới hạn theo Qt model) | ✓ | [02](02-cell-system.md) |
| 4 cell modes (Ready/Enter/Edit/Point) | **không có Point/Enter chuẩn**, Edit/Ready có ngầm | ✓ | [03](03-cell-modes.md) |
| Name Box + Formula Bar | có cơ bản (Formula Bar, không Name Box drop-down, không Function Wizard) | ✓ | [04](04-name-box-formula-bar.md) |
| AutoFill / AutoComplete / Flash Fill | AutoFill có, AutoComplete chưa, Flash Fill chưa | ✓ | [05](05-data-entry-autofill.md) |
| Context menus (cell/row/col/sheet) | cell có, row/col/sheet ít | ✓ | [06](06-context-menus.md) |
| Ribbon | có (Home-ish), thiếu nhiều tab + contextual | ✓ | [07](07-ribbon.md) |
| Format Cells dialog 6 tab | thiếu (chỉ ribbon button rời) | ✓ | [08](08-format-cells-dialog.md) |
| Row/Col/Sheet operations | resize/insert/delete/hide có; group/outline chưa | ✓ | [09](09-row-col-operations.md) |
| Sheet tabs (multi sheet) | **chưa** | ✓ | [10](10-sheet-tabs.md) |
| Status Bar | có Sum/Avg/Count cơ bản, thiếu Cell Mode, View buttons | ✓ | [11](11-status-bar.md) |
| Formula engine | ~120 hàm (v0.12.0), chưa có Function Wizard / Error smart tag / Trace | ✓ | [12](12-formula-system.md) |
| Clipboard / Paste Special | Ctrl+C/X/V có, Paste Special chỉ "values" partial | ✓ | [13](13-clipboard-paste-special.md) |
| Freeze / Split / Views | Freeze có; Split/Page Layout/Page Break chưa | ✓ | [14](14-freeze-split-views.md) |
| Filter / Sort | có | ✓ | [15](15-filter-sort.md) |
| Table (Ctrl+T) | chưa | ✓ | [16](16-table.md) |
| Conditional Formatting | chưa (đã có chỗ trong undo snapshot) | ✓ | [17](17-conditional-formatting.md) |
| PivotTable | chưa | ✓ | [18](18-pivot-table.md) |
| Chart | chưa | ✓ | [19](19-chart.md) |
| Power Query | chưa | ✓ | [20](20-power-query.md) |
| VBA / Macro | chưa | ✓ | [21](21-vba-macro.md) |
| Modern (Checkbox / Regex / Python / Copilot / Focus Cell) | chưa | ✓ | [22](22-modern-features.md) |
| Keyboard shortcuts | một phần | ✓ | [23](23-keyboard-shortcuts.md) |

> Bảng trạng thái trên mới liệt kê spec 01–23. Repo có **51 spec** (24–51:
> print, validation, comments, data-tools, what-if, protection, themes, named
> ranges, sparklines, file-formats, copilot, ... đến start-screen) — xem
> `README.md` và các Phase 6–7 bên dưới. Rà soát chất lượng: `../SPEC_AUDIT.md`.

## Phase roadmap

### Phase 1 — Core UX gap-close (1-2 tuần)
Mục tiêu: hành xử đúng *kiểu Excel* với những gì đã có. **Không** thêm tính năng lớn — sửa hành vi cho khớp spec.

- [03 Cell Modes](03-cell-modes.md) — implement state machine Ready/Enter/Edit/Point + Status Bar indicator
- [04 Name Box + Formula Bar](04-name-box-formula-bar.md) — Name Box navigate (gõ A1 → nhảy), dropdown Named Ranges, expand button, Confirm/Cancel button
- [11 Status Bar](11-status-bar.md) — Cell Mode label, right-click customize, View buttons + Zoom slider chuẩn
- [02 Cell System](02-cell-system.md) — multi-range selection (Ctrl+Click), Name Box hiểu `A1:B3,D5,F1:F10`
- [23 Keyboard Shortcuts](23-keyboard-shortcuts.md) — bù bảng phím tắt thiếu (Ctrl+Shift+arrow đã có; bổ sung F2/F5/Shift+F3/Ctrl+`/Alt+=)

### Phase 2 — Format Cells dialog + định dạng nâng cao (2-3 tuần)
Đã có roadmap cũ phase 2 — gộp + cập nhật theo spec mới.

- [08 Format Cells Dialog](08-format-cells-dialog.md) — dialog 6 tab (Number / Alignment / Font / Border / Fill / Protection)
- [13 Clipboard & Paste Special](13-clipboard-paste-special.md) — Paste Special dialog đầy đủ (Values / Formulas / Formats / Transpose / Skip Blanks / Add/Sub/Mul/Div)
- [09 Row/Col Operations](09-row-col-operations.md) — Group/Outline, Hide/Unhide đầy đủ, AutoFit cột/hàng
- [06 Context Menus](06-context-menus.md) — Mini Toolbar floating + menu chuẩn cho row/col/sheet header

### Phase 3 — Multi-sheet + Tables (3-4 tuần)
Refactor kiến trúc + thêm 2 container.

- [10 Sheet Tabs](10-sheet-tabs.md) — `Workbook` class, tab bar, tham chiếu `Sheet1!A1` trong formula
- [16 Table (Ctrl+T)](16-table.md) — Table container + Structured References + Total Row
- [14 Freeze / Split / Views](14-freeze-split-views.md) — Split view, Page Layout / Page Break Preview, Multiple Windows

### Phase 4 — Formula UX cao cấp + Conditional Formatting (2-3 tuần)

- [12 Formula System (UX)](12-formula-system.md) — Function Wizard (Shift+F3), autocomplete dropdown, ScreenTip, error smart tag, Trace Precedents/Dependents, Evaluate Formula
- [17 Conditional Formatting](17-conditional-formatting.md) — 5 loại preset + custom formula rule + Manage Rules + Stop If True priority
- [05 AutoFill / AutoComplete / Flash Fill](05-data-entry-autofill.md) — AutoComplete cột text, Flash Fill Ctrl+E, Pick From Dropdown List

### Phase 5 — Filter / Sort nâng cao + Modern features + Data Tools (2-3 tuần)

- [15 Filter / Sort](15-filter-sort.md) — multi-level sort dialog, Text/Number/Date filter sub-menu, Sort by Color
- [22 Modern features](22-modern-features.md) — Checkbox in cell, REGEX functions, Focus Cell, TRIMRANGE
- [26 Comments & Notes](26-comments-notes.md) — Threaded Comments (priority); legacy Notes minimal
- [27 Data Tools](27-data-tools.md) — Text to Columns, Remove Duplicates, Subtotal, Consolidate, Forecast Sheet
- [30 Themes & Cell Styles](30-themes-cell-styles.md) — Theme cascade + Cell Styles gallery + Custom Lists
- [33 Sparklines](33-sparklines.md) — Line / Column / Win-Loss
- [36 File Formats / AutoSave / AutoRecover](36-file-formats-autosave.md)
- [40 Quick Analysis](40-quick-analysis.md) — Ctrl+Q + Recommended Charts/PivotTables

### Phase 6 — Reporting & analytics + AI (sau cùng)
Phụ thuộc đa số module trước.

- [18 PivotTable](18-pivot-table.md)
- [19 Chart](19-chart.md)
- [20 Power Query](20-power-query.md)
- [21 Macro (Python)](21-vba-macro.md) — không VBA, dùng Python
- [28 What-If Analysis](28-what-if-analysis.md) — Goal Seek / Scenario / Solver / Data Table
- [29 Protection](29-protection.md) — Sheet / Workbook / Encryption
- [38 Linked Data Types](38-linked-data-types.md) — Stocks / Geography / Currency (modern Excel 365)
- [39 Copilot / Agent Mode](39-copilot-agent.md) — AI integration (NEW 2024-2025)

### Phase 7 — Ribbon hoàn chỉnh + In ấn + Objects (parallel với Phase 6)

- [07 Ribbon](07-ribbon.md) — full tab Home / Insert / Page Layout / Formulas / Data / Review / View + Contextual tabs (Table Design, Chart Design, PivotTable Analyze)
- [24 Print & Page Setup & Export PDF](24-print-page-setup.md)
- [34 Shapes / Images / SmartArt / Hyperlinks](34-shapes-images-smartart.md)
- [37 Form Controls](37-form-controls.md) — legacy compat, deprioritize

---

## Cách dùng plan này

1. Đọc spec của tính năng cần làm — spec là **single source of truth** cho UX.
2. Spec chỉ rõ "đã có" / "thiếu" / "khác Excel"; chỉ làm phần "thiếu" + "khác Excel".
3. Mỗi PR commit một acceptance criterion (hoặc gom nhỏ). Reference spec line trong commit message.
4. Khi spec lệch với hành vi Excel thật → cập nhật spec, không sửa code chệch.
5. Tính năng ngoài phạm vi 7 phase trên: tạo spec riêng khi cần.

## Cập nhật so với research 2024-2025

- **Copilot in Excel** ([Spec 39](39-copilot-agent.md)) — Agent Mode, COPILOT function trong formula, Formula Completion AI (mới 2025).
- **Linked Data Types value tokens** ([Spec 38](38-linked-data-types.md)) — Formula Bar phân biệt linked vs text (mới 2024).
- **PIVOTBY / GROUPBY** functions — native (đã có trong [Spec 12](12-formula-system.md) nhóm dynamic array).
- **Python in Excel** — đã có ở [Spec 22](22-modern-features.md).
- **Focus Cell, Navigation Highlighting** — [Spec 22](22-modern-features.md).
- **Modernized Get Data dialog** — [Spec 20](20-power-query.md).
- **Edit data label text in Excel for the web** — out of scope desktop.

## Tham chiếu

- Doc gốc: `Excel_UX_Spec_Clone_Guide.docx` (bản extract: `bot-server-dedicated/.claude/channels/discord/inbox/spec_extracted.txt`)
- Web research 2024-2025: techcommunity.microsoft.com (What's New in Excel), howtogeek.com, neowin.net
- Roadmap cũ: `docs/roadmap.md`
- Performance plan: `docs/plans/2026-06-02-performance-optimization.md`
- CLAUDE.md (architecture & conventions): repo root
