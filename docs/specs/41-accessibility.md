# SPEC 41 — Accessibility (Accessibility Checker / Read Aloud / Immersive Reader / Alt Text)

## Mục tiêu
Workbook accessible: Accessibility Checker phát hiện issue, Alt Text cho objects, Read Aloud, screen reader support.

## Trạng thái hiện tại
- ✗ Chưa có.

## 41.1 Accessibility Checker (Review → Check Accessibility)

### Pane bên phải
```
┌─ Accessibility ───────────────────────┐
│ Inspection Results                     │
│ ──────────────────────────────────────│
│ ▼ Errors                               │
│   ▣ Missing alt text                   │
│      - Sheet1!A1 (image)               │
│      - Sheet2!B5 (chart)               │
│   ▣ Hard-to-read text contrast         │
│      - Sheet1!C3                       │
│ ▼ Warnings                             │
│   ▣ Default sheet name                 │
│      - Sheet1 (rename suggested)       │
│   ▣ Merged cells                       │
│      - Sheet1!A1:D1                    │
│ ▼ Tips                                 │
│   ▣ Add table headers                  │
│      - Table1                          │
│ ──────────────────────────────────────│
│ Additional Information:                │
│ Why fix: Screen readers need alt text  │
│ How to fix: Right-click image → Edit   │
│ Alt Text...                            │
│ ──────────────────────────────────────│
│ [Recommended Actions ▼]                │
│   - Generate alt text using AI         │
│   - Mark as decorative                 │
└────────────────────────────────────────┘
```

### Issue categories

**Errors** (must fix):
- Missing alt text on images, shapes, charts, SmartArt
- Tables with no header row
- Hard-to-read text color contrast (< 4.5:1 ratio)

**Warnings** (should fix):
- Default sheet names (Sheet1, Sheet2 — rename to meaningful)
- Merged cells (screen reader skips merged)
- Sheets only contain image (no text alternative)
- Hyperlink text not descriptive (e.g. "click here")

**Tips** (suggested):
- Add table headers
- Use semantic styles (Title, Heading 1...) thay vì bold ad-hoc
- Provide named ranges for important data

### Keep accessibility checker running
- Toggle at bottom of pane: "Keep accessibility checker running while I work"
- Khi bật: status bar hiện "Accessibility: Investigate" / "Good to go" indicator.

## 41.2 Alt Text

Right-click object → Edit Alt Text → pane bên phải:
- Description textarea (mô tả cho screen reader).
- "Mark as decorative" checkbox (object trang trí — screen reader skip).
- "Generate a description for me" button (AI auto-generate — modern Excel).

## 41.3 Read Aloud

Review → Read Aloud:
- Reads selected cells aloud (TTS).
- Settings: voice, speed.
- Continue reading: arrow keys move forward/back.

## 41.4 Immersive Reader (Web Excel only)

Out of scope cho Ezcel desktop. Stub disabled trong View tab.

## 41.5 Screen Reader Support

### ARIA-like roles cho QTableView
- Mỗi cell có "name" = `<sheet> <addr> <value>` cho screen reader.
- Cell mode announcement: "Ready / Edit / Enter / Point".
- Selection change → announce new selection.
- Formula bar change → announce formula.

### Keyboard-only navigation
- Mọi action accessible qua keyboard (no mouse-required).
- Tab navigation theo logical order (ribbon → name box → formula bar → grid → status bar → sheet tabs).
- Focus indicators rõ ràng (viền + contrast).

### High contrast mode
- Detect Windows high contrast → override colors.

## Implementation note

### QAccessible
- PySide6 hỗ trợ QAccessible.
- Set role per widget: `QAccessibleInterface.role()`.
- Cells: `QAccessibleTableCellInterface`.
- Test: NVDA / Narrator screen reader.

### Accessibility Checker engine
- Iterate sheets + cells + objects.
- Check rules:
  - Image without alt text → error
  - Cell merged → warning
  - Text contrast (compute WCAG 2.1 contrast ratio from `_fmt.color` + `_fmt.bg`)
  - Sheet name == default pattern → warning
- Async (don't block UI on large workbook).

### Color contrast formula (WCAG 2.1)
```
L1 = luminance(color1)
L2 = luminance(color2)
ratio = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)
# AA: ≥ 4.5:1 normal text, ≥ 3:1 large text
# AAA: ≥ 7:1 normal, ≥ 4.5:1 large
```

## Acceptance criteria
1. Workbook có image không alt text → Review → Check Accessibility → pane hiện "Missing alt text" với cell ref.
2. Click issue → cell/object focus.
3. Right-click image → Edit Alt Text → gõ description → save → re-check → issue mất.
4. Merged A1:D1 → Accessibility check → warning "Merged cells".
5. Cell text màu vàng nhạt trên nền trắng → low contrast warning.
6. Toggle "Keep checker running" → status bar hiện indicator real-time.
7. NVDA screen reader open Ezcel → navigate cells → đọc đúng "B5 100"; F2 → "Edit mode"; type → đọc lại ký tự.

## Phụ thuộc
- [34 Shapes / Images](34-shapes-images-smartart.md) — alt text storage.
- [11 Status Bar](11-status-bar.md) — accessibility indicator.

## Risk
Trung bình. QAccessible integration phải test với NVDA/Narrator thực tế. Color contrast cho gradient/theme color phức tạp.
