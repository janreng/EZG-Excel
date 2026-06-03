# UX Flow — Spec 51 Start Screen / Backstage

> Spec gốc: [../51-start-screen-backstage.md](../51-start-screen-backstage.md)

## App startup flow

```mermaid
flowchart TD
    A[User launches Ezcel] --> B{Args provided?}
    
    B -->|"None"| C[Show Start Screen full window]
    B -->|"File path arg"| D[Load file directly to workbook view]
    
    C --> E[Sidebar tabs: Home / New / Open / Account / Feedback / Options]
    C --> F[Default tab = Home]
    
    F --> G[Show: Welcome banner + Recent files + Templates carousel]
    
    G --> H{User action}
    
    H -->|Click recent file| I[Load file → workbook view]
    H -->|Click 'New blank workbook'| J[Empty workbook → workbook view]
    H -->|Click template thumbnail| K[Load template → workbook view]
    H -->|Click Open tab| L[File picker dialog]
    H -->|Click Account tab| M[Account pane]
    H -->|Close window| N[Quit app]
    
    L --> O[User picks file]
    O --> I
    
    I --> P[Workbook view]
    J --> P
    K --> P
```

## Start Screen — Home tab mockup

```
┌─ Ezcel ──────────────────────────────────────────────────────────────┐
│ [≡ menu]  [Search templates and online help_____________]  [👤 user] │
├──────────────────┬───────────────────────────────────────────────────┤
│ Home      ◀      │  Good morning, soinhoxiu                           │
│ New              │  ──────────────────────────────────────────────── │
│ Open             │  Quick access:                                      │
│ Account          │  ┌─────────┐ ┌─────────┐ ┌─────────┐               │
│ Feedback         │  │ 🆕 New  │ │ 📂 Open │ │ 📋 Tpl  │               │
│ Options          │  │ blank   │ │  ...    │ │  ...    │               │
│                  │  └─────────┘ └─────────┘ └─────────┘               │
│                  │                                                      │
│                  │  ──────────────────────────────────────────────── │
│                  │  Recent      [Pinned] [Shared with Me]              │
│                  │  ──────────────────────────────────────────────── │
│                  │  📊 Budget 2026.xlsx                                │
│                  │     C:\Users\pc\Documents\         2 hours ago      │
│                  │     [⭐] [×]                                         │
│                  │                                                      │
│                  │  📊 Sales Q1.xlsx                                   │
│                  │     C:\Users\pc\Desktop\           Yesterday        │
│                  │     [⭐] [×]                                         │
│                  │                                                      │
│                  │  📊 Inventory.xlsx                                  │
│                  │     OneDrive\Work                   3 days ago       │
│                  │     [⭐] [×]                                         │
│                  │                                                      │
│                  │  📊 Project Plan.xlsx                               │
│                  │     C:\Users\pc\Projects\          Last week        │
│                  │     [⭐] [×]                                         │
│                  │                                                      │
│                  │  [More workbooks...]                                │
│                  │                                                      │
│                  │  ──────────────────────────────────────────────── │
│                  │  Suggested templates:                                │
│                  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐    │
│                  │  │      │ │  📅  │ │  💰  │ │  📦  │ │  🎯  │    │
│                  │  │Blank │ │ Cal- │ │Budg- │ │ Inv- │ │ Goal │    │
│                  │  │      │ │endar │ │ et   │ │entory│ │Track │    │
│                  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘    │
│                  │                                                      │
│                  │  [More templates ▶]                                 │
└──────────────────┴───────────────────────────────────────────────────┘
```

## File → Backstage navigation

```mermaid
flowchart TD
    A[Workbook view] --> B[Click File button top-left]
    B --> C[Backstage view full window]
    
    C --> D{User clicks sidebar tab}
    
    D -->|Home| E[Same as Start Screen Home]
    D -->|New| F[Templates gallery]
    D -->|Open| G[Recent + Browse + Cloud]
    D -->|Info| H[Current workbook properties]
    D -->|Save| I[Quick save Ctrl+S]
    D -->|Save As| J[File picker with format dropdown]
    D -->|Print| K[Print Preview - Spec 24]
    D -->|Share| L[Sharing options - Spec 44]
    D -->|Export| M[PDF/XPS/Change File Type]
    D -->|Close| N[Close current workbook]
    D -->|Account| O[User info + theme switcher]
    D -->|Feedback| P[Bug report form]
    D -->|Options| Q[Settings dialog modal]
    
    I --> A
    N --> R{Other workbooks open?}
    R -->|Yes| A
    R -->|No| S[Back to Start Screen]
```

## Backstage Info tab mockup

```
┌─ Ezcel ── Budget 2026.xlsx ──────────────────────────────────────────┐
│ [≡]  [▤ ribbon collapsed]                                  [👤 user]  │
├──────────────────┬───────────────────────────────────────────────────┤
│ Home             │  Info                                               │
│ New              │  ──────────────────────────────────────────────── │
│ Open             │                                                      │
│ Info     ◀       │  📊 Budget 2026.xlsx                                │
│ Save             │     C:\Users\pc\Documents\Budget 2026.xlsx          │
│ Save As          │                                                      │
│ Print            │  ┌────────────────────────────────────────────────┐│
│ Share            │  │ 🔒 Protect Workbook ▼                          ││
│ Export           │  │ Control what types of changes people can make. ││
│ Close            │  └────────────────────────────────────────────────┘│
│ ──────────────   │  ┌────────────────────────────────────────────────┐│
│ Account          │  │ 🔍 Inspect Workbook ▼                          ││
│ Feedback         │  │ Before sharing this file, check for issues:    ││
│ Options          │  │ • Document Inspector                            ││
│                  │  │ • Accessibility Checker                         ││
│                  │  │ • Compatibility Checker                         ││
│                  │  └────────────────────────────────────────────────┘│
│                  │  ┌────────────────────────────────────────────────┐│
│                  │  │ 📂 Manage Workbook ▼                            ││
│                  │  │ Today, 14:30 (no unsaved changes)               ││
│                  │  │ ▸ Recover Unsaved Workbooks                    ││
│                  │  │ ▸ Delete All Unsaved Workbooks                  ││
│                  │  └────────────────────────────────────────────────┘│
│                  │  ┌────────────────────────────────────────────────┐│
│                  │  │ 🕐 Version History (5 versions)                 ││
│                  │  │ Browse and restore previous versions            ││
│                  │  └────────────────────────────────────────────────┘│
│                  │  Properties:                          (sidebar) ▼  │
│                  │  Size: 2.4 MB                                        │
│                  │  Title: Q1 2026 Budget                              │
│                  │  Tags: Add a tag                                    │
│                  │  Categories: Finance                                │
│                  │  Author: Nguyen Van A                               │
│                  │  Last modified by: Nguyen Van A                     │
│                  │  Last modified: Today, 14:30                        │
│                  │  Created: 2026-01-15 09:00                          │
│                  │  Last printed: 2026-02-01 11:23                     │
│                  │                                                      │
│                  │  [Show All Properties]                              │
└──────────────────┴───────────────────────────────────────────────────┘
```

## Backstage New tab mockup

```
┌─ Ezcel ── Backstage ── New ──────────────────────────────────────────┐
│ Home             │  New                                               │
│ New      ◀       │  ──────────────────────────────────────────────── │
│ Open             │  Search for online templates                         │
│ ...              │  ┌──────────────────────────────────────────────┐ │
│                  │  │ [____________________________________________]│ │
│                  │  └──────────────────────────────────────────────┘ │
│                  │  Suggested: Budget · Calendar · Invoice · Plan · │
│                  │             Goal Track · Inventory                 │
│                  │  ──────────────────────────────────────────────── │
│                  │                                                      │
│                  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│                  │  │        │ │  📅    │ │  💰    │ │  📊    │     │
│                  │  │ Blank  │ │ Calen- │ │ Budget │ │Tracker │     │
│                  │  │ Work-  │ │  dar   │ │        │ │        │     │
│                  │  │ book   │ │        │ │        │ │        │     │
│                  │  └────────┘ └────────┘ └────────┘ └────────┘     │
│                  │                                                      │
│                  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│                  │  │  📦    │ │  🧾    │ │  🎯    │ │  📈    │     │
│                  │  │ Invn-  │ │ Invoi- │ │ Goal-  │ │ KPI    │     │
│                  │  │ tory   │ │   ce   │ │  set   │ │ Dash   │     │
│                  │  └────────┘ └────────┘ └────────┘ └────────┘     │
│                  │                                                      │
│                  │  Categories: Business · Personal · Education · …   │
└──────────────────┴───────────────────────────────────────────────────┘
```

## Backstage Account tab mockup

```
┌─ Ezcel ── Backstage ── Account ──────────────────────────────────────┐
│ Home             │  Account                                            │
│ New              │  ──────────────────────────────────────────────── │
│ Open             │  User Information                                   │
│ ...              │  ┌──────────────────────────────────────────────┐ │
│ Account  ◀       │  │ 👤 Nguyen Van A                               │ │
│                  │  │ phantrongluc001.ezg@gmail.com                  │ │
│                  │  │ [Sign out]   [Switch account]                  │ │
│                  │  └──────────────────────────────────────────────┘ │
│                  │                                                      │
│                  │  Connected Services                                  │
│                  │  ┌──────────────────────────────────────────────┐ │
│                  │  │ • OneDrive (not connected)        [Add]       │ │
│                  │  │ • Google Drive                    [Add]       │ │
│                  │  └──────────────────────────────────────────────┘ │
│                  │                                                      │
│                  │  Office Theme                                       │
│                  │  ┌──────────────────────────────────────────────┐ │
│                  │  │ [Colorful (green Excel header)            ▼] │ │
│                  │  │   ● Colorful (default)                        │ │
│                  │  │   ◯ Dark Gray                                  │ │
│                  │  │   ◯ Black                                      │ │
│                  │  │   ◯ White                                      │ │
│                  │  │   ◯ Use system setting                         │ │
│                  │  └──────────────────────────────────────────────┘ │
│                  │                                                      │
│                  │  Product Information                                 │
│                  │  ┌──────────────────────────────────────────────┐ │
│                  │  │ Ezcel v0.12.1                                  │ │
│                  │  │ License: MIT                                    │ │
│                  │  │ [Check for Updates]                             │ │
│                  │  └──────────────────────────────────────────────┘ │
└──────────────────┴───────────────────────────────────────────────────┘
```

## Recent files interaction flow

```mermaid
sequenceDiagram
    actor User
    participant List as Recent List
    participant FS as File System
    participant App

    User->>List: Hover row
    List->>User: Show [⭐] [×] buttons (action icons)
    
    alt Click row body
        User->>List: Click
        List->>FS: Check file exists
        alt File exists
            FS-->>List: OK
            List->>App: Open file
        else File missing
            FS-->>List: Not found
            List->>User: "File not found at C:\... Remove from list?"
        end
    else Click ⭐ pin
        User->>List: Click ⭐
        List->>List: Mark pinned, move to top
        List->>List: Save QSettings
    else Click × remove
        User->>List: Click ×
        List->>List: Remove from recent
        List->>List: Save QSettings
    else Right-click
        User->>List: Right-click
        List->>User: Context menu:
        Note over User: - Open file location<br/>- Copy path<br/>- Remove from list<br/>- Clear unpinned<br/>- Pin/Unpin
    end
```

## Implementation hints cho Slave

- **`QStackedWidget`** chứa: Start Screen page + Workbook View page + Backstage page (cùng app, switch giữa).
- **Sidebar tabs** = `QListWidget` styled với icon + label; selection-changed → switch content widget.
- **Recent files** = `QSettings.value("recent_files")` list[dict(path, opened_at, pinned)]; max 50 + unlimited pinned.
- **Templates** = bundle `.xltx` files trong `assets/templates/`; mỗi template thumbnail PNG cùng folder.
- **Theme switcher** trong Account tab:
  - "Colorful" → ribbon background green Excel.
  - "Dark Gray" → ribbon + grid dark gray.
  - "Black" → full dark mode.
  - "White" → minimal light.
  - "System" → detect OS theme.
- **Close behavior**: nếu workbook có unsaved changes → modal dialog "Save?" Save/Don't Save/Cancel.
- **Close last workbook** → `QStackedWidget.setCurrentIndex(start_screen)`, không quit app.
- **Quit app**: chỉ khi close Start Screen (X button hoặc Cmd/Alt+F4).
