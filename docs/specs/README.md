# Ezcel — Specs

Đây là **single source of truth** cho UX. Đọc kèm [PLAN.md](PLAN.md) (master roadmap).

> **Định hướng:** Theo **Microsoft 365 / Excel 2024-2025** (bản hiện đại). Tính năng legacy (VBA, Notes cũ, Form Controls cũ, ActiveX) chỉ giữ làm tham khảo compat — KHÔNG ưu tiên implement.

## Cách dùng

1. Đọc [PLAN.md](PLAN.md) trước — biết tính năng nằm phase nào.
2. Trước khi sửa code, đọc spec tương ứng. Spec phân biệt rõ "đã có" / "thiếu" / "khác Excel".
3. Implement xong → verify từng acceptance criterion trong spec.
4. Phát hiện hành vi Excel thật khác spec → cập nhật spec, **không** sửa code chệch.

## Danh sách specs (40 files)

### Core UX (1-11) — Nền tảng
| # | Title | Phase | File |
|---|---|---|---|
| 01 | Grid Engine (Layout) | nền tảng | [01-grid-engine.md](01-grid-engine.md) |
| 02 | Cell System (Selection) | 1 | [02-cell-system.md](02-cell-system.md) |
| 03 | 4 Cell Modes | 1 | [03-cell-modes.md](03-cell-modes.md) |
| 04 | Name Box & Formula Bar | 1 | [04-name-box-formula-bar.md](04-name-box-formula-bar.md) |
| 05 | Data Entry / AutoFill / Flash Fill | 4 | [05-data-entry-autofill.md](05-data-entry-autofill.md) |
| 06 | Context Menus + Mini Toolbar | 2 | [06-context-menus.md](06-context-menus.md) |
| 07 | Ribbon | 7 | [07-ribbon.md](07-ribbon.md) |
| 08 | Format Cells Dialog (6 tabs) | 2 | [08-format-cells-dialog.md](08-format-cells-dialog.md) |
| 09 | Row/Col Operations | 2 | [09-row-col-operations.md](09-row-col-operations.md) |
| 10 | Sheet Tabs (Multi-sheet) | 3 | [10-sheet-tabs.md](10-sheet-tabs.md) |
| 11 | Status Bar | 1 | [11-status-bar.md](11-status-bar.md) |

### Formulas & Data (12-17)
| # | Title | Phase | File |
|---|---|---|---|
| 12 | Formula System (UX nâng cao) | 4 | [12-formula-system.md](12-formula-system.md) |
| 13 | Clipboard & Paste Special | 2 | [13-clipboard-paste-special.md](13-clipboard-paste-special.md) |
| 14 | Freeze / Split / Views | 3 | [14-freeze-split-views.md](14-freeze-split-views.md) |
| 15 | Filter / Sort | 5 | [15-filter-sort.md](15-filter-sort.md) |
| 16 | Table (Ctrl+T) | 3 | [16-table.md](16-table.md) |
| 17 | Conditional Formatting | 4 | [17-conditional-formatting.md](17-conditional-formatting.md) |

### Analytics & Reporting (18-20)
| # | Title | Phase | File |
|---|---|---|---|
| 18 | PivotTable | 6 | [18-pivot-table.md](18-pivot-table.md) |
| 19 | Chart | 6 | [19-chart.md](19-chart.md) |
| 20 | Power Query | 6 | [20-power-query.md](20-power-query.md) |

### Programmability (21)
| # | Title | Phase | File |
|---|---|---|---|
| 21 | Macro (Python — thay VBA) | 6 | [21-vba-macro.md](21-vba-macro.md) |

### Modern features (22-23)
| # | Title | Phase | File |
|---|---|---|---|
| 22 | Modern features (Checkbox / Regex / Focus Cell) | 5 | [22-modern-features.md](22-modern-features.md) |
| 23 | Keyboard Shortcuts | 1 | [23-keyboard-shortcuts.md](23-keyboard-shortcuts.md) |

### Print & Data Tools (24-28)
| # | Title | Phase | File |
|---|---|---|---|
| 24 | Print & Page Setup & Export PDF | 7 | [24-print-page-setup.md](24-print-page-setup.md) |
| 25 | Data Validation | 4 | [25-data-validation.md](25-data-validation.md) |
| 26 | Comments & Notes | 5 | [26-comments-notes.md](26-comments-notes.md) |
| 27 | Data Tools (Text-to-Columns / Remove Duplicates / Subtotal / Consolidate / Forecast Sheet) | 5 | [27-data-tools.md](27-data-tools.md) |
| 28 | What-If Analysis (Goal Seek / Solver / Scenario) | 6 | [28-what-if-analysis.md](28-what-if-analysis.md) |

### Protection & Styling (29-31)
| # | Title | Phase | File |
|---|---|---|---|
| 29 | Protection (Sheet / Workbook / Encryption) | 6 | [29-protection.md](29-protection.md) |
| 30 | Themes / Cell Styles / Table Styles / Custom Lists | 5 | [30-themes-cell-styles.md](30-themes-cell-styles.md) |
| 31 | Named Ranges (Name Manager) | 4 | [31-named-ranges.md](31-named-ranges.md) |

### Navigation & Objects (32-34)
| # | Title | Phase | File |
|---|---|---|---|
| 32 | Find / Replace / Go To / Go To Special | 1 | [32-find-replace-goto.md](32-find-replace-goto.md) |
| 33 | Sparklines | 5 | [33-sparklines.md](33-sparklines.md) |
| 34 | Shapes / Images / SmartArt / Hyperlinks / Header & Footer | 7 | [34-shapes-images-smartart.md](34-shapes-images-smartart.md) |

### Engine & File (35-37)
| # | Title | Phase | File |
|---|---|---|---|
| 35 | Calculation Engine (Modes / Volatile / Date / R1C1) | 4 | [35-calculation-engine.md](35-calculation-engine.md) |
| 36 | File Formats / AutoSave / AutoRecover | 5 | [36-file-formats-autosave.md](36-file-formats-autosave.md) |
| 37 | Form Controls (legacy compat) | 7+ | [37-form-controls.md](37-form-controls.md) |

### Modern AI & Data Types (38-40)
| # | Title | Phase | File |
|---|---|---|---|
| 38 | Linked Data Types (Stocks / Geography / Currency) | 6 | [38-linked-data-types.md](38-linked-data-types.md) |
| 39 | Copilot (Pane / COPILOT function / Agent Mode / Formula Completion) | 6 | [39-copilot-agent.md](39-copilot-agent.md) |
| 40 | Quick Analysis (Ctrl+Q) & Recommended Charts/PivotTables | 5 | [40-quick-analysis.md](40-quick-analysis.md) |

### Accessibility, Proofing, Collaboration (41-44)
| # | Title | Phase | File |
|---|---|---|---|
| 41 | Accessibility (Checker / Alt Text / Read Aloud / Screen Reader) | 6 | [41-accessibility.md](41-accessibility.md) |
| 42 | Proofing (Spell / AutoCorrect / Translate / Smart Lookup / Thesaurus) | 5 | [42-proofing-translate.md](42-proofing-translate.md) |
| 43 | Office Scripts (TypeScript) — **OUT OF SCOPE decision** | — | [43-office-scripts.md](43-office-scripts.md) |
| 44 | Collaboration / Version History / Track Changes | 5+ | [44-collaboration-version-history.md](44-collaboration-version-history.md) |

### Advanced Analytics & Misc (45-49)
| # | Title | Phase | File |
|---|---|---|---|
| 45 | Power Pivot / Data Model / DAX | 6+ (subset) | [45-power-pivot-data-model.md](45-power-pivot-data-model.md) |
| 46 | 3D Maps (Power Map) — out of scope | — | [46-3d-maps.md](46-3d-maps.md) |
| 47 | Camera Tool (Live Linked Picture) | 7+ | [47-camera-snapshot.md](47-camera-snapshot.md) |
| 48 | Touch Mode / Pen / Ink | 5+ (touch), 7+ (pen) | [48-touch-pen-ink.md](48-touch-pen-ink.md) |
| 49 | Trust Center / Privacy / Macro Security | 6+ | [49-trust-center-privacy.md](49-trust-center-privacy.md) |

### Design System & Home Experience (50-51) — **VISUAL CONTRACT**
| # | Title | Phase | File |
|---|---|---|---|
| 50 | **Design System** (Colors / Typography / Spacing / Icons) | nền tảng | [50-design-system.md](50-design-system.md) |
| 51 | Start Screen / Backstage (File menu / Home / Templates / Account) | 2 | [51-start-screen-backstage.md](51-start-screen-backstage.md) |

## Format mỗi spec

- **Mục tiêu** — 1-2 câu, không phải "to-do".
- **Trạng thái hiện tại** — ✓ đã có / ✗ thiếu / ⚠ khác Excel.
- **Spec chi tiết** — Functional + UX flow + edge cases + tables.
- **Implementation note** — đề xuất ngắn (file nào, class nào). Không phải code.
- **Acceptance criteria** — bullet point đo được; mỗi cái = test case manual hoặc auto.
- **Phụ thuộc** — link spec khác.
- **Risk** — Thấp / Trung bình / Cao + lý do.

## Tổng số: **51 specs**

## Ngoài phạm vi (chưa có spec — đánh giá khi cần)

- Office.js Add-ins runtime (Excel Add-in store apps)
- Excel Online Web-specific features (Excel for the Web only)
- Power Automate / Power Apps integration
- Custom XML parts / OOXML extensions
- Excel COM Add-ins (Windows-only DLL)
- VBE (VBA Editor) deep features — replaced by Python ([Spec 21])
- ActiveX Controls — replaced by [Spec 22] checkbox cell-native
- DDE (Dynamic Data Exchange) — legacy, out of scope
- File encryption with smartcard / digital signature workflow
- VeryHidden sheet attribute
- Excel Survey / Web Form (deprecated)
- Excel Map (Insert → Map Chart 2D) — subset của [Spec 19 Chart]
- Workbook Link external (other workbook references) — minimal in [Spec 49]
- Insights / Ideas legacy pane — replaced by [Spec 39 Copilot]
- Microsoft Forms integration

Cần spec mới → tạo file `5X-name.md` + thêm vào PLAN.md & README.
