# Ezcel v0.11.1

Bản vá hiệu năng — không đổi tính năng/hành vi nhìn thấy.

## ⚡ Cải thiện hiệu năng
- **Chọn cột/hàng lớn không còn khựng**: phần sáng tiêu đề (header highlight)
  tính theo *vùng* (range) thay vì liệt kê từng ô.
- **Kéo-điền (fill) & dán (paste) nhanh hơn**: chỉ tính lại các công thức bị
  ảnh hưởng (ô thay đổi + ô phụ thuộc), không tính lại toàn bộ sheet.
- **`data()` nhẹ hơn**: bỏ qua quét định dạng có điều kiện khi sheet không có
  quy tắc nào.
- Gộp tín hiệu chọn ô vào một chỗ → giảm vẽ lại thừa.

## Ghi chú
- Cài đè được lên bản cũ (cùng AppId).
- Nâng cấp khuyến nghị cho ai dùng file/lưới lớn.
