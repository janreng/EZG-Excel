# UX Flow — Spec 05 AutoFill / AutoComplete / Flash Fill / Drag & Drop

> Spec gốc: [../05-data-entry-autofill.md](../05-data-entry-autofill.md)

## Fill Handle UI states

### Idle — selection có fill handle
```
┌───┬───┬───┐
│   │   │   │
│   │▓██│   │  ← selected B5
│   │   │   │  
└───┴───┴─█─┘  ← fill handle (4x4px green square)
              góc dưới phải
```

### Hover fill handle
```
┌───┬───┬───┐
│   │▓██│   │
│   │   │   │
└───┴───┴─█─┘
          ▲
          + (cursor đổi thành crosshair đen mỏng)
```

### Drag fill handle xuống 5 cells
```
┌───┬───┬───┐
│   │▓██│   │  B5 = 1
│   │██▓│   │  drag start
│   │   │   │
│   │   │   │  ← preview tooltip:
│   │   │   │     "5"
└───┴───┴───┘  ← drop position
```

## AutoFill drag flow

```mermaid
flowchart TD
    A[User select cell hoặc range] --> B[Fill handle visible góc dưới phải]
    B --> C{Mouse action}
    
    C -->|Hover| D[Cursor → crosshair +]
    C -->|Drag| E[Show preview tooltip với value cuối]
    C -->|Double-click| F[Auto-fill xuống đến cuối data cột bên cạnh]
    C -->|Right-click + drag| G[Hiển thị menu sau khi thả]
    C -->|Ctrl + drag| H["ĐẢO hành vi mặc định — số đơn thành TẠO series, ngày/chuỗi-series thành ép COPY"]
    
    E --> I[User release mouse]
    I --> J[Apply fill]
    J --> K[Smart Tag icon xuất hiện cuối vùng fill]
    K --> L{User click Smart Tag?}
    L -->|Yes| M[Menu: Copy Cells / Fill Series / Fill Formatting Only / Fill Without Formatting / Flash Fill]
    L -->|No| N[Smart Tag fade after few seconds or click outside]
    
    G --> O[Menu: Copy / Fill Series / Fill Days / Fill Weekdays / Fill Months / Fill Years / ...]
```

## Smart Tag (Auto Fill Options) UI

Sau khi fill A1=1 drag xuống A10 (kéo thường, KHÔNG giữ Ctrl):
```
┌───┐
│ 1 │ A1
├───┤
│ 1 │  ← mặc định COPY: tất cả = 1
├───┤
│ 1 │
...
├───┤
│ 1 │ A10
├───┤
│   │
└───┘
     ┌─⌄┐  ← Smart Tag icon (góc dưới phải vùng fill)
     └──┘
     
Click icon → menu:
┌────────────────────────────┐
│ ● Copy Cells               │  ← mặc định cho SỐ đơn = Copy
│ ◯ Fill Series              │  ← chọn cái này → 1,2,3,...,10
│ ◯ Fill Formatting Only     │
│ ◯ Fill Without Formatting  │
│ ──────────────────────────  │
│ ◯ Flash Fill               │
└────────────────────────────┘
```

> **Số đơn:** kéo thường = **copy** (1,1,…); muốn 1,2,3… thì chọn *Fill Series*
> hoặc **giữ Ctrl khi kéo**. Ngược lại với chuỗi-series (ngày, "Mon", "Q1"): kéo
> thường = **series**, giữ Ctrl khi kéo = **copy**. (Hai-số làm seed như 1,3 →
> series 1,3,5,… ngay cả khi kéo thường.)

## Pattern recognition examples

```mermaid
flowchart LR
    subgraph Single
        A1["[1]"] -->|drag| A2["1,1,1,1,1"]
    end
    
    subgraph Number_with_step
        B1["[1,2]"] -->|drag| B2["3,4,5,6,7"]
    end
    
    subgraph Day_short
        C1["[Mon]"] -->|drag| C2["Tue,Wed,Thu..."]
    end
    
    subgraph Month
        D1["[Jan]"] -->|drag| D2["Feb,Mar,Apr..."]
    end
    
    subgraph Quarter
        E1["[Q1]"] -->|drag| E2["Q2,Q3,Q4,Q1"]
    end
    
    subgraph Date
        F1["[01/01/2024]"] -->|drag| F2["02/01,03/01..."]
    end
    
    subgraph Text_number
        G1["[Product1]"] -->|drag| G2["Product2,Product3..."]
    end
    
    subgraph Formula
        H1["[=A1]"] -->|drag| H2["=A2,=A3 relative"]
    end
```

## Flash Fill (Ctrl+E) flow

```mermaid
sequenceDiagram
    actor User
    participant Source as Column A (data)
    participant Target as Column B (example)
    participant Engine as Flash Fill Engine

    Note over Source: Column A:<br/>"Nguyen Van A"<br/>"Tran Van B"<br/>"Le Thi C"
    
    User->>Target: B1 = "Nguyen"
    User->>Target: B2 = "Tran"
    Note over Target: 2 ví dụ user nhập tay
    
    User->>Target: Ctrl+E
    Target->>Engine: Analyze pattern (col A → col B)
    Engine->>Engine: Detect pattern = lấy token đầu tiên (split by space)
    Engine-->>Target: Fill B3,B4,B5... = ["Le", "Pham", "Hoang", ...]
    
    Note over Target: All B cells filled
```

### Flash Fill auto-suggestion (khi gõ)

```
User đang gõ row 3 sau khi đã làm 2 row đầu:

Col A         Col B
"Nguyen Van A" "Nguyen"
"Tran Van B"   "Tran"
"Le Thi C"     [Le      ] ← user just typed "L"
"Pham..."      [Pham    ]  ← ghost preview xám
"Hoang..."     [Hoang   ]  ← Flash Fill suggest
"Do..."        [Do      ]
                          
User press Enter → accept all suggestions
User type → reject and continue manual
```

## AutoComplete (text column) flow

```mermaid
sequenceDiagram
    actor User
    participant Cell
    participant Column as Cell's column data

    Note over Column: Existing values: "Apple", "Banana", "Cherry"
    
    User->>Cell: type "A"
    Cell->>Column: scan for prefix match
    Column-->>Cell: 1 match = "Apple"
    Cell->>User: show "Apple" with "pple" in gray (ghost text)
    
    alt User accepts
        User->>Cell: press Enter or Tab
        Cell->>Cell: complete to "Apple"
    else User continues typing
        User->>Cell: type "n"  (anomaly)
        Cell->>Column: scan for "An"
        Column-->>Cell: 0 match
        Cell->>Cell: clear suggestion, keep "An" only
    else User presses Delete
        Cell->>Cell: clear suggestion, keep "A"
    end
```

### AutoComplete UI

```
Cột A có: Apple, Banana, Cherry

User gõ "A" vào A5:

┌───────────────┐
│Apple          │  ← "A" trắng (user typed), "pple" xám (suggested)
└───────────────┘

→ Enter → cell = "Apple"
→ Backspace → cell = "" (cancel)
→ tiếp tục gõ "B" → suggestion clear, cell = "AB"
```

## Drag & drop cells flow

```mermaid
flowchart TD
    A[User select A1:B3 range] --> B[Hover viền selection]
    B --> C{Cursor changes to 4-arrow}
    C --> D{Drag action}
    
    D -->|Plain drag| E[Move range to drop position]
    D -->|Ctrl + drag| F[Copy range to drop position]
    D -->|Shift + drag| G[Insert at drop position, push other cells]
    
    E --> H{Drop on cells with data?}
    F --> H
    G --> H
    
    H -->|Yes| I[Dialog: 'Replace the contents?' OK/Cancel]
    H -->|No| J[Apply directly]
    
    I -->|OK| J
    I -->|Cancel| K[Revert]
```

### Drag & drop visual

```
Step 1 — Hover viền selection:
┌───┬───┬───┬───┐
│   │   │   │   │
│   │▓██│██▓│   │  ← A1:B3 selected
│   │██▓│▓██│   │
│   │▓██│██▓│   │
└───┴───┴───┴───┘
       ▲
       cursor on border → 4-arrow ✣

Step 2 — Drag start (Ctrl held for copy):
┌───┬───┬───┬───┐
│   │░░░│░░░│   │  ← original ghosted
│   │░░░│░░░│   │
│   │░░░│░░░│   │
└───┴───┴───┴───┘
              ╲
               ╲   drag direction
                ▼
┌───┬───┬───┬───┐
│   │   │██░│██░│  ← drop preview
│   │   │░██│██░│
│   │   │░░░│██░│
└───┴───┴───┴───┘
        ▲
        cursor + tooltip "D1:E3"
```

## Right-click drag menu

```
After right-click drag from A1 to A10:

┌──────────────────────────────────────┐
│ ● Copy Cells                          │
│ ◯ Fill Series                         │
│ ◯ Fill Formatting Only                │
│ ◯ Fill Without Formatting             │
│ ──────────────────────────────────── │
│ ◯ Fill Days                           │
│ ◯ Fill Weekdays                       │
│ ◯ Fill Months                         │
│ ◯ Fill Years                          │
│ ──────────────────────────────────── │
│ ◯ Linear Trend                        │
│ ◯ Growth Trend                        │
│ ──────────────────────────────────── │
│ ◯ Series...                           │  ← opens Series dialog
└──────────────────────────────────────┘
```

## Implementation hints cho Slave

- **Fill handle render** trong `CellDelegate.paint()` khi cell là góc dưới phải của selection.
- **Hit testing**: detect mouse position trong 4x4 region của handle, hot path cần check chỉ selection bounding box.
- **Pattern recognition** = function `detect_pattern(values: list[str]) → Pattern | None`:
  - Check số đơn / arithmetic progression / date / day name / month name / Q + digit / text + trailing digit / formula.
  - Trả `Pattern` object với `next(idx) → str` method.
- **Smart Tag** = floating `QToolButton` overlay anchored cuối vùng fill, parent = MainWindow.
- **Flash Fill engine** = rule-based:
  - Detect operation: substring (split + take N) / case change / format mask / concatenation.
  - Try multiple candidates, score by consistency với user examples.
- **AutoComplete inline suggestion** = render trong delegate (gray text after user input position).
- **Drag & drop**: hook `QTableView.mousePressEvent` + `mouseMoveEvent`, detect hover on border → change cursor + initiate drag with QDrag.
