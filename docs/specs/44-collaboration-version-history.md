# SPEC 44 — Co-authoring / Version History / Track Changes / Share

## Mục tiêu
Real-time collaboration (multi-user edit), Version History (timeline restore), Share (link + permissions). Track Changes legacy chỉ giữ làm reference.

## Trạng thái hiện tại
- ✗ Chưa có toàn bộ.

## 44.1 Co-authoring (Real-time multi-user)

### Excel 365 behavior
- File trên OneDrive/SharePoint → multiple users edit cùng lúc.
- Mỗi user có **presence indicator** (avatar + flag colored ở cell selection).
- Edits **broadcast real-time** sang user khác.
- Conflict resolution: OT (Operational Transform) hoặc CRDT.
- Cursor sharing: thấy selection của user khác.

### Excel 365 features
- Status Bar hiển thị danh sách user đang xem/edit.
- Click avatar → jump đến cell user đó đang select.
- Chat pane (in Excel for Web) cho team discussion.

## 44.2 Ezcel approach

**Phase rất muộn / Out of scope MVP.** Requires:
- Backend server (sync, auth, conflict resolution).
- Cell-level diff protocol over WebSocket.
- CRDT or OT algorithm.

### Possible incremental approach
1. **Phase A: Local diff format**. Save diff log thay vì full file → smaller commits, support undo across sessions.
2. **Phase B: Git-based**. Workbook = folder of sheet xlsx + commit diffs. User dùng git merge thủ công.
3. **Phase C: Backend sync**. Real-time server (Phase rất xa).

## 44.3 Version History

### Excel 365: File → Info → Version History
- Pane hiển thị danh sách versions (timestamp + user).
- Click version → mở read-only preview.
- "Restore" button → revert workbook về version đó.

### Ezcel implementation
- **Phase 5+**. Khả thi mà không cần backend.
- Mỗi save → tạo snapshot `{filename}_v{N}_{timestamp}.xlsx.bak` trong `.ezcel-history/` folder cạnh file.
- Cleanup policy: keep last 50 versions, hoặc theo time (last 30 days).
- UI pane: File → Info → Version History → list snapshots → preview / restore.

## 44.4 Track Changes (Legacy)

Excel 2013 trước có Track Changes (Review → Track Changes). Excel 2016+ **removed** (replaced by co-authoring + Version History).

### Behavior (legacy)
- Bật → mọi edit lưu vào "change log".
- Highlight cells bị thay đổi với border + comment "User X changed B5 from 10 to 20 on 2026-06-02".
- Accept / Reject Changes dialog.

### Ezcel approach
**Out of scope.** Modern Excel bỏ.

## 44.5 Share (File → Share)

### Excel 365
- "Share" button góc trên phải.
- Send link to: People / Group.
- Permission: Can edit / Can view / Can review.
- "Anyone with the link" / "People in your organization" / "Specific people".
- Expiration date.
- Password.
- Block download.

### Ezcel
**Out of scope** without backend. Stub button → "Share is not available in standalone mode" dialog.

Alternative: "Save to OneDrive" hyperlink (đưa user ra ngoài app).

## 44.6 Comments (Threaded — modern collaboration)

Xem [Spec 26 Comments](26-comments-notes.md). Comment thread + @mention là collaboration primitive cơ bản.

### Without backend
- Comments lưu trong workbook xlsx.
- Author = current Windows user (Settings → User Name).
- Open file → comments của user khác hiển thị.

## Acceptance criteria

### Version History (Phase 5+)
1. File → Info → Version History → pane hiển thị 5 snapshots gần nhất (Ezcel auto-save).
2. Click snapshot → mở read-only preview window.
3. "Restore this version" → workbook revert; old version snapshot trước restore.

### Co-authoring
- N/A trừ khi có backend.

### Track Changes
- N/A — không implement (legacy).

## Phụ thuộc
- [36 File Formats / AutoSave](36-file-formats-autosave.md) — AutoSave + AutoRecover infrastructure overlap.
- [26 Comments & Notes](26-comments-notes.md) — threaded comments với author info.

## Risk
- Real-time co-authoring: backend phức tạp → out of scope MVP.
- Version History local: dễ làm; chỉ cần disk space cho snapshots.

## Phase
- Version History: Phase 5+.
- Co-authoring / Share: out of scope.
- Track Changes legacy: out of scope (bỏ theo modern Excel).
