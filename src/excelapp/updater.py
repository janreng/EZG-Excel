"""Kiểm tra & tải bản cập nhật từ GitHub Releases.

Cơ chế: app đọc release mới nhất qua GitHub API, so sánh phiên bản với bản
đang chạy. Nếu mới hơn, tải file installer (.exe) đính kèm release rồi chạy nó
để cài đè (cùng AppId nên cập nhật tại chỗ).

➜ Sửa GITHUB_OWNER / GITHUB_REPO cho đúng repo của bạn.
"""

from __future__ import annotations

import json
import re
import ssl
import urllib.request

from PySide6.QtCore import QThread, Signal

GITHUB_OWNER = "janreng"
GITHUB_REPO = "EZG-Excel"

_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
_TIMEOUT = 15

_ssl_ctx: ssl.SSLContext | None = None


def _ssl_context() -> ssl.SSLContext:
    """Tạo SSL context xác thực được chứng chỉ HTTPS trên mọi máy.

    Khi đóng gói bằng PyInstaller, Python không tự tìm thấy kho CA của hệ thống
    nên xác thực HTTPS hay lỗi ``CERTIFICATE_VERIFY_FAILED``. Ưu tiên dùng
    ``truststore`` (kho chứng chỉ của Windows — hợp cả môi trường công ty), nếu
    không có thì dùng CA bundle của ``certifi``, cuối cùng mới về mặc định.
    """
    global _ssl_ctx
    if _ssl_ctx is not None:
        return _ssl_ctx
    try:
        import truststore

        _ssl_ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return _ssl_ctx
    except Exception:  # noqa: BLE001
        pass
    try:
        import certifi

        _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        return _ssl_ctx
    except Exception:  # noqa: BLE001
        _ssl_ctx = ssl.create_default_context()
        return _ssl_ctx


class UpdateError(Exception):
    pass


def _parse_version(text: str) -> tuple[int, ...]:
    """'v0.7.0' / '0.7.0' -> (0, 7, 0). Phần không phải số -> bỏ qua."""
    nums = re.findall(r"\d+", text or "")
    return tuple(int(n) for n in nums) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return _parse_version(latest) > _parse_version(current)


def check_latest() -> dict:
    """Trả về {version, notes, url, name} của release mới nhất trên GitHub."""
    url = _API.format(owner=GITHUB_OWNER, repo=GITHUB_REPO)
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Ezcel-Updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise UpdateError(str(exc))

    tag = data.get("tag_name") or data.get("name") or ""
    notes = data.get("body") or ""
    # Tìm file .exe đính kèm (ưu tiên tên có 'setup').
    assets = data.get("assets", [])
    exe = next(
        (a for a in assets if a.get("name", "").lower().endswith(".exe")), None
    )
    if exe is None:
        raise UpdateError("Release chưa có file .exe đính kèm")
    return {
        "version": tag,
        "notes": notes,
        "url": exe["browser_download_url"],
        "name": exe["name"],
    }


class DownloadThread(QThread):
    """Tải file installer ở luồng nền, báo tiến độ %."""

    progress = Signal(int)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, dest: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest = dest

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                self._url, headers={"User-Agent": "Ezcel-Updater"}
            )
            with urllib.request.urlopen(
                req, timeout=_TIMEOUT, context=_ssl_context()
            ) as resp, open(self._dest, "wb") as f:
                total = int(resp.headers.get("Content-Length", 0))
                read = 0
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    read += len(chunk)
                    if total:
                        self.progress.emit(int(read * 100 / total))
            self.done.emit(self._dest)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
