# Changelog

Mọi thay đổi đáng chú ý của Ezcel. Định dạng theo [Keep a Changelog],
phiên bản theo [SemVer].

[Keep a Changelog]: https://keepachangelog.com/vi/1.0.0/
[SemVer]: https://semver.org/lang/vi/

## [0.14.2] - 2026-06-03

### Thêm mới
- **Menu chuột phải trên tiêu đề dòng/cột**: bấm phải vào tiêu đề để Chèn / Xóa /
  Ẩn / Hiện / Dãn vừa nội dung ngay tại dòng-cột đó.
- **Dãn vừa nội dung (AutoFit)** cho cột và dòng đang chọn — cũng có trong menu Cấu trúc.

## [0.14.1] - 2026-06-03

### Thêm mới
- **Ẩn / Hiện dòng & cột**: chọn dòng/cột rồi **Ẩn dòng** / **Ẩn cột** để giấu đi;
  chọn vùng trùm phần đang ẩn rồi **Hiện lại** để cho hiện trở lại. Có trong menu
  Cấu trúc và menu chuột phải. (Trạng thái ẩn không lưu vào tệp.)

## [0.14.0] - 2026-06-03

### Thêm mới
- **Dán đặc biệt (Ctrl+Alt+V)** với hộp thoại chọn cách dán:
  - **Dán**: Tất cả / Công thức / Giá trị (kết quả đã tính) / Định dạng.
  - **Phép tính**: Cộng / Trừ / Nhân / Chia giá trị nguồn vào ô đích.
  - **Bỏ qua ô trống**: không ghi đè ô đích khi ô nguồn trống.
  - **Xoay hàng / cột** (transpose).
  - Dán xong là **một bước hoàn tác (Ctrl+Z)**.

## [0.13.0] - 2026-06-03

### Thêm mới
- **Hộp thoại Định dạng ô (Ctrl+1)** với 6 thẻ: **Số, Căn lề, Phông chữ, Viền,
  Tô màu, Bảo vệ** — gộp mọi tùy chọn định dạng vào một chỗ:
  - Thẻ **Số**: chọn thể loại (Số, Phần trăm, Tiền VND/USD, Ngày, Giờ, Khoa học…),
    chỉnh số chữ số thập phân, dấu phân tách hàng nghìn, mã tùy chỉnh — có ô **xem
    trước** kết quả ngay.
  - Thẻ **Căn lề / Phông chữ / Tô màu**: căn ngang–dọc, xuống dòng, phông, cỡ chữ,
    in đậm/nghiêng/gạch, màu chữ, màu nền.
  - Thẻ **Viền**: chọn kiểu viền áp cho vùng.
  - Thẻ **Bảo vệ**: đánh dấu Khóa ô / Ẩn công thức (có hiệu lực khi bật bảo vệ trang).
  - Bấm **OK một lần = hoàn tác một lần (Ctrl+Z)**, áp cho mọi vùng đang chọn.

## [0.12.10] - 2026-06-03

### Thêm mới
- **Chọn nhiều vùng rời (Ctrl+Click)**: giữ **Ctrl** rồi bấm hoặc kéo để chọn thêm
  những ô/vùng không liền nhau. Mỗi vùng được tô sáng riêng. Thống kê ở thanh trạng
  thái và các thao tác định dạng (in đậm, màu, viền), xóa nội dung đều áp cho tất cả
  vùng đang chọn.

## [0.12.9] - 2026-06-03

### Thêm mới
- **Chèn ngày / giờ hiện tại**: nhấn **Ctrl+;** để chèn ngày hôm nay, **Ctrl+Shift+;**
  để chèn giờ hiện tại vào ô đang chọn (giá trị tĩnh). Cũng có trong menu Dữ liệu.

## [0.12.8] - 2026-06-03

### Thêm mới
- **Phóng to / thu nhỏ trang tính (Zoom)**: giữ **Ctrl + lăn chuột** để phóng to
  hoặc thu nhỏ bảng tính (10%–400%). Mức phóng hiện ở góc phải thanh trạng thái —
  bấm vào đó để về 100%.

## [0.12.7] - 2026-06-03

### Sửa
- Sửa **menu thả xuống bị nền đen** khiến chữ khó đọc — giờ nền trắng, chữ rõ.

## [0.12.6] - 2026-06-03

### Thay đổi
- **Bộ icon mới sắc nét** cho thanh công cụ — thay icon cũ bị mờ, nhìn hiện đại và
  rõ nét hơn trên mọi màn hình.

## [0.12.5] - 2026-06-03

### Thêm mới
- **Hiện công thức (Ctrl+`)**: bật/tắt xem công thức gốc thay vì kết quả trên cả
  trang tính — tiện rà soát công thức. Có trong menu Xem. Mỗi sheet nhớ riêng trạng
  thái bật/tắt.

## [0.12.4] - 2026-06-03

### Thêm mới
- **AutoSum (Alt+=)**: bấm `Alt` + `=` để tự chèn `=SUM(...)` cho dải số ngay phía
  trên ô (hoặc bên trái nếu trên không có số). Nếu không có dải số liền kề, ô để sẵn
  `=SUM()` cho bạn tự quét vùng. Có trong menu Dữ liệu.

## [0.12.3] - 2026-06-03

### Thêm mới
- **Thanh trạng thái thống kê đầy đủ hơn**: thêm **Đếm số / Nhỏ nhất / Lớn nhất**
  bên cạnh Trung bình / Đếm / Tổng.
- **Chuột phải vào thanh trạng thái** để bật/tắt từng mục thống kê; lựa chọn được
  ghi nhớ cho lần mở sau. Mặc định bật Trung bình / Đếm / Tổng.

### Sửa
- Chọn nhiều vùng rời cho số liệu đúng các ô đã chọn.
- Số lớn hiển thị đầy đủ thay vì dạng rút gọn.

## [0.12.2] - 2026-06-03

### Thêm mới
- **Hiển thị chế độ ô ở thanh trạng thái** (góc trái): **Sẵn sàng** khi đang di
  chuyển; **Nhập** khi vừa gõ vào ô; **Chỉnh sửa** khi F2 / nhấp đúp ô có dữ liệu;
  **Trỏ** khi chọn ô làm tham chiếu lúc soạn công thức. Nhấn Enter / Esc / chuyển ô
  để quay về **Sẵn sàng** (một lần Esc hủy cả chỉnh sửa).

## [0.12.1] - 2026-06-03

### Thêm mới
- **Ô địa chỉ "Đi tới" (Name Box)**: gõ địa chỉ rồi Enter để nhảy tới ô đơn `A1`,
  vùng `A1:C5` (gõ ngược `C5:A1` cũng được), cả cột `A:A`, cả hàng `1:1`. Tham chiếu
  sai sẽ báo "Tham chiếu không hợp lệ." và giữ nguyên ô đang chọn.
- **F5** hoặc **Ctrl+G** để nhảy nhanh vào ô địa chỉ; **Esc** để hủy.

## [0.12.0] - 2026-06-02

### Thêm mới
- **Mở rộng thư viện hàm từ ~60 lên ~120 hàm**:
  - Thông tin: `ISNUMBER, ISTEXT, ISNONTEXT, ISBLANK, ISLOGICAL, ISEVEN,`
    `ISODD, ISERROR, ISERR, ISNA, NA`
  - Logic: `XOR, IFNA, SWITCH`
  - Chuỗi: `TEXTJOIN, EXACT, CHAR, UNICHAR, CODE, UNICODE, CLEAN, T, FIXED`
  - Tra cứu: `XLOOKUP, CHOOSE`
  - Toán/lượng giác: `SIN, COS, TAN, ASIN, ACOS, ATAN, ATAN2, SINH, COSH,`
    `TANH, DEGREES, RADIANS, LOG10, GCD, LCM, FACT, COMBIN, PERMUT, MROUND,`
    `EVEN, ODD, QUOTIENT, SUMSQ`
  - Thống kê: `AVERAGEIFS, MAXIFS, MINIFS, STDEVP, VARP, GEOMEAN, HARMEAN,`
    `AVERAGEA`
  - Ngày/giờ: `EDATE, EOMONTH, TIME, SECOND, DAYS, DATEVALUE, WEEKNUM,`
    `ISOWEEKNUM`
- **Mã lỗi rõ ràng**: ô hiển thị `#DIV/0!`, `#N/A`, `#VALUE!`, `#NUM!`, `#NAME?`,
  `#REF!` theo đúng loại lỗi.

### Sửa
- Công thức gây lỗi không còn làm hỏng việc tính lại — đều trả về mã lỗi rõ ràng.
- Tên hàm kết thúc bằng số (`ATAN2`, `LOG10`) không còn bị nhầm thành tham chiếu ô.

## [0.11.2] - 2026-06-02

### Thêm mới
- **Soạn công thức bằng chuột**: khi đang gõ công thức (bắt đầu bằng `=`), bấm vào
  ô để chèn tham chiếu ô đó.
- **Bấm tiêu đề cột/hàng** để bôi đen cả cột/hàng đó.

### Sửa
- Popup chọn phông/cỡ chữ không còn bị nền đen.

### Thay đổi
- Nút định dạng chữ hiển thị chữ cái có style (**B** đậm, *I* nghiêng, U gạch chân,
  S gạch ngang) thay vì cả từ.

## [0.11.1] - 2026-06-02

### Cải thiện
- Chọn cả cột/hàng và tính lại công thức mượt hơn.

## [0.11.0] - 2026-06-02

### Thay đổi
- **Đổi tên ứng dụng thành Ezcel** (tên hiển thị, exe, bộ cài). Cài đè được lên
  bản cũ.

### Cải thiện
- Chọn ô/vùng mượt hơn.

## [0.10.1] - 2026-06-02

### Sửa
- Sửa lỗi không kiểm tra/tải được cập nhật trên một số máy.
- Popup chọn phông/cỡ chữ không còn bị nền đen.

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
- **Định dạng**: màu nền, màu chữ, gạch ngang, kẻ viền ô (tất cả/ngoài/từng cạnh),
  định dạng số (số, phần trăm, tiền VND/USD, ngày, giờ, khoa học)
- **Gộp ô** (merge / unmerge)
- **Định dạng có điều kiện**: tô màu theo điều kiện (lớn hơn/nhỏ hơn/bằng/trong
  khoảng/chứa chữ)
- **Lưu định dạng + ô gộp vào file .xlsx** (đọc lại giữ nguyên)
- **Nhiều sheet/tab**: thêm/xóa/đổi tên/nhân bản/kéo thả tab; lưu & mở workbook
  nhiều sheet

## [0.9.0]
- Bản nền: dropdown căn lề/xuống dòng, bộ lọc, ribbon, đọc/ghi CSV & XLSX.
