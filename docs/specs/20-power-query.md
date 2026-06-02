# SPEC 20 — Power Query Editor (Get & Transform)

## Mục tiêu
Cửa sổ riêng để load + transform data; mỗi bước = 1 step lưu lại (M language); Close & Load vào Excel Table.

## Trạng thái hiện tại
- ✗ Chưa có.

> **Phase 6+**. Quy mô lớn. Cần đánh giá có thực sự cần thiết — nhiều user thay thế bằng pandas script.

## 20.1 Layout Power Query Editor (§20.1)

Cửa sổ riêng (`QDialog` modal hoặc `QMainWindow` con).

```
┌─ Power Query Editor ────────────────────────────────────────────┐
│ Home  Transform  Add Column  View                                │
│ ────────────────────────────────────────────────────────────────│
│ Queries          Data Preview                  Applied Steps    │
│ ┌────────────┐  ┌──────────────────────────┐  ┌──────────────┐ │
│ │ Query1     │  │ Col1 | Col2 | Col3        │  │ Source       │ │
│ │ Query2     │  │ ...                       │  │ Promoted...  │ │
│ │            │  │                           │  │ Changed Type │ │
│ │            │  │                           │  │ Filtered     │ │
│ └────────────┘  └──────────────────────────┘  └──────────────┘ │
│ fx = Table.PromoteHeaders(#"Source", [PromoteAllScalars=true])  │
│                                  [Close & Load▼] [Cancel]       │
└─────────────────────────────────────────────────────────────────┘
```

### Components
- **Home Ribbon**: New Source / Recent Sources / Manage Connections / Combine Queries / Manage Parameters / Refresh Preview.
- **Queries Pane** (trái): danh sách queries trong workbook.
- **Data Preview** (giữa): preview sau step đang chọn (max 1000 rows mặc định).
- **Applied Steps Pane** (phải): danh sách bước (mỗi bước = 1 dòng code M).
- **Formula Bar**: hiển thị code M của step đang chọn; edit trực tiếp.

## 20.2 Applied Steps (§20.2)

Mỗi thao tác (đổi tên cột, filter, xóa cột, group by...) = 1 step.

- Click step: preview hiện kết quả đến step đó.
- Right-click step: Rename / Delete / Move Up/Down / Insert Step After.
- Xóa step → data về trạng thái trước.
- Gear icon ⚙ bên phải step: mở dialog settings của step.

## 20.3 Close & Load (§20.3)

- Home → Close & Load: load kết quả vào Excel Table trên sheet mới.
- Close & Load To...: dialog
  - Table / PivotTable / Chart / Connection Only
  - Existing sheet / New sheet
  - Add to Data Model checkbox
- Refresh: Data → Refresh All / Ctrl+Alt+F5 → re-run query với data mới.

## Sources hỗ trợ
- From File: CSV / Excel / JSON / XML / Text / PDF / Folder.
- From Database: SQL Server / MySQL / PostgreSQL / SQLite — Phase rất sau.
- From Web: URL → parse HTML table.
- From Table/Range: data hiện tại trong workbook.

## Transformations cơ bản

| Group | Operation |
|---|---|
| Manage Columns | Choose / Remove / Reorder |
| Reduce Rows | Keep Top N / Keep Range / Remove Top N / Remove Duplicates / Remove Blank |
| Transform | Use First Row as Headers / Detect Type / Replace Values / Split Column / Merge Columns |
| Filter | Filter dropdown trên header (Text/Number/Date filters) |
| Group By | Group + aggregation |
| Sort | Ascending / Descending; multi-level |
| Add Column | Custom Column (M formula) / Conditional Column / Index Column |
| Combine | Append Queries / Merge Queries (join) |

## M Language

Đơn giản hóa cho Phase đầu — chỉ implement subset:
- `let ... in ...` expression
- `Source = Csv.Document(...)` 
- `Table.RenameColumns(table, {{"OldName", "NewName"}})`
- `Table.SelectRows(table, each [Col] > 100)`
- `Table.RemoveColumns(table, {"Col1", "Col2"})`
- `Table.AddColumn(table, "NewCol", each [Col1] + [Col2])`
- `Table.Group(...)`
- `Table.NestedJoin(...)`

Implementation:
- Parser M (lexer + recursive descent).
- Evaluator dùng pandas DataFrame backend (mỗi step → pandas operation).
- Code-gen dialog → M string (mỗi UI action sinh M code, append vào let block).

## Acceptance criteria
1. Data → Get Data → From CSV → chọn file → Power Query Editor mở.
2. Click cột → Remove → step "Removed Columns" thêm vào pane.
3. Filter cột số > 100 → step "Filtered Rows".
4. Home → Use First Row as Headers → step "Promoted Headers".
5. Delete step "Filtered Rows" → preview về trạng thái sau "Promoted Headers".
6. Close & Load → sheet mới với Excel Table chứa kết quả.
7. Sau khi load: thay đổi file CSV → Data → Refresh All → table update.

## Phụ thuộc
- [16 Table](16-table.md) — load vào Excel Table.
- [10 Sheet Tabs](10-sheet-tabs.md) — load vào sheet mới.
- pandas (đã có) — backend.

## Risk
**Rất cao.** Module riêng quy mô lớn. Đánh giá lại priority: có thể giảm scope xuống "CSV/Excel import + transformation cơ bản" thay vì full Power Query.
