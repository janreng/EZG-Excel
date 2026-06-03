"""Unit test cho state machine 4 cell modes (cell_mode.transition).

ASCII-only. Chay: python -m pytest tests/
Doi chieu bang chuyen trang thai Spec 03 (docs/specs/03-cell-modes.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from excelapp.cell_mode import CellMode, ModeEvent, transition  # noqa: E402

R = CellMode.READY
EN = CellMode.ENTER
ED = CellMode.EDIT
PT = CellMode.POINT


# ---------------------------------------------------------------- tu READY
def test_ready_type_char_to_enter():
    assert transition(R, ModeEvent.TYPE_CHAR) == EN


def test_ready_start_formula_to_enter():
    assert transition(R, ModeEvent.START_FORMULA) == EN


def test_ready_f2_to_edit():
    assert transition(R, ModeEvent.F2) == ED


def test_ready_dblclick_to_edit():
    assert transition(R, ModeEvent.DBLCLICK_DATA) == ED


def test_ready_focus_formula_bar_to_edit():
    assert transition(R, ModeEvent.FOCUS_FORMULA_BAR) == ED


def test_ready_ignores_commit_cancel():
    # Khong dang sua thi commit/cancel khong lam gi
    assert transition(R, ModeEvent.COMMIT) == R
    assert transition(R, ModeEvent.CANCEL) == R
    assert transition(R, ModeEvent.PICK_REF) == R


# ---------------------------------------------------------------- tu ENTER
def test_enter_f2_to_edit():
    assert transition(EN, ModeEvent.F2) == ED


def test_enter_pick_ref_to_point():
    assert transition(EN, ModeEvent.PICK_REF) == PT


def test_enter_commit_and_cancel_to_ready():
    assert transition(EN, ModeEvent.COMMIT) == R
    assert transition(EN, ModeEvent.CANCEL) == R


# ---------------------------------------------------------------- tu EDIT
def test_edit_f2_to_point():
    assert transition(ED, ModeEvent.F2) == PT


def test_edit_pick_ref_to_point():
    assert transition(ED, ModeEvent.PICK_REF) == PT


def test_edit_commit_and_cancel_to_ready():
    assert transition(ED, ModeEvent.COMMIT) == R
    assert transition(ED, ModeEvent.CANCEL) == R


# ---------------------------------------------------------------- tu POINT
def test_point_f2_to_edit():
    assert transition(PT, ModeEvent.F2) == ED


def test_point_type_non_op_to_edit():
    assert transition(PT, ModeEvent.TYPE_NON_OP) == ED


def test_point_pick_ref_stays_point():
    assert transition(PT, ModeEvent.PICK_REF) == PT


def test_point_commit_and_cancel_to_ready():
    # Mot lan Esc (CANCEL) o POINT -> thang ve READY (khong co buoc trung gian)
    assert transition(PT, ModeEvent.CANCEL) == R
    assert transition(PT, ModeEvent.COMMIT) == R


# ---------------------------------------------------------------- bat bien
def test_invalid_event_keeps_mode():
    # Su kien khong hop le o mode hien tai -> giu nguyen
    assert transition(R, ModeEvent.TYPE_NON_OP) == R
    assert transition(EN, ModeEvent.DBLCLICK_DATA) == EN
    assert transition(ED, ModeEvent.START_FORMULA) == ED


def test_full_formula_journey():
    # READY -go "="-> ENTER -pick A2-> POINT -pick A3-> POINT -commit-> READY
    m = R
    m = transition(m, ModeEvent.START_FORMULA); assert m == EN
    m = transition(m, ModeEvent.PICK_REF);      assert m == PT
    m = transition(m, ModeEvent.PICK_REF);      assert m == PT
    m = transition(m, ModeEvent.COMMIT);        assert m == R


def test_f2_cycle_edit_point_edit():
    # F2 tren o co data: READY->EDIT->POINT->EDIT
    m = transition(R, ModeEvent.F2);  assert m == ED
    m = transition(m, ModeEvent.F2);  assert m == PT
    m = transition(m, ModeEvent.F2);  assert m == ED
