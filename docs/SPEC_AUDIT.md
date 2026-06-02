# SPEC AUDIT — rà soát 51 spec (2026-06-02)

Kết quả quét toàn bộ `docs/specs/` (01–51 + PLAN + README) bằng 6 agent song song.
**114 finding** (12 high, phần còn lại medium/low). Spec mô tả tính năng CHƯA build
(Phase 2–7) nên đây là nợ cần trả KHI build từng phase — dùng file này làm checklist.

Trạng thái xử lý:
- ✅ Đã fix: mâu thuẫn điều phối (PLAN.md số hàm + Phase trùng + bảng trạng thái;
  README số file); spec 12 (đã cập nhật ở release v0.12.0); spec 35 serial DATE.
- ⏳ Chưa fix (chờ làm khi build phase tương ứng, hoặc theo yêu cầu): các finding
  nội dung từng spec bên dưới.

## 12 finding HIGH (ưu tiên)

| Spec | Vấn đề | Fix |
|---|---|---|
| 02-cell-system | AC#3 "Count cột rỗng = 1048576" sai — Excel chỉ đếm ô non-empty, cột rỗng không hiện Count | AC: cột rỗng → không hiện Count; có N ô data → Count=N |
| 09-row-col | "Unhide Col: Ctrl+Shift+0" — Windows tắt phím này mặc định | Ghi phương án chính: right-click → Unhide / Home→Format→Unhide |
| 12-formula | ~120 hàm (spec) vs ~60 (PLAN) mâu thuẫn | ✅ đã đồng bộ PLAN → ~120 |
| 23-keyboard | Ctrl+F4 ghi "Close Excel app" sai (đó là đóng workbook; Alt+F4 mới đóng app) | Sửa Ctrl+F4 = close workbook; thêm Alt+F4 = close app |
| 28-what-if | AC#4 Data Table địa chỉ ô mâu thuẫn (B1:B6 vs B11:B16 vs A10:B16) | Chuẩn hóa 1 dải ô nhất quán, formula góc trên-phải block |
| 29-protection | Password hashing ghi SHA-1 legacy | Dùng agile SHA-512 + salt + spinCount=100000 (Excel hiện đại); AES mặc định 128 |
| 30-themes | Danh sách theme là Excel 2007-2013, lỗi thời | Thay bằng theme set M365 (Office/Facet/Integral/Ion/...) hoặc tham chiếu runtime |
| 35-calc-engine | AC#6 "DATE(2026,6,2) → 46155" SAI (đúng 46175) | ✅ đã sửa thành 46175 |
| 38-linked-data | Liệt kê Wolfram data types (Movies/Books/...) đã bị gỡ 06/2023 | Chỉ còn Stocks/Currencies/Geography (+Organization/Power Query); ghi chú Wolfram EOL |
| 39-copilot | Bịa API: COPILOT() có tham số model "sonnet/opus/gpt-4o" | Excel COPILOT() không chọn model; việc chọn Anthropic/OpenAI là thiết kế RIÊNG Ezcel |
| 43-office-scripts | Premise sai "Office Scripts chỉ chạy web" | Thực ra chạy cả desktop Win/Mac (2022+); chỉ Action Recorder web-only |
| 46-3d-maps | Mô tả 3D Maps như "Modern Excel" | Microsoft đã KHAI TỬ 3D Maps khỏi 365 (2024-2025) — đánh dấu LEGACY/RETIRED |
| 50-design-system | AC5 "cell font Segoe UI" mâu thuẫn §50.2 "Aptos Narrow" | Cell content = Aptos Narrow 11pt; UI font = Segoe UI |
| README (specs) | "40 files" nhưng thực 51 | ✅ đã sửa 51 |
| PLAN.md | 2 heading "Phase 5" trùng; bảng trạng thái dừng ở spec 23 dù có 51 spec | ✅ đã dọn |

## Tóm tắt theo nhóm (từ 6 agent)

**01–09:** cấu trúc tốt; nặng nhất spec 02 (Count) & 09 (Ctrl+Shift+0). Cần tinh chỉnh:
03 (state machine ASCII lệch bảng, Esc ở Point mode mô tả sai), 07 (QAT/KeyTips Alt+số
mô tả sai, "Ideas"→"Analyze Data"), 06 (Paste Options thiếu mục, Mini Toolbar 2s sai),
08 (custom format thiếu token @ ? * và 4-section).

**10–18:** spec 12 vs PLAN số hàm; 15-filter-sort còn "cần verify" (chưa chốt); 13 (Office
Clipboard Ctrl+C 2 lần là legacy), 14 (Freeze/Split loại trừ nhau — Risk ghi ngược),
17 (CF màu cố định thay vì preset dialog), 16 (AutoFilter table tắt riêng được).

**19–27:** 23 (nhiều phím sai), 22 (REGEXEXTRACT sai chữ ký return_mode; TRANSLATE
dùng Microsoft Translator không cần API key; Checkbox ở Insert tab không phải Home),
25 ("225"→255), 21 (tách Python-in-Excel cloud vs Python-macro Ezcel). 27 sạch nhất.

**28–36:** 35 serial DATE sai (✅), 30 themes lỗi thời, 29 hashing SHA-1, 28 Data Table
mâu thuẫn ô, 36 AutoSave/AutoRecover lẫn lộn + lệch phase PLAN. 34-shapes sạch.

**37–45:** 43 (premise Office Scripts sai), 38 (Wolfram types đã gỡ; Refinitiv→LSEG),
39 (bịa API COPILOT model). 40, 42 ổn. 41, 45 lỗi nhỏ thuật ngữ.

**46–51:** 46 (3D Maps đã khai tử), 50 (font cell mâu thuẫn), điều phối PLAN/README.
47 (Linked Picture không ở Paste Special dialog), 51 (Backstage thừa "Save as Adobe PDF"),
49 ("Phases" + "4 levels" sai). 48 gần ổn.

> Danh sách finding đầy đủ (114, kèm medium/low + fix từng cái): xem transcript workflow
> spec-audit `wf_1ee1c15a-41d` hoặc chạy lại workflow `ezcel-spec-audit`.
