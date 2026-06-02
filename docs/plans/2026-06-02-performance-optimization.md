# Performance Optimization (selection/drag jank + formula cache) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate jank when selecting/dragging cells and cut redundant formula recomputation, without changing any user-visible behavior.

**Architecture:** Two independent fronts. (A) The *selection* hot path in `view.py`: replace enumerating every `QModelIndex` of the selection with reading the bounding box from the *ranges* of `selectionModel().selection()` (O(number of ranges) instead of O(number of cells)). (B) *Selective cache invalidation* in `table_model.py`: `fill`/`paste` only drop the cache of changed cells + their dependents instead of `clear()`-ing everything; `data()` skips conditional-rule scanning when there are no rules.

**Tech Stack:** Python 3.10+, PySide6 (Qt Widgets/Core), pytest (headless `QT_QPA_PLATFORM=offscreen`).

---

## SPEC

### Background
EZG-Excel is an interactive spreadsheet app (Qt Model–View). The user reports the app "feels laggy". A code review (2026-06-02) identified expensive hot paths. This plan implements the **low-risk, high-value** fixes already agreed on; the heavier architectural work (range-based dependency graph) is deferred to a later plan.

### Problems to solve (priority order)
1. **`_selection_box()` enumerates every selected cell, re-run on every paint** — [view.py:220-229](../../src/excelapp/view.py#L220-L229). `selectionModel().selectedIndexes()` creates one `QModelIndex` per **cell**; selecting a whole column = tens of thousands of objects. `paintEvent` ([view.py:439](../../src/excelapp/view.py#L439)) calls it on **every** repaint; `mouseMoveEvent` during a drag repeatedly triggers `viewport().update()`. → jank when selecting/dragging.
2. **`_update_header_highlight()` also walks the full `selectedIndexes()`** — [view.py:397-408](../../src/excelapp/view.py#L397-L408). Runs on **every** `selectionChanged`/`currentChanged`.
3. **One selection action triggers multiple repaints + recomputes** — [view.py:410-416](../../src/excelapp/view.py#L410-L416). 4 lambda connections; each click emits both `selectionChanged` and `currentChanged`.
4. **`fill()` and `paste_block()` clear the ENTIRE `_eval_cache`** — [table_model.py:800](../../src/excelapp/table_model.py#L800), [table_model.py:727-730](../../src/excelapp/table_model.py#L727-L730). Every formula in the sheet recomputes on the next paint, even unrelated ones. Both also call `_rebuild_deps()`, a full-grid rescan.
5. **`data()` scans conditional rules twice per cell per paint** — [table_model.py:84-95](../../src/excelapp/table_model.py#L84-L95). `BackgroundRole` and `ForegroundRole` both call `_matching_rule()`, even when there are no rules.

### Goals
- Selecting/dragging a large region (e.g. a 100k-cell column) is no longer janky; `_selection_box()` and `_update_header_highlight()` no longer scale linearly with the *number of selected cells*.
- `fill`/`paste` only invalidate the cache of affected cells (changed cells + their dependents), leaving unrelated formulas untouched.
- `data()` incurs no conditional-formatting cost when the sheet has no conditional rules.
- **No user-visible behavior change**: selection box, header highlight, formula values, undo/redo, and conditional formatting all behave exactly as before.

### Out of scope (deferred to a later plan)
- **#6 — `_rebuild_deps()` full-grid rescan** in insert/remove/move row-col and sort: cell indices shift, so a full rebuild is the safest option; keep it. (`fill`/`paste` are optimized here because cell indices don't shift.)
- **#7 — `extract_refs` "expanding" a range into individual cells** ([formula.py:1415-1417](../../src/excelapp/formula.py#L1415-L1417)): storing ranges as boxes is an architectural change to the dependency graph + `_recalculate` BFS; needs its own plan with full regression tests.
- IO/dialog/`_apply_filters` optimization: rarely run, not the bottleneck; untouched.

### Acceptance criteria
- AC1: All existing tests stay green (`python -m pytest tests/`).
- AC2: `tests/test_view_selection.py` green — `_selection_box()` returns the correct bounding box for single cell / range / multiple ranges / full column; and the timing test (large selection) is within threshold (would FAIL on the old code).
- AC3: `tests/test_model_invalidation.py` green — `fill`/`paste` keep the cache of unrelated formulas but drop the cache of dependent formulas; computed values are correct.
- AC4: Manual check: open the app, select+drag a whole column, drag the Fill Handle down a few hundred cells — smooth, no jank; values/formatting correct.

### Risks & mitigations
- **`selection()` returns an empty `QItemSelection`**: check `is None or .isEmpty()` before deriving from `currentIndex()` (preserve the existing fallback branch).
- **Selective invalidation misses a dependent cell** → stale value shown: use the existing `_dependents` graph (BFS) exactly as `_recalculate(changed)` does; covered by AC3.
- **Each change small, committed separately**: easy to `git bisect` on regression.

---

## FILE STRUCTURE

| File | Create/Modify | Responsibility |
|------|---------------|----------------|
| `tests/conftest.py` | **Create** | `qapp` fixture (offscreen QApplication) + inject `src` into `sys.path` for all Qt tests |
| `tests/test_view_selection.py` | **Create** | Tests for bounding box & selection hot-path performance |
| `tests/test_model_invalidation.py` | **Create** | Tests for selective cache invalidation in `fill`/`paste` |
| `src/excelapp/view.py` | Modify | `_selection_box`, `_update_header_highlight`, consolidate signal connections |
| `src/excelapp/table_model.py` | Modify | Add `_recalc_cells`; fix `fill`, `paste_block`; add rule guard in `data()` |

---

## Task 1: Qt test infrastructure (conftest)

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest with an offscreen QApplication fixture**

`tests/conftest.py`:
```python
"""Shared fixtures for Qt tests. ASCII only (Windows console cp1252)."""
import os
import sys
from pathlib import Path

# Must be set before importing PySide6 -> no real display needed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication shared across the test session."""
    app = QApplication.instance() or QApplication([])
    yield app
```

- [ ] **Step 2: Run to confirm existing tests aren't broken by the conftest**

Run: `.venv\Scripts\python -m pytest tests/ -q`
Expected: PASS (same test count as before; conftest only adds a fixture, runs nothing on its own).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add offscreen QApplication fixture for Qt tests"
```

---

## Task 2: `_selection_box()` reads the bounding box from ranges

**Files:**
- Test: `tests/test_view_selection.py`
- Modify: `src/excelapp/view.py:220-229`

- [ ] **Step 1: Write the failing tests (correctness + performance)**

`tests/test_view_selection.py`:
```python
"""Tests for the cell-selection hot path (view.py). ASCII only."""
import time

import pytest

from excelapp.table_model import SpreadsheetModel
from excelapp.view import SpreadsheetView


def _make_view(rows, cols):
    view = SpreadsheetView()
    model = SpreadsheetModel([[""] * cols for _ in range(rows)])
    view.setModel(model)
    return view, model


def test_selection_box_single_cell(qapp):
    view, model = _make_view(10, 5)
    view.setCurrentIndex(model.index(3, 2))
    assert view._selection_box() == (3, 2, 3, 2)


def test_selection_box_rectangular_range(qapp):
    view, model = _make_view(10, 5)
    view.select_box((1, 1, 4, 3))
    assert view._selection_box() == (1, 1, 4, 3)


def test_selection_box_no_selection_returns_none(qapp):
    view, model = _make_view(10, 5)
    view.clearSelection()
    view.selectionModel().clearCurrentIndex()
    assert view._selection_box() is None


def test_selection_box_full_column_is_fast(qapp):
    # 100k-cell column: the old approach (selectedIndexes) builds 100k
    # QModelIndex objects on every call.
    view, model = _make_view(100_000, 5)
    view.select_box((0, 0, 99_999, 0))
    assert view._selection_box() == (0, 0, 99_999, 0)
    start = time.perf_counter()
    for _ in range(50):
        view._selection_box()
    elapsed = time.perf_counter() - start
    # New approach is O(number of ranges) -> very fast. Generous threshold
    # (the old approach would blow well past it).
    assert elapsed < 0.5, f"too slow: {elapsed:.3f}s"
```

- [ ] **Step 2: Run to confirm the test FAILS**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py -v`
Expected: `test_selection_box_full_column_is_fast` FAILS (too slow / over threshold) on the old code; the others may PASS.

- [ ] **Step 3: Replace `_selection_box()` to use ranges**

At [view.py:220-229](../../src/excelapp/view.py#L220-L229), replace the whole method:
```python
    def _selection_box(self) -> tuple[int, int, int, int] | None:
        sm = self.selectionModel()
        sel = sm.selection() if sm is not None else None
        if sel is None or sel.isEmpty():
            idx = self.currentIndex()
            if not idx.isValid():
                return None
            return (idx.row(), idx.column(), idx.row(), idx.column())
        # Bounding box over the selection ranges (O of #ranges), never enumerate cells.
        top = left = None
        bottom = right = -1
        for rng in sel:  # QItemSelectionRange
            t, l, b, r = rng.top(), rng.left(), rng.bottom(), rng.right()
            top = t if top is None else min(top, t)
            left = l if left is None else min(left, l)
            bottom = max(bottom, b)
            right = max(right, r)
        return (top, left, bottom, right)
```

- [ ] **Step 4: Run to confirm PASS**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/view.py tests/test_view_selection.py
git commit -m "perf(view): _selection_box reads bounding-box from ranges (drop selectedIndexes)"
```

---

## Task 3: `_update_header_highlight()` reads from ranges

**Files:**
- Test: `tests/test_view_selection.py` (extend)
- Modify: `src/excelapp/view.py:397-408`

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_view_selection.py`:
```python
def test_header_highlight_full_column(qapp):
    view, model = _make_view(10, 5)
    view.select_box((0, 2, 9, 2))  # select the whole column 2
    view._update_header_highlight()
    assert 2 in view._h_header.selected_cols
    assert view._v_header.selected_rows == set(range(10))


def test_header_highlight_is_fast(qapp):
    view, model = _make_view(100_000, 5)
    view.select_box((0, 0, 99_999, 0))
    start = time.perf_counter()
    for _ in range(20):
        view._update_header_highlight()
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5, f"too slow: {elapsed:.3f}s"
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py::test_header_highlight_is_fast -v`
Expected: FAILS (over threshold) on the old code.

- [ ] **Step 3: Replace `_update_header_highlight()`**

At [view.py:397-408](../../src/excelapp/view.py#L397-L408), replace the whole method:
```python
    def _update_header_highlight(self) -> None:
        """Update the selected column/row sets so headers highlight like Excel."""
        sm = self.selectionModel()
        cols: set[int] = set()
        rows: set[int] = set()
        if sm is not None:
            for rng in sm.selection():  # by range, never enumerate cells
                cols.update(range(rng.left(), rng.right() + 1))
                rows.update(range(rng.top(), rng.bottom() + 1))
        cur = self.currentIndex() if sm is not None else None
        if cur is not None and cur.isValid():
            cols.add(cur.column())
            rows.add(cur.row())
        self._h_header.set_selected_cols(cols)
        self._v_header.set_selected_rows(rows)
```

- [ ] **Step 4: Run to confirm PASS**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/view.py tests/test_view_selection.py
git commit -m "perf(view): _update_header_highlight reads from ranges (drop selectedIndexes)"
```

---

## Task 4: Consolidate & clean up selection signal connections

**Files:**
- Test: `tests/test_view_selection.py` (extend)
- Modify: `src/excelapp/view.py:410-416`

> Goal: replace 4 lambdas with 1 named slot, gathering header update + repaint in one place; no behavior change.

- [ ] **Step 1: Add a behavior test**

Append to `tests/test_view_selection.py`:
```python
def test_selection_change_updates_header(qapp):
    view, model = _make_view(10, 5)
    # Changing the selection -> the slot must refresh header highlight.
    view.select_box((0, 1, 0, 1))
    view._on_selection_state_changed()
    assert 1 in view._h_header.selected_cols
    assert 0 in view._v_header.selected_rows
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py::test_selection_change_updates_header -v`
Expected: FAILS — `AttributeError: 'SpreadsheetView' object has no attribute '_on_selection_state_changed'`.

- [ ] **Step 3: Add the merged slot & update `setSelectionModel`**

At [view.py:410-416](../../src/excelapp/view.py#L410-L416), replace `setSelectionModel` and add the new slot right below it:
```python
    def setSelectionModel(self, model):
        super().setSelectionModel(model)
        if model is not None:
            model.selectionChanged.connect(self._on_selection_state_changed)
            model.currentChanged.connect(self._on_selection_state_changed)

    def _on_selection_state_changed(self, *args) -> None:
        """Refresh header highlight + repaint the selection overlay (single place)."""
        self._update_header_highlight()
        self.viewport().update()
```

- [ ] **Step 4: Re-run the full view test file**

Run: `.venv\Scripts\python -m pytest tests/test_view_selection.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/view.py tests/test_view_selection.py
git commit -m "refactor(view): consolidate selection signal connections into one slot"
```

---

## Task 5: `_recalc_cells()` helper — selective cache invalidation by cell set

**Files:**
- Test: `tests/test_model_invalidation.py`
- Modify: `src/excelapp/table_model.py` (add a method next to `_recalculate`, after line 284)

> `_recalculate(changed)` currently takes a **single** cell. `fill`/`paste` change **many** cells. Extract the shared BFS into `_recalc_cells(cells)` that returns the "dirty" set.

- [ ] **Step 1: Write the failing test**

`tests/test_model_invalidation.py`:
```python
"""Tests for selective cache invalidation (table_model.py). ASCII only."""
import pytest

from excelapp.table_model import SpreadsheetModel


def _model(rows=20, cols=5):
    return SpreadsheetModel([[""] * cols for _ in range(rows)])


def test_recalc_cells_returns_changed_and_dependents():
    m = _model()
    m.setData(m.index(0, 0), "1")        # A1 = 1
    m.setData(m.index(1, 0), "=A1+1")    # A2 = A1+1 depends on A1
    assert m._cell_value(1, 0) == 2
    # Make A1 dirty -> result must include A2 (dependent).
    dirty = m._recalc_cells({(0, 0)})
    assert (0, 0) in dirty
    assert (1, 0) in dirty
    assert (0, 0) not in m._eval_cache
    assert (1, 0) not in m._eval_cache
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py::test_recalc_cells_returns_changed_and_dependents -v`
Expected: FAILS — `AttributeError: ... has no attribute '_recalc_cells'`.

- [ ] **Step 3: Add the `_recalc_cells` method**

Add to `table_model.py` right after `_recalculate` (after [table_model.py:284](../../src/excelapp/table_model.py#L284)):
```python
    def _recalc_cells(self, cells) -> set[tuple[int, int]]:
        """Invalidate the cache for ``cells`` + every dependent (reverse BFS).

        Returns the 'dirty' set whose cache was dropped. Does not emit
        dataChanged (the caller decides which region to repaint).
        """
        dirty: set[tuple[int, int]] = set()
        queue = list(cells)
        while queue:
            cell = queue.pop()
            if cell in dirty:
                continue
            dirty.add(cell)
            for dep in self._dependents.get(cell, ()):
                if dep not in dirty:
                    queue.append(dep)
        for cell in dirty:
            self._eval_cache.pop(cell, None)
        return dirty
```

- [ ] **Step 4: Run to confirm PASS**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/table_model.py tests/test_model_invalidation.py
git commit -m "perf(model): add _recalc_cells (invalidate cache by cell set)"
```

---

## Task 6: `fill()` uses selective invalidation + local dep update

**Files:**
- Test: `tests/test_model_invalidation.py` (extend)
- Modify: `src/excelapp/table_model.py:767-803` (the `fill` method)

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_model_invalidation.py`:
```python
def test_fill_keeps_unrelated_formula_cache():
    m = _model()
    m.setData(m.index(0, 4), "=2*2")     # E1 formula, UNRELATED
    assert m._cell_value(0, 4) == 4
    assert (0, 4) in m._eval_cache
    m.setData(m.index(0, 0), "5")        # A1 = 5
    m.fill((0, 0, 0, 0), (0, 0, 4, 0))   # fill down A1..A5
    # E1's cache (unrelated) must survive.
    assert (0, 4) in m._eval_cache


def test_fill_invalidates_dependent_formula():
    m = _model()
    m.setData(m.index(0, 0), "1")        # A1 = 1
    m.setData(m.index(0, 2), "=A3")      # C1 = A3 (depends on A3)
    m._cell_value(0, 2)
    assert (0, 2) in m._eval_cache
    m.fill((0, 0, 0, 0), (0, 0, 4, 0))   # overwrites A2..A5 (incl. A3)
    # A3 changed -> C1's cache must be dropped.
    assert (0, 2) not in m._eval_cache
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py::test_fill_keeps_unrelated_formula_cache -v`
Expected: FAILS (current `fill` does `_eval_cache.clear()`, dropping E1 too).

- [ ] **Step 3: Edit the tail of `fill()`**

At [table_model.py:797-803](../../src/excelapp/table_model.py#L797-L803), replace from `self._push_undo(changes)` to the end of the method:
```python
        self._push_undo(("cells", changes))

        # Update deps locally for the written cells (no full-grid rebuild).
        for r, c, _old, _new in changes:
            self._update_deps(r, c)
        # Selective invalidation: changed cells + their dependents.
        changed_cells = {(r, c) for r, c, _o, _n in changes}
        dirty = self._recalc_cells(changed_cells)
        # Repaint a bounding box covering the destination + any out-of-range dependents.
        rows_ = [dt, db] + [r for r, _ in dirty]
        cols_ = [dl, dr] + [c for _, c in dirty]
        self.dataChanged.emit(
            self.index(min(rows_), min(cols_)),
            self.index(max(rows_), max(cols_)),
            [Qt.DisplayRole, Qt.EditRole],
        )
```

> Note: `dt, dl, db, dr` already exist at the top of `fill()` (unpacked from `dst`). Remove the old `self._rebuild_deps()` and `self._eval_cache.clear()` lines.

- [ ] **Step 4: Run to confirm PASS (incl. old tests)**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py tests/test_formula.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/table_model.py tests/test_model_invalidation.py
git commit -m "perf(model): fill uses selective invalidation + local dep update"
```

---

## Task 7: `paste_block()` uses selective invalidation (non-grow branch)

**Files:**
- Test: `tests/test_model_invalidation.py` (extend)
- Modify: `src/excelapp/table_model.py:724-735` (tail of `paste_block`)

> Only optimize the branch that does **not** grow the grid (`grew is False`). The `grew` branch already does `beginResetModel`/`endResetModel` (size change), so keeping the full `clear()` there is correct.

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_model_invalidation.py`:
```python
def test_paste_keeps_unrelated_formula_cache():
    m = _model()
    m.setData(m.index(9, 4), "=3+3")     # E10 formula, UNRELATED
    assert m._cell_value(9, 4) == 6
    assert (9, 4) in m._eval_cache
    # Paste a 2x2 block at the top-left (does not grow the grid).
    m.paste_block(0, 0, [["1", "2"], ["3", "4"]])
    assert (9, 4) in m._eval_cache       # E10 survives
    assert m._cell_value(0, 0) == 1      # pasted value correct


def test_paste_invalidates_dependent_formula():
    m = _model()
    m.setData(m.index(5, 0), "=A1")      # A6 = A1
    m._cell_value(5, 0)
    assert (5, 0) in m._eval_cache
    m.paste_block(0, 0, [["9"]])         # writes A1 = 9
    assert (5, 0) not in m._eval_cache   # A1 changed -> A6 loses its cache
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py::test_paste_keeps_unrelated_formula_cache -v`
Expected: FAILS (the non-grow branch currently does `_eval_cache.clear()`).

- [ ] **Step 3: Edit the tail of `paste_block()`**

At [table_model.py:724-735](../../src/excelapp/table_model.py#L724-L735), replace from `self._push_undo(changes)` to the end of the method:
```python
        self._push_undo(("cells", changes))
        if grew:
            # Size changed -> a full rebuild + clear is the safest option.
            self._rebuild_deps()
            self._eval_cache.clear()
            self.endResetModel()
        else:
            # Local dep update + selective cache invalidation.
            for r, c, _old, _new in changes:
                self._update_deps(r, c)
            changed_cells = {(r, c) for r, c, _o, _n in changes}
            dirty = self._recalc_cells(changed_cells)
            rows_ = [top, top + rows - 1] + [r for r, _ in dirty]
            cols_ = [left, left + cols - 1] + [c for _, c in dirty]
            self.dataChanged.emit(
                self.index(min(rows_), min(cols_)),
                self.index(max(rows_), max(cols_)),
                [Qt.DisplayRole, Qt.EditRole],
            )
```

> Note: `rows`, `cols`, `top`, `left` already exist in the method. The `grew` branch keeps `_rebuild_deps()` (size changed).

- [ ] **Step 4: Run to confirm PASS (incl. old tests)**

Run: `.venv\Scripts\python -m pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/table_model.py tests/test_model_invalidation.py
git commit -m "perf(model): paste uses selective invalidation (non-grow branch)"
```

---

## Task 8: `data()` skips conditional rules when the sheet has none

**Files:**
- Test: `tests/test_model_invalidation.py` (extend)
- Modify: `src/excelapp/table_model.py:84-95` (Background/Foreground branches in `data`)

- [ ] **Step 1: Add the tests (count `_matching_rule` calls)**

Append to `tests/test_model_invalidation.py` (put the imports at the top of the file too):
```python
from PySide6.QtCore import Qt  # noqa: E402  (may sit at the top of the file)


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
    from PySide6.QtGui import QColor
    m = _model()
    m.setData(m.index(0, 0), "100")
    m.add_cond_rule({"box": (0, 0, 0, 0), "op": "gt", "v1": 50, "bg": "#FF0000"})
    assert m.data(m.index(0, 0), Qt.BackgroundRole) == QColor("#FF0000")
```

- [ ] **Step 2: Run to confirm FAIL**

Run: `.venv\Scripts\python -m pytest tests/test_model_invalidation.py::test_data_skips_cond_check_when_no_rules -v`
Expected: FAILS (current `data()` always calls `_matching_rule`).

- [ ] **Step 3: Add the `if self._cond_rules` guard**

At [table_model.py:84-95](../../src/excelapp/table_model.py#L84-L95), replace both branches:
```python
        if role == Qt.BackgroundRole:
            if self._cond_rules:
                rule = self._matching_rule(row, col)
                if rule and rule.get("bg"):
                    return QColor(rule["bg"])
            bg = self._fmt.get((row, col), {}).get("bg")
            return QColor(bg) if bg else None
        if role == Qt.ForegroundRole:
            if self._cond_rules:
                rule = self._matching_rule(row, col)
                if rule and rule.get("color"):
                    return QColor(rule["color"])
            color = self._fmt.get((row, col), {}).get("color")
            return QColor(color) if color else None
```

- [ ] **Step 4: Run to confirm PASS**

Run: `.venv\Scripts\python -m pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/excelapp/table_model.py tests/test_model_invalidation.py
git commit -m "perf(model): data skips conditional-rule scan when no rules exist"
```

---

## Task 9: Overall verification + manual check

- [ ] **Step 1: Run the whole test suite**

Run: `.venv\Scripts\python -m pytest tests/ -q`
Expected: all PASS (AC1–AC3).

- [ ] **Step 2: Manual check (AC4)**

Run: `run.bat` (or `.venv\Scripts\python run.py`). Verify:
- Enter some data + a few formulas; select+drag a whole column by clicking the header and dragging — **smooth**, no jank.
- Drag the Fill Handle down a few hundred cells — filled values correct, no lag.
- Enable conditional formatting (color by condition) — still displays correctly.
- Undo/redo after fill/paste — data & formatting correct.

- [ ] **Step 3: (If the user confirms "ok") release per RELEASE.md**

Per repo convention: bump version in two places → `build.bat` → `build_installer.bat` → GitHub Release. (Only when the user agrees.)

---

## PHASE C — Deep-optimization notes (NOT in this plan)

Deferred to a separate plan because they require architectural changes + full regression tests:

- **C1 — Range-based dependency graph, no per-cell expansion** ([formula.py:1387-1429](../../src/excelapp/formula.py#L1387-L1429)): `extract_refs` returns *boxes* `(t,l,b,r)`; `_deps`/`_dependents` store boxes; `_recalc_cells`/BFS test box intersection. Greatly reduces memory & time when large-range formulas exist (`=SUM(A1:A10000)`).
- **C2 — Avoid `_rebuild_deps()` full-grid rescan in insert/remove/move/sort**: requires remapping cell indices in the dep map when structure changes (complex, error-prone); only do it if profiling shows it's a real bottleneck.
- **C3 — Cache `_matching_rule` per (row,col)** with a lifecycle tied to `_eval_cache`: only worth it if a user sets many conditional rules over a large region.

---

## SELF-REVIEW (done)

- **Spec coverage:** Problem #1→Task 2; #2→Task 3; #3→Task 4; #4→Task 6+7 (+helper Task 5); #5→Task 8. #6/#7 explicitly out of scope (Phase C). Complete.
- **Placeholder scan:** No TBD / "appropriate error handling" / "similar to task N"; every step has real code & a run command + expected result.
- **Type consistency:** `_recalc_cells(cells) -> set` (Task 5) is used in Task 6/7 with the correct name, its return value used as `dirty`. `_on_selection_state_changed` (Task 4) matches between definition & connection. `_update_deps` already exists ([table_model.py:233](../../src/excelapp/table_model.py#L233)) — Task 6/7 reuse it with the correct signature.
