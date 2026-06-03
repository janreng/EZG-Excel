# UX Flow — Spec 04 Name Box & Formula Bar

> Spec gốc: [../04-name-box-formula-bar.md](../04-name-box-formula-bar.md)

## Layout — components

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  ┌──────────┐ ┌───┐ ┌──────────────────────────────┐ ┌──────┐  │
│  │ Name Box │ │fx │ │      Formula Bar Text Area    │ │ ▼    │  │
│  │  [A1   ▼]│ │   │ │                                │ │      │  │
│  └──────────┘ └───┘ └──────────────────────────────┘ └──────┘  │
│   80-120px wide                                       expand btn │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                       ▲                ▲
                              Confirm ✓ |   Cancel ✗   (chỉ khi đang Edit)
```

## Name Box navigate flow

```mermaid
flowchart TD
    A[User click Name Box hoặc Ctrl+G/F5] --> B[Name Box focus, text highlighted]
    B --> C{User gõ gì?}
    C -->|"Z100"| D[Validate: A1 syntax]
    C -->|"A1:C5"| E[Validate: range syntax]
    C -->|"DoanhThu"| F[Lookup Named Range]
    C -->|"A1:B3,D5,F1:F10"| G[Validate: multi-range]
    C -->|"Sheet2!D5"| H[Validate: cross-sheet ref]
    
    D --> I[Enter pressed?]
    E --> I
    F --> I
    G --> I
    H --> I
    
    I -->|Yes| J[Jump to address/range/name]
    I -->|Esc| K[Restore old address]
    I -->|Invalid syntax| L[Error: 'Reference is not valid']
```

## Formula Bar states

### State 1: Ready, ô trống
```
┌────────┐ ┌──┐ ┌────────────────────────┐
│  A1    │ │fx│ │                        │
└────────┘ └──┘ └────────────────────────┘
```

### State 2: Ô có số 123
```
┌────────┐ ┌──┐ ┌────────────────────────┐
│  A1    │ │fx│ │ 123                    │
└────────┘ └──┘ └────────────────────────┘
```

### State 3: Ô có công thức =SUM(A1:A10) (kết quả = 55)
```
Cell B5 hiển thị: 55
Formula Bar hiển thị: =SUM(A1:A10)  ← original formula

┌────────┐ ┌──┐ ┌────────────────────────────────┐
│  B5    │ │fx│ │ =SUM(A1:A10)                   │
└────────┘ └──┘ └────────────────────────────────┘
```

### State 4: Edit mode (đang sửa formula)
```
┌────────┐ ┌──┐ ┌──────────────────────────────────┐ ┌─┐ ┌─┐
│  B5    │ │fx│ │ =SUM(A1:A10)|                    │ │✗│ │✓│
└────────┘ └──┘ └──────────────────────────────────┘ └─┘ └─┘
                                            ↑ cursor   Cancel Confirm
```

### State 5: Expand mode (Ctrl+Shift+U) — multi-line
```
┌────────┐ ┌──┐ ┌──────────────────────────────────┐ ┌─┐ ┌─┐
│  B5    │ │fx│ │ =IF(A1>1000,                     │ │✗│ │✓│
└────────┘ └──┘ │     "High",                       │ └─┘ └─┘
                │     IF(A1>500,                    │
                │         "Medium",                  │
                │         "Low"))                    │
                └──────────────────────────────────┘
                                                  ▲
                                            ▼ collapse btn
```

## Autocomplete dropdown flow

```mermaid
sequenceDiagram
    actor User
    participant Cell as Active Cell
    participant Dropdown
    participant Engine as Formula Engine

    User->>Cell: type "="
    Note over Cell: ENTER mode, no dropdown
    
    User->>Cell: type "S"
    Cell->>Engine: query("S")
    Engine-->>Dropdown: ["SUM","SUMIF","SUMIFS","SUBSTITUTE",...]
    Dropdown->>User: show dropdown anchored below cell
    
    User->>Cell: type "U"
    Cell->>Engine: query("SU")
    Engine-->>Dropdown: ["SUM","SUMIF","SUMIFS","SUMPRODUCT"]
    Dropdown->>User: update list
    
    User->>Dropdown: ArrowDown to highlight "SUMIF"
    
    User->>Dropdown: Press Tab
    Dropdown->>Cell: insert "SUMIF("
    Note over Cell: cursor after "("
    Dropdown->>Dropdown: close
    
    Note over Cell: ScreenTip xuất hiện:
    Note over Cell: SUMIF(**range**, criteria, [sum_range])
```

## Autocomplete dropdown UI

```
Active Cell B5 đang gõ "=SU":

┌───┬───┬───┬───┐
│ A │ B │ C │ D │
│ 5 │   │=SU|│   │
└───┴───┴───┴───┘
       │
       ▼
┌──────────────────────────────────┐
│ fx SUM           ← keyboard hint │
│ fx SUMIF                         │
│ fx SUMIFS                        │
│ fx SUMPRODUCT                    │
│ fx SUMSQ                         │
│ fx SUMX2MY2                      │
│ fx SUMX2PY2                      │
│ fx SUMXMY2                       │
│ fx SUBSTITUTE                    │
│ fx SUBTOTAL                      │
│ ─────────                        │
│ 📋 SubTotalRange  ← named range │
│ 📋 SummaryTable   ← table name  │
└──────────────────────────────────┘
```

## ScreenTip syntax flow

```mermaid
flowchart LR
    A[User typed "=VLOOKUP("] --> B[ScreenTip xuất hiện]
    B --> C["=VLOOKUP(**lookup_value**, table_array, col_index_num, [range_lookup])"]
    C --> D{User type comma}
    D -->|after lookup_value| E["=VLOOKUP(A1, **table_array**, col_index_num, [range_lookup])"]
    E -->|after table_array| F["=VLOOKUP(A1, B:C, **col_index_num**, [range_lookup])"]
    F -->|after col_index_num| G["=VLOOKUP(A1, B:C, 2, **[range_lookup]**)"]
    G -->|user type ")"| H[ScreenTip closes]
```

ScreenTip mockup:
```
Cell typing: =VLOOKUP(A1, B:C, 2, |
                                  ↑ cursor after 3rd comma

┌─────────────────────────────────────────────────────────────────┐
│ VLOOKUP(lookup_value, table_array, col_index_num, **[range_lookup]**) │
└─────────────────────────────────────────────────────────────────┘
                                                       ↑ bold = current arg
```

## Sequence — Click fx button (Insert Function)

```mermaid
sequenceDiagram
    actor User
    participant FxBtn as fx Button
    participant Dialog as Insert Function Dialog
    participant ArgDlg as Function Arguments Dialog
    participant Cell

    User->>FxBtn: Click fx (or Shift+F3)
    FxBtn->>Dialog: Open
    
    Dialog->>User: Show search + category dropdown + list
    User->>Dialog: Search "vlookup"
    Dialog->>User: Filter list, show VLOOKUP, XLOOKUP, HLOOKUP
    User->>Dialog: Click VLOOKUP
    User->>Dialog: Click OK
    
    Dialog->>ArgDlg: Open with VLOOKUP args
    ArgDlg->>User: Show 4 input fields (lookup_value, table_array, col_index_num, [range_lookup])
    
    User->>ArgDlg: Click range picker ↗ next to lookup_value
    ArgDlg->>ArgDlg: Minimize (rolled up)
    User->>Cell: Drag select A1
    Cell->>ArgDlg: Return to full size, input = "A1"
    
    User->>ArgDlg: Click range picker for table_array
    User->>Cell: Drag select B:C
    Cell->>ArgDlg: input = "B:C"
    
    User->>ArgDlg: type "2" in col_index_num
    User->>ArgDlg: type "FALSE" in range_lookup
    
    ArgDlg->>User: Show preview "= 'Apple'" at bottom
    
    User->>ArgDlg: Click OK
    ArgDlg->>Cell: Insert "=VLOOKUP(A1,B:C,2,FALSE)"
```

## Implementation hints cho Slave

- **Name Box** = `QLineEdit` (custom subclass) + dropdown `QListView` cho Named Ranges.
- **Formula Bar text area** = `QLineEdit` mode default; switch sang `QPlainTextEdit` khi expand.
- **fx button** = `QPushButton` với icon "fx" (font Italic).
- **Confirm/Cancel buttons** chỉ visible khi `MainWindow.mode in {ENTER, EDIT}` (signal-driven).
- **Autocomplete dropdown** = floating `QListWidget` anchored cell bottom-left; trigger sau key event với debounce 50ms.
- **ScreenTip** = `QLabel` styled tooltip, position dưới active cell; track current arg index bằng parser (count commas after `(`).
