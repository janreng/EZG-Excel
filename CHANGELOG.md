# Changelog

Mọi thay đổi đáng chú ý của Ezcel. Định dạng theo [Keep a Changelog],
phiên bản theo [SemVer].

[Keep a Changelog]: https://keepachangelog.com/vi/1.0.0/
[SemVer]: https://semver.org/lang/vi/

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
