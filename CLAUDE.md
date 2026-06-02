# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo này.

> **Ngôn ngữ:** Trao đổi với người dùng và viết comment/chuỗi UI **bằng tiếng Việt**.

## Tổng quan

**EZG - Excel** — ứng dụng bảng tính kiểu Excel viết bằng Python + PySide6. Đọc/ghi CSV và XLSX, có formula engine, undo/redo, freeze panes, filter, sort, autofill, đa ngôn ngữ Việt/Anh, auto-update qua GitHub Releases.

- Python 3.10+ (máy dev dùng 3.14; PySide6 dùng wheel `abi3` nên chạy được trên 3.14).
- PySide6 ≥ 6.10, openpyxl ≥ 3.1, pandas ≥ 2.0, pillow (sinh icon), pyinstaller (build).
- Phiên bản hiện tại: xem `src/excelapp/__init__.py`. Repo cập nhật: `janreng/EZG-Excel`.

## Lệnh thường dùng

```bat
:: Cài môi trường
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

:: Chạy app (một trong các cách)
run.bat
.venv\Scripts\python run.py
.venv\Scripts\python run.py duongdan\file.xlsx   :: mở kèm file

:: Đóng gói .exe (PyInstaller)
build.bat                  :: -> dist\EZG-Excel\EZG-Excel.exe

:: Tạo bộ cài (cần Inno Setup)
build_installer.bat        :: -> installer\EZG-Excel-Setup-<ver>.exe

:: Chạy test (sau khi có thư mục tests/)
.venv\Scripts\python -m pytest tests/
```

## Kiến trúc

Mã nguồn ở `src/excelapp/`. Mẫu Model–View (Qt) với formula engine tách riêng.

| File | Vai trò |
|------|---------|
| `main.py` / `__main__.py` | Điểm vào: tạo `QApplication`, mở `MainWindow`, nhận file từ CLI |
| `main_window.py` | Giao diện chính: **ribbon** (`_RibbonBar`/`_RibbonSection`), menu, thanh công thức + name box, tab sheet, hộp thoại, find/replace, filter, freeze, updater. **Đọc/ghi file chạy thread riêng** qua `_IoWorker` (không treo UI) |
| `table_model.py` | `SpreadsheetModel(QAbstractTableModel)` — dữ liệu, tính công thức (cache), undo/redo, định dạng, copy/paste, autofill, sort, `move_row/move_column` |
| `view.py` | `SpreadsheetView(QTableView)` + `CellDelegate` (bôi đen, wrap mode, núm kéo AutoFill) + `FilterHeaderView` (phễu lọc + highlight cột chọn) + `RowHeaderView` (highlight hàng chọn) |
| `formula.py` | Engine công thức: tokenizer → `_Parser` (recursive-descent) → registry `_FUNCTIONS` |
| `io_utils.py` | Đọc/ghi CSV (auto dialect) và XLSX (openpyxl) |
| `freeze.py` | Freeze panes bằng 3 overlay QTableView |
| `i18n.py` | Đa ngôn ngữ: dict `STRINGS{key:{vi,en}}`, `tr(key, **kw)`, lưu bằng QSettings |
| `shortcuts.py` | Phím tắt tùy chỉnh (QSettings) |
| `updater.py` | Auto-update từ GitHub Releases |
| `icons.py` / `resources.py` | SVG→QIcon, phân giải đường dẫn tài nguyên (PyInstaller vs source) |

### Cấu trúc dữ liệu model (`table_model.py`)

```python
self._data: list[list[str]]                 # lưới thô (chuỗi/công thức)
self._eval_cache: dict[(row,col), object]   # giá trị công thức đã tính (xóa khi đổi)
self._fmt: dict[(row,col), dict]            # định dạng từng ô: font,size,bold,italic,halign,valign,wrap
self._undo / self._redo: list[tuple]        # snapshot (_data, _fmt), tối đa 100
```

### Formula engine (`formula.py`)

- Công thức là chuỗi bắt đầu `=`. `evaluate(formula, resolver)` với `resolver(row,col)→giá trị`.
- Tokenizer regex `_TOKEN_RE` (NUMBER/STRING/CELL/IDENT/OP/WS) → `_Parser` tính trực tiếp (không AST).
- **Thêm hàm mới:** viết `_fn_ten()` nhận `args: list`, đăng ký vào dict `_FUNCTIONS` (key viết HOA).
- `_arg()` mở rộng vùng `A1:B3` thành list giá trị phẳng — phù hợp hàm gộp (SUM…). Hàm cần ma trận 2D (VLOOKUP/INDEX/MATCH) cần xử lý vùng dạng 2 chiều riêng.
- `offset_formula(text, drow, dcol)` dịch tham chiếu tương đối khi kéo-điền/paste; tham chiếu `$` giữ nguyên.

## Quy ước & lưu ý

- **Comment/chuỗi tiếng Việt** xuyên suốt mã nguồn — giữ nhất quán.
- Chuỗi UI mới **phải** thêm vào `i18n.py` ở **cả** `vi` và `en`.
- **Console Windows dùng cp1252** — tránh `print` tiếng Việt trong script test (dùng assert/pytest, không print Unicode).
- **XLSX lưu được định dạng + ô gộp** (`io_utils.save_xlsx/load_xlsx` map sang openpyxl styles). CSV chỉ lưu giá trị. `load_file` trả `(rows, fmt, merges)`. Conditional formatting chưa ghi vào file.
- Undo/redo dựa trên snapshot `("snapshot", data, fmt, merges, cond)` → state mới muốn được hoàn tác phải nằm trong snapshot.
- Một sheet mỗi file (chưa hỗ trợ nhiều sheet/tab).
- Khi user xác nhận "ok/ổn" cho một feature → tự commit feature đó.

## Nguyên tắc khi sửa code (giữ dự án dễ bảo trì)

1. **Tôn trọng ranh giới module** (xem bảng Kiến trúc). Dữ liệu/định dạng/undo → `table_model`;
   hiển thị/tương tác lưới → `view`; điều phối UI/lệnh → `main_window`; tính công thức →
   `formula`. Đừng nhét logic dữ liệu vào widget hay ngược lại.
2. **Mọi thay đổi dữ liệu/định dạng trong model phải `_push_undo()`** ở đầu hàm, rồi phát
   `dataChanged`/`layoutChanged` (hoặc `begin/endResetModel` khi đổi kích thước).
3. **Chuỗi UI luôn qua `tr()`**, thêm key vào `i18n.py` ở **cả `vi` và `en`**. Không hardcode.
4. **Bump version ở HAI nơi** khi phát hành: `src/excelapp/__init__.py` (`__version__`) **và**
   `installer.iss` (`MyAppVersion`). Quên một nơi → auto-update so sai phiên bản.
5. **Chỉ dùng thư viện đã có** (PySide6, pandas, openpyxl). Mạng dùng `urllib` (stdlib),
   không thêm `requests`. Tránh thêm dependency nặng nếu không thật cần.
6. Code mới **giống code xung quanh**: type hint nhẹ, `from __future__ import annotations`,
   docstring/comment tiếng Việt ngắn gọn.

## Cách thêm tính năng (recipes)

- **Hàm công thức mới**: `_fn_ten(args)` trong `formula.py`, đăng ký vào `_FUNCTIONS` (key HOA).
- **Nút trên ribbon**: dùng `_ribbon_btn` / `_ribbon_toggle` / `_ribbon_dropdown` trong
  `_build_toolbar` (`main_window.py`).
- **Icon mới**: thêm path Material (viewBox 24×24) vào `PATHS` (`icons.py`) → `make_icon("ten")`.
- **Mục menu + phím tắt tùy biến**: `_cmd_action(menu, cmd_id, slot)` + thêm `cmd_id` vào
  `shortcuts.DEFAULTS` (nhãn lấy từ `tr(cmd_id)`).
- **Thuộc tính định dạng ô mới**: thêm vào `_FORMAT_KEYS` (`table_model.py`), xử lý trong
  `data()` theo role phù hợp; `set_format` đã generic.

## Kiểm thử

- **Logic** (model/formula): chạy headless `QT_QPA_PLATFORM=offscreen`.
- **Giao diện**: chụp ảnh thật bằng `app.primaryScreen().grabWindow(w.winId())` rồi đọc lại;
  `widget.grab()` có thể sai z-order với overlay (freeze) — tránh dùng cho phần đó.
- **cp1252**: script test chỉ in ASCII; KHÔNG in tiếng Việt (sẽ `UnicodeEncodeError`).

## Đừng phá vỡ (gotchas đã trả giá)

- **Giữ `app.setStyle("Fusion")`** trong `main.py` — để bỏ "thanh accent chọn ô" của Windows 11
  (style native vẽ vạch xanh bên trái ô, không tắt được bằng delegate/stylesheet).
- **QtSvg phải được PyInstaller đóng gói**: `icons.py` import `QtSvg` nên nó tự được gói —
  đừng bỏ import đó khi còn dùng `make_icon`.
- **QSettings org/app = `("PyExcel","PyExcel")`** — giữ nguyên để không mất cấu hình
  ngôn ngữ/phím tắt của bản đã cài cũ.
- **Freeze panes** dùng overlay chia sẻ model + `viewport().stackUnder(...)` + nền đục;
  nếu sửa, kiểm tra kỹ khi cuộn (dễ chồng/nhòe chữ).

## Phát hành & auto-update

- Quy trình ra bản mới: xem `RELEASE.md` (bump version → `build.bat` → `build_installer.bat`
  → tạo GitHub Release tag `vX.Y.Z` + đính kèm file installer `.exe`).
- **Repo phải public** để app đọc release ẩn danh qua GitHub API.
- Đổi repo cập nhật ở `GITHUB_OWNER`/`GITHUB_REPO` trong `updater.py`.

## Roadmap

Kế hoạch phát triển 4 phase (mở rộng hàm công thức → định dạng nâng cao UI → lưu định dạng vào file → nhiều sheet/tab) ở `docs/roadmap.html` (mở bằng trình duyệt để xem).
