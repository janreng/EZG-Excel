# UX Flow — Spec 13 Clipboard & Paste Special

> Spec gốc: [../13-clipboard-paste-special.md](../13-clipboard-paste-special.md)

## Copy → Paste flow

```mermaid
sequenceDiagram
    actor User
    participant Source as Source Cells
    participant Clipboard
    participant Target as Target Cells
    participant Icon as Paste Options Icon

    User->>Source: Select A1:B3, Ctrl+C
    Source-->>Source: Marching ants animation on border
    Source->>Clipboard: Push (TSV plain + HTML + internal format dict)
    
    User->>Target: Click D5, Ctrl+V
    Clipboard-->>Target: Paste with default = Keep Source Formatting
    Target->>Icon: Show Paste Options icon at bottom-right of pasted range
    
    Note over Icon: Icon stays until next action
    
    User->>Icon: Click icon
    Icon->>User: Dropdown with 9 paste options
    
    User->>Icon: Click "Values"
    Icon->>Target: Re-paste with values only (no formulas/format)
    Icon-->>Icon: Stay visible until next typing or another paste
```

## Marching ants animation

```
Step 1 — Just copied A1:B3:
┌──┬──┬──┬──┐
│- │- │  │  │  ← top border dashed animating
│ -│  │  │  │  ← right border dashed
│  │  │  │  │
│ -│- │  │  │  ← bottom border dashed
└──┴──┴──┴──┘

Step 2 — Animation cycles (offset every ~200ms):
┌──┬──┬──┬──┐
│ -│ -│  │  │
│- │  │  │  │
│  │  │  │  │
│ -│ -│  │  │
└──┴──┴──┴──┘

Press Esc → animation stops, clipboard cleared.
```

## Paste Options icon-bar

```
After Ctrl+V at D5 (vùng dán):
┌──┬──┬──┐
│  │  │  │
│  │  │██│  ← D5:E7 vừa paste
│  │  │██│
└──┴──┴──┘
         ╲
          ▼
         ┌─⌄┐
         │📋│  ← Paste Options icon ở góc dưới phải vùng dán
         └──┘
         
Click icon → menu:
┌────────────────────────────────────────────┐
│ Paste                                       │
│ ┌──┐ ┌──┐ ┌──┐ ┌──┐                       │
│ │📋│ │123│ │fx│ │ T │                       │
│ │K │ │ V │ │F │ │ T │  ← row 1: 4 icons   │
│ └──┘ └──┘ └──┘ └──┘                       │
│ Keep   Values Form. Formatting              │
│ Source  (V)   (F)   only (T)                │
│                                              │
│ ┌──┐ ┌──┐ ┌──┐ ┌──┐                       │
│ │A │ │⤴│ │🔗│ │📷│                        │
│ └──┘ └──┘ └──┘ └──┘                       │
│ Values Trans- Link  Picture                  │
│ & Src  pose                                  │
│  (A)   (E)   (N)                            │
│                                              │
│ Paste Special...  ← opens full dialog       │
└────────────────────────────────────────────┘

Press 'V' on keyboard (after Ctrl+V) → quick select Values
```

## Paste Special dialog (Ctrl+Alt+V)

```
┌─ Paste Special ─────────────────────────────────────┐
│ Paste                                                │
│ ● All                       ◯ All using Source theme │
│ ◯ Formulas                  ◯ All except borders     │
│ ◯ Values                    ◯ Column widths          │
│ ◯ Formats                   ◯ Formulas and number    │
│ ◯ Comments and Notes          formats                │
│ ◯ Validation                ◯ Values and number      │
│                               formats                │
│                                                       │
│ Operation                                            │
│ ● None     ◯ Add                                     │
│ ◯ Subtract ◯ Multiply                                │
│ ◯ Divide                                             │
│                                                       │
│ ☐ Skip Blanks      ☐ Transpose                       │
│                                                       │
│  [Paste Link]   [ OK ]   [ Cancel ]                  │
└──────────────────────────────────────────────────────┘
```

## Paste Special use cases

```mermaid
flowchart TD
    A[Source: A1:A5 = numbers 10,20,30,40,50] --> B[Ctrl+C]
    
    B --> C{Target action}
    
    C -->|"Ctrl+V default"| D[D1:D5 = 10,20,30,40,50 with format copied]
    C -->|"Values only"| E[D1:D5 = 10,20,30,40,50 no format]
    C -->|"Transpose"| F[D1:H1 = 10,20,30,40,50 horizontal]
    
    C -->|"Add operation"| G{If D1:D5 already has 5,5,5,5,5}
    G --> H[After paste Add: D1:D5 = 15,25,35,45,55]
    
    C -->|"Skip Blanks"| I{If source has gap: 10,_,30,_,50}
    I --> J[Target D1:D5 = 10,old,30,old,50 - blanks not overwritten]
    
    C -->|"Link"| K[D1:D5 = =A1, =A2, =A3, =A4, =A5 with relative refs]
```

## Skip Blanks visual example

```
Source A1:A5:
┌──┐
│10│
│  │  ← blank
│30│
│  │  ← blank
│50│
└──┘

Target D1:D5 already has:
┌──┐
│ 1│
│ 2│
│ 3│
│ 4│
│ 5│
└──┘

After Ctrl+Alt+V → Skip Blanks → OK:
┌──┐
│10│  ← overwritten
│ 2│  ← NOT overwritten (source blank)
│30│  ← overwritten
│ 4│  ← NOT overwritten
│50│  ← overwritten
└──┘
```

## Transpose visual example

```
Source A1:A4 (vertical):
┌──┐
│ 1│
│ 2│
│ 3│
│ 4│
└──┘

After Paste Special → ☑ Transpose at D1:
┌──┬──┬──┬──┐
│ 1│ 2│ 3│ 4│  ← horizontal D1:G1
└──┴──┴──┴──┘
```

## Operation paste flow

```mermaid
sequenceDiagram
    actor User
    participant Source
    participant Target

    Note over Source: A1=5, A2=10, A3=15
    Note over Target: B1=100, B2=200, B3=300
    
    User->>Source: Select A1:A3, Ctrl+C
    
    User->>Target: Select B1:B3
    User->>Target: Ctrl+Alt+V
    
    Note over Target: Paste Special dialog opens
    User->>Target: Choose Values + Operation Multiply
    User->>Target: Click OK
    
    Note over Target: B1 = 100*5 = 500
    Note over Target: B2 = 200*10 = 2000
    Note over Target: B3 = 300*15 = 4500
```

## Clipboard pane (Home → Clipboard launcher)

> ⚠ Phím tắt **Ctrl+C 2 lần** để mở Office Clipboard đã bị **gỡ ở Office 365 hiện
> đại** — đừng implement. Cách mở duy nhất bây giờ: tab **Home → nhóm Clipboard →
> nút launcher (mũi tên góc dưới-phải)**. Giữ Ctrl+C-twice chỉ để tham khảo legacy.

```
┌─ Clipboard (Office) ───────────────────┐
│ [Paste All]  [Clear All]                │
│ ──────────────────────────────────────  │
│ ▼ Click an item to paste:                │
│                                          │
│ 📋 1,234.56                              │
│    (latest, from Sheet1!A1)              │
│                                          │
│ 📋 "Nguyen Van A"                        │
│    (from Sheet1!B5)                      │
│                                          │
│ 📋 =SUM(A1:A10)                          │
│    (from Sheet2!C3)                      │
│                                          │
│ 📋 [Image]                               │
│    (from Word)                           │
│                                          │
│ ... (max 24 items)                       │
│ ──────────────────────────────────────  │
│ Options ▼                                │
└──────────────────────────────────────────┘

Modern alternative:
- Win+V → Windows Clipboard History (system-level, cross-app)
```

## Drag & drop from external app

```mermaid
sequenceDiagram
    actor User
    participant Browser as Web Browser
    participant Excel as Ezcel
    
    User->>Browser: Select HTML table
    User->>Browser: Ctrl+C
    Note over Browser: Clipboard has HTML + plain text
    
    User->>Excel: Click A1, Ctrl+V
    Excel->>Excel: Detect HTML format in clipboard
    Excel->>Excel: Parse HTML <table><tr><td> → grid structure
    Excel->>Excel: Preserve cell formatting (colors, alignment, bold)
    Excel->>User: Show in A1:D10 with formatting
    
    Excel->>Excel: Show Paste Options icon
    User->>Excel: Optionally click → "Keep Text Only" to strip formatting
```

## Implementation hints cho Slave

- **Clipboard format**: Excel pushes 3+ formats:
  - `text/plain` (TSV)
  - `text/html` (with full styling)
  - `application/vnd.ms-excel` (internal binary blob)
- **Internal copy** trong Ezcel: dùng cấu trúc dict `{cells: matrix, format: matrix, formulas: matrix}` lưu trong app singleton; ngoài còn push plain TSV + HTML to system clipboard for interop.
- **Marching ants**: `QTimer.singleShot(200ms, ...)` cycle dash offset; redraw selection range with `QPen(Qt.DashLine)` styled.
- **Paste Options icon**: floating `QToolButton` overlay anchored bottom-right của pasted range; persists until next type/paste/Esc.
- **Paste Special dialog**: standard `QDialog` với radio groups + checkboxes.
- **Skip Blanks logic**: when applying paste, for each source cell that's empty → skip writing to target.
- **Transpose**: matrix transpose `[[a,b],[c,d]] → [[a,c],[b,d]]` before paste.
- **Operation paste**: load existing target values, apply op cell-by-cell, write back.
- **HTML paste from external**: parse with `lxml.html` or built-in Python `html.parser`; map CSS styles → format dict.
