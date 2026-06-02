# SPEC 26 — Comments & Notes (Threaded Comments + Legacy Notes)

## Mục tiêu
Hai cơ chế ghi chú cell:
- **Threaded Comments** (modern, có reply, có author): Review → New Comment.
- **Notes** (legacy, plain text, không reply): Review → Notes → New Note. Tương đương "Comment" cũ trước 2019.

## Trạng thái hiện tại
- ✗ Chưa có cả 2.

## 26.1 Threaded Comments

### Truy cập
- Right-click cell → New Comment.
- Review → Comments → New Comment.
- Shift+F2.
- Chèn `@mention` (chỉ có với co-authoring + workbook đã sync OneDrive).

### Visual
- Cell có purple **bubble** ở góc trên phải (khác đỏ của Note).
- Click bubble (hoặc cell + hover) → comment popup hiện.
- Comment pane (Review → Show Comments): list tất cả comments sheet bên phải.

### Comment thread structure
```
Comment 1
  Author: Nguyen A
  Date: 2026-06-02 14:30
  Text: "Số này có đúng không?"
  Replies:
    - Author: Tran B, Date: ..., Text: "Đã verify, đúng"
    - Author: Nguyen A, Text: "OK thanks"
  Resolved: false
```

### Actions
- Edit (chỉ author hoặc admin).
- Delete (xóa toàn thread).
- Reply.
- Resolve (đánh dấu giải quyết — vẫn hiển thị nhưng faded).
- Reopen.
- Link to (copy direct URL — chỉ cloud).

## 26.2 Notes (Legacy)

### Truy cập
- Right-click cell → New Note.
- Review → Notes → New Note.
- Shift+F2 (Excel pre-2019).

### Visual
- Cell có **red triangle** ở góc trên phải.
- Hover cell → note popup yellow sticky-note style.
- Drag để di chuyển popup; resize handle.

### Properties
- Author (User name, mặc định lấy từ Options).
- Plain text (no rich formatting in default popup; right-click → Format Comment cho font/size/color/border/fill).
- Show/Hide: Right-click → Show/Hide Note. Hidden notes vẫn có triangle.

## Convert
- Right-click comment → "Convert to Note" / "Convert to Comment" (Microsoft 365).

## Model

```python
class Comment:
    type: "comment" | "note"
    cell: (row, col)
    author: str
    created_at: datetime
    text: str
    replies: list[Reply]    # comment only
    resolved: bool          # comment only
    show: bool              # note only
    position: (x, y, w, h)  # note popup position
    format: dict            # note formatting

Sheet:
    _comments: dict[(row,col), Comment]
```

## UX flow

1. Right-click cell → New Comment → Modal popup attached to cell, focus textarea.
2. User type + Enter (Ctrl+Enter for newline) → save.
3. Cell hiện bubble; click bubble → popup show.
4. Reply box dưới mỗi comment.
5. Hover Threaded → "Edit / Delete / Resolve / Reply" buttons.

## Status Bar
- Khi cell có comment, Status Bar trái hiện indicator nhỏ + tooltip "Has comment".

## Print options ([Spec 24](24-print-page-setup.md))
- Print comments: At end of sheet (list table sau grid) / As displayed on sheet / None.

## Implementation note

- Comment popup: `QWidget` floating top-level (frameless), parent = MainWindow. Position theo cell global rect.
- Auto-hide khi click ngoài hoặc Esc.
- Render bubble + triangle trong `CellDelegate.paint()` — vẽ 3 pixel góc trên phải.
- Hot path: chỉ paint indicator nếu `_comments.get((r,c))` exists — O(1) dict lookup.
- xlsx: openpyxl `Comment(text, author)`; threaded comments xlsx mới có namespace riêng — `<threadedComment>` trong `xl/threadedComments/*.xml`.

## Acceptance criteria
1. Right-click A1 → New Comment → popup xuất hiện cạnh A1. Gõ "Test", click ngoài → popup hide, A1 có bubble tím.
2. Hover A1 → comment popup hiện text "Test" + author + timestamp.
3. Right-click A1 → "Reply" → thêm reply; thread hiện 2 entries.
4. Mark Resolve → bubble đổi faded; vẫn hover hiện thread.
5. Right-click B2 → New Note → yellow sticky popup; gõ text + click ngoài → B2 có tam giác đỏ.
6. Drag corner Note popup → resize; di chuyển → vị trí new lưu.
7. Save xlsx → open lại → cả Comment thread + Note còn nguyên.

## Phụ thuộc
- [06 Context Menus](06-context-menus.md).
- [11 Status Bar](11-status-bar.md).
- [24 Print](24-print-page-setup.md) — print comments option.

## Risk
Trung bình. Threaded Comments xlsx serialization mới (Microsoft 365); openpyxl chưa hỗ trợ đầy đủ → có thể fallback ghi thành legacy Note khi save.
