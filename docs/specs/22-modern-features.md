# SPEC 22 — Tính năng mới Excel 2024-2025

## Mục tiêu
Bù các tính năng mới Excel 365: Checkbox in cell, Regex functions, Focus Cell, TRIMRANGE, Navigation highlighting, Translate, Modernized Grid features. (Copilot / Python in Excel: chỉ khái niệm, không implement full.)

## Trạng thái hiện tại
- ✗ Toàn bộ chưa có.

## 22.1 Checkbox trong ô (§22.1)

- Insert → Checkbox (hoặc nút trong Home tab).
- Giá trị: `TRUE` checked / `FALSE` unchecked.
- Toggle: click ô → checkbox toggle; Space key khi ô selected cũng toggle.
- Dùng trong formula: `=IF(A1, "Done", "Pending")`, `=COUNTIF(A1:A10, TRUE)`.
- Format: màu checkbox đổi qua Format Cells → Font Color.
- Khác Form Control Checkbox cũ: **cell-native**, không phải floating object.

### Implementation
- `_fmt[(r,c)]["checkbox"] = True` → render checkbox icon trong cell (vẽ trong delegate).
- Data: `TRUE` / `FALSE` string trong `_data`.
- Click delegate: detect click vào checkbox area → toggle.
- Space key listener khi mode = Ready, cell có checkbox → toggle.

## 22.2 Regex Functions (§22.2)

| Hàm | Cú pháp | Mô tả |
|---|---|---|
| REGEXTEST | `=REGEXTEST(text, pattern, [case_sensitive])` | TRUE nếu match |
| REGEXEXTRACT | `=REGEXEXTRACT(text, pattern, [instance_num], [case_sensitive])` | Trích xuất chuỗi match |
| REGEXREPLACE | `=REGEXREPLACE(text, pattern, replacement, [instance_num], [case_sensitive])` | Thay thế match |

### Examples
- `=REGEXEXTRACT(A1, "\d{3,4}")` → lấy số 3-4 chữ số đầu tiên.
- `=REGEXTEST(A1, "^[\w.]+@[\w]+\.[\w]{2,}$")` → validate email.
- `=REGEXREPLACE(A1, "\d", "*")` → mask số.

### Implementation
- Add 3 hàm vào `formula._FUNCTIONS`, dùng `re` của Python.
- `case_sensitive` default TRUE; FALSE → flag `re.IGNORECASE`.

## 22.3 Python in Excel (§22.3) — concept only

- `=PY(` trong cell → cell vào Python mode (viền xanh lá; icon 🐍).
- Có sẵn: pandas, numpy, matplotlib, sklearn, seaborn.
- Reference Excel data: `xl("A1:C10", headers=True)` → pandas DataFrame.
- Output modes: Python object (hiển thị trong cell) hoặc Excel value (số/text).
- Ctrl+Alt+Shift+M: đổi output type.

> Implementation phức tạp — gắn liền với macro/Python runtime ([Spec 21](21-vba-macro.md)). Phase rất sau.

## 22.4 Copilot trong Excel (§22.4) — concept only

- Yêu cầu API key LLM (Anthropic / OpenAI). Optional dependency.
- Mở: Home → AI Assist button → chat pane phải.
- Prompts: "Highlight sales > 1M", "Add a column for profit margin", "Create a PivotTable showing sales by region".
- Engine: LLM-based, tool calling vào internal API (similar to macro API).

> Phase rất sau. Architectural placeholder bây giờ: nút disabled với tooltip "Coming soon".

## 22.5 Focus Cell (§22.5)

- View → Focus Cell toggle.
- Highlight hàng + cột của active cell bằng màu nhạt.
- Không ảnh hưởng print.
- Setting lưu QSettings.

### Implementation
- Khi bật + active cell đổi: invalidate hàng + cột của active.
- Delegate paint: nếu cell ở cùng hàng hoặc cột với active → blend màu highlight.
- **Hot path** — cần invalidate diện rộng (1 hàng + 1 cột), nhưng chỉ vùng visible nên OK.

## 22.6 TRIMRANGE Function (§22.6)

`=TRIMRANGE(range, [trim_rows], [trim_cols])`

- Loại bỏ hàng/cột trống ở các cạnh của range.
- `trim_rows`: 0=none, 1=trailing, 2=leading, 3=both.
- `trim_cols`: 0=none, 1=trailing, 2=leading, 3=both.
- Thường kết hợp `SORT`, `FILTER`: `=SORT(TRIMRANGE(A1:Z1000))`.

### Implementation
- Add vào `formula._FUNCTIONS`.
- Return type: range (cần dynamic array — Phase 6 [Spec 12](12-formula-system.md)).

## 22.7 Navigation Highlighting (§22.7)

- Khi scroll hoặc navigate, brief highlight row/col header của active cell (~500ms fade).
- Giúp không bị mất vị trí khi scroll nhanh.

### Implementation
- Animation: `QPropertyAnimation` opacity trên row/col header item.
- Trigger: `currentChanged` signal.

## 22.8 Translate & Detect Language (§22.8)

| Hàm | Cú pháp |
|---|---|
| TRANSLATE | `=TRANSLATE(text, [source_lang], [target_lang])` |
| DETECTLANGUAGE | `=DETECTLANGUAGE(text)` → mã ngôn ngữ (`vi`, `en`) |

### Implementation
- Cần internet + API (Google Translate / DeepL / Anthropic). Optional dependency.
- Nếu offline → `#N/A`.
- Cache theo `(text, source, target)` để giảm call.

## 22.9 Modernized Grid (§22.9) — Web Excel only

- `+` button khi hover header để add row/col.
- Filter Comments theo trạng thái / author / date.

> Ezcel là desktop — feature này map sang:
> - Hover row/col header → button `+` xuất hiện ở edge (Insert).

## Acceptance criteria
1. Insert → Checkbox vào A1 → ô có checkbox; click toggle TRUE/FALSE; Space cũng toggle.
2. `=COUNTIF(A1:A10, TRUE)` đếm số ô checked đúng.
3. `=REGEXEXTRACT("abc123def", "\d+")` → `123`.
4. View → Focus Cell bật → click D5 → hàng 5 + cột D có background nhạt.
5. Scroll xa cell D5 rồi quay lại → khi D5 visible, row header 5 + col header D flash highlight 500ms.
6. `=TRIMRANGE(A1:Z1000)` → range thực sự không có trailing empty rows/cols.
7. `=TRANSLATE("Xin chào", "vi", "en")` → `"Hello"` (cần API key).

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — register REGEX/TRIMRANGE/TRANSLATE.
- [21 VBA / Macro](21-vba-macro.md) — Python in Excel + Copilot tool calling.
- [11 Status Bar](11-status-bar.md) — View Focus Cell toggle.

## Risk
- Checkbox cell-native cần thay đổi delegate hit-testing.
- Focus Cell + Navigation highlight: animation trên hot path; cẩn thận frame drop.
- TRANSLATE: external API → cần fallback graceful khi offline.
