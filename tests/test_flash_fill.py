"""Tests cho Flash Fill (Ctrl+E) — Spec 05. Offscreen, ASCII only."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402

from excelapp.flash_fill import infer_and_fill  # noqa: E402
from excelapp.i18n import set_lang  # noqa: E402


# ------------------------------------------------------------ suy luận thuần
def test_token_reorder():
    out = infer_and_fill(["John Smith", "Jane Doe", "Bob Lee"], {0: "Smith, John"})
    assert out == ["Smith, John", "Doe, Jane", "Lee, Bob"]


def test_extract_first_token():
    out = infer_and_fill(["John Smith", "Jane Doe"], {0: "John"})
    assert out == ["John", "Jane"]


def test_whole_upper():
    assert infer_and_fill(["abc", "def"], {0: "ABC"}) == ["ABC", "DEF"]


def test_whole_title():
    assert infer_and_fill(["john smith", "jane doe"], {0: "John Smith"}) == ["John Smith", "Jane Doe"]


def test_inconsistent_examples_returns_none():
    # Hai ví dụ mâu thuẫn -> không điền bừa.
    assert infer_and_fill(["John Smith", "Jane Doe"], {0: "Smith, John", 1: "Jane"}) is None


def test_no_examples_returns_none():
    assert infer_and_fill(["a", "b"], {}) is None


def test_verified_across_multiple_examples():
    # 2 ví dụ cùng mẫu -> ap dung; dòng thứ 3 suy ra dung.
    out = infer_and_fill(["A B", "C D", "E F"], {0: "B-A", 1: "D-C"})
    assert out == ["B-A", "D-C", "F-E"]


# ------------------------------------------------------------ tích hợp
@pytest.fixture
def win(qapp):
    from excelapp.main_window import MainWindow
    set_lang("en")
    w = MainWindow()
    yield w
    w.close()
    set_lang("vi")


def test_flash_fill_command_fills_and_single_undo(win):
    m = win.model
    names = ["John Smith", "Jane Doe", "Bob Lee"]
    for r, n in enumerate(names):
        m.setData(m.index(r, 0), n)        # cot A = nguon
    m.setData(m.index(0, 1), "Smith, John")  # B1 = vi du
    win.view.setCurrentIndex(m.index(0, 1))
    win.flash_fill_command()
    assert m._data[1][1] == "Doe, Jane"
    assert m._data[2][1] == "Lee, Bob"
    # mot Ctrl+Z hoan tac het phan dien (B1 vi du van con)
    assert m.undo() is True
    assert m._data[1][1] == ""
    assert m._data[2][1] == ""
    assert m._data[0][1] == "Smith, John"


def test_flash_fill_no_source_column(win):
    win.model.setData(win.model.index(0, 0), "x")
    win.view.setCurrentIndex(win.model.index(0, 0))   # cot 0 -> khong co nguon trai
    win.flash_fill_command()
    assert win.statusBar().currentMessage() != ""     # bao loi, khong treo
