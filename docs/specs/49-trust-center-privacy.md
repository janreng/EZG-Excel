# SPEC 49 — Trust Center, Privacy & Security Settings

## Mục tiêu
File → Options → Trust Center: settings về macro security, ActiveX, protected view, privacy options, network access.

## Trạng thái hiện tại
- ✗ Chưa có.

## 49.1 Trust Center Settings

### Trusted Publishers
- List của publishers có signed certificate được trust.
- Macro signed by trusted publisher → tự động enable (skip prompt).

### Trusted Locations
- Folders mà files trong đó → tự động skip Protected View / enable macros.
- Add: path + "Subfolders of this location are also trusted" checkbox.
- Built-in trusted: `%AppData%\Microsoft\Excel\XLSTART\`, `%ProgramFiles%\Microsoft Office\Templates\`.

### Trusted Documents
- Mỗi document từng được user "Enable Content" sẽ remember + auto-enable next time.
- Clear list: button reset.

### Trusted App Catalogs
- Office Add-ins gallery URL.

### Add-ins
- Manage trust cho COM Add-ins, Excel Add-ins (`.xlam`), Office Web Add-ins.
- Disable per add-in.

### ActiveX Settings (4 levels)
- Disable all controls without notification.
- Prompt me before enabling all controls with minimal restrictions.
- Prompt me before enabling Unsafe for Initialization (UFI) controls with additional restrictions and Safe for Initialization (SFI) controls with minimal restrictions.
- Enable all controls without restrictions and without prompting (NOT RECOMMENDED).

⚠ Ezcel **không support ActiveX** ([Spec 37](37-form-controls.md)) → setting này stub disabled.

### Macro Settings (4 levels)
- Disable all macros without notification.
- Disable all macros with notification (default).
- Disable all macros except digitally signed macros.
- Enable VBA macros (NOT RECOMMENDED).
- ☑ Trust access to the VBA project object model.

Ezcel: VBA → Python ([Spec 21](21-vba-macro.md)). Setting tương đương cho Python macro:
- Disable all Python macros.
- Disable all macros with notification (default).
- Disable except signed.
- Enable all.

### Protected View

3 triggers cho Protected View (read-only sandbox):
1. **Files originating from the Internet** ✓.
2. **Files located in potentially unsafe locations** ✓.
3. **Files opened from Outlook attachments** ✓.

UI: yellow bar trên cùng "PROTECTED VIEW — Be careful — files from the Internet can contain viruses. [Enable Editing]".

### Message Bar
- Settings để hiển thị / hide security alerts.

### File Block Settings
- Block opening / saving của file types cụ thể:
  - Excel 4 Workbooks (`.xlw`)
  - Excel 95 Workbooks
  - Excel 97-2003 (`.xls`)
  - dBase III/IV
  - XML 2003
  - Web Pages
  - ...
- Default: Excel 4 + dBase block (security history).

### Privacy Options
- ☑ Enable optional connected experiences (Insights, Recommended Pictures).
- ☑ Enable experiences that analyze content.
- ☑ Enable experiences that download online content.
- ☑ Send Microsoft information about how I use Office (telemetry).
- "Microsoft Privacy Statement" link.

### Form-based Sign-in
- Manage trusted authentication URLs.

### External Content
- Security settings for Workbook Links (other workbooks):
  - Enable automatic update for all Workbook Links (not recommended).
  - Prompt user on automatic update for Workbook Links.
  - Disable automatic update of Workbook Links.
- Linked Data Types ([Spec 38](38-linked-data-types.md)) network access toggle.
- Dynamic Data Exchange (DDE) — legacy, off by default.

## 49.2 Privacy Dashboard

File → Account → Manage Settings → Privacy → web page.

Phases:
- Required diagnostic data toggle.
- Optional diagnostic data toggle.
- Connected experiences (3 categories).
- AI-based experiences (Copilot — [Spec 39](39-copilot-agent.md)).

## Ezcel implementation

### Minimal viable
- Settings dialog Privacy section:
  - ☑ Enable internet features (Translate, Smart Lookup, Linked Data Types, Copilot).
  - ☑ Enable telemetry.
  - Default: opt-IN ban đầu (lần mở app đầu → dialog "Enable connected experiences?").
- Trusted Locations: list folders; new file in trusted → skip Protected View dialog.
- Protected View: nếu file path không trong trusted locations + file vừa download (zone identifier `Zone.Identifier` trên Windows NTFS) → mở read-only với yellow bar "Enable Editing".

### Macro Settings (Python)
- 4 levels như trên.
- Default: "Disable all macros with notification" — file có script → yellow bar.

### File Block
- Implement read-only mode cho `.xls` (BIFF8) — không write.
- Path-based block: extension trong block list → dialog warning.

## Acceptance criteria
1. File → Options → Trust Center → Trust Center Settings → tabs Privacy / Trusted Locations / Macros / Protected View visible.
2. Add `C:\TrustedFolder\` to Trusted Locations → file trong folder mở normal, không có yellow bar.
3. Open file từ Downloads folder (Zone.Identifier) → yellow bar "PROTECTED VIEW — Enable Editing".
4. Macro setting "Disable with notification" → file có Python macro → yellow bar "Macros are disabled. Enable Content".
5. Privacy → disable internet features → Translate / Linked Data Types / Copilot grayed out.
6. Setting persist via QSettings — restart app, settings retained.

## Phụ thuộc
- [21 Macro (Python)](21-vba-macro.md) — Macro settings.
- [38 Linked Data Types](38-linked-data-types.md), [39 Copilot](39-copilot-agent.md) — connected experiences.
- [36 File Formats](36-file-formats-autosave.md) — File Block.

## Risk
Thấp-trung bình. Mostly UI + state. Protected View "sandbox" thực sự khó (cần process isolation) → bắt đầu với read-only mode đủ.

## Phase
Phase 6+ (sau Macro implementation).
