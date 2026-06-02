# Ezcel

Ứng dụng bảng tính đơn giản (kiểu Excel) viết bằng Python + PySide6.
Đọc/ghi **CSV** và **XLSX**, hỗ trợ công thức cơ bản.

## Tính năng

- 📂 Mở & xem file `.csv`, `.xlsx`
- ✏️ Sửa từng ô, lưu lại ra CSV/XLSX (Lưu / Lưu thành)
- ➕➖ Chèn / xóa dòng và cột (menu **Sửa**)
- 🔢 **Công thức** (gõ bắt đầu bằng `=`) — ~60 hàm:
  - Toán tử: `+ - * / ^`, ngoặc `()`, so sánh `> < >= <= = <>`
  - Tham chiếu ô `A1`, vùng `A1:B5`
  - Gộp: `SUM, AVERAGE, MIN, MAX, COUNT, COUNTA, COUNTBLANK, PRODUCT`
  - Logic: `IF, AND, OR, NOT, IFERROR, IFS, TRUE, FALSE`
  - Điều kiện: `COUNTIF, COUNTIFS, SUMIF, SUMIFS, AVERAGEIF`
  - Tra cứu: `VLOOKUP, HLOOKUP, INDEX, MATCH, LOOKUP`
  - Chuỗi: `LEFT, RIGHT, MID, LEN, TRIM, UPPER, LOWER, PROPER, REPT,`
    `REPLACE, SUBSTITUTE, FIND, SEARCH, VALUE, TEXT, CONCAT`
  - Toán: `ABS, ROUND, ROUNDUP, ROUNDDOWN, SQRT, INT, MOD, POWER,`
    `CEILING, FLOOR, TRUNC, SIGN, SUMPRODUCT, PI, EXP, LOG, LN`
  - Ngày/giờ: `TODAY, NOW, DATE, YEAR, MONTH, DAY, HOUR, MINUTE,`
    `WEEKDAY, DATEDIF`
  - Thống kê: `MEDIAN, MODE, STDEV, VAR, LARGE, SMALL, RANK`
  - Ngẫu nhiên: `RAND/RANDOM, RANDBETWEEN`
  - Ví dụ: `=SUM(A1:A10)`, `=VLOOKUP(B2,D:E,2,FALSE())`,
    `=IF(B2>5,"Đạt","Trượt")`, `=COUNTIF(A:A,">100")`
- 🔍 Tìm kiếm (Ctrl+F mở popup, tự vòng lại)
- ↕️ Sắp xếp theo cột (menu **Dữ liệu**, hoặc nhấp đúp tiêu đề cột)
- 🖱️ **Menu chuột phải** (copy, cut, paste, chèn/xóa dòng-cột, xóa nội dung)
- 🎨 **Bôi đen kiểu Google Sheets**: viền xanh quanh vùng chọn, ô hiện tại
  để trắng, các ô còn lại tô xanh nhạt
- 🌐 **Đa ngôn ngữ**: Tiếng Việt / English (menu **Ngôn ngữ**, tự nhớ lựa chọn)
- 🅰️ **Định dạng**: phông chữ, cỡ chữ, in đậm/nghiêng; **dropdown** canh lề
  ngang/dọc và xuống dòng (Tràn / Xuống dòng / Cắt) kiểu Google Sheets
- 🔻 **Bộ lọc (Filter)** như Excel: nút phễu → Sort A→Z/Z→A + tick chọn giá trị
  (có ô tìm, Select all/Clear) → ẩn dòng không khớp
- 📌 **Cố định dòng/cột (Freeze)** kiểu Google Sheets (menu **Xem**)
- 📋 **Dán văn bản thuần** (Ctrl+Shift+V — chỉ dán giá trị)
- ⌨️ **Tùy chỉnh phím tắt** (menu **Cài đặt → Tùy chỉnh phím tắt**, tự nhớ)
- ↔️ **Di chuyển cột/hàng**: kéo tiêu đề cột/dòng để dời (dời dữ liệu thật)
- ⤓ **Ctrl+Shift+mũi tên**: mở rộng vùng chọn đến mép dữ liệu (như Excel)
- 📐 **Auto-fit**: nhấp đúp viền tiêu đề để dãn cột/dòng vừa nội dung;
  nhấp đúp nút góc trên-trái để auto-fit toàn bộ
- 🔄 **Tự cập nhật**: **Trợ giúp → Kiểm tra cập nhật** — tải bản mới từ
  GitHub Releases và cài đè (xem [RELEASE.md](RELEASE.md) để biết cách phát hành)
- 🖱️ **AutoFill (kéo-điền)**: chọn ô → kéo **núm xanh** ở góc dưới-phải:
  - Số: `1, 2` → `3, 4, 5...`; một số đơn → sao chép
  - Công thức: tự dịch tham chiếu tương đối (`=A1` → `=A2`), giữ `$` tuyệt đối
  - Chữ có số ở cuối: `Item1` → `Item2, Item3...`
  - Phím tắt: **Ctrl+D** (điền xuống), **Ctrl+R** (điền sang phải)
- 📋 **Copy / Cut / Paste** nhiều ô (tương thích Excel qua clipboard)
- ↩️ **Hoàn tác / Làm lại** không giới hạn (tới 100 bước)
- 🔁 **Tìm & thay thế** (có tùy chọn phân biệt hoa/thường)

### Phím tắt

| Phím | Chức năng | Phím | Chức năng |
|------|-----------|------|-----------|
| Ctrl+N | Tạo mới | Ctrl+C | Sao chép |
| Ctrl+O | Mở file | Ctrl+X | Cắt |
| Ctrl+S | Lưu | Ctrl+V | Dán |
| Ctrl+Z | Hoàn tác | Delete | Xóa nội dung ô |
| Ctrl+Y | Làm lại | Ctrl+F | Tìm kiếm |
| Ctrl+D | Điền xuống | Ctrl+H | Tìm & thay thế |
| Ctrl+R | Điền sang phải | Ctrl+A | Chọn tất cả |
| Ctrl+Shift+V | Dán văn bản thuần | | |

> Tất cả phím tắt trên đều **đổi được** trong **Cài đặt → Tùy chỉnh phím tắt**.

## Chạy thử (cần Python 3.10+)

```bat
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
run.bat
```

Hoặc mở kèm file: `run.bat duongdan\file.xlsx`

## Đóng gói thành .exe (chạy không cần Python)

```bat
build.bat
```

Tạo dạng **thư mục**: `dist\Ezcel\Ezcel.exe` (kèm thư mục `_internal`).
Mở nhanh, có sẵn icon. Copy cả thư mục `dist\Ezcel` sang máy khác là chạy được.

## Tạo bộ cài đặt (Setup.exe)

Cần [Inno Setup](https://jrsoftware.org/isinfo.php)
(`winget install JRSoftware.InnoSetup`). Sau khi đã chạy `build.bat`:

```bat
build_installer.bat
```

Tạo ra `installer\Ezcel-Setup-<ver>.exe`. Bộ cài đặt này:

- Cài vào thư mục người dùng (không cần quyền admin)
- Tạo shortcut Start Menu, tùy chọn Desktop
- Tùy chọn thêm "Open with Ezcel" vào menu chuột phải của `.csv`/`.xlsx`
  (không thay chương trình mặc định nên không tranh chấp với Excel)
- Có sẵn trình gỡ cài đặt

## Icon

Icon ở `assets\icon.ico`, sinh ra từ `tools\make_icon.py` (cần Pillow).
Sửa màu/hình trong file đó rồi chạy lại để đổi icon.

## Cấu trúc mã

| File | Vai trò |
|------|---------|
| File | Vai trò |
|------|---------|
| `src/excelapp/formula.py`     | Engine phân tích & tính công thức |
| `src/excelapp/io_utils.py`    | Đọc/ghi CSV, XLSX |
| `src/excelapp/table_model.py` | Model lưới + công thức + định dạng + undo |
| `src/excelapp/view.py`        | Bảng lưới: bôi đen, núm kéo AutoFill, wrap |
| `src/excelapp/freeze.py`      | Cố định dòng/cột (freeze panes) |
| `src/excelapp/i18n.py`        | Đa ngôn ngữ Việt/Anh |
| `src/excelapp/shortcuts.py`   | Phím tắt tùy chỉnh |
| `src/excelapp/main_window.py` | Giao diện: menu, toolbar, hộp thoại |
| `src/excelapp/main.py`        | Khởi chạy ứng dụng |

## Giới hạn hiện tại

- **CSV** không lưu định dạng (đúng bản chất CSV). Lưu **XLSX** để giữ định
  dạng (màu nền/chữ, viền, căn lề, định dạng số) và **ô gộp**.
- Định dạng có điều kiện (conditional formatting) hiện chưa ghi vào file.
- Sắp xếp di chuyển vật lý các dòng nên công thức dùng tham chiếu tuyệt đối
  (vd `A1`) có thể lệch sau khi sắp xếp — giống thao tác sort thủ công.
- Một sheet mỗi file; chưa có biểu đồ.
