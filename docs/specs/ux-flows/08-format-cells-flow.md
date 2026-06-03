# UX Flow — Spec 08 Format Cells Dialog (Ctrl+1)

> Spec gốc: [../08-format-cells-dialog.md](../08-format-cells-dialog.md)

## Entry points

```mermaid
flowchart LR
    A[User trigger] --> B(Format Cells dialog)
    
    A1[Ctrl+1] --> B
    A2[Right-click cell → Format Cells...] --> B
    A3[Home → Cells group → Format → Format Cells] --> B
    A4[Ribbon Dialog Box Launcher của Font/Alignment/Number group] --> B
    A5[Mini Toolbar → Format Cells] --> B
```

## Dialog layout — 6 tab

```
┌─ Format Cells ─────────────────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ (Active tab content here)                                       │
│                                                                  │
│                                                                  │
│                                                                  │
│                                                                  │
│                                                                  │
│                                                                  │
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Number layout

```
┌─ Format Cells / Number ────────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ Category:              Sample:                                  │
│ ┌───────────────────┐  ┌────────────────────────────────┐     │
│ │ General           │  │  $1,234.56                      │     │
│ │ Number            │  └────────────────────────────────┘     │
│ │ Currency  ▶        │                                          │
│ │ Accounting        │   Decimal places: [2  ▲▼]                │
│ │ Date              │                                          │
│ │ Time              │   Symbol: [$ English (US)        ▼]     │
│ │ Percentage        │                                          │
│ │ Fraction          │   Negative numbers:                      │
│ │ Scientific        │   ┌──────────────────────────────────┐  │
│ │ Text              │   │ $-1,234.10                         │  │
│ │ Special           │   │ $1,234.10                          │  │
│ │ Custom            │   │ ($1,234.10)         ← selected     │  │
│ └───────────────────┘   │ ($1,234.10)  (red)                 │  │
│                         └──────────────────────────────────┘  │
│                                                                  │
│ Description:                                                     │
│ Currency formats are used for general monetary values...        │
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Border — interactive border picker

```
┌─ Format Cells / Border ────────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ Presets:                Line:                                    │
│ ┌──┐ ┌──┐ ┌──┐         Style:                                   │
│ │  │ │██│ │██│         ┌───────────────────┐                   │
│ │  │ │██│ │██│         │ (None)            │                   │
│ └──┘ └██┘ └██┘         │ ─────────         │                   │
│ None Outline Inside    │ ─────  (dashed)   │                   │
│                        │ ............      │                   │
│ Border (preview):      │ ▓▓▓▓▓▓▓▓ (thick)  │                   │
│   ┌─[Top]─┐            │ ════════ (double) │                   │
│   │       │            │ ─ ─ ─ ─ ─        │                   │
│   │ [LR]  │            └───────────────────┘                   │
│  [Diag] [Diag2]                                                  │
│   │       │            Color:                                    │
│   └[Bottom]┘           ┌──────────────────┐                    │
│                         │ ■ Automatic ▼    │                    │
│                         └──────────────────┘                    │
│  Click cạnh để toggle                                            │
│                                                                  │
│  ☐ Same line for diagonal                                        │
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Border interactive flow

```mermaid
flowchart TD
    A[User open Border tab] --> B[Default state: no border]
    B --> C{User action}
    
    C -->|Click 'Outline' preset| D[All 4 outer edges toggle ON với current Style+Color]
    C -->|Click 'Inside' preset| E[Inner gridlines ON between selected cells]
    C -->|Click 'None' preset| F[All borders OFF]
    
    C -->|Click individual edge in preview| G[Toggle that edge ON/OFF]
    C -->|Change Style first then click edge| H[Edge gets new style]
    C -->|Change Color first then click edge| I[Edge gets new color]
    
    G --> J{User clicks more edges}
    J --> G
    
    D --> K[User clicks OK]
    E --> K
    F --> K
    G --> K
    H --> K
    I --> K
    
    K --> L[Apply borders to selection]
```

## Tab Number — Custom format code flow

```mermaid
sequenceDiagram
    actor User
    participant Dialog as Format Cells
    participant Parser as Format Code Parser
    participant Sample as Sample Display

    User->>Dialog: Select Category = "Custom"
    Dialog->>User: Show list of preset codes + Type box
    
    User->>Dialog: Type "#,##0.00_);[Red](#,##0.00)"
    Dialog->>Parser: Validate code
    Parser-->>Dialog: 4 sections detected (positive, negative, zero, text)
    
    Dialog->>Sample: Apply format with current cell value
    Sample->>User: Show "1,234.56" (positive)
    
    Note over Dialog: User wants to see negative behavior
    Note over Dialog: (Sample shows positive only by default)
    
    User->>Dialog: Click OK
    Dialog->>Dialog: Apply to selection
    
    Note over Dialog: Cell with -500 now shows "(500.00)" in red
```

## Custom format code visual breakdown

```
Format code: #,##0.00_);[Red](#,##0.00);0.00;"N/A: "@

  ┌──────────────────────────────────────────────┐
  │ Section 1 (positive): #,##0.00_)              │  → 1234.5 → "1,234.50 "
  │ Section 2 (negative): [Red](#,##0.00)         │  → -1234.5 → "(1,234.50)" red
  │ Section 3 (zero):     0.00                    │  → 0 → "0.00"
  │ Section 4 (text):     "N/A: "@                │  → "abc" → "N/A: abc"
  └──────────────────────────────────────────────┘
                    ▲
            ; separator between sections
```

## Tab Font

```
┌─ Format Cells / Font ──────────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ Font:                          Font style:    Size:              │
│ ┌─────────────────────────┐  ┌──────────┐  ┌────┐              │
│ │ Aptos Narrow      ✓     │  │ Regular  │  │ 11 │              │
│ │ Aptos                    │  │ Italic   │  │ 12 │              │
│ │ Arial                    │  │ Bold     │  │ 14 │              │
│ │ Calibri                  │  │ Bold     │  │ 16 │              │
│ │ Cambria                  │  │ Italic   │  │ 18 │              │
│ │ ...                      │  │          │  │... │              │
│ └─────────────────────────┘  └──────────┘  └────┘              │
│                                                                  │
│ Underline:                    Color:                             │
│ ┌──────────────────────┐    ┌──────────────────┐               │
│ │ None              ✓  │    │ ■ Automatic   ▼  │               │
│ └──────────────────────┘    └──────────────────┘               │
│                                                                  │
│ Effects:                      Preview:                           │
│ ☐ Strikethrough              ┌────────────────────┐            │
│ ☐ Superscript                │  AaBbCcYyZz        │            │
│ ☐ Subscript                  └────────────────────┘            │
│                                                                  │
│ ☑ Normal font                                                   │
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Fill

```
┌─ Format Cells / Fill ──────────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ Background Color:                Pattern Color:                  │
│ ┌─────────────────────────┐    ┌──────────────────┐            │
│ │ No Color   [More]   ⌄   │    │ ■ Automatic   ▼  │            │
│ │                          │    └──────────────────┘            │
│ │ ▓▓▓▓ Theme Colors        │    Pattern Style:                  │
│ │ ▓▓▓▓                     │    ┌──────────────────┐            │
│ │                          │    │ (None)        ▼  │            │
│ │ ▓▓▓▓ Standard Colors     │    └──────────────────┘            │
│ │ ▓▓▓▓                     │                                    │
│ │                          │    [Fill Effects...] [More Colors] │
│ │ Recent Colors            │                                    │
│ │ ▓▓                       │                                    │
│ └─────────────────────────┘                                    │
│                                                                  │
│ Sample:                                                          │
│ ┌────────────────────────────┐                                  │
│ │                              │  ← preview                       │
│ │                              │                                  │
│ └────────────────────────────┘                                  │
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Alignment

```
┌─ Format Cells / Alignment ─────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│ Text alignment             │  Orientation                       │
│  Horizontal: [General   ▼] │   ┌───────────┐                    │
│   (General/Left(Indent)/   │   │     Text  │  ← kim xoay        │
│    Center/Right(Indent)/   │   │    •      │   kéo hoặc gõ độ    │
│    Fill/Justify/Center     │   │   Text    │                    │
│    Across Selection/       │   └───────────┘                    │
│    Distributed)            │   Degrees: [ 0 ]°  (-90…90)         │
│  Vertical:   [Bottom    ▼] │                                    │
│   (Top/Center/Bottom/      │                                    │
│    Justify/Distributed)    │                                    │
│  Indent: [ 0 ]             │                                    │
│ ───────────────────────────┤                                    │
│ Text control               │                                    │
│  ☐ Wrap text               │                                    │
│  ☐ Shrink to fit           │                                    │
│  ☐ Merge cells             │                                    │
│ ───────────────────────────┤                                    │
│ Right-to-left              │                                    │
│  Text direction: [Context ▼] (Context/Left-to-Right/Right-to-Left)│
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

> Lưu ý: *Shrink to fit* và *Wrap text* loại trừ nhau; *Merge cells* + *Center
> Across Selection* khác nhau (merge gộp ô thật, center-across chỉ canh hiển thị).

## Tab Protection

```
┌─ Format Cells / Protection ────────────────────────────────────┐
│ [Number] [Alignment] [Font] [Border] [Fill] [Protection]        │
│ ──────────────────────────────────────────────────────────────│
│  ☑ Locked                                                       │
│  ☐ Hidden                                                       │
│                                                                  │
│  ⓘ Khóa ô hoặc ẩn công thức CHỈ có tác dụng sau khi bảo vệ      │
│    sheet (Review → Protect Sheet). Mặc định mọi ô đều Locked;   │
│    muốn cho sửa vài ô thì bỏ Locked ở ô đó rồi mới Protect.     │
│    Hidden = ẩn công thức trên Formula Bar khi sheet được bảo vệ.│
│ ──────────────────────────────────────────────────────────────│
│                                              [ OK ]  [ Cancel ] │
└─────────────────────────────────────────────────────────────────┘
```

> Protection tab chỉ set cờ `locked`/`hidden` trên ô — hành vi thật do
> [Spec 29 Protection](../29-protection.md) thực thi khi Protect Sheet bật.

## Implementation hints cho Slave

- **Dialog** = `QDialog` modal, parent = MainWindow.
- **Tab widget** = `QTabWidget` với 6 page widgets.
- **Number tab Category list** = `QListWidget`; on select → swap right-side content widget.
- **Custom format parser** trong `formula.py` extension hoặc `number_format.py` module mới:
  - Parse 1-4 sections separated by `;`.
  - Tokenize: digit placeholders `#0?` / decimal `.` / thousand `,` / percent `%` / scientific `E+E-` / color `[Red]` / conditional `[>1000]` / literal `"..."` / escape `\<c>` / spacer `_<c>` / repeat `*<c>` / text `@`.
  - Format value → string per current section based on sign.
- **Border tab preview** = custom `QWidget` với `paintEvent`; hit-test click → toggle edge dict.
- **Fill tab color picker** = `QColorDialog` for "More Colors"; theme colors gallery custom widget.
- **Live preview** trong Sample box: re-render khi tab content change.
- **Apply on OK**: collect dict format → call `model.set_format(selection_range, fmt_dict)` với `_push_undo()` đầu.
