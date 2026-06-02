# SPEC 03 — 4 Cell Modes (Ready / Enter / Edit / Point)

## Mục tiêu
Implement đúng state machine 4 mode của Excel. **Đây là gốc rễ của mọi keyboard behavior** — sai mode → sai toàn bộ UX.

## Trạng thái hiện tại
- ✗ Không có mode explicit. QTableView có "edit/no-edit" ngầm, nhưng:
  - Không có Enter mode (gõ vào ô trống tạo formula reference khi nhấn arrow).
  - Không có Point mode (sau `=` trong formula, arrow phải chọn cell ref, không di chuyển cursor).
  - Không có Status Bar indicator cho mode.
- Hệ quả: gõ `=` rồi nhấn ↑ hiện đang **di chuyển active cell** thay vì chèn `A0` vào formula → sai.

## State machine (§3.1)

```
                     ┌─────────────────────────┐
                     │                         │
                     ▼                         │
   ┌───────┐  type   ┌───────┐  F2     ┌──────┐
   │ READY │────────▶│ ENTER │────────▶│ EDIT │
   └───────┘         └───────┘         └──────┘
       ▲                 │  =+-*/         │
       │                 ▼  + arrow       ▼  F2
       │            ┌───────┐         ┌───────┐
       │   commit   │ POINT │◀────────│ POINT │
       │            └───────┘         └───────┘
       │                 │
       └─────────────────┴── Enter/Tab (commit) | Esc (cancel)
```

### Transitions

| From → To | Trigger |
|---|---|
| READY → ENTER | gõ bất kỳ ký tự; hoặc `=`/`+`/`-` để bắt đầu formula |
| READY → EDIT | F2; double-click ô có data; click Formula Bar |
| ENTER → EDIT | F2 |
| ENTER → POINT | sau `=`/`+`/`-`/`*`/`/` → nhấn arrow hoặc click ô khác |
| EDIT → POINT | F2 lần nữa |
| POINT → EDIT | F2; click Formula Bar |
| BẤT KỲ → READY | Esc (hủy thay đổi) |
| BẤT KỲ → READY + commit | Enter / Tab / click ô khác |

## Keyboard behavior trong từng mode (§3.2)

| Phím | Ready | Enter | Edit | Point |
|---|---|---|---|---|
| Arrow ↑↓←→ | Di chuyển active cell | Commit + di chuyển | Di chuyển cursor trong ô | Chọn cell tham chiếu / mở rộng |
| Enter | Xuống 1 ô | Commit + xuống 1 | Commit + xuống 1 | Kết thúc selection ref |
| Tab | Sang phải | Commit + phải | Commit + phải | — |
| Escape | — | Hủy, khôi phục giá trị cũ | Hủy, khôi phục | Hủy ref, về Edit |
| Delete/Backspace | Xóa nội dung ô | Xóa ký tự | Xóa ký tự tại cursor | — |
| F2 | → Edit | → Edit (giữ nội dung) | → Point | → Edit |
| Ctrl+Z | Undo | Undo trong formula | Undo gõ | — |
| Home/End | A1 / cuối row | Đầu/cuối nội dung ô | Đầu/cuối cursor | — |

## Confirm key behavior (§5.1)

| Phím | Sau khi nhập |
|---|---|
| Enter | Xuống 1 ô (default — đổi được trong Options) |
| Shift+Enter | Lên 1 ô |
| Tab | Sang phải |
| Shift+Tab | Sang trái |
| Ctrl+Enter | Xác nhận, **giữ nguyên cell** (đặc biệt: multi-select → fill cùng giá trị) |
| Arrow (Enter mode) | Commit + di chuyển theo hướng |
| Esc | Hủy |

## Implementation note

- Thêm enum `CellMode` (`READY/ENTER/EDIT/POINT`) trong `main_window.py` (hoặc tách `cell_mode.py`).
- Signal `mode_changed(CellMode)` → Status Bar update label.
- Trong Enter mode: bắt key event tại cấp `QTableView.event()`; khi `arrow` mà text bắt đầu bằng `=` hoặc cursor đứng sau operator → chuyển Point mode, insert cell ref vào Formula Bar text.
- Trong Point mode: arrow KHÔNG commit, mà extend reference selection và update text trong Formula Bar.
- Click cell khác trong Enter/Point: insert cell ref + giữ Edit/Enter mode (KHÔNG commit). Click trong Edit: commit + select cell mới.

## Acceptance criteria
1. Gõ `5` vào A1 → Status Bar hiện **Enter**; nhấn ↓ → commit `5` + xuống A2.
2. Gõ `=` vào A1 → Status Bar hiện **Enter**; nhấn ↓ → Status Bar đổi **Point**, Formula Bar hiện `=A2`, viền chấm xanh quanh A2.
3. F2 trên ô có `=SUM(A1)` → Status Bar **Edit**; cursor trong ô; arrow di chuyển cursor trong text, KHÔNG đổi selection.
4. F2 lần nữa trong Edit → Status Bar **Point**; arrow extend reference.
5. Esc bất cứ lúc nào → về Ready, giá trị cũ giữ nguyên.
6. Multi-select A1:B3, gõ `hi` rồi Ctrl+Enter → tất cả 6 ô = `hi`.

## Phụ thuộc
- [11 Status Bar](11-status-bar.md) — cần label "Ready/Enter/Edit/Point".
- [02 Cell System](02-cell-system.md) — reference highlight visual khi Point mode.

## Risk
**Cao.** Phải hook key event cấp thấp; dễ xung đột với behavior mặc định của QTableView/QLineEdit. Cần test offscreen với key event giả lập.
