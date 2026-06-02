# SPEC 35 — Calculation Engine (Modes / Volatile / Dependency / Date System)

## Mục tiêu
Engine recalc đúng và nhanh: 3 mode calculation, volatile functions, dependency graph, date serial system, R1C1 reference style.

## Trạng thái hiện tại
- ✓ Recalc on-cell-change cơ bản (immediate).
- ✓ `_eval_cache` cache per-cell.
- ✓ ~60 hàm.
- ✗ Calculation mode toggle (Automatic / Manual / Automatic except for tables).
- ✗ Volatile functions tracking.
- ✗ Iterative calculation (đã đề cập [Spec 28](28-what-if-analysis.md)).
- ✗ R1C1 reference style toggle.
- ✗ Dependency graph explicit (Trace Precedents [Spec 12](12-formula-system.md) cần graph).

## 35.1 Calculation Options

File → Options → Formulas → Calculation options:

### Workbook Calculation
- **Automatic** (default): recalc khi bất kỳ cell input đổi.
- **Automatic except for data tables**: tables tính manual (F9), khác auto.
- **Manual**: chỉ tính khi F9 / Shift+F9 / Ctrl+Alt+F9.
- "Recalculate workbook before saving" checkbox (chỉ áp cho Manual).

### Enable iterative calculation
- Maximum Iterations (default 100).
- Maximum Change (default 0.001).

### Working with formulas
- **R1C1 reference style** checkbox: chuyển toàn workbook sang `R1C1` notation thay vì `A1`.
- Formula AutoComplete ✓.
- Use table names in formulas ✓.
- Use GetPivotData functions for PivotTable references ✓.

## 35.2 Recalc Triggers

### Auto
- Cell value/formula change.
- Insert / Delete row/col.
- Named Range add/edit/delete.
- Sheet rename (formulas reference đó update).
- Open workbook.

### Manual
| Phím | Hành vi |
|---|---|
| F9 | Recalc all open workbooks |
| Shift + F9 | Recalc active sheet |
| Ctrl + Alt + F9 | **Force** recalc all (including non-dirty cells) |
| Ctrl + Shift + Alt + F9 | Rebuild dependency graph + force recalc |

## 35.3 Volatile Functions

Recalc mỗi lần Excel recalculate (kể cả không có data đổi).

| Function | Volatile? | Lý do |
|---|---|---|
| `NOW()` | ✓ | Time đổi liên tục |
| `TODAY()` | ✓ | Date có thể đổi |
| `RAND()` | ✓ | Random |
| `RANDBETWEEN()` | ✓ | Random |
| `RANDARRAY()` | ✓ | Random |
| `OFFSET()` | ✓ | Reference dynamic |
| `INDIRECT()` | ✓ | Reference qua string |
| `CELL("contents",...)` | ✓ | Trả về dynamic info |
| `INFO()` | ✓ | System info |
| `SUMIF` với INDIRECT/OFFSET | gián tiếp | Inherit volatility |

⚠ **Performance**: lạm dụng volatile trên file lớn → recalc liên tục, lag.

### Implementation
- Mark volatile functions trong `_FUNCTIONS` registry: `_VOLATILE_FUNCS = {"NOW","TODAY","RAND","RANDBETWEEN","OFFSET","INDIRECT","CELL","INFO"}`.
- Khi build dep graph: cell formula chứa volatile function → add edge từ "VOLATILE_PSEUDO_NODE" để recalc every cycle.

## 35.4 Dependency Graph

DAG (Directed Acyclic Graph):
- **Node**: cell `(sheet, row, col)` hoặc named range.
- **Edge**: A → B nếu A là precedent của B (B's formula references A).

### Operations
- **Add edge**: khi parse formula trong cell B, extract refs → add A→B.
- **Remove edges**: khi formula B thay đổi → remove tất cả edges đến B.
- **Topological sort**: recalc order = topo sort.
- **Cycle detection**: nếu add edge tạo cycle → circular reference warning.

### Recalc dirty propagation
- Cell A đổi → mark A dirty.
- Propagate: tất cả nodes downstream của A → dirty.
- Topo iterate dirty nodes → eval → cache.

### Phần đã có
Code review cho `formula.py` + `table_model.py` — hiện không có dep graph rõ rệt; `_recalculate(changed)` chỉ refresh `_eval_cache` lazy. Đề xuất:
- Build graph khi load workbook.
- Update incremental khi formula đổi.
- Cell có volatile fn → add edge từ pseudo "VolatileSource".

## 35.5 Date Serial System

### Default: 1900 date system
- `1` = 1900-01-01
- `2` = 1900-01-02
- ...
- `59` = 1900-02-28
- `60` = **1900-02-29** (NGÀY GIẢ — Excel bug giữ lại cho compat với Lotus 1-2-3)
- `61` = 1900-03-01
- Range: 1900-01-01 → 9999-12-31.

### Optional: 1904 date system
- `0` = 1904-01-01.
- Mac Excel legacy.
- File → Options → Advanced → "Use 1904 date system" checkbox (per workbook).

### Time
- Decimal part: `0.5` = 12:00:00 noon, `0.25` = 06:00:00.

### Date functions
- `DATE(year, month, day)` → serial.
- `YEAR/MONTH/DAY(serial)` → component.
- `NOW()` / `TODAY()` → current.

## 35.6 R1C1 Reference Style

Toggle: File → Options → Formulas → "R1C1 reference style".

| A1 style | R1C1 style |
|---|---|
| `A1` | `R1C1` |
| `B5` | `R5C2` |
| `$A$1` | `R1C1` (absolute always) |
| `A1` (relative trong B2) | `R[-1]C[-1]` |
| `$A1` | `R[+x]C1` |
| `A$1` | `R1C[+x]` |
| `A:A` | `C1` |
| `1:1` | `R1` |

R1C1 tiện hơn cho macro programming. Đa số user quen A1.

### Implementation
- Format setting workbook: `_a1_style: bool = True`.
- Render formula trong Formula Bar / Name Box theo style.
- Parser xử lý cả 2 style.

## 35.7 Array Formulas (Legacy {Ctrl+Shift+Enter})

Excel 2019 trở xuống: formula trả mảng phải nhập với Ctrl+Shift+Enter, bao quanh bởi `{}`.

Excel 365: Dynamic Arrays — không cần CSE; mảng spill tự động ([Spec 12](12-formula-system.md)).

### Compatibility
- Workbook có CSE formula → giữ behavior CSE.
- Implicit Intersection Operator `@`: `=@A1:A10` → giá trị tại hàng tương ứng (legacy behavior).

## Acceptance criteria
1. File → Options → Calculation → Manual → đổi A1 → C1 (`=A1*2`) không update. F9 → C1 update.
2. `=NOW()` trong A1 → F9 → giá trị refresh đến giây mới.
3. `=A1` ở B1; `=B1` ở A1 → popup "Circular reference: A1, B1". Status Bar hiện "Circular".
4. Enable iterative + circular setup → max 100 iterations, converge nếu max change < 0.001.
5. R1C1 toggle bật → Formula Bar hiện `=R[-1]C` thay vì `=A1` (cho công thức trong A2).
6. `=DATE(2026,6,2)` → serial 46155 (date format hiển thị 02/06/2026).
7. `=NOW()` ô A1; gõ vào A5 → A1 cập nhật (volatile).
8. File lớn 100k cells với 1 cell volatile → recalc < 200ms (graph propagation chỉ touch dependents).

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — engine.
- [28 What-If](28-what-if-analysis.md) — iterative.

## Risk
**Cao.** Refactor recalc engine sang graph-based — đụng vào hot path nhất của app. Cần benchmark trước/sau.
