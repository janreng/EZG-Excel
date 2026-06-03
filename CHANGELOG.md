# Changelog

Mọi thay đổi đáng chú ý của Ezcel. Định dạng theo [Keep a Changelog],
phiên bản theo [SemVer].

[Keep a Changelog]: https://keepachangelog.com/vi/1.0.0/
[SemVer]: https://semver.org/lang/vi/

## [0.12.2] - 2026-06-03

### Thêm mới
- **Cell Mode indicator kiểu Excel** (Spec 03, Phase 1): thanh trạng thái góc
  trái hiển thị mode hiện tại — **Sẵn sàng / Nhập / Chỉnh sửa / Trỏ**
  (Ready / Enter / Edit / Point):
  - Gõ ký tự vào ô → **Nhập (Enter)**; F2 / double-click ô có data → **Chỉnh
    sửa (Edit)**; chọn ô làm tham chiếu khi soạn công thức → **Trỏ (Point)**;
    commit / Esc / di chuyển ô → **Sẵn sàng (Ready)**.
  - State machine tách module thuần `cell_mode.py` (`CellMode` + `transition()`),
    19 unit test bám bảng chuyển trạng thái Spec 03.
  - Esc khi đang sửa: hủy toàn bộ về Ready (đúng Excel — không có bước trung gian).

### Ghi chú
- Bản này làm **indicator + state machine** (gốc của mọi keyboard behavior).
  Phần Point mode dùng **phím mũi tên** để chọn/mở rộng tham chiếu (gõ `=` rồi ↑↓)
  còn hoãn sang bản sau — hiện Point kích hoạt qua **click ô** khi soạn công thức.

## [0.12.1] - 2026-06-03

### Thêm mới
- **Name Box "Go To" kiểu Excel** (Spec 04, Phase 1):
  - Gõ địa chỉ vào Name Box rồi Enter để nhảy tới: ô đơn `A1`/`$A$1`,
    vùng ô `A1:C5` (tự chuẩn hóa nếu đảo ngược `C5:A1`), cả cột `A:A`/`A:C`,
    cả hàng `1:1`/`2:5`. Không phân biệt hoa thường, chấp nhận dấu `$`.
  - Tham chiếu vượt lưới được kẹp về biên; tham chiếu sai cú pháp hoặc nằm
    hoàn toàn ngoài lưới → hộp thoại "Tham chiếu không hợp lệ.", giữ nguyên ô
    đang chọn.
  - **F5** và **Ctrl+G** = Go To: đưa con trỏ vào Name Box và bôi đen sẵn.
  - **Esc** trong Name Box: bỏ chỉnh sửa, khôi phục địa chỉ ô, trả focus về lưới.
  - Bộ phân tích tham chiếu (`formula.parse_grid_reference`) là hàm thuần,
    regex compile-once (không cấp phát thừa trên hot path), 25 unit test.

### Ghi chú
- Named range, vùng rời rạc (`A1:B3,D5`) và tham chiếu chéo sheet (`Sheet2!A1`)
  trong Name Box: dời sang Phase sau (cần Spec 31 + lớp vẽ đa vùng + multi-sheet).
  Hiện các dạng này hiển thị hộp thoại lỗi thay vì crash.

## [0.12.0] - 2026-06-02

### Thêm mới
- **Mở rộng thư viện hàm từ ~60 lên ~120 hàm** (toàn bộ là hàm vô hướng,
  không đổi mô hình ô — an toàn, tương thích ngược):
  - Thông tin: `ISNUMBER, ISTEXT, ISNONTEXT, ISBLANK, ISLOGICAL, ISEVEN,`
    `ISODD, ISERROR, ISERR, ISNA, NA`
  - Logic: `XOR, IFNA, SWITCH`
  - Chuỗi: `TEXTJOIN, EXACT, CHAR, UNICHAR, CODE, UNICODE, CLEAN, T, FIXED`
  - Tra cứu: `XLOOKUP` (match_mode 0/-1/1/2 + search_mode 1/-1), `CHOOSE`
  - Toán/lượng giác: `SIN, COS, TAN, ASIN, ACOS, ATAN, ATAN2, SINH, COSH,`
    `TANH, DEGREES, RADIANS, LOG10, GCD, LCM, FACT, COMBIN, PERMUT, MROUND,`
    `EVEN, ODD, QUOTIENT, SUMSQ`
  - Thống kê: `AVERAGEIFS, MAXIFS, MINIFS, STDEVP, VARP, GEOMEAN, HARMEAN,`
    `AVERAGEA`
  - Ngày/giờ: `EDATE, EOMONTH, TIME, SECOND, DAYS, DATEVALUE, WEEKNUM,`
    `ISOWEEKNUM`
- **Mã lỗi kiểu Excel**: ô hiển thị `#DIV/0!`, `#N/A`, `#VALUE!`, `#NUM!`,
  `#NAME?`, `#REF!` thay vì `#LỖI!` chung chung. `ISERROR/ISERR/ISNA/IFNA`
  phân loại đúng theo mã.

### Sửa lỗi
- **Chống treo (crash)**: các công thức gây lỗi Python (không phải lỗi công
  thức) trước đây làm hỏng việc tính lại — nay đều trả mã lỗi:
  - `*IFS` với các vùng lệch kích thước → `#VALUE!` (trước: treo `IndexError`).
  - Giá trị `inf`/`NaN`, số quá lớn (`FACT(171)`, `POWER(10,1000)`, tổng tràn)
    → `#NUM!`.
  - `UNICHAR` mã ngoài phạm vi, `EDATE/EOMONTH` ngày ngoài `1..9999` → lỗi
    rõ ràng thay vì treo.
  - `CHOOSE` trả về vùng nhiều ô không còn hiển thị rác `<_Range object>`.
- **Tokenizer**: tên hàm kết thúc bằng số (`ATAN2`, `LOG10`) không còn bị
  nhầm thành tham chiếu ô.
- `GCD/LCM` với số âm → `#NUM!` (đúng Excel, trước đây lấy trị tuyệt đối).

### Cải thiện (hiệu năng)
- **Tiêu chí `*IF/*IFS` biên dịch một lần** thay vì phân tích lại trên mỗi ô:
  bỏ cấp phát dict thừa trên đường nóng (`_compile_criteria`). Đo trên 100k ô:
  khớp tiêu chí nhanh hơn **~3.8×** (291ms → 77ms).
- Wildcard (`*`, `?`, `~`) trong `COUNTIF/SUMIF/XLOOKUP` khớp đúng kiểu Excel
  (không còn diễn giải `[...]` như fnmatch).

## [0.11.2] - 2026-06-02

### Thêm mới
- **Soạn công thức kiểu Excel**: khi đang gõ công thức ở thanh công thức (bắt đầu
  bằng `=`), bấm vào ô để chèn tham chiếu ô đó (vd `=D3+B1` bằng cách bấm chuột).
- **Bấm tiêu đề cột/hàng** để bôi đen cả cột/hàng đó.

### Sửa lỗi
- **Dropdown nền đen**: ép giao diện nền sáng (không chạy theo dark mode Windows)
  + nền trắng cho popup chọn phông/cỡ chữ.

### Thay đổi
- Nút định dạng chữ hiển thị **chữ cái có style** (B đậm, I nghiêng, U gạch chân,
  S gạch ngang) thay vì cả từ.

## [0.11.1] - 2026-06-02

### Cải thiện (hiệu năng)
- Header highlight (sáng cột/hàng đang chọn) tính theo *range* thay vì liệt kê
  từng ô — chọn cả cột/hàng không còn khựng.
- `fill` (kéo-điền) và `paste` chỉ vô hiệu cache công thức bị ảnh hưởng (ô đổi +
  ô phụ thuộc) thay vì tính lại toàn bộ công thức của sheet.
- `data()` bỏ qua quét định dạng có điều kiện khi sheet không có quy tắc nào.
- Gộp tín hiệu selection vào một slot (giảm repaint thừa mỗi lần chọn).

## [0.11.0] - 2026-06-02

### Thay đổi
- **Đổi tên ứng dụng** từ "EZG - Excel" thành **Ezcel** (tên hiển thị, exe,
  bộ cài). Giữ nguyên AppId nên cài đè được lên bản cũ; kho GitHub vẫn là
  `EZG-Excel` (auto-update không đổi).

### Cải thiện
- Chọn ô/vùng mượt hơn: lấy bounding-box theo *range* thay vì liệt kê từng ô
  (`selectedIndexes()`) — chọn cả cột/hàng không còn khựng.

## [0.10.1] - 2026-06-02

### Sửa lỗi
- **Cập nhật**: sửa lỗi `SSL: CERTIFICATE_VERIFY_FAILED` (unable to get local
  issuer certificate) khi kiểm tra/tải cập nhật trên máy khác. App nay xác thực
  HTTPS bằng kho chứng chỉ Windows (`truststore`), dự phòng `certifi`.
- **Giao diện**: sửa popup dropdown (phông chữ, cỡ chữ) bị nền đen không đọc
  được — nay nền trắng, chữ đen, dòng chọn xanh.

### Cải thiện
- Chọn ô mượt hơn: cache QIcon theo (tên, màu, cỡ) nên không render lại SVG
  mỗi lần đồng bộ toolbar khi đổi ô.

## [0.10.0] - 2026-06-02

### Thêm mới
- **Công thức**: mở rộng từ 17 lên ~60 hàm:
  - Logic: `AND, OR, NOT, IFERROR, IFS, TRUE, FALSE`
  - Điều kiện: `COUNTIF, COUNTIFS, SUMIF, SUMIFS, AVERAGEIF, COUNTA, COUNTBLANK`
  - Tra cứu: `VLOOKUP, HLOOKUP, INDEX, MATCH, LOOKUP`
  - Chuỗi: `LEFT, RIGHT, MID, LEN, TRIM, UPPER, LOWER, PROPER, REPT, REPLACE,`
    `SUBSTITUTE, FIND, SEARCH, VALUE, TEXT`
  - Toán: `CEILING, FLOOR, TRUNC, SIGN, PRODUCT, SUMPRODUCT, ROUNDUP,`
    `ROUNDDOWN, PI, EXP, LOG, LN`
  - Ngày/giờ: `TODAY, NOW, DATE, YEAR, MONTH, DAY, HOUR, MINUTE, WEEKDAY, DATEDIF`
  - Thống kê: `MEDIAN, MODE, STDEV, VAR, LARGE, SMALL, RANK`
  - `IF/IFERROR/IFS` tính lười (không tính nhánh thừa, bắt được lỗi)
- **Định dạng**: màu nền, màu chữ, gạch ngang, kẻ viền ô (tất cả/ngoài/từng cạnh),
  định dạng số (số, phần trăm, tiền VND/USD, ngày, giờ, khoa học)
- **Gộp ô** (merge / unmerge cells)
- **Định dạng có điều kiện**: tô màu theo điều kiện (lớn hơn/nhỏ hơn/bằng/trong
  khoảng/chứa chữ)
- **Lưu định dạng + ô gộp vào file .xlsx** (đọc lại giữ nguyên)
- **Nhiều sheet/tab**: thêm/xóa/đổi tên/nhân bản/kéo thả tab; lưu & mở workbook
  nhiều sheet

### Sửa lỗi
- Sửa lỗi `AttributeError` khi vẽ tiêu đề cột đang chọn (code chết trong
  `FilterHeaderView.paintSection`)

### Ghi chú
- Tham chiếu chéo sheet (`=Sheet2!A1`) và ghi conditional formatting vào file
  chưa được hỗ trợ.

## [0.9.0]
- Bản nền: dropdown căn lề/xuống dòng, bộ lọc kiểu Excel, ribbon, đọc/ghi
  CSV & XLSX (chỉ giá trị + công thức).
