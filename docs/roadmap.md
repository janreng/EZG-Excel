# Roadmap: Phát triển EZG - Excel tiến gần Microsoft Excel

> Bản Markdown để AI thực thi. Bản HTML để đọc trực quan: [roadmap.html](roadmap.html).

## Context (Bối cảnh)

EZG - Excel (`d:\Python\excel`) là một spreadsheet PySide6 đã khá hoàn chỉnh: formula engine 17 hàm, undo/redo 100 mức, freeze panes, filter, sort, autofill (fill handle kiểu Google Sheets), find/replace, i18n Việt/Anh, auto-update qua GitHub. Tuy nhiên so với Microsoft Excel còn thiếu nhiều mảng lớn.

Phát triển **4 nhóm tính năng**, theo dạng roadmap toàn diện:
1. **Mở rộng hàm công thức** (Excel 400+, app mới 17)
2. **Định dạng nâng cao trong UI** (màu nền/chữ, border, merge, định dạng số, conditional formatting)
3. **Lưu định dạng vào file** (hiện định dạng chỉ tồn tại trong phiên — lỗ hổng lớn nhất)
4. **Nhiều sheet/tab** (hiện 1 sheet/file)

Roadmap sắp xếp theo **độ phụ thuộc kỹ thuật**: hàm công thức (độc lập, rủi ro thấp) → định dạng UI nâng cao → lưu định dạng (phụ thuộc model định dạng) → multi-sheet (thay đổi kiến trúc lớn nhất).

### So sánh tổng quan với Microsoft Excel

| Mảng | EZG hiện tại | Excel | Trong roadmap |
|------|-------------|-------|---------------|
| Hàm công thức | 17 hàm | 400+ | **Phase 1** |
| Màu nền/chữ ô | ✗ | ✓ | **Phase 2** |
| Border | ✗ | ✓ | **Phase 2** |
| Merge cells | ✗ | ✓ | **Phase 2** |
| Định dạng số (tiền tệ, %, ngày) | ✗ (chỉ auto) | ✓ | **Phase 2** |
| Conditional formatting | ✗ | ✓ | **Phase 2 (mở rộng)** |
| Lưu định dạng vào xlsx | ✗ | ✓ | **Phase 3** |
| Nhiều sheet/tab | ✗ | ✓ | **Phase 4** |
| Pivot table | ✗ | ✓ | Ngoài phạm vi |
| Chart/biểu đồ | ✗ | ✓ | Ngoài phạm vi |
| Data validation / dropdown | ✗ | ✓ | Ngoài phạm vi |
| Cell comments/notes | ✗ | ✓ | Ngoài phạm vi |
| Named ranges | ✗ | ✓ | Ngoài phạm vi |
| Macros/VBA | ✗ | ✓ | Ngoài phạm vi |
| In ấn / xuất PDF | ✗ | ✓ | Ngoài phạm vi |

---

## Phase 1 — Mở rộng hàm công thức

**Mục tiêu:** Đưa từ 17 → ~50-60 hàm phổ biến nhất, đủ dùng cho 90% nhu cầu thực tế. Đây là phase **độc lập, rủi ro thấp**, thuần túy bổ sung vào `src/excelapp/formula.py`.

**Vị trí sửa:** Dict `_FUNCTIONS` trong `formula.py` và các hàm `_fn_*`. Parser recursive-descent (`_Parser`) đã hỗ trợ gọi hàm lồng nhau và range, nên đa số hàm chỉ cần thêm vào registry.

**Các hàm cần thêm theo nhóm:**

- **Logic:** `AND`, `OR`, `NOT`, `IFERROR`, `IFS`, `TRUE`, `FALSE`
- **Thống kê có điều kiện:** `COUNTIF`, `COUNTIFS`, `SUMIF`, `SUMIFS`, `AVERAGEIF`, `COUNTA`, `COUNTBLANK`
- **Tra cứu:** `VLOOKUP`, `HLOOKUP`, `INDEX`, `MATCH`, `LOOKUP` *(VLOOKUP yêu cầu nhiều nhất)*
- **Chuỗi:** `LEFT`, `RIGHT`, `MID`, `LEN`, `TRIM`, `UPPER`, `LOWER`, `PROPER`, `REPLACE`, `SUBSTITUTE`, `FIND`, `SEARCH`, `TEXT`, `VALUE`, `REPT`
- **Toán bổ sung:** `CEILING`, `FLOOR`, `TRUNC`, `SIGN`, `PRODUCT`, `SUMPRODUCT`, `ROUNDUP`, `ROUNDDOWN`, `PI`, `EXP`, `LOG`, `LN`
- **Ngày/giờ:** `TODAY`, `NOW`, `DATE`, `YEAR`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `WEEKDAY`, `DATEDIF`
- **Thống kê:** `MEDIAN`, `MODE`, `STDEV`, `VAR`, `LARGE`, `SMALL`, `RANK`

**Lưu ý kỹ thuật:**
- `VLOOKUP/HLOOKUP/MATCH/INDEX` cần truy cập **vùng 2 chiều** chứ không chỉ list giá trị phẳng. Thêm lớp `_Range` giữ ma trận (row×col); cập nhật `_arg`/`_expand_range` trả `_Range`, và helper `_flatten`/`_numbers` mở rộng `_Range` để hàm gộp cũ (SUM…) vẫn chạy. Đây là điểm rủi ro chính.
- Ngày/giờ: dùng chuẩn serial date của Excel (epoch 1899-12-30). `datetime.now()`/`date.today()` cho `TODAY`/`NOW`.
- Mở rộng `_TOKEN_RE` regex nếu cần.
- Cập nhật docstring đầu file `formula.py`.

**Test:** Tạo `tests/test_formula.py` (project chưa có thư mục test) — unit test từng nhóm hàm với resolver giả lập. Chạy `QT_QPA_PLATFORM=offscreen`, chỉ in ASCII (cp1252).

---

## Phase 2 — Định dạng nâng cao trong UI

**Mục tiêu:** Thêm màu nền, màu chữ, border, merge cells, định dạng số. Nền tảng bắt buộc cho Phase 3.

**Model định dạng:** Mở rộng dict `_fmt[(row,col)]` trong `table_model.py` (hiện có `font, size, bold, italic, halign, valign, wrap`). Thêm:
- `bg` — màu nền (hex `#RRGGBB`)
- `color` — màu chữ
- `border` — dict 4 cạnh `{top, bottom, left, right}` (style + màu)
- `underline`, `strikethrough`
- `number_format` — mã định dạng (vd `"#,##0.00"`, `"0%"`, `"dd/mm/yyyy"`, `"$#,##0"`)

Thêm vào `_FORMAT_KEYS` để `set_format` xử lý generic.

**Render (View):** Mở rộng `CellDelegate.paint()` trong `view.py` vẽ màu nền + border. Màu chữ/underline qua `Qt.ForegroundRole`/font trong `data()`.

**Định dạng số:** Áp `number_format` lên giá trị hiển thị trong `_display_value()`/`_format()` của `table_model.py`. Tái dùng mã định dạng openpyxl hoặc viết formatter cho preset (Số, Tiền tệ, %, Ngày, Khoa học, Phân số).

**Merge cells:** Phức tạp nhất phase này.
- Lưu danh sách vùng merge trong model (`_merges: list[box]`)
- Dùng `setSpan(row,col,rowSpan,colSpan)` của QTableView
- Xử lý chọn/sửa/copy trên ô merge, cập nhật khi insert/delete (tái dùng `_shift_fmt`)

**Toolbar/UI (ribbon):** Mở rộng trong `main_window.py` — dùng `_ribbon_btn`/`_ribbon_toggle`/`_ribbon_dropdown` trong `_build_toolbar`:
- Màu nền (`QColorDialog`), màu chữ, dropdown border, Merge & Center, dropdown định dạng số, underline, strikethrough
- Chuỗi mới thêm vào `i18n.py` (cả `vi` và `en`)
- Icon mới thêm path vào `PATHS` trong `icons.py`

**Conditional formatting (làm sau cùng của phase):** Dialog quy tắc (lớn hơn/nhỏ hơn/chứa text/top-N, color scale, data bar). Lưu rule ở cấp model, áp khi tính `data()`. Tái dùng formula engine (Phase 1).

**Undo/redo:** Snapshot `(_data, _fmt)` tự bao phủ thuộc tính mới — đảm bảo `_merges` và rule conditional cũng vào snapshot. Mọi thay đổi gọi `_push_undo()` đầu hàm.

---

## Phase 3 — Lưu định dạng vào file (xlsx)

**Mục tiêu:** Định dạng (Phase 2) được ghi xuống `.xlsx` và đọc lại. **Phụ thuộc Phase 2.**

**Vị trí sửa:** `io_utils.py` — hiện `save_xlsx`/`load_xlsx` bỏ qua hoàn toàn định dạng.

**Thay đổi `save_xlsx`:**
- Đổi chữ ký: `save_xlsx(path, rows, fmt=None, merges=None)`
- Map `_fmt[(r,c)]` → openpyxl: `Font(name,size,bold,italic,underline,color)`, `PatternFill(fgColor=bg)`, `Border(...)`, `Alignment(horizontal,vertical,wrap_text)`, `cell.number_format`
- Ghi merge: `ws.merge_cells(...)`; bỏ chế độ read-only

**Thay đổi `load_xlsx`:**
- Bỏ `read_only=True` (không đọc đủ style) → đọc giá trị + style
- Trả về grid + dict định dạng + danh sách merge; map ngược openpyxl → dict `_fmt`

**Kết nối model:** Tái dùng `replace_all_with_fmt(rows, fmt)` có sẵn; cập nhật `save_file`/`open_file` (qua `_IoWorker` thread) trong `main_window.py` truyền dict định dạng + merges. CSV vẫn không lưu định dạng. Cập nhật `README.md` gỡ mục "định dạng không được lưu".

---

## Phase 4 — Nhiều sheet/tab

**Mục tiêu:** Một file chứa nhiều sheet, có thanh tab dưới cùng. **Thay đổi kiến trúc lớn nhất — làm sau cùng.**

**Kiến trúc:** Hiện `MainWindow` giữ **một** `SpreadsheetModel`. Refactor sang khái niệm "workbook":
- Lớp `Workbook` giữ `list[SpreadsheetModel]` + tên sheet + sheet active
- Đổi tab → `view.setModel(workbook.sheets[i])`
- Freeze/filter/undo là **per-sheet** → di chuyển state (`_filters`, `_undo`, freeze config) từ MainWindow vào từng model

**UI thanh tab:** `QTabBar` dưới cùng (tên sheet, tab `+`, right-click đổi tên/xóa/di chuyển/đổi màu/nhân bản). Chuỗi mới vào `i18n.py`.

**File I/O đa sheet:** `load_xlsx` lặp `wb.worksheets`; `save_xlsx` tạo nhiều worksheet. CSV chỉ 1 sheet (cảnh báo khi lưu workbook nhiều sheet → chỉ lưu sheet active).

**Tham chiếu chéo sheet:** Mở rộng `formula.py` hỗ trợ `Sheet1!A1`; resolver cần biết workbook. Phần rủi ro nhất — có thể tách làm bước phụ sau khi tab cơ bản chạy.

---

## Thứ tự thực thi đề xuất

1. **Phase 1** trước (độc lập, giá trị cao ngay, dễ test).
2. **Phase 2** (nền tảng định dạng).
3. **Phase 3** ngay sau Phase 2.
4. **Phase 4** sau cùng (refactor kiến trúc).

Mỗi phase một nhánh git riêng, commit theo từng nhóm tính năng hoàn chỉnh (auto-commit khi user "ok/ổn").

---

## Verification (Cách kiểm thử end-to-end)

**Chạy app:** `python run.py` (hoặc `python -m excelapp`) từ `d:\Python\excel`.

- **Phase 1:** `python -m pytest tests/`; trong app nhập `=VLOOKUP(...)`, `=COUNTIF(...)`, `=LEFT(...)`, `=TODAY()`.
- **Phase 2:** chọn vùng → đổi màu nền/chữ/border/merge/định dạng số; kiểm tra render; Ctrl+Z/Ctrl+Y hoàn tác được định dạng.
- **Phase 3:** định dạng → Lưu `.xlsx` → mở lại trong app **và** Microsoft Excel thật (round-trip test).
- **Phase 4:** tạo nhiều sheet, đổi tên/xóa/di chuyển tab, nhập `=Sheet2!A1`, lưu xlsx nhiều sheet rồi mở lại.

**Lưu ý môi trường:** Console Windows dùng cp1252 — script test chỉ in ASCII, dùng assert/pytest.

---

## Ngoài phạm vi roadmap này

Đề xuất tương lai (Phase 5+): **Chart/biểu đồ**, **Pivot table**, **Data validation/dropdown**, **Cell comments/notes**, **Named ranges**, **In ấn & xuất PDF**, **Macros/scripting**, **Split nâng cao**. Mỗi cái nên là một plan riêng.
