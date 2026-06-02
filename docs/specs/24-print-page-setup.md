# SPEC 24 — Print & Page Setup & Export PDF

## Mục tiêu
Hỗ trợ đầy đủ Print Preview, Page Setup (margin / orientation / paper size / scale / header & footer), Print Area, Print Titles, Page Breaks, Export PDF.

## Trạng thái hiện tại
- ✗ Hoàn toàn chưa có.

## 24.1 Print dialog (Ctrl+P)

Excel modern: Backstage view "Print" (File → Print):
- **Left**: settings panel
  - Copies (spin)
  - Printer dropdown
  - Settings:
    - Print Active Sheets / Print Entire Workbook / Print Selection / Print Selected Table
    - Pages: from / to
    - Print One Sided / Both Sides
    - Collated / Uncollated
    - Portrait / Landscape
    - Paper size (Letter / A4 / Legal / A3 / A5 / custom)
    - Margins preset (Normal / Wide / Narrow / Last Custom Setting / Custom Margins...)
    - Scaling: No Scaling / Fit Sheet on One Page / Fit All Columns on One Page / Fit All Rows / Custom Scaling Options
- **Right**: Live print preview (page navigation arrows)

## 24.2 Page Setup dialog (Page Layout → Dialog Box Launcher)

4 tab:

### Tab Page
- Orientation: Portrait / Landscape
- Scaling: Adjust to N% / Fit to W page wide × H tall
- Paper size
- Print quality (DPI)
- First page number (Auto / number)

### Tab Margins
- Top / Bottom / Left / Right (inches or cm)
- Header / Footer margins
- Center on page: Horizontally / Vertically (2 checkbox)
- Preview với mép xanh

### Tab Header / Footer
- Header dropdown: 24+ preset (`Page 1`, `Page 1 of ?`, `Confidential, 1/1/2024, Page 1`, ...) + custom
- Footer dropdown: tương tự
- Custom Header/Footer dialog: 3 zone (Left/Center/Right), buttons (Page #, Total Pages, Date, Time, File Path, File Name, Sheet Name, Picture, Format Picture)
- Different odd/even pages
- Different first page
- Scale with document
- Align with page margins

### Tab Sheet
- Print area: range
- **Print titles**: Rows to repeat at top (`$1:$3`), Columns to repeat at left
- Print:
  - Gridlines
  - Black and white
  - Draft quality
  - Row and column headings
  - Comments and notes: At end of sheet / As displayed on sheet / None
  - Cell errors as: Displayed / `<blank>` / `--` / `#N/A`
- Page order: Down, then over / Over, then down

## 24.3 Page Breaks

- Auto break: Excel tự chèn theo paper size + margin.
- Manual break: Page Layout → Breaks → Insert Page Break / Remove Page Break / Reset All Page Breaks.
- View → Page Break Preview ([Spec 14](14-freeze-split-views.md)): đường xanh đậm = manual, xanh nhạt = auto; kéo để adjust.

## 24.4 Print Area

- Page Layout → Print Area → Set Print Area / Clear / Add to Print Area.
- Multi-region print area: mỗi region in trang riêng.
- File → Page Setup → Sheet tab → "Print area" textbox.

## 24.5 Export PDF

- File → Export → Create PDF/XPS Document → dialog Publish as PDF.
- Options:
  - Page range: All / Page from-to / Selection / Active Sheets / Entire Workbook / Table
  - Publish what: Workbook / Sheet
  - Include non-printing info (document properties, accessibility tags)
  - Optimize: Standard (publishing online + printing) / Minimum size (online only)
  - ISO 19005-1 compliant (PDF/A)
- Hoặc Save As → file type `.pdf`.

## Implementation note

- **Phase 7** (sau cùng) — phụ thuộc nhiều spec.
- PySide6: `QPrinter` + `QPrintDialog` + `QPrintPreviewDialog`. Render từng cell qua `QPainter` lên printer device.
- Custom rendering: tự vẽ vì `QTableView.render()` không support pagination tốt.
- Page break: tính dựa trên column widths + row heights, paper size, margin. Một paginator riêng class `Paginator(sheet, page_setup) → list[PageInfo]`.
- Header/Footer: parser placeholder `&P` (page), `&N` (total pages), `&D` (date), `&T` (time), `&F` (file), `&A` (sheet), `&G` (picture), `&L`/`&C`/`&R` (left/center/right zone), `&B` (bold), `&I` (italic), `&"font,style"` (font).
- PDF export: PySide6 `QPdfWriter` (cùng API painter).

## Page Setup model

```python
class PageSetup:
    orientation: "portrait"|"landscape"
    paper_size: str            # "A4", "Letter", "Legal", ...
    scaling: int               # %
    fit_to_pages_wide: int | None
    fit_to_pages_tall: int | None
    margins: {top, bottom, left, right, header, footer}
    center_horizontally: bool
    center_vertically: bool
    header: {left, center, right}
    footer: {left, center, right}
    different_odd_even: bool
    different_first: bool
    print_area: list[Range]
    print_titles_rows: Range | None      # "$1:$3"
    print_titles_cols: Range | None
    print_gridlines: bool
    print_headings: bool
    print_bw: bool
    print_draft: bool
    print_comments: "none"|"end"|"asdisplayed"
    print_errors: "displayed"|"blank"|"dash"|"na"
    page_order: "down_then_over"|"over_then_down"
    page_breaks_manual: list[(row, col)]
```

Per-sheet. Lưu vào model. xlsx mapping: `Worksheet.print_options`, `Worksheet.page_setup`, `Worksheet.page_margins`, `Worksheet.header_footer`, `print_titles`.

## Acceptance criteria
1. Ctrl+P → backstage Print với preview bên phải.
2. Page Setup → Margins tab → đổi Top 2cm, Center Horizontally → preview update.
3. Page Setup → Header/Footer → Custom Header → zone giữa `Page &P of &N` → preview hiện "Page 1 of 3".
4. Page Setup → Sheet → Print titles rows `$1:$1` → mọi trang in lặp hàng 1.
5. Select A1:E50 → Page Layout → Print Area → Set Print Area → in chỉ vùng đó.
6. Page Layout → Breaks → Insert Page Break tại C20 → break tại C/20.
7. File → Export PDF → file `out.pdf` mở được, đúng layout.

## Phụ thuộc
- [10 Sheet Tabs](10-sheet-tabs.md) — multi-sheet print.
- [14 Freeze/Split/Views](14-freeze-split-views.md) — Page Layout / Page Break Preview views.
- [08 Format Cells](08-format-cells-dialog.md) — number format áp dụng khi in.

## Risk
**Cao.** Pagination engine viết từ scratch. Header/footer placeholder parser. Print preview live update.
