"""Tests for selective cache invalidation (table_model.py). ASCII only."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from excelapp.table_model import SpreadsheetModel


def _model(rows=20, cols=5):
    return SpreadsheetModel([[""] * cols for _ in range(rows)])


# ---- Task 5: _recalc_cells ----

def test_recalc_cells_returns_changed_and_dependents():
    m = _model()
    m.setData(m.index(0, 0), "1")        # A1 = 1
    m.setData(m.index(1, 0), "=A1+1")    # A2 = A1+1 depends on A1
    assert m._cell_value(1, 0) == 2
    dirty = m._recalc_cells({(0, 0)})
    assert (0, 0) in dirty
    assert (1, 0) in dirty
    assert (0, 0) not in m._eval_cache
    assert (1, 0) not in m._eval_cache


# ---- Task 6: fill selective invalidation ----

def test_fill_keeps_unrelated_formula_cache():
    m = _model()
    m.setData(m.index(0, 4), "=2*2")     # E1 formula, UNRELATED
    assert m._cell_value(0, 4) == 4
    assert (0, 4) in m._eval_cache
    m.setData(m.index(0, 0), "5")        # A1 = 5
    m.fill((0, 0, 0, 0), (0, 0, 4, 0))   # fill down A1..A5
    assert (0, 4) in m._eval_cache       # E1 survives


def test_fill_invalidates_dependent_formula():
    m = _model()
    m.setData(m.index(0, 0), "1")        # A1 = 1
    m.setData(m.index(0, 2), "=A3")      # C1 = A3 (depends on A3)
    m._cell_value(0, 2)
    assert (0, 2) in m._eval_cache
    m.fill((0, 0, 0, 0), (0, 0, 4, 0))   # overwrites A2..A5 (incl. A3)
    assert (0, 2) not in m._eval_cache   # A3 changed -> C1 cache dropped


# ---- Task 7: paste selective invalidation (non-grow) ----

def test_paste_keeps_unrelated_formula_cache():
    m = _model()
    m.setData(m.index(9, 4), "=3+3")     # E10 formula, UNRELATED
    assert m._cell_value(9, 4) == 6
    assert (9, 4) in m._eval_cache
    m.paste_block(0, 0, [["1", "2"], ["3", "4"]])  # 2x2, does not grow
    assert (9, 4) in m._eval_cache       # E10 survives
    assert m._cell_value(0, 0) == 1


def test_paste_invalidates_dependent_formula():
    m = _model()
    m.setData(m.index(5, 0), "=A1")      # A6 = A1
    m._cell_value(5, 0)
    assert (5, 0) in m._eval_cache
    m.paste_block(0, 0, [["9"]])         # writes A1 = 9
    assert (5, 0) not in m._eval_cache   # A1 changed -> A6 loses cache


# ---- Task 8: data() conditional-rule guard ----

def test_data_skips_cond_check_when_no_rules():
    m = _model()
    calls = {"n": 0}
    orig = m._matching_rule
    m._matching_rule = lambda r, c: (calls.__setitem__("n", calls["n"] + 1), orig(r, c))[1]
    idx = m.index(0, 0)
    m.data(idx, Qt.BackgroundRole)
    m.data(idx, Qt.ForegroundRole)
    assert calls["n"] == 0  # no rules -> _matching_rule never called


def test_data_uses_cond_rule_when_present():
    m = _model()
    m.setData(m.index(0, 0), "100")
    m.add_cond_rule({"box": (0, 0, 0, 0), "op": "gt", "v1": 50, "bg": "#FF0000"})
    assert m.data(m.index(0, 0), Qt.BackgroundRole) == QColor("#FF0000")
