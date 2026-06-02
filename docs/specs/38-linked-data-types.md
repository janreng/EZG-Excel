# SPEC 38 — Linked Data Types (Stocks / Geography / Currencies)

## Mục tiêu
Cell chứa "rich data type" — không chỉ string/number mà là **object có nhiều fields** lấy live từ cloud. Microsoft 365 modern feature (2018+, value tokens added 2024).

## Trạng thái hiện tại
- ✗ Chưa có. Modern Excel feature, value tokens là update 2024.

## 38.1 Loại Linked Data Types

| Type | Domain | Source |
|---|---|---|
| Stocks | Mã cổ phiếu (MSFT, AAPL, VNI) | Refinitiv (Microsoft partner) |
| Geography | Thành phố, quốc gia, vùng | Bing |
| Currencies | Cặp tiền tệ (USD/VND, EUR/USD) | Refinitiv |
| Organization (preview) | Stocks subset cho enterprise | Org data |

## 38.2 Tạo Linked Data Type

### Cách 1: Convert
- Cell có text "Microsoft" → Data → Data Types → Stocks → Excel resolve → cell biến thành Stock object.
- Cell có "Hanoi" → Data → Data Types → Geography → resolve → Geography object.
- Icon đặc trưng xuất hiện cạnh value:
  - 🏦 Stock
  - 🗺️ Geography
  - 💱 Currency

### Cách 2: Trong Formula
- `=A1.Price` → field accessor (dot notation).
- `=A1.Population` cho Geography.

### Cách 3: Data Types gallery
- Data → Data Types → More (gallery 30+ types: Movies, Books, Foods, Universities, Animals, Plants, Yoga poses, Elements...).

## 38.3 Card View

Click icon trong cell → card popup hiển thị tất cả fields available:

```
┌─ Stock: Microsoft Corp (MSFT) ─┐
│  Price                  413.84  │
│  Change                +1.25%   │
│  Market cap             3.1T    │
│  Volume                 21M     │
│  52 week high           468.35  │
│  52 week low            362.90  │
│  P/E ratio              35.12   │
│  Industry               Tech    │
│  Headquarters           Redmond │
│  Employees              228,000 │
│  CEO                    Satya N │
│  ...                            │
│  [Extract to cells]             │
└────────────────────────────────┘
```

- Mỗi field có "↗ Insert" button → drag/click insert vào ô bên cạnh.

## 38.4 Value Tokens (New 2024)

Cell hiển thị value (vd "Microsoft"), nhưng Formula Bar hiện **token** đặc biệt — cho biết đây là linked data type chứ không phải text. Click token → mở card.

- Trước 2024: Formula Bar hiển thị `Microsoft` (giống text → confusing).
- 2024+: Token icon + name trong Formula Bar.

## 38.5 Field Accessor Syntax

- `=A1.Price` — single field
- `=A1.[52 Week High]` — field có space → bracket
- `=A1.Industry` — text field

### Functions
- `=FIELDVALUE(A1, "Price")` — explicit accessor.
- Array of fields: `=FIELDVALUE(A1, {"Price","Change","Volume"})` → spill 3 ô.

## 38.6 Refresh

- Data → Refresh All / Ctrl+Alt+F5: re-fetch all linked data types.
- Auto-refresh: không (manual).
- Online required: nếu offline → fields trả `#GETTING_DATA`.

## 38.7 Data Type Gallery (Insert → Data Types)

Custom data type (Power Query Data Types — advanced):
- Tạo Power Query truy vấn (vd SQL Server employee table).
- Mark column as identifier.
- Save as data type → xuất hiện trong gallery.

## Implementation note

### Architecture
- Backend: Ezcel cần API key cho data provider:
  - Stocks: Alpha Vantage / Yahoo Finance API / IEX Cloud (free tier).
  - Geography: REST Countries API / Wikipedia API.
  - Currencies: exchangerate-api.com / Alpha Vantage.
- API key trong Settings.

### Data Model
```python
class LinkedDataType:
    type: "stock" | "geography" | "currency" | "custom"
    identifier: str               # "MSFT", "Hanoi"
    fields: dict[str, Any]        # {price: 413.84, change: 0.0125, ...}
    last_refreshed: datetime
    display_value: str            # "Microsoft Corp"
    icon: str                     # path/url
```

Cell `_data[r][c]` có thể là LinkedDataType instance (thay vì string).

### Render
- `delegate.paint()`: nếu cell value là `LinkedDataType` → vẽ icon trước text.
- Click icon → mở card popup.

### Formula
- Parser: token `IDENT.FIELD` → resolve to `FIELDVALUE(cell, "FIELD")`.
- `FIELDVALUE` function: nếu cell là LDT → return field; else `#FIELD!`.

### Offline behavior
- Cache fields trong workbook (xlsx custom XML).
- Khi reopen offline → load từ cache, show "Stale" indicator.
- Refresh → call API → update cache.

## Acceptance criteria
1. A1 = "Microsoft" → Data → Data Types → Stocks → cell biến thành Stock icon + "Microsoft Corp".
2. Click icon A1 → card popup hiển thị Price, Volume, Market Cap, ...
3. B1 = `=A1.Price` → real-time price.
4. C1 = `=FIELDVALUE(A1, "P/E ratio")` → P/E.
5. A2 = "Hanoi" → Geography → card hiện Population, Area, Country, Time zone, ...
6. Save xlsx → mở lại offline → fields vẫn hiển thị (từ cache); "Stale" indicator nếu > 24h.
7. Online + Data → Refresh All → fields update.
8. Formula Bar khi click A1 → hiển thị value token (icon + "Microsoft") chứ không phải plain text.

## Phụ thuộc
- [12 Formula System](12-formula-system.md) — parser cho `.FieldName`, function FIELDVALUE.
- Internet API + API key management (Settings dialog).

## Risk
**Trung bình-cao.**
- Phụ thuộc external API → rate limit, downtime.
- API key cần user setup (UX phức tạp).
- Card popup UI lớn.
- Stocks data có thể commercial-licensed → check ToS providers.

## Phase
Phase 6+. Sau khi modern features (Copilot, dynamic arrays) ổn.
