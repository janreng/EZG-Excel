# SPEC 39 — Copilot trong Excel (Pane, COPILOT function, Agent Mode, Formula Completion)

## Mục tiêu
AI assistant tích hợp sâu vào Excel theo cập nhật 2024-2025: side pane chat, in-formula `=COPILOT(...)`, Agent Mode (multi-step), Formula Completion AI suggest khi gõ `=`.

## Trạng thái hiện tại
- ✗ Chưa có.

## 39.1 Copilot Pane (Home → Copilot button)

### UI
- Pane bên phải màn hình (như Field List PivotTable).
- Chat conversation panel.
- Input textbox + Send button + Voice button (Windows).
- Suggested prompts chips trên cùng:
  - "Show insights about my data"
  - "Highlight rows where Sales > 1000"
  - "Add a column with profit margin"
  - "Create a PivotTable showing sales by region"
  - "Summarize this data"
  - "Forecast next quarter"

### Capabilities (single-action)
- Apply Conditional Formatting via natural language.
- Add calculated column.
- Sort/Filter.
- Create chart.
- Create PivotTable.
- Insight generation (trend analysis, anomaly detection).
- Cell-level Q&A: "What's the average?"

### UX flow
1. User: "Highlight rows where Sales > 1000 in red"
2. Copilot:
   - Identifies range
   - Proposes action (preview)
   - User: Apply / Modify / Discard
3. Apply → actually executes via internal API + adds to undo stack.

## 39.2 COPILOT Function (2025)

`=COPILOT(prompt, [context_range], [model])` — LLM directly in formula:

### Examples
- `=COPILOT("Translate to English: " & A1)` — translate cell A1.
- `=COPILOT("Sentiment of: " & A1, , "haiku")` — classify sentiment.
- `=COPILOT("Summarize this paragraph", A1:A10)` — summarize multi-cell.
- `=COPILOT("Extract phone number: " & A1)` — entity extraction.

### Properties
- Async: cell hiện `#LOADING` while waiting; auto-update khi response.
- Cache: same prompt → cached response (giảm cost).
- Cost meter: Status Bar hiển thị token usage.
- Rate limit handling.

### Model parameter
- `"sonnet"` / `"haiku"` / `"opus"` (Anthropic models) — 2025 Excel có option Claude.
- `"gpt-4o"` / `"gpt-4o-mini"` (OpenAI default).
- Default lấy từ Settings.

## 39.3 Agent Mode (2025-2026)

**Update T1/2026:** Agent Mode **generally available** trên Excel Windows + Excel for Web (Dec 2025) + Excel Mac (rollout T1/2026). Excel for Web có full Power Query experience tích hợp với Agent.

**Dec 2025 update:** Copilot Chat khả dụng trong **modern workbooks lưu local** (không cần OneDrive).

Multi-step autonomous task — Copilot lập kế hoạch + thực thi nhiều action liên tiếp.

### Trigger
- Copilot pane → switch tab "Agent".
- Hoặc dropdown trên pane: ⚡ Agent.

### Example task
User: "Create a sales analysis dashboard from this data"

Agent plan (hiển thị step list):
1. Read source data range.
2. Create PivotTable summarizing by Product × Region.
3. Insert Line Chart for trend over time.
4. Add Conditional Formatting to highlight top performers.
5. Create summary text box with insights.

User: Approve plan → execute step-by-step (animation cell highlight) → done with summary.

### Web search trong Agent (2025)
- Agent có thể `web_search("Q3 2025 industry benchmarks")` → kéo vào sheet.
- Trust source labels.

## 39.4 Formula Completion với Copilot

Khi user gõ `=`, AI suggest hoàn chỉnh formula dựa workbook context.

### UX
- Gõ `=` → ghost text mờ hiện trong cell:
  - Cell context: header column = "Total Sales", neighbor = "Q1", "Q2", "Q3"
  - AI suggest: `=SUM(B2:D2)`
  - Tab accept; tiếp tục gõ override.
- Hoặc gõ formula partial: `=SUM(` → AI hoàn nốt args dựa context.

### Settings
- File → Options → Copilot → Formula completion: On / Off / Suggest only on Tab.

## 39.5 Settings Pane

- API provider: Anthropic / OpenAI / Local LLM (Ollama).
- API key (encrypted in QSettings).
- Model preferences for each function.
- Usage budget alarm.
- Privacy: "Allow Copilot to read other sheets" toggle.

## Implementation note

### Architecture
- LLM client class wraps Anthropic SDK (đã có file system, dùng `anthropic` library — không có nhưng prep cho add).
- Tool calling: define internal tools (`apply_format`, `create_pivot`, `create_chart`, `add_formula`, `filter_rows`, ...).
- Agent mode: agentic loop với multi-tool calling pattern + plan display.
- Streaming: stream tokens vào pane cho UX nhanh.

### Anthropic SDK pattern
- Prompt caching (cache workbook context — system prompt).
- Tool use: tool schemas cho từng action type.
- Sonnet 4.6 mặc định (fast + smart).
- Token usage tracking.

### Workbook context cho Copilot
- Active sheet headers + first 20 rows (preview).
- Named ranges list.
- Charts/Tables list.
- Cell type hints (number / date / text per column).
- Compress để fit context limit.

### Tool implementation
```python
@tool("apply_conditional_formatting")
def apply_cf(range_addr: str, rule_type: str, condition: dict, format: dict):
    # Add CF rule via internal API
    sheet.add_cf_rule(range_addr, rule_type, condition, format)
    return {"success": True, "applied_to": range_addr}
```

### Async + UI
- LLM call trong thread (không block UI).
- Cell value `#LOADING` while waiting.
- Stream response → update pane progressively.

## Acceptance criteria
1. Home → Copilot → pane mở; suggested prompts hiện.
2. Prompt "Highlight Sales > 1000 in red" → propose action → click Apply → CF rule applied, undo-able.
3. `=COPILOT("Translate to English: " & A1)` với A1="Xin chào" → cell hiển thị "Hello" (sau loading).
4. Agent task "Create dashboard" → list 5 step → user approve → 5 actions execute với animation.
5. Gõ `=` vào cell trong table → ghost text suggest `=SUM(...)` → Tab accept.
6. Settings → switch model → Anthropic Claude Sonnet → COPILOT function dùng Claude.
7. Status Bar hiện token usage hôm nay.

## Phụ thuộc
- Anthropic SDK (cần add) hoặc OpenAI SDK.
- Tất cả command modules (CF, PivotTable, Chart, Formula, ...) cần expose **command API** để Copilot gọi.
- [21 VBA / Macro](21-vba-macro.md) Python API → một phần overlap.

## Risk
**Cao.**
- LLM costs $.
- Network reliability.
- Tool use correctness (LLM có thể gọi tool sai args → confirm preview trước apply là bắt buộc).
- Privacy: workbook data sent to cloud — clear consent UI.
- Implement Phase rất muộn (sau MVP).
