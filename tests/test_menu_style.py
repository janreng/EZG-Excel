"""Test popup menu KHONG bi nen den (fix dropdown vien). ASCII only.

Tai hien bug: QMenu la con cua widget co stylesheet (nhu ribbon) -> neu khong
co rule QMenu se render nen toi. Sau khi ap _MENU_QSS toan app -> nen trang.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtWidgets import QWidget, QMenu  # noqa: E402


def test_menu_qss_defines_white_background():
    from excelapp.ui_style import MENU_QSS
    assert "QMenu {" in MENU_QSS
    assert "#ffffff" in MENU_QSS.lower() or "#fff" in MENU_QSS.lower()


def _menu_bg(qapp, menu):
    menu.adjustSize()
    menu.show()
    qapp.processEvents()
    img = menu.grab().toImage()
    menu.hide()
    return img.pixelColor(5, 5)  # diem nen gan goc, qua vien 1px


def test_child_menu_renders_light_background(qapp):
    # Bug: menu la con cua widget co stylesheet toi -> render nen den.
    # Fix: dat MENU_QSS THANG len menu (widget-level thang cascade tu cha).
    from excelapp.ui_style import MENU_QSS
    parent = QWidget()
    parent.setStyleSheet("QWidget { background: #2b2b2b; }")
    menu = QMenu(parent)
    menu.setStyleSheet(MENU_QSS)
    menu.addAction("All borders")
    menu.addAction("Top border")
    c = _menu_bg(qapp, menu)
    assert c.red() > 200 and c.green() > 200 and c.blue() > 200, (
        c.red(), c.green(), c.blue()
    )


def test_ribbon_dropdowns_styled(qapp):
    # Cac dropdown ribbon thuc te phai duoc set MENU_QSS (khong con den).
    from excelapp.main_window import MainWindow
    from excelapp.ui_style import MENU_QSS
    w = MainWindow()
    try:
        menus = w.findChildren(QMenu)
        styled = [m for m in menus if m.styleSheet() == MENU_QSS]
        # It nhat cac dropdown vien/dinh dang so + context menu da duoc style
        assert len(styled) >= 2
    finally:
        w.close()
