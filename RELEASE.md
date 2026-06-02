# Phát hành bản mới (để tính năng auto-update hoạt động)

App kiểm tra cập nhật qua **GitHub Releases** của repo
`janreng/EZG-Excel` (cấu hình trong [src/excelapp/updater.py](src/excelapp/updater.py)).

Mỗi lần ra bản mới, làm theo các bước sau:

## 1. Tăng số phiên bản
Sửa cùng một số ở 2 nơi:
- [src/excelapp/__init__.py](src/excelapp/__init__.py) → `__version__`
- [installer.iss](installer.iss) → `MyAppVersion`

## 2. Build app + installer
```bat
build.bat
build_installer.bat
```
→ tạo `installer\EZG-Excel-Setup-<version>.exe`

## 3. Tạo GitHub Release
Dùng web GitHub (Releases → Draft a new release) hoặc CLI `gh`:
```bat
gh release create v0.8.0 "installer\EZG-Excel-Setup-0.8.0.exe" --title "v0.8.0" --notes "Mô tả thay đổi"
```
Yêu cầu:
- **Tag** đặt theo phiên bản, vd `v0.8.0` (app tự bỏ chữ `v` khi so sánh).
- **Đính kèm** file `EZG-Excel-Setup-<version>.exe` làm asset (app tìm file `.exe`).

## 4. Người dùng cập nhật
Trên máy đã cài bản cũ: **Trợ giúp → Kiểm tra cập nhật** → thấy bản mới →
**Cập nhật ngay** → app tải installer và tự chạy → cài đè (cùng AppId).

> Repo phải **public** để app đọc release ẩn danh. Nếu để private cần thêm
> token vào header trong `updater.py`.
