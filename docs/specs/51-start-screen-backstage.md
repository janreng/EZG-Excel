# SPEC 51 — Start Screen / Backstage (File Menu / Home / New / Open / Info / Save / Print / Account)

## Mục tiêu
Trải nghiệm "home" và File menu hiện đại của Excel: Start Screen khi mở app + Backstage view (File menu) với tabs Home/New/Open/Info/Save/Save As/Print/Share/Export/Publish/Close/Account/Feedback/Options.

## Trạng thái hiện tại
- ✗ Chưa có Start Screen — app mở thẳng workbook trống.
- ✗ Chưa có Backstage view — File menu chỉ là menubar đơn giản.
- ✗ Chưa có Recent files list.
- ✗ Chưa có Templates gallery.
- ✗ Chưa có Account pane.

## 51.1 Start Screen (Mở app, không kèm file)

Khi user mở Ezcel KHÔNG kèm file argument, hiển thị Start Screen full window thay vì workbook trống.

### Layout (vertical split)
```
┌─────────────────────────────────────────────────────────────────┐
│ ▲ [Ezcel logo]    [Search templates ____________________] [👤] │
├──────────────────┬──────────────────────────────────────────────┤
│                  │  ▶ Home  │ New │ Open                        │
│  [Sidebar]       │ ──────────────────────────────────────────── │
│                  │                                                │
│  ▶ Home          │  Welcome to Ezcel                              │
│  ◯ New           │                                                │
│  ◯ Open          │  Recent          Pinned          Shared       │
│  ◯ Account       │  ──────────────────────────────────────────── │
│  ◯ Feedback      │  📊 Budget 2026.xlsx        2 hours ago        │
│  ◯ Options       │  📊 Sales Q1.xlsx           Yesterday          │
│                  │  📊 Inventory.xlsx          3 days ago         │
│                  │  📊 Project Plan.xlsx       Last week          │
│                  │                                                │
│                  │  [More workbooks...]                           │
│                  │                                                │
│                  │  ──────────────────────────────────────────── │
│                  │  Templates:                                    │
│                  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐     │
│                  │  │Blank│ │Cal- │ │Bud- │ │Inv- │ │Goal │     │
│                  │  │     │ │endar│ │ get │ │entory│ │Track│     │
│                  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘     │
│                  │  [More templates ▶]                            │
└──────────────────┴──────────────────────────────────────────────┘
```

### Tabs trong sidebar
- **Home** (default): Recent + Pinned + Shared + Templates featured.
- **New**: Templates gallery full.
- **Open**: file picker + Recent / Pinned / Shared / Browse.
- **Account**: user info + license + connected services + theme toggle.
- **Feedback**: send feedback / report bug.
- **Options**: shortcut → File → Options dialog.

### Home tab sections
- **Welcome banner** (large): "Welcome to Ezcel" + 3 quick action buttons:
  - 🆕 New blank workbook (Ctrl+N)
  - 📂 Open... (Ctrl+O)
  - 📋 New from template
- **Recent** (default tab; tabs: Recent / Pinned / Shared with Me):
  - List file với icon + name + path + last opened + author avatar.
  - Hover row → ⭐ pin button + ✕ remove from list.
  - Click → open file.
  - Right-click → Open file location / Copy path / Remove from list / Clear unpinned.
- **Templates carousel**: 5-10 featured templates với thumbnail.

### Recent files behavior
- Sort: last opened descending.
- Pin: pinned items lên đầu, không bị evict khi list đầy 50.
- Persist: QSettings.
- Cleanup: nếu file path không tồn tại → mark grayed + tooltip "File not found".

## 51.2 Backstage View (File menu khi đã mở workbook)

Click File button (góc trên trái ribbon) → toàn cửa sổ chuyển sang Backstage view (giống Word/PowerPoint Office 365).

### Sidebar tabs
1. **Home** — same as Start Screen Home.
2. **New** — templates gallery.
3. **Open** — recent + browse.
4. **Info** — current workbook properties + protection + accessibility check.
5. **Save** — quick save (Ctrl+S).
6. **Save As** — save to OneDrive / This PC / file picker.
7. **Save as Adobe PDF** — direct PDF export (nếu có Acrobat) hoặc bỏ.
8. **Print** — [Spec 24](24-print-page-setup.md).
9. **Share** — [Spec 44](44-collaboration-version-history.md) (stub).
10. **Export** — Create PDF/XPS / Change File Type.
11. **Publish** — to OneDrive / SharePoint (stub).
12. **Close** — close workbook (Ctrl+W).
13. **Account** — user info, license, theme.
14. **Feedback** — issue report.
15. **Options** — Settings dialog.

### Info tab — Current Workbook
```
┌─ Info ─────────────────────────────────────────────────┐
│ Budget 2026.xlsx                                        │
│ ──────────────────────────────────────────────────────│
│ Protect Workbook                                        │
│  ┌────────────────────────────────────────────────────┐│
│  │ 🔒 [Protect Workbook ▼]                            ││
│  │     Control what changes can be made               ││
│  └────────────────────────────────────────────────────┘│
│ ──────────────────────────────────────────────────────│
│ Inspect Workbook                                        │
│  ┌────────────────────────────────────────────────────┐│
│  │ 🔍 [Check for Issues ▼]                            ││
│  │     • Inspect Document                             ││
│  │     • Check Accessibility                          ││
│  │     • Check Compatibility                          ││
│  └────────────────────────────────────────────────────┘│
│ ──────────────────────────────────────────────────────│
│ Manage Workbook                                         │
│  ┌────────────────────────────────────────────────────┐│
│  │ 📂 [Manage Workbook ▼]                             ││
│  │     There are no unsaved changes                   ││
│  └────────────────────────────────────────────────────┘│
│ ──────────────────────────────────────────────────────│
│ Version History                                         │
│  ┌────────────────────────────────────────────────────┐│
│  │ 🕐 [Version History]                               ││
│  │     5 versions available                           ││
│  └────────────────────────────────────────────────────┘│
│ ──────────────────────────────────────────────────────│
│ Browser View Options                                    │
│ Compatibility Mode                                      │
│ ─────────────────────────────────────────  Properties: │
│                                              Size: 2 MB │
│                                              Author: NV │
│                                              Tags:      │
│                                              ...        │
└──────────────────────────────────────────────────────────┘
```

### New tab — Templates gallery
```
┌─ New ──────────────────────────────────────────────────┐
│ Search for online templates [_________________________] │
│ Suggested searches: Budget · Calendar · Invoice · Plan  │
│ ──────────────────────────────────────────────────────│
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│
│ │ Blank  │ │ Calen- │ │ Budget │ │ Inven- │ │ Time-  ││
│ │Workbook│ │  dar   │ │        │ │  tory  │ │ sheet  ││
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘│
│ ─────────────────────────────────────────────────────│
│ Categories:                                            │
│ Business · Personal · Education · Industry · Lists ... │
└─────────────────────────────────────────────────────────┘
```

### Account tab
```
┌─ Account ──────────────────────────────────────────────┐
│ User Information                                        │
│ ┌──────────────────────────────────────────────────────┤
│ │ 👤 Nguyen Van A                                       │
│ │ phantrongluc001.ezg@gmail.com                         │
│ │ [Sign out]   [Switch account]                         │
│ └──────────────────────────────────────────────────────┤
│ Connected Services                                      │
│  • OneDrive (not connected) [Add]                       │
│  • Google Drive [Add]                                   │
│ ──────────────────────────────────────────────────────│
│ Office Theme: [Colorful ▼]                              │
│  • Colorful (default green Excel header)                │
│  • Dark Gray                                            │
│  • Black                                                │
│  • White                                                │
│  • Use system setting                                   │
│ ──────────────────────────────────────────────────────│
│ Product Information                                     │
│  Ezcel v0.11.2                                          │
│  License: MIT                                           │
│  [Check for Updates]                                    │
└─────────────────────────────────────────────────────────┘
```

## 51.3 Options dialog (File → Options)

Standard settings dialog với sidebar categories:
- General
- Formulas
- Data
- Proofing
- Save
- Language
- Accessibility
- Advanced
- Customize Ribbon
- Quick Access Toolbar
- Add-ins
- Trust Center
- Copilot

Mỗi category page với form fields.

## 51.4 Closing app behavior

- File có unsaved changes → dialog "Do you want to save changes to X.xlsx?" Save / Don't Save / Cancel.
- Multiple workbooks → loop từng file.
- Close last workbook → quay về Start Screen (không quit app); user phải close Start Screen (window X) để quit.

## Implementation note

### Stack
- Start Screen + Backstage = `QStackedWidget` page (toàn cửa sổ).
- Sidebar = `QListWidget` với delegate custom (icon + label).
- Content area = từng QWidget per tab.
- Animation: fade transition 200ms khi switch tab (hoặc instant).

### Recent files
- `QSettings.value("recent_files")` → list[dict(path, opened_at, pinned)].
- Max 50 items không pinned + unlimited pinned.

### Templates
- Bundle `.xltx` files trong `assets/templates/`.
- Online templates: optional phase muộn — kéo từ Microsoft Office Templates Library (cần API key, có thể skip).

### Theme switching
- 4 theme: Colorful / Dark Gray / Black / White.
- Override QApplication palette + ribbon stylesheet.
- Persist QSettings.

## 51.5 Reference design (ảnh)

User cần ảnh ref thực sự cho Slave (bot-main code), download từ:

### Excel Start Screen real
- https://support.microsoft.com/en-us/office/welcome-to-excel-c5b15c12-d294-46c8-841a-aab3b13d4dd0 (có screenshot)
- https://learn.microsoft.com/en-us/training/modules/excel-design/

### Excel Backstage View real
- https://support.microsoft.com/en-us/office/where-is-backstage-view-7ada6dc4-e8b5-4d36-9b09-b06b39b3e0f4
- https://learn.microsoft.com/en-us/office/dev/add-ins/excel/

### Fluent Design refs
- https://fluent2.microsoft.design/ — full design system với hình + token.

### Concrete artifacts cần Slave có
1. **Screenshot Excel Start Screen** (Windows 11 layout, light + dark theme).
2. **Screenshot Backstage Info tab**.
3. **Screenshot Templates gallery**.
4. **Screenshot Account tab**.
5. **Fluent Icons SVG set** — download từ https://github.com/microsoft/fluentui-system-icons.

Đặt vào `docs/specs/_assets/screenshots/excel-*.png` và reference từ spec markdown:
```markdown
![Excel Start Screen](./_assets/screenshots/excel-start-screen-win11.png)
```

## Acceptance criteria
1. Mở Ezcel không kèm file → Start Screen full window thay vì workbook trống.
2. Recent list hiển thị 5 file gần nhất; click → mở.
3. Pin file → pin icon ⭐ filled; lên đầu list.
4. File → Backstage view → tab Home active mặc định.
5. Backstage Info tab → hiển thị file size, author, sheet count, properties.
6. Backstage Account tab → đổi theme "Dark Gray" → toàn app sang dark theme; restart vẫn giữ.
7. Backstage New tab → templates gallery; click "Blank Workbook" → workbook mới.
8. Close last workbook → quay về Start Screen (không quit).

## Phụ thuộc
- [50 Design System](50-design-system.md) — colors/typography.
- [36 File Formats](36-file-formats-autosave.md) — Recent files persistence.
- [24 Print](24-print-page-setup.md) — Print tab.
- [44 Collaboration](44-collaboration-version-history.md) — Share/Version History.
- [29 Protection](29-protection.md) — Protect Workbook trong Info tab.
- [41 Accessibility](41-accessibility.md) — Check Accessibility trong Info.

## Risk
Trung bình. UI lớn nhưng pattern chuẩn (Word/PowerPoint cùng layout). Bottleneck thực là recent files persistence + theme switching.
