# Ezcel v0.11.3

Mở rộng lớn thư viện hàm công thức + mã lỗi kiểu Excel + vá nhiều lỗi treo.

## ✨ Thêm mới — ~60 hàm mới (tổng ~120)

- **Thông tin**: `ISNUMBER, ISTEXT, ISNONTEXT, ISBLANK, ISLOGICAL, ISEVEN,
  ISODD, ISERROR, ISERR, ISNA, NA`
- **Logic**: `XOR, IFNA, SWITCH`
- **Chuỗi**: `TEXTJOIN, EXACT, CHAR, UNICHAR, CODE, UNICODE, CLEAN, T, FIXED`
- **Tra cứu**: `XLOOKUP` (đủ match_mode 0/-1/1/2, search_mode xuôi/ngược), `CHOOSE`
- **Toán & lượng giác**: `SIN, COS, TAN, ASIN, ACOS, ATAN, ATAN2, SINH, COSH,
  TANH, DEGREES, RADIANS, LOG10, GCD, LCM, FACT, COMBIN, PERMUT, MROUND, EVEN,
  ODD, QUOTIENT, SUMSQ`
- **Thống kê**: `AVERAGEIFS, MAXIFS, MINIFS, STDEVP, VARP, GEOMEAN, HARMEAN,
  AVERAGEA`
- **Ngày/giờ**: `EDATE, EOMONTH, TIME, SECOND, DAYS, DATEVALUE, WEEKNUM,
  ISOWEEKNUM`

## 🟥 Mã lỗi kiểu Excel

Ô báo lỗi nay hiển thị đúng mã: `#DIV/0!`, `#N/A`, `#VALUE!`, `#NUM!`,
`#NAME?`, `#REF!` (thay vì `#LỖI!`). `ISERROR/ISERR/ISNA/IFNA` phân loại theo mã.

## 🐞 Sửa lỗi (chống treo)

- Công thức `*IFS` với vùng lệch kích thước → `#VALUE!` (trước đây làm treo).
- `inf/NaN`, số quá lớn (`FACT(171)`, `POWER(10,1000)`...) → `#NUM!`.
- `UNICHAR`/ngày ngoài phạm vi → lỗi rõ ràng thay vì treo.
- `CHOOSE` trả vùng nhiều ô không còn hiện rác `<_Range object>`.
- Tên hàm có số (`ATAN2`, `LOG10`) không còn bị nhầm thành ô.
- `GCD/LCM` số âm → `#NUM!` (đúng Excel).

## ⚡ Hiệu năng

- Tiêu chí `*IF/*IFS` **biên dịch 1 lần** thay vì parse lại mỗi ô — nhanh hơn
  **~3.8×** trên 100k ô (291ms → 77ms). Wildcard khớp đúng kiểu Excel.

## Ghi chú

- Toàn bộ hàm mới là **vô hướng** (không tạo spill range). Function Wizard,
  smart-tag lỗi, dynamic array (FILTER/SORT/UNIQUE/spill) chưa có — xem
  `docs/specs/12-formula-system.md` (Phase 4 & 6).
- Cài đè được lên bản cũ (cùng AppId). Người dùng 0.11.x bấm Trợ giúp → Kiểm
  tra cập nhật để lên 0.11.3.
