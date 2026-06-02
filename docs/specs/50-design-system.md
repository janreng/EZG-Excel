# SPEC 50 — Design System (Colors / Typography / Spacing / Icons / Sizing)

> **Visual single source of truth.** Mọi UI mới phải lấy color/font/spacing từ spec này; không hardcode.

## Mục tiêu
Quy chuẩn visual design áp dụng toàn app theo Microsoft Fluent Design + Excel-specific palette. Ref ảnh + token cụ thể để code không phải đoán.

## Trạng thái hiện tại
- ⚠ Code đã có `app.setStyle("Fusion")` (CLAUDE.md gotcha — giữ).
- ⚠ Color rải rác trong code (#217346 selection border đề cập ở [Spec 01]).
- ✗ Chưa có file `design_tokens.py` / `styles.py` tập trung.

## 50.1 Color Palette

### Brand & Accent (Excel signature green)

| Token | Hex | RGB | Dùng cho |
|---|---|---|---|
| `--excel-green-100` | `#107C41` | 16, 124, 65 | Excel brand primary (logo, splash) |
| `--excel-green-80` | `#185C37` | 24, 92, 55 | Title bar (Mac) / button hover |
| `--excel-green-60` | `#21A366` | 33, 163, 102 | Accent secondary |
| `--excel-green-40` | `#33C481` | 51, 196, 129 | Accent hover state |
| `--excel-green-20` | `#9FE2BF` | 159, 226, 191 | Subtle background |
| `--excel-green-10` | `#E8F5EE` | 232, 245, 238 | Selection range fill |
| **`--selection-border`** | `#217346` | 33, 115, 70 | **Selection border 2px** (chuẩn Excel) |

### Neutrals (Office grayscale)

| Token | Hex | Dùng cho |
|---|---|---|
| `--gray-900` | `#201F1E` | Text primary dark mode |
| `--gray-800` | `#323130` | Text primary light mode |
| `--gray-700` | `#605E5C` | Text secondary |
| `--gray-600` | `#8A8886` | Disabled text |
| `--gray-500` | `#A19F9D` | Borders subtle |
| `--gray-400` | `#C8C6C4` | Divider lines |
| `--gray-300` | `#E1DFDD` | Gridlines |
| `--gray-200` | `#EDEBE9` | Hover background |
| `--gray-100` | `#F3F2F1` | Ribbon background |
| `--gray-50` | `#FAF9F8` | Card background |
| `--white` | `#FFFFFF` | Cell background, card |
| `--black` | `#000000` | Text contrast |

### Semantic colors

| Token | Hex | Dùng cho |
|---|---|---|
| `--error` | `#A4262C` | Error text + border |
| `--error-bg` | `#FDE7E9` | Error background |
| `--warning` | `#797673` | Warning text |
| `--warning-bg` | `#FFF4CE` | Warning background |
| `--success` | `#107C10` | Success text |
| `--success-bg` | `#DFF6DD` | Success background |
| `--info` | `#0078D4` | Info text + hyperlink |
| `--info-bg` | `#DEECF9` | Info background |

### Conditional Formatting presets

| Token | Hex | Mô tả |
|---|---|---|
| `--cf-red` | `#FFC7CE` | Light Red Fill (Greater Than preset) |
| `--cf-red-text` | `#9C0006` | Dark Red Text |
| `--cf-yellow` | `#FFEB9C` | Yellow Fill |
| `--cf-yellow-text` | `#9C6500` | Dark Yellow Text |
| `--cf-green` | `#C6EFCE` | Green Fill |
| `--cf-green-text` | `#006100` | Dark Green Text |

### Theme colors (cho Page Layout → Themes — [Spec 30](30-themes-cell-styles.md))
Office default theme:
- Background 1: `#FFFFFF`
- Text 1: `#000000`
- Background 2: `#E7E6E6`
- Text 2: `#44546A`
- Accent 1: `#4472C4` (blue)
- Accent 2: `#ED7D31` (orange)
- Accent 3: `#A5A5A5` (gray)
- Accent 4: `#FFC000` (gold)
- Accent 5: `#5B9BD5` (light blue)
- Accent 6: `#70AD47` (green)
- Hyperlink: `#0563C1`
- Followed Hyperlink: `#954F72`

## 50.2 Typography

### Font stack
- Default UI: **Segoe UI** (Windows), San Francisco (Mac), Roboto (Linux fallback) — sans-serif.
- Default cell content: **Aptos Narrow** 11pt (Excel 365 default 2023+; thay Calibri).
- Monospace (formula bar optional): **Cascadia Mono** / Consolas.

### Sizes (pt)

| Token | Pt | Px (96 DPI) | Dùng cho |
|---|---|---|---|
| `--text-xs` | 9 | 12 | Status bar small, tooltip |
| `--text-sm` | 10 | 13 | Status bar default |
| `--text-base` | 11 | 15 | **Cell default, ribbon button** |
| `--text-md` | 12 | 16 | Dialog body, comment |
| `--text-lg` | 14 | 19 | Dialog title, ribbon tab label |
| `--text-xl` | 16 | 21 | Section heading |
| `--text-2xl` | 18 | 24 | Cell Style "Heading 1" |
| `--text-3xl` | 24 | 32 | Cell Style "Title" |

### Weight
- Regular: 400
- Semibold: 600 (ribbon tab active, dialog title)
- Bold: 700 (Cell Style "Heading", emphasis)

## 50.3 Spacing (8px grid)

| Token | Px | Dùng cho |
|---|---|---|
| `--space-0` | 0 | |
| `--space-1` | 2 | Tight icon spacing |
| `--space-2` | 4 | Compact padding |
| `--space-3` | 8 | **Default padding** |
| `--space-4` | 12 | Card padding |
| `--space-5` | 16 | Section gap |
| `--space-6` | 24 | Dialog padding |
| `--space-7` | 32 | Page heading margin |

## 50.4 Sizing (component standards)

| Component | Width | Height |
|---|---|---|
| Cell default | 64px | 20px |
| Cell selection border | — | 2px |
| Row header | 40px | — |
| Column header | — | 20px |
| Ribbon (expanded) | — | 110px |
| Ribbon (collapsed) | — | 22px |
| Name Box | 80-120px (resizable) | 26px |
| Formula Bar | flex | 26px |
| Status Bar | — | 22px |
| Sheet Tab bar | — | 22px |
| Sheet Tab button | auto | 22px |
| Dialog title bar | — | 30px |
| Dialog button | min 75px | 24px |
| Ribbon button (large) | 32px | 64px (icon 24 + label 2 dòng) |
| Ribbon button (small) | 22px | 22px (chỉ icon) |
| Touch button minimum | 44px | 44px (WCAG AA target) |

## 50.5 Border radius

| Token | Px | Dùng cho |
|---|---|---|
| `--radius-none` | 0 | Cell, header (Excel grid không bo) |
| `--radius-sm` | 2 | Button |
| `--radius-md` | 4 | Card, dialog |
| `--radius-lg` | 8 | Modal, dropdown |
| `--radius-full` | 9999 | Pill button, badge |

## 50.6 Shadows

| Token | CSS-like value | Dùng cho |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Card resting |
| `--shadow-md` | `0 2px 8px rgba(0,0,0,0.12)` | Dropdown, popover |
| `--shadow-lg` | `0 4px 16px rgba(0,0,0,0.16)` | Modal dialog |
| `--shadow-xl` | `0 8px 32px rgba(0,0,0,0.2)` | Floating mini toolbar |

## 50.7 Iconography

### System
- **Fluent UI Icons** (Microsoft open-source) → vector SVG 16×16, 20×20, 24×24.
- Repo: https://github.com/microsoft/fluentui-system-icons
- Style: Regular (outlined) cho idle, Filled cho selected/active.

### Excel-specific
- Ribbon buttons: 24×24 cho large, 16×16 cho small.
- Cell delegate icons (sort arrow, filter funnel, comment bubble): 12×12.
- Status bar indicators: 14×14.

### Stroke / Fill
- Stroke icons: 1.5px stroke trong viewBox 24×24.
- Fill icons: solid fill.
- Color: kế thừa text color (currentColor pattern).

### Hiện tại
- Code có `icons.py` với `PATHS` dict + `make_icon("name")`. Mở rộng theo Fluent UI palette.

## 50.8 Cursors

| Cursor | Dùng cho |
|---|---|
| `default` | Default |
| `cell` (white cross) | Grid hover |
| `column-resize` (↔) | Hover column header border |
| `row-resize` (↕) | Hover row header border |
| `crosshair` (+ black thin) | Fill handle hover |
| `move` (4-arrow) | Drag cell range |
| `not-allowed` | Forbidden drop target |
| `text` (I-beam) | Edit mode |
| `progress` (spinner) | Loading data type / Copilot |
| `wait` (hourglass) | Heavy recalc |

## 50.9 Motion / Animation

| Property | Duration | Easing | Dùng cho |
|---|---|---|---|
| Hover | 100ms | ease-out | Button background |
| Focus ring | 150ms | ease-out | Input border |
| Dropdown open | 150ms | ease-out | Popover |
| Modal enter | 200ms | ease-out | Dialog scale 0.95 → 1 |
| Toast | 250ms | ease-out | Slide from bottom |
| Marching ants | 400ms loop | linear | Copy/cut border |
| Navigation highlight | 500ms | ease-out → fade | Active cell header pulse |
| Sparkline draw | 800ms | ease-in-out | Initial render |

**Reduce motion preference:** detect OS → disable nonessential animation (chỉ functional transitions).

## 50.10 Reference images & resources

Vì spec là markdown text, không kèm ảnh inline. Reference sources:

### Ảnh Excel UI thật (chính chủ)
- **Microsoft Learn Excel docs:** https://learn.microsoft.com/excel — mỗi page có screenshot.
- **Excel Help support center:** https://support.microsoft.com/excel — UX guide với hình.
- **What's new blog (techcommunity):** https://techcommunity.microsoft.com/category/excel/blog/excelblog — feature announcements với hình.

### Design system reference
- **Fluent UI:** https://fluent2.microsoft.design/ — Microsoft official design system (colors, type, motion, icons).
- **Fluent UI Icons:** https://github.com/microsoft/fluentui-system-icons.
- **Office UI Fabric (legacy):** https://developer.microsoft.com/en-us/fluentui — predecessor.

### Tham chiếu khi cần screenshot cụ thể
- Boss download Excel desktop trial → screenshot từng dialog → lưu vào `docs/specs/_assets/` folder của repo.
- Hoặc dùng tool `gh` để pull ảnh từ Microsoft Learn (URL trong page docs).

### Khi implement
- Code wrapper class `theme.py`:
  ```python
  # theme.py — design tokens single source
  EXCEL_GREEN = "#107C41"
  SELECTION_BORDER = "#217346"
  GRAY_300 = "#E1DFDD"
  # ...

  class Color:
      excel_green = "#107C41"
      selection_border = "#217346"
      # ...

  class Size:
      text_base = 11  # pt
      cell_default_w = 64  # px
      # ...
  ```
- Import ở khắp nơi: `from excelapp.theme import Color, Size`.
- Đổi token = đổi 1 chỗ, áp lan tỏa.

## Acceptance criteria
1. File `src/excelapp/theme.py` chứa toàn bộ token từ §50.1-50.10.
2. Grep codebase: KHÔNG còn hardcode hex color (`#XXXXXX`) ngoại trừ `theme.py`. (`rg "#[0-9A-Fa-f]{6}" -t py` chỉ ra hits ngoài theme.py).
3. Cell selection border = `Color.selection_border` (#217346) — verify visual.
4. Ribbon background = `Color.gray_100` (#F3F2F1).
5. Cell default font = "Segoe UI" 11pt; trên Mac fallback "SF Pro" 11pt.
6. Tất cả dialog padding multiples of 8px.
7. Touch mode bật ([Spec 48](48-touch-pen-ink.md)) → touch target ≥ 44×44.

## Phụ thuộc
Mọi UI spec phụ thuộc design system này. Không sửa color/font/size ngoài file `theme.py`.

## Risk
Thấp-trung bình. Refactor color hardcode ra theme.py là 1-shot mass-replace. Sau đó dễ maintain.
