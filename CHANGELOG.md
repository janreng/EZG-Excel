# Changelog

Mọi thay đổi đáng chú ý của EZG - Excel. Định dạng theo [Keep a Changelog],
phiên bản theo [SemVer].

[Keep a Changelog]: https://keepachangelog.com/vi/1.0.0/
[SemVer]: https://semver.org/lang/vi/

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
