# SPEC 42 — Proofing & Language (Spell Check / AutoCorrect / Translate / Smart Lookup / Thesaurus)

## Mục tiêu
Tab Review → Proofing + Language: Spelling (F7), AutoCorrect, Smart Lookup, Translate, Thesaurus.

## Trạng thái hiện tại
- ✗ Chưa có toàn bộ.

## 42.1 Spelling (Review → Spelling / F7)

### Flow
1. F7 → engine quét toàn sheet (cells text + comments + headers/footers).
2. Phát hiện từ sai chính tả → dialog:

```
┌─ Spelling: English (Vietnam) ──────────────────────┐
│ Not in Dictionary:                                  │
│ [aplle                                           ]  │
│                                                     │
│ Suggestions:                                        │
│ ┌─────────────────────────────────────────────┐    │
│ │ apple                                        │    │
│ │ apply                                        │    │
│ │ appleseed                                    │    │
│ └─────────────────────────────────────────────┘    │
│                                                     │
│ Dictionary language: [English (Vietnam)         ▼] │
│                                                     │
│ [Ignore Once] [Ignore All] [Add to Dictionary]      │
│ [Change] [Change All] [AutoCorrect]                 │
│ [Options...] [Undo Last] [Cancel]                   │
└─────────────────────────────────────────────────────┘
```

### Settings (File → Options → Proofing)
- Dictionary language (per workbook).
- Ignore words in UPPERCASE.
- Ignore words that contain numbers.
- Ignore Internet and file addresses.
- Flag repeated words.
- Custom Dictionary: list user-added words (CUSTOM.DIC).

### Vietnamese spell check
- Hunspell engine với `vi_VN.aff/dic` (Hunspell standard).
- Hoặc dùng `language-tool-python` (offline mode).

## 42.2 AutoCorrect (File → Options → Proofing → AutoCorrect Options)

### Tab AutoCorrect
- Show AutoCorrect Options buttons ✓.
- Correct TWo INitial CApitals ✓.
- Capitalize first letter of sentences ✓.
- Capitalize names of days ✓.
- Correct accidental usage of cAPS LOCK key ✓.
- Replace text as you type:
  - Replacement list:
    - `(c)` → `©`
    - `(r)` → `®`
    - `(tm)` → `™`
    - `--` → `—`
    - `:)` → `☺`
    - User-defined: gõ shortcut → auto-expand.

### Tab Math AutoCorrect
- `\alpha` → α, `\beta` → β, `\sum` → ∑ (LaTeX-like).

### Tab Smart Tags
- Phase muộn.

## 42.3 Smart Lookup (Review → Smart Lookup)

- Chọn cell có text → Right-click → Smart Lookup hoặc Review → Smart Lookup.
- Pane bên phải:
  - Bing search results.
  - Wikipedia summary.
  - Image results.
  - Web links.
- Privacy: text gửi đi Microsoft search → opt-in dialog lần đầu.

### Ezcel approach
- Optional feature.
- Dùng Wikipedia REST API (no key) + DuckDuckGo Instant Answer.
- Pane stub disabled hoặc đơn giản.

## 42.4 Translate (Review → Translate)

### Pane Translator
```
┌─ Translator ──────────────────────┐
│ From: [Vietnamese            ▼]   │
│ ──────────────────────────────────│
│ [Xin chào bạn                    ]│
│                                    │
│ To:   [English               ▼]   │
│ ──────────────────────────────────│
│ Hello you                          │
│ ──────────────────────────────────│
│ [Insert] [Listen 🔊] [Copy]        │
└────────────────────────────────────┘
```

- Select cell text → Translate → pane hiện text + dropdown languages.
- "Insert" → thay text trong cell.

### TRANSLATE / DETECTLANGUAGE functions
Đã có trong [Spec 22](22-modern-features.md).

### API
- Cần internet + API key (Microsoft Translator / Google Translate / DeepL).
- Settings → API key.

## 42.5 Thesaurus (Review → Thesaurus / Shift+F7)

- Chọn từ → pane hiện synonyms + antonyms.
- Phân chia theo nghĩa (noun / verb / adj).
- Click synonym → Insert / Copy / Look Up (recursive).

### Ezcel approach
- English: WordNet (offline, package `nltk` hoặc `wn`).
- Vietnamese: limited (Vietnamese WordNet không phổ biến).
- Optional dependency.

## 42.6 Set Proofing Language

Review → Language → Set Proofing Language → dialog:
- List language với checkmark hiện language hiện tại.
- "Do not check spelling or grammar" checkbox (force skip cell).
- "Default" button: dùng cho workbook mới.

Per-cell hoặc per-range.

## Implementation note

### Spell check engine
- Hunspell (`pyhunspell` hoặc `hunspell` library binding).
- Dictionaries: bundle `en_US`, `vi_VN`. Download từ LibreOffice extension.
- Wavy red underline: render trong delegate khi `_fmt.spell_check_enabled` (default True) + word fail check.
- Background scan: process cells khi idle, không block UI.

### AutoCorrect
- Hook keyPressEvent trong Edit mode: sau khi gõ space hoặc punctuation, check previous word against replacement list.

### Smart Lookup + Translate
- HTTP client (`urllib` đã có trong stdlib — match CLAUDE.md "không thêm `requests`").
- Async với QNetworkAccessManager hoặc thread pool.

## Acceptance criteria
1. F7 → dialog Spelling cho từ "aplle" → suggestions "apple, apply" → Change → cell update.
2. Add to Dictionary → "aplle" → next F7 không flag nữa.
3. Wavy red underline trên cells có typo (real-time).
4. Gõ `(c)` + space → auto thành `©`.
5. AutoCorrect custom: gõ `ezcel` → expand `Ezcel Spreadsheet App`.
6. Select cell "Xin chào" → Translate pane → English "Hello" → Insert → cell update.
7. Shift+F7 trên "good" → Thesaurus pane → synonyms "great, fine, excellent".
8. Set Proofing Language: A1 = "VBA code goes here" → Vietnamese spell check không flag (do "Do not check" + English context).

## Phụ thuộc
- [22 Modern features](22-modern-features.md) — REGEX, TRANSLATE function.
- [26 Comments & Notes](26-comments-notes.md) — spell check trong comment.
- Hunspell, optional WordNet.

## Risk
- Spell check hot path: wavy underline mỗi cell painted; cần cache result per cell text hash.
- Translate API key UX: nếu user không setup → graceful disable pane.
