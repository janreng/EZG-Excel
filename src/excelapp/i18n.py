"""Đa ngôn ngữ đơn giản (Việt / Anh) cho PyExcel.

Dùng ``tr("key")`` để lấy chuỗi theo ngôn ngữ hiện tại. Lưu lựa chọn bằng
QSettings để lần mở sau giữ nguyên.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings

_LANG = "vi"

STRINGS: dict[str, dict[str, str]] = {
    # --- menu: Tệp ---
    "menu_file": {"vi": "&Tệp", "en": "&File"},
    "new": {"vi": "Mới", "en": "New"},
    "open": {"vi": "Mở...", "en": "Open..."},
    "save": {"vi": "Lưu", "en": "Save"},
    "save_as": {"vi": "Lưu thành...", "en": "Save As..."},
    "quit": {"vi": "Thoát", "en": "Exit"},
    # --- menu: Sửa ---
    "menu_edit": {"vi": "&Sửa", "en": "&Edit"},
    "undo": {"vi": "Hoàn tác", "en": "Undo"},
    "redo": {"vi": "Làm lại", "en": "Redo"},
    "copy": {"vi": "Sao chép", "en": "Copy"},
    "cut": {"vi": "Cắt", "en": "Cut"},
    "paste": {"vi": "Dán", "en": "Paste"},
    "clear": {"vi": "Xóa nội dung", "en": "Clear contents"},
    "fill_down": {"vi": "Điền xuống", "en": "Fill Down"},
    "fill_right": {"vi": "Điền sang phải", "en": "Fill Right"},
    # --- menu: Cấu trúc ---
    "menu_structure": {"vi": "&Cấu trúc", "en": "&Structure"},
    "insert_row": {"vi": "Chèn dòng phía trên", "en": "Insert row above"},
    "insert_row_below": {"vi": "Chèn dòng phía dưới", "en": "Insert row below"},
    "insert_col": {"vi": "Chèn cột bên trái", "en": "Insert column left"},
    "insert_col_right": {"vi": "Chèn cột bên phải", "en": "Insert column right"},
    "delete_row": {"vi": "Xóa dòng", "en": "Delete row"},
    "delete_col": {"vi": "Xóa cột", "en": "Delete column"},
    # --- menu: Dữ liệu ---
    "menu_data": {"vi": "&Dữ liệu", "en": "&Data"},
    "find": {"vi": "Tìm kiếm", "en": "Find"},
    "replace": {"vi": "Tìm & thay thế", "en": "Find & Replace"},
    "sort_asc": {"vi": "Sắp xếp tăng dần", "en": "Sort ascending"},
    "sort_desc": {"vi": "Sắp xếp giảm dần", "en": "Sort descending"},
    # --- menu: Ngôn ngữ ---
    "menu_language": {"vi": "&Ngôn ngữ", "en": "&Language"},
    "lang_vi": {"vi": "Tiếng Việt", "en": "Vietnamese"},
    "lang_en": {"vi": "Tiếng Anh", "en": "English"},
    # --- menu: Trợ giúp ---
    "menu_help": {"vi": "&Trợ giúp", "en": "&Help"},
    "about": {"vi": "Giới thiệu Ezcel", "en": "About Ezcel"},
    "check_updates": {"vi": "Kiểm tra cập nhật...", "en": "Check for updates..."},
    "checking_updates": {"vi": "Đang kiểm tra cập nhật...", "en": "Checking for updates..."},
    "up_to_date": {
        "vi": "Bạn đang dùng phiên bản mới nhất ({ver}).",
        "en": "You are on the latest version ({ver}).",
    },
    "update_available": {"vi": "Đã có bản cập nhật", "en": "Update available"},
    "update_prompt": {
        "vi": "Phiên bản mới <b>{new}</b> đã có (bạn đang dùng {cur}).<br><br>{notes}<br><br>Cập nhật ngay?",
        "en": "Version <b>{new}</b> is available (you have {cur}).<br><br>{notes}<br><br>Update now?",
    },
    "update_now": {"vi": "Cập nhật ngay", "en": "Update now"},
    "downloading": {"vi": "Đang tải bản cập nhật...", "en": "Downloading update..."},
    "update_error": {"vi": "Lỗi cập nhật", "en": "Update error"},
    "update_check_failed": {
        "vi": "Không kiểm tra được cập nhật:\n{err}",
        "en": "Could not check for updates:\n{err}",
    },
    "update_ready": {
        "vi": "Đã tải xong. Ứng dụng sẽ đóng để chạy trình cài đặt.",
        "en": "Download complete. The app will close to run the installer.",
    },
    # --- thanh công thức / UI ---
    "formula_placeholder": {
        "vi": "Nhập giá trị hoặc công thức, ví dụ =SUM(A1:A5)",
        "en": "Enter a value or formula, e.g. =SUM(A1:A5)",
    },
    "ready": {
        "vi": "Sẵn sàng — nhấp đúp tiêu đề cột để sắp xếp",
        "en": "Ready — double-click a column header to sort",
    },
    "untitled": {"vi": "Chưa đặt tên", "en": "Untitled"},
    # --- hộp thoại tìm kiếm / thay thế ---
    "find_title": {"vi": "Tìm kiếm", "en": "Find"},
    "replace_title": {"vi": "Tìm & thay thế", "en": "Find & Replace"},
    "find_label": {"vi": "Tìm:", "en": "Find:"},
    "replace_with_label": {"vi": "Thay bằng:", "en": "Replace with:"},
    "match_case": {"vi": "Phân biệt hoa/thường", "en": "Match case"},
    "find_next": {"vi": "Tìm tiếp", "en": "Find Next"},
    "replace_btn": {"vi": "Thay thế", "en": "Replace"},
    "replace_all_btn": {"vi": "Thay tất cả", "en": "Replace All"},
    "close": {"vi": "Đóng", "en": "Close"},
    # --- hộp thoại tệp ---
    "open_title": {"vi": "Mở tệp", "en": "Open file"},
    "save_title": {"vi": "Lưu thành", "en": "Save As"},
    "file_filter": {
        "vi": "Bảng tính (*.csv *.xlsx);;CSV (*.csv);;Excel (*.xlsx);;Tất cả (*)",
        "en": "Spreadsheets (*.csv *.xlsx);;CSV (*.csv);;Excel (*.xlsx);;All files (*)",
    },
    # --- thông báo ---
    "copied": {"vi": "Đã sao chép", "en": "Copied"},
    "cut_done": {"vi": "Đã cắt", "en": "Cut"},
    "pasted": {"vi": "Đã dán", "en": "Pasted"},
    "nothing_undo": {"vi": "Không có gì để hoàn tác", "en": "Nothing to undo"},
    "nothing_redo": {"vi": "Không có gì để làm lại", "en": "Nothing to redo"},
    "not_found": {"vi": "Không tìm thấy", "en": "Not found"},
    "cannot_delete_row": {
        "vi": "Không thể xóa dòng cuối cùng",
        "en": "Cannot delete the last row",
    },
    "cannot_delete_col": {
        "vi": "Không thể xóa cột cuối cùng",
        "en": "Cannot delete the last column",
    },
    "open_error": {"vi": "Lỗi mở tệp", "en": "Error opening file"},
    "save_error": {"vi": "Lỗi lưu tệp", "en": "Error saving file"},
    "opening_file": {"vi": "Đang mở tệp...", "en": "Opening file..."},
    "saving_file": {"vi": "Đang lưu tệp...", "en": "Saving file..."},
    # các chuỗi có tham số dùng .format()
    "found_at": {"vi": "Tìm thấy tại {ref}", "en": "Found at {ref}"},
    "opened": {"vi": "Đã mở {path}", "en": "Opened {path}"},
    "saved": {"vi": "Đã lưu {path}", "en": "Saved {path}"},
    "replaced_n": {"vi": "Đã thay {n} ô", "en": "Replaced {n} cell(s)"},
    "sorted_msg": {
        "vi": "Đã sắp xếp theo cột {col} ({dir})",
        "en": "Sorted by column {col} ({dir})",
    },
    "dir_asc": {"vi": "tăng dần", "en": "ascending"},
    "dir_desc": {"vi": "giảm dần", "en": "descending"},
    # --- định dạng (toolbar) ---
    "tooltip_font": {"vi": "Phông chữ", "en": "Font"},
    "tooltip_size": {"vi": "Cỡ chữ", "en": "Font size"},
    "bold": {"vi": "In đậm", "en": "Bold"},
    "italic": {"vi": "In nghiêng", "en": "Italic"},
    "align_left": {"vi": "Canh trái", "en": "Align left"},
    "align_center": {"vi": "Canh giữa", "en": "Align center"},
    "align_right": {"vi": "Canh phải", "en": "Align right"},
    "valign_top": {"vi": "Canh trên", "en": "Align top"},
    "valign_middle": {"vi": "Canh giữa (dọc)", "en": "Align middle"},
    "valign_bottom": {"vi": "Canh dưới", "en": "Align bottom"},
    "wrap": {"vi": "Xuống dòng", "en": "Wrap text"},
    "halign_tip": {"vi": "Canh lề ngang", "en": "Horizontal align"},
    "valign_tip": {"vi": "Canh lề dọc", "en": "Vertical align"},
    "wrap_tip": {"vi": "Xuống dòng / Tràn / Cắt", "en": "Text wrapping"},
    # --- ribbon section labels ---
    "sec_clipboard": {"vi": "Bảng tạm", "en": "Clipboard"},
    "sec_undo":      {"vi": "Hoàn tác",  "en": "Undo"},
    "sec_font":      {"vi": "Phông chữ", "en": "Font"},
    "sec_alignment": {"vi": "Căn lề",   "en": "Alignment"},
    "sec_editing":   {"vi": "Sửa",      "en": "Editing"},
    "sec_cell":      {"vi": "Ô",        "en": "Cell"},
    # --- new toolbar actions ---
    "underline": {"vi": "Gạch dưới", "en": "Underline"},
    "strike": {"vi": "Gạch ngang", "en": "Strikethrough"},
    "font_color": {"vi": "Màu chữ", "en": "Text color"},
    "fill_color": {"vi": "Màu nền", "en": "Fill color"},
    # --- viền ---
    "borders_tip": {"vi": "Kẻ viền ô", "en": "Borders"},
    "border_all": {"vi": "Tất cả viền", "en": "All borders"},
    "border_outer": {"vi": "Viền ngoài", "en": "Outer borders"},
    "border_top": {"vi": "Viền trên", "en": "Top border"},
    "border_bottom": {"vi": "Viền dưới", "en": "Bottom border"},
    "border_left": {"vi": "Viền trái", "en": "Left border"},
    "border_right": {"vi": "Viền phải", "en": "Right border"},
    "border_none": {"vi": "Bỏ viền", "en": "No border"},
    # --- định dạng số ---
    "number_format_tip": {"vi": "Định dạng số", "en": "Number format"},
    "numfmt_general": {"vi": "Tự động", "en": "General"},
    "numfmt_number": {"vi": "Số (1.234,56)", "en": "Number (1,234.56)"},
    "numfmt_percent": {"vi": "Phần trăm (%)", "en": "Percent (%)"},
    "numfmt_vnd": {"vi": "Tiền VND (₫)", "en": "Currency VND (₫)"},
    "numfmt_usd": {"vi": "Tiền USD ($)", "en": "Currency USD ($)"},
    "numfmt_date": {"vi": "Ngày (dd/mm/yyyy)", "en": "Date (dd/mm/yyyy)"},
    "numfmt_time": {"vi": "Giờ (hh:mm:ss)", "en": "Time (hh:mm:ss)"},
    "numfmt_scientific": {"vi": "Khoa học", "en": "Scientific"},
    # --- gộp ô ---
    "merge_tip": {"vi": "Gộp / bỏ gộp ô", "en": "Merge / unmerge cells"},
    # --- sheet ---
    "sheet_add": {"vi": "Thêm sheet", "en": "Add sheet"},
    "sheet_rename": {"vi": "Đổi tên sheet", "en": "Rename sheet"},
    "sheet_duplicate": {"vi": "Nhân bản sheet", "en": "Duplicate sheet"},
    "sheet_delete": {"vi": "Xóa sheet", "en": "Delete sheet"},
    "sheet_name": {"vi": "Tên sheet:", "en": "Sheet name:"},
    "sheet_dup": {"vi": "Tên sheet đã tồn tại", "en": "Sheet name already exists"},
    "sheet_min": {"vi": "Phải còn ít nhất một sheet", "en": "At least one sheet is required"},
    # --- Name Box / Go To ---
    "name_box_invalid_ref": {
        "vi": "Tham chiếu không hợp lệ.",
        "en": "Reference is not valid.",
    },
    # --- Cell Mode indicator (Spec 03) ---
    "mode_ready": {"vi": "Sẵn sàng", "en": "Ready"},
    "mode_enter": {"vi": "Nhập", "en": "Enter"},
    "mode_edit": {"vi": "Chỉnh sửa", "en": "Edit"},
    "mode_point": {"vi": "Trỏ", "en": "Point"},
    # --- định dạng có điều kiện ---
    "cond_tip": {"vi": "Định dạng có điều kiện", "en": "Conditional formatting"},
    "cond_add": {"vi": "Thêm quy tắc...", "en": "Add rule..."},
    "cond_clear": {"vi": "Xóa quy tắc trong vùng chọn", "en": "Clear rules in selection"},
    "cond_title": {"vi": "Định dạng có điều kiện", "en": "Conditional formatting"},
    "cond_gt": {"vi": "Lớn hơn", "en": "Greater than"},
    "cond_lt": {"vi": "Nhỏ hơn", "en": "Less than"},
    "cond_eq": {"vi": "Bằng", "en": "Equal to"},
    "cond_between": {"vi": "Trong khoảng", "en": "Between"},
    "cond_contains": {"vi": "Chứa chữ", "en": "Text contains"},
    "cond_value": {"vi": "Giá trị", "en": "Value"},
    "cond_value2": {"vi": "Giá trị thứ hai", "en": "Second value"},
    "cond_pick_color": {"vi": "Chọn màu tô", "en": "Pick fill color"},
    "cond_invalid": {"vi": "Giá trị không hợp lệ", "en": "Invalid value"},
    "wrap_overflow": {"vi": "Tràn", "en": "Overflow"},
    "wrap_wrap": {"vi": "Xuống dòng", "en": "Wrap"},
    "wrap_clip": {"vi": "Cắt", "en": "Clip"},
    "paste_special": {"vi": "Dán dạng văn bản thuần", "en": "Paste values only"},
    # --- bộ lọc ---
    "filter_tip": {"vi": "Lọc cột hiện tại", "en": "Filter current column"},
    "filter_title": {"vi": "Lọc — cột {col}", "en": "Filter — column {col}"},
    "clear_filters": {"vi": "Xóa tất cả bộ lọc", "en": "Clear all filters"},
    "filter_menu": {"vi": "Lọc cột hiện tại...", "en": "Filter current column..."},
    "sort_az": {"vi": "Sắp xếp A → Z", "en": "Sort A → Z"},
    "sort_za": {"vi": "Sắp xếp Z → A", "en": "Sort Z → A"},
    "select_all": {"vi": "Chọn tất cả", "en": "Select all"},
    "clear_sel": {"vi": "Bỏ chọn", "en": "Clear"},
    "blanks": {"vi": "(Trống)", "en": "(Blanks)"},
    "search_ph": {"vi": "Tìm trong danh sách...", "en": "Search the list..."},
    "ok": {"vi": "OK", "en": "OK"},
    "cancel": {"vi": "Hủy", "en": "Cancel"},
    # --- menu Xem / Freeze ---
    "menu_view": {"vi": "&Xem", "en": "&View"},
    "freeze": {"vi": "Cố định (Freeze)", "en": "Freeze"},
    "no_rows": {"vi": "Không cố định dòng", "en": "No rows"},
    "one_row": {"vi": "1 dòng", "en": "1 row"},
    "two_rows": {"vi": "2 dòng", "en": "2 rows"},
    "up_to_row": {"vi": "Đến dòng {n}", "en": "Up to row {n}"},
    "no_cols": {"vi": "Không cố định cột", "en": "No columns"},
    "one_col": {"vi": "1 cột", "en": "1 column"},
    "two_cols": {"vi": "2 cột", "en": "2 columns"},
    "up_to_col": {"vi": "Đến cột {c}", "en": "Up to column {c}"},
    # --- trình chỉnh phím tắt ---
    "keybindings": {"vi": "Tùy chỉnh phím tắt...", "en": "Customize shortcuts..."},
    "keybindings_title": {"vi": "Tùy chỉnh phím tắt", "en": "Customize Shortcuts"},
    "col_command": {"vi": "Lệnh", "en": "Command"},
    "col_shortcut": {"vi": "Phím tắt", "en": "Shortcut"},
    "reset_defaults": {"vi": "Khôi phục mặc định", "en": "Restore defaults"},
    "save_close": {"vi": "Lưu & đóng", "en": "Save & Close"},
    "menu_settings": {"vi": "&Cài đặt", "en": "&Settings"},
    "about_body": {
        "vi": (
            "<h3>Ezcel</h3><p>Phiên bản <b>{ver}</b></p>"
            "<p>Ứng dụng bảng tính đơn giản — đọc/ghi CSV &amp; XLSX, "
            "công thức, AutoFill.</p><p>Xây dựng bằng Python + PySide6.</p>"
        ),
        "en": (
            "<h3>Ezcel</h3><p>Version <b>{ver}</b></p>"
            "<p>A simple spreadsheet app — read/write CSV &amp; XLSX, "
            "formulas, AutoFill.</p><p>Built with Python + PySide6.</p>"
        ),
    },
}


def _settings() -> QSettings:
    return QSettings("PyExcel", "PyExcel")


def load_lang() -> str:
    global _LANG
    saved = _settings().value("language", "vi")
    _LANG = saved if saved in ("vi", "en") else "vi"
    return _LANG


def set_lang(lang: str) -> None:
    global _LANG
    if lang in ("vi", "en"):
        _LANG = lang
        _settings().setValue("language", lang)


def current_lang() -> str:
    return _LANG


def tr(key: str, **kwargs) -> str:
    text = STRINGS.get(key, {}).get(_LANG, key)
    return text.format(**kwargs) if kwargs else text
