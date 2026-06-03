"""State machine 4 mode của ô theo Excel (Spec 03): Ready / Enter / Edit / Point.

Module thuần (không phụ thuộc Qt) để kiểm thử headless. Phần Qt (status bar,
hook key/mouse) ở ``main_window.py`` gọi ``transition()`` rồi cập nhật UI.

Bảng chuyển trạng thái bám theo `docs/specs/03-cell-modes.md` §3.1/§3.2:
- READY: chưa sửa; phím mũi tên di chuyển ô.
- ENTER: vừa gõ ký tự/`=` vào ô (nhập mới); Enter/arrow = commit + di chuyển.
- EDIT: sửa nội dung sẵn có (F2 / double-click / focus Formula Bar); arrow di
  chuyển con trỏ trong text.
- POINT: đang soạn công thức và chọn ô làm tham chiếu; arrow chọn/mở rộng ref.

Lưu ý hành vi Esc: một lần Esc ở bất kỳ mode đang-sửa nào (Enter/Edit/Point) hủy
TOÀN BỘ chỉnh sửa và về READY — KHÔNG có bước "Esc hủy mỗi ref rồi giữ formula".
"""

from __future__ import annotations

from enum import Enum


class CellMode(Enum):
    READY = "ready"
    ENTER = "enter"
    EDIT = "edit"
    POINT = "point"


class ModeEvent(Enum):
    TYPE_CHAR = "type_char"            # gõ ký tự thường vào ô trống/đè nội dung
    START_FORMULA = "start_formula"   # gõ `=`/`+`/`-` bắt đầu công thức
    F2 = "f2"                         # phím F2 (toggle Edit/Point)
    DBLCLICK_DATA = "dblclick_data"   # double-click ô (vào Edit)
    FOCUS_FORMULA_BAR = "focus_formula_bar"  # click/focus thanh công thức
    PICK_REF = "pick_ref"             # đang soạn formula, chọn 1 ô làm tham chiếu
    TYPE_NON_OP = "type_non_op"       # trong POINT gõ ký tự thường -> quay lại nhập
    COMMIT = "commit"                 # Enter / Tab / click ô khác (xác nhận)
    CANCEL = "cancel"                 # Esc (hủy)


# current mode -> { event -> next mode }. Sự kiện không có trong bảng = giữ nguyên.
_TABLE: dict[CellMode, dict[ModeEvent, CellMode]] = {
    CellMode.READY: {
        ModeEvent.TYPE_CHAR: CellMode.ENTER,
        ModeEvent.START_FORMULA: CellMode.ENTER,
        ModeEvent.F2: CellMode.EDIT,
        ModeEvent.DBLCLICK_DATA: CellMode.EDIT,
        ModeEvent.FOCUS_FORMULA_BAR: CellMode.EDIT,
    },
    CellMode.ENTER: {
        ModeEvent.F2: CellMode.EDIT,
        ModeEvent.PICK_REF: CellMode.POINT,
        ModeEvent.COMMIT: CellMode.READY,
        ModeEvent.CANCEL: CellMode.READY,
    },
    CellMode.EDIT: {
        ModeEvent.F2: CellMode.POINT,
        ModeEvent.PICK_REF: CellMode.POINT,
        ModeEvent.COMMIT: CellMode.READY,
        ModeEvent.CANCEL: CellMode.READY,
    },
    CellMode.POINT: {
        ModeEvent.F2: CellMode.EDIT,
        ModeEvent.TYPE_NON_OP: CellMode.EDIT,
        ModeEvent.PICK_REF: CellMode.POINT,   # tiếp tục chọn ref khác
        ModeEvent.COMMIT: CellMode.READY,
        ModeEvent.CANCEL: CellMode.READY,
    },
}


def transition(current: CellMode, event: ModeEvent) -> CellMode:
    """Trả về mode kế tiếp theo bảng Spec 03.

    Sự kiện không hợp lệ ở mode hiện tại -> giữ nguyên mode (no-op an toàn,
    để hook Qt không cần biết trước event nào hợp lệ ở đâu).
    """
    return _TABLE.get(current, {}).get(event, current)
