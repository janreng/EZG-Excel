# NIGHT NOTES — phiên làm đêm 2026-06-02 (v0.11.3)

Ghi chú cho sếp đọc sáng. Tóm tắt việc đã làm, quyết định tự ra, và những thứ
cần sếp để mắt.

---

## ✅ Đã làm — v0.11.3 "Mở rộng thư viện hàm + taxonomy lỗi"

- Thêm **~60 hàm Excel** (tổng ~120): Information (IS*), Logical (XOR/IFNA/
  SWITCH), Text (TEXTJOIN/EXACT/CHAR/CODE/CLEAN/T/FIXED), Lookup (XLOOKUP/
  CHOOSE), Math+Trig, Stats (AVERAGEIFS/MAXIFS/MINIFS/STDEVP/VARP/GEOMEAN...),
  Date (EDATE/EOMONTH/TIME/WEEKNUM...). Chi tiết: `CHANGELOG.md`,
  `docs/release-notes-v0.11.3.md`.
- **Mã lỗi kiểu Excel** (`#DIV/0! #N/A #VALUE! #NUM! #NAME? #REF!`) thay cho
  `#LỖI!` chung chung. `table_model.py` hiển thị `FormulaError.etype`.
- **Test**: `tests/test_formula_v0113.py` — **74/74 pass** (gồm test chống treo).
- **Build**: `dist\Ezcel\Ezcel.exe` build OK (PyInstaller onedir, 6.2 MB).

## 🔎 Đội agent review (5 agent: correctness×2, performance, adversarial, spec)
36 finding. Đã **fix toàn bộ critical/high + medium quan trọng**:

- **CRASH (đã vá)** — trước đây ném exception Python lọt qua `_cell_value` làm
  treo recalc, nay trả mã lỗi:
  - `*IFS` vùng lệch kích thước → `#VALUE!` (lỗi này **có sẵn từ trước** ở
    COUNTIFS/SUMIFS, không chỉ hàm mới).
  - `inf/NaN` (vd `VALUE("inf")`), số quá lớn (`FACT(171)`, `POWER(10,1000)`,
    tổng tràn), `UNICHAR` ngoài phạm vi, ngày ngoài `1..9999` → `#NUM!`/`#VALUE!`.
  - `CHOOSE` trả vùng → không còn hiện rác `<_Range object>`.
- **Bug tự phát hiện trước review**: tokenizer nuốt `ATAN2`/`LOG10` thành tham
  chiếu ô; VLOOKUP/HLOOKUP miss trả sai mã lỗi.
- **Performance** (đúng cái sếp dặn): tiêu chí `*IF/*IFS` giờ **biên dịch 1 lần**
  (`_compile_criteria`) thay vì parse lại mỗi ô → **~3.8× nhanh hơn** trên 100k
  ô (291ms → 77ms). Wildcard (`* ? ~`) khớp đúng Excel (bỏ fnmatch `[...]`).
  Agent có research web (nguồn ghi trong commit/review): CPython genexpr/zip
  bytecode opt, benchmarking-spreadsheets literature.

## 🧭 Quyết định tự ra (vì sếp bảo "tự quyết, đừng hỏi")

1. **Scope = mở rộng hàm formula**, không đụng UI/model → an toàn ship cho user
   qua auto-update. Coi đây là **1 tính năng cohesive = 1 release v0.11.3**
   (KHÔNG gom thêm feature khác). Feature sau (multi-sheet, Format Cells...) sẽ
   tách release riêng như sếp dặn. Nếu sếp muốn tách nhỏ hơn (mỗi nhóm hàm 1
   bản) → nói em làm lại.
2. **Release để PRERELEASE** trên GitHub. Lý do: GitHub `/releases/latest`
   (mà `updater.py` gọi) **BỎ QUA prerelease** → user đang dùng vẫn ở 0.11.2,
   KHÔNG bị auto-update bản chưa người duyệt. Sáng sếp test xong, vào GitHub
   Releases → bỏ tick "pre-release" (set là Latest) là user mới nhận.
3. **Đính chính**: lúc đầu em báo nhầm "thiếu hàm IF" — thực ra IF/IFERROR/IFS
   có sẵn ở dict `_LAZY_FUNCTIONS`, em đếm sót. Đã sửa nhận định.

## ⚠️ Blocker / hạn chế cần sếp biết

- **Inno Setup CHƯA cài trên máy** → KHÔNG build được installer
  `Ezcel-Setup-0.11.3.exe`. Release đính kèm bản **portable .zip** (onedir) thay
  thế. Auto-update của user cần file installer `.exe` → muốn user update được
  qua nút "Kiểm tra cập nhật", sếp cần: cài Inno Setup → `build_installer.bat`
  → upload `.exe` vào release → bỏ prerelease. (Em để prerelease nên chưa ảnh
  hưởng ai.)
- **`.env` chứa PAT**: token sếp dán lên Discord coi như **đã lộ** → vào GitHub
  Settings revoke + tạo token mới. `.env` đã được `.gitignore` (KHÔNG commit).
- **Exe build OK nhưng chưa smoke-test GUI** (chỉ test source bằng pytest). Khả
  năng cao chạy ổn vì code y hệt, nhưng sếp mở thử `dist\Ezcel\Ezcel.exe` cho
  chắc.

## 📌 Nợ kỹ thuật / đề xuất (CHƯA làm — để release sau, tránh gom)

- **`table_model.data()` đánh giá rule định dạng có điều kiện 2 lần/ô** mỗi lần
  repaint (Background + Foreground role). Agent perf đề xuất cache 1-slot. Em
  KHÔNG sửa lần này vì ngoài phạm vi feature formula + đụng hot-path render
  (rủi ro, cần test kỹ). → nên làm 1 release perf riêng.
- **Scientific notation chưa hỗ trợ**: gõ `=1E300` parse lỗi (tokenizer chưa có
  exponent). Nên thêm vào NUMBER regex (release nhỏ riêng).
- **`ROUND` dùng banker's rounding** (Python `round`), Excel làm nửa-ra-xa-0.
  Hàm mới `MROUND` đã đúng; `ROUND` cũ còn lệch ở ca .5 — chưa sửa vì sợ đổi
  hành vi bản cũ, nên tách riêng + test.
- **Metadata cho Function Wizard (Phase 4)**: ~120 hàm chưa có metadata
  (category/args/description). Spec đã ghi chú nợ này (`docs/specs/12-...md`).
- **Spec docs**: đã cập nhật `12-formula-system.md` (mã lỗi + acceptance criteria
  mục A cho phần đã ship + đánh dấu out-of-scope). Các spec khác (01–51) chưa rà.

## 🚀 Cách phát hành chính thức (khi sếp duyệt)
1. Mở `dist\Ezcel\Ezcel.exe` kiểm tra nhanh vài công thức mới.
2. Cài Inno Setup → chạy `build_installer.bat` → ra `installer\Ezcel-Setup-0.11.3.exe`.
3. Vào GitHub release `v0.11.3`: upload file installer `.exe`, **bỏ tick
   pre-release** (đặt là Latest).
4. User bấm Trợ giúp → Kiểm tra cập nhật → lên 0.11.3.
