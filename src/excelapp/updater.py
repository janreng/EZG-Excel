"""Kiểm tra & tải bản cập nhật từ GitHub Releases.

Cơ chế: app đọc release mới nhất qua GitHub API, so sánh phiên bản với bản
đang chạy. Nếu mới hơn, tải file installer (.exe) đính kèm release rồi chạy nó
để cài đè (cùng AppId nên cập nhật tại chỗ).

➜ Sửa GITHUB_OWNER / GITHUB_REPO cho đúng repo của bạn.
"""

from __future__ import annotations

import json
import re
import urllib.request

from PySide6.QtCore import QThread, Signal

GITHUB_OWNER = "janreng"
GITHUB_REPO = "EZG-Excel"

_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
_TIMEOUT = 15


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
            "User-Agent": "EZG-Excel-Updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
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
                self._url, headers={"User-Agent": "EZG-Excel-Updater"}
            )
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp, open(
                self._dest, "wb"
            ) as f:
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
