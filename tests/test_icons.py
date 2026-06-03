"""Test bo icon Lucide render dung + net (HiDPI). ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402


def test_all_icons_render(qapp):
    from excelapp.icons import make_icon
    from excelapp.lucide_data import ICONS
    assert len(ICONS) == 28
    for name in ICONS:
        ic = make_icon(name)
        assert not ic.isNull(), name
        pm = ic.pixmap(20, 20)
        assert not pm.isNull(), name


def test_icon_has_visible_content(qapp):
    # Icon thuc su ve duoc net (co pixel khong trong suot), khong phai o trong
    from excelapp.icons import make_icon
    img = make_icon("bold", size=20).pixmap(40, 40).toImage()
    has = any(
        img.pixelColor(x, y).alpha() > 0
        for x in range(0, 40, 2)
        for y in range(0, 40, 2)
    )
    assert has


def test_unknown_icon_is_safe(qapp):
    from excelapp.icons import make_icon
    assert make_icon("khong_ton_tai").isNull()  # rong, khong vo UI


def test_icon_cache(qapp):
    from excelapp.icons import make_icon
    assert make_icon("bold") is make_icon("bold")
    assert make_icon("bold", "#000000") is not make_icon("bold", "#ffffff")
