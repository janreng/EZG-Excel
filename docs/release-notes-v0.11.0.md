# Ezcel v0.11.0

> Bản đầu tiên mang tên **Ezcel** (trước đây là "EZG - Excel"). Tổng hợp mọi
> thay đổi kể từ v0.9.0.

## ✨ Tính năng mới
- **Công thức**: mở rộng từ 17 lên ~60 hàm — logic (`IF, AND, OR, IFERROR, IFS`),
  điều kiện (`COUNTIF, SUMIF, COUNTIFS, SUMIFS, AVERAGEIF`), tra cứu
  (`VLOOKUP, HLOOKUP, INDEX, MATCH, LOOKUP`), chuỗi (`LEFT, MID, TRIM, SUBSTITUTE...`),
  toán (`CEILING, FLOOR, SUMPRODUCT, LOG...`), ngày giờ (`TODAY, DATE, DATEDIF...`),
  thống kê (`MEDIAN, STDEV, LARGE, RANK...`).
- **Định dạng**: màu nền, màu chữ, gạch ngang, kẻ viền, định dạng số
  (số, %, tiền VND/USD, ngày, giờ, khoa học).
- **Gộp ô** (merge cells).
- **Định dạng có điều kiện** (tô màu theo điều kiện).
- **Lưu định dạng + ô gộp vào file .xlsx** (đọc lại giữ nguyên).
- **Nhiều sheet/tab**: thêm/xóa/đổi tên/nhân bản/kéo thả; lưu & mở workbook nhiều sheet.

## 🐞 Sửa lỗi
- **Cập nhật**: sửa lỗi `SSL: CERTIFICATE_VERIFY_FAILED` khi kiểm tra/tải cập nhật
  trên máy khác (dùng kho chứng chỉ Windows `truststore`, dự phòng `certifi`).
- **Giao diện**: popup dropdown (phông/cỡ chữ) không còn bị nền đen.
- Sửa lỗi khi vẽ tiêu đề cột đang chọn.

## ⚡ Cải thiện
- Chọn ô/vùng mượt hơn (cache icon + lấy vùng chọn theo range).

## ⚠️ Lưu ý cập nhật
- Bản **0.9.0/0.10.x cũ dính lỗi SSL** nên KHÔNG tự cập nhật được — hãy tải và
  chạy `Ezcel-Setup-0.11.0.exe` thủ công lần này. Từ 0.11.0 trở đi auto-update hoạt động.
- Cài đè được lên bản cũ (cùng AppId).
