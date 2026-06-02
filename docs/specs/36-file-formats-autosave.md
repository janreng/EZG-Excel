# SPEC 36 — File Formats, AutoSave & AutoRecover

## Mục tiêu
Đầy đủ hỗ trợ file formats hiện đại của Excel; AutoSave (cloud) và AutoRecover (local) để không mất dữ liệu.

## Trạng thái hiện tại
- ✓ Đọc/ghi `.xlsx` và `.csv`.
- ✗ `.xlsm` (macro), `.xlsb` (binary nhanh hơn cho file lớn), `.xltx`/`.xltm` (template), `.xml`, `.ods`, `.pdf` (export), `.html`.
- ✗ AutoSave (lưu liên tục).
- ✗ AutoRecover (snapshot mỗi N phút phòng crash).
- ✗ Recent files list nâng cao.
- ✗ Document properties (author, title, tags...).

## 36.1 File Formats

### Modern Excel formats

| Format | Extension | Mục đích |
|---|---|---|
| Excel Workbook | `.xlsx` | Default, OOXML (zip + XML) |
| Excel Macro-Enabled Workbook | `.xlsm` | xlsx + VBA/macro |
| Excel Binary Workbook | `.xlsb` | Binary, nhanh hơn cho file 50MB+ |
| Excel Template | `.xltx` | Template, không macro |
| Excel Macro-Enabled Template | `.xltm` | Template + macro |
| Excel 97-2003 Workbook | `.xls` | Legacy binary BIFF8 — read-only support |
| OpenDocument Spreadsheet | `.ods` | ISO/IEC 26300, LibreOffice compat |
| CSV (Comma delimited) | `.csv` | Plain text, no format |
| CSV UTF-8 | `.csv` | UTF-8 encoded |
| Text (Tab delimited) | `.txt` | Tab separator |
| XML Spreadsheet 2003 | `.xml` | XML Excel 2002/2003 format |
| Web Page | `.htm` / `.html` | Static HTML table |
| Single File Web Page | `.mht` / `.mhtml` | HTML + resources trong 1 file |
| PDF | `.pdf` | Export only [Spec 24](24-print-page-setup.md) |
| XPS | `.xps` | Microsoft alternative to PDF |
| Symbolic Link | `.slk` | Legacy SYLK |
| DIF | `.dif` | Data Interchange Format legacy |
| Strict Open XML Spreadsheet | `.xlsx` | ISO/IEC 29500 strict variant |

### Save As dialog
- File → Save As (F12) → file picker + "Save as type" dropdown.
- Save As → OneDrive / SharePoint → trigger AutoSave on.

### Open dialog
- File → Open (Ctrl+O) → recent / browse.
- File type filter dropdown.

### Recommendations cho Ezcel
- **Phase 2**: `.xlsx` round-trip với format đầy đủ ([roadmap.md Phase 3](../roadmap.md)).
- **Phase 5**: `.csv` UTF-8, `.txt` tab.
- **Phase 6**: `.ods` (cross-compat LibreOffice/Calc).
- **Phase 7**: `.xlsm` (Python-macro instead VBA — [Spec 21](21-vba-macro.md)).
- **Phase 7+**: `.xlsb` (binary fast read/write — nghiên cứu library `pyxlsb`).

## 36.2 AutoSave

Modern Excel: AutoSave toggle góc trên trái cạnh QAT.

### Khi bật
- Mỗi thay đổi → save ngay vào OneDrive/SharePoint (cloud only).
- Không có "Save" button (luôn saved).
- Version History: File → Info → Version History → list các bản trước, restore được.

### Khi tắt
- Save manual Ctrl+S.

### Ezcel implementation
- Cloud sync ngoài scope (cần backend).
- Có thể hỗ trợ AutoSave **local** (file local, save mỗi 30s khi có change). UI toggle giống Excel.

## 36.3 AutoRecover

Khi crash, Excel tự phục hồi từ snapshot gần nhất.

### Settings (File → Options → Save)
- Save AutoRecover information every **N minutes** (default 10).
- Keep the last AutoRecovered version if I close without saving ✓.
- AutoRecover file location: `%AppData%\Microsoft\Excel\`.

### Recovery flow
- App crash → next start → "Document Recovery" pane bên trái → list các file đang mở khi crash.
- Click → mở file recovered → so sánh với original → save hoặc discard.

### Ezcel implementation
- Background timer `QTimer` → mỗi 10 phút serialize state vào temp folder (`%LocalAppData%\Ezcel\AutoRecover\`).
- Tên file: `{workbook_hash}_{timestamp}.xlsx.bak`.
- Cleanup: keep 5 bản gần nhất, xóa khi user manual save.
- Crash recovery dialog: check folder có file mới hơn last successful save → prompt.

## 36.4 Document Properties (File → Info)

### Properties pane
- Title, Subject, Tags, Categories
- Author (default từ Options → General → User name)
- Last modified by
- Created / Modified date
- Total Editing Time
- Words, Characters, Lines (with content statistics)
- Status (custom: Draft / In Review / Final)
- Comments / Custom properties

### Document Inspector (File → Info → Check for Issues → Inspect Document)
- Tìm + xóa: comments, hidden text, hidden sheets, embedded files, custom XML, headers/footers, ink annotations, document properties.

### Compatibility Checker
- Kiểm tra workbook có features không tương thích với Excel cũ.
- List: "X feature is not supported in Excel 2003".

### Accessibility Checker
- Issues: missing alt text, color contrast, ...

## 36.5 Recent Files

File → Open → Recent:
- List 50 file mới nhất (configurable).
- Pin ⭐ favorite items đầu.
- Folder list bên cạnh (recent folders).
- Right-click → "Remove from list" / "Clear unpinned" / "Open file location".

## 36.6 Workbook Views (File → Info → Customize Workbook Views — not the same as Custom Views)

- Document properties.
- Custom Views ([Spec 14](14-freeze-split-views.md)).

## Implementation note

### xlsx read/write — đã có cơ bản
- openpyxl: full feature.
- Hiện `io_utils.save_xlsx/load_xlsx` chưa lưu format → roadmap Phase 3 đã có.

### .xlsm
- Cùng schema xlsx + thêm folder `xl/vbaProject.bin` (binary VBA blob).
- Ezcel approach: thay vào đó lưu Python scripts ở custom XML part `xl/customXml/python/Module1.py` → file giữ `.xlsm` extension cho hint nhưng không phải VBA thật.

### .xlsb
- Binary, schema khác. Library: `pyxlsb` (read), `xlsxwriter` không support write xlsb.
- Phase rất muộn.

### .ods
- OpenDocument. Library: `odfpy` hoặc `ezodf`.

### AutoRecover
- Background thread (`QTimer` không phải `threading.Timer` để integrate Qt event loop).
- Save: dùng `_io_worker` đã có (không treo UI).
- Compaction: nén `.bak` bằng zlib để tiết kiệm disk.

## Acceptance criteria
1. File → Save As → "Save as type" dropdown hiện `.xlsx / .xlsm / .csv / .txt / .pdf / .ods / .html`.
2. Save `.csv UTF-8` → mở Notepad: tiếng Việt không lỗi font.
3. Export PDF → file mở đúng layout (link với [Spec 24](24-print-page-setup.md)).
4. AutoSave toggle on → mỗi cell change save background; status hiện "Saved 14:30".
5. Crash test: kill app khi đang edit → next start → "Document Recovery" pane → list file → restore được.
6. File → Options → Save → AutoRecover every 5 min → wait 5 min không save manual → `%LocalAppData%\Ezcel\AutoRecover\*.xlsx.bak` xuất hiện.
7. File → Info → Properties → Author, Title editable; lưu xlsx → mở Excel real → properties còn nguyên.

## Phụ thuộc
- [21 VBA / Macro](21-vba-macro.md) — `.xlsm` chứa Python script.
- [24 Print](24-print-page-setup.md) — export PDF.

## Risk
- `.xlsb` library hạn chế — đánh giá lại có nên support.
- AutoSave local conflict với chính action save manual của user → cần lock.
- Document Inspector + Compatibility Checker là 2 module riêng phức tạp.
