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
    "hide_rows": {"vi": "Ẩn dòng", "en": "Hide rows"},
    "hide_cols": {"vi": "Ẩn cột", "en": "Hide columns"},
    "unhide": {"vi": "Hiện lại (trong vùng chọn)", "en": "Unhide (in selection)"},
    "autofit_col": {"vi": "Dãn cột vừa nội dung", "en": "Auto-fit column width"},
    "autofit_row": {"vi": "Dãn dòng vừa nội dung", "en": "Auto-fit row height"},
    "outline_menu": {"vi": "Nhóm (Outline)", "en": "Group (Outline)"},
    "group_rows": {"vi": "Nhóm dòng", "en": "Group rows"},
    "group_cols": {"vi": "Nhóm cột", "en": "Group columns"},
    "ungroup_rows": {"vi": "Bỏ nhóm dòng", "en": "Ungroup rows"},
    "ungroup_cols": {"vi": "Bỏ nhóm cột", "en": "Ungroup columns"},
    "toggle_group_rows": {"vi": "Gập / mở nhóm dòng", "en": "Collapse / expand rows"},
    "toggle_group_cols": {"vi": "Gập / mở nhóm cột", "en": "Collapse / expand columns"},
    "table_create": {"vi": "Tạo bảng (Ctrl+T)", "en": "Create table (Ctrl+T)"},
    "table_total_row": {"vi": "Bật / tắt hàng Tổng", "en": "Toggle total row"},
    "table_remove": {"vi": "Bỏ bảng", "en": "Remove table"},
    "table_created": {"vi": "Đã tạo bảng", "en": "Table created"},
    "table_overlap": {"vi": "Vùng chồng lấn bảng có sẵn", "en": "Range overlaps an existing table"},
    "not_in_table": {"vi": "Ô không nằm trong bảng nào", "en": "Cell is not in a table"},
    "total_label": {"vi": "Tổng", "en": "Total"},
    "flash_fill": {"vi": "Flash Fill (Ctrl+E)", "en": "Flash Fill (Ctrl+E)"},
    "flash_no_source": {"vi": "Cần một cột dữ liệu bên trái để suy mẫu.", "en": "Need a source column to the left."},
    "flash_need_example": {"vi": "Hãy gõ ít nhất một ví dụ ở cột này trước.", "en": "Type at least one example in this column first."},
    "flash_no_pattern": {"vi": "Không suy được mẫu để điền.", "en": "Could not infer a fill pattern."},
    "flash_done": {"vi": "Đã điền theo mẫu", "en": "Filled by example"},
    "trace_prec": {"vi": "Truy vết ô tham chiếu (cùng sheet)", "en": "Trace precedents (same sheet)"},
    "trace_dep": {"vi": "Truy vết ô phụ thuộc (cùng sheet)", "en": "Trace dependents (same sheet)"},
    "trace_prec_none": {"vi": "Ô này không tham chiếu ô nào.", "en": "This cell references no cells."},
    "trace_dep_none": {"vi": "Không ô nào phụ thuộc ô này.", "en": "No cells depend on this cell."},
    "total_row_busy": {
        "vi": "Dòng dưới bảng đang có dữ liệu — không thể thêm hàng Tổng.",
        "en": "The row below the table is not empty — cannot add a total row.",
    },
    # --- menu: Dữ liệu ---
    "menu_data": {"vi": "&Dữ liệu", "en": "&Data"},
    "autosum": {"vi": "Tự động tính tổng (AutoSum)", "en": "AutoSum"},
    "insert_date": {"vi": "Chèn ngày hôm nay", "en": "Insert current date"},
    "insert_time": {"vi": "Chèn giờ hiện tại", "en": "Insert current time"},
    "show_formulas": {"vi": "Hiện công thức", "en": "Show Formulas"},
    "zoom_reset_tip": {
        "vi": "Mức phóng to — bấm để về 100% (Ctrl + lăn chuột để phóng)",
        "en": "Zoom level — click to reset to 100% (Ctrl + scroll to zoom)",
    },
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
    "multi_range_copy": {
        "vi": "Không thể dùng lệnh này cho nhiều vùng chọn.",
        "en": "That command cannot be used on multiple selections.",
    },
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
    # --- Status Bar statistics (Spec 11.2) ---
    "stat_average": {"vi": "Trung bình", "en": "Average"},
    "stat_count": {"vi": "Đếm", "en": "Count"},
    "stat_numerical_count": {"vi": "Đếm số", "en": "Numerical Count"},
    "stat_min": {"vi": "Nhỏ nhất", "en": "Min"},
    "stat_max": {"vi": "Lớn nhất", "en": "Max"},
    "stat_sum": {"vi": "Tổng", "en": "Sum"},
    "statusbar_customize": {"vi": "Tùy chỉnh thanh trạng thái", "en": "Customize Status Bar"},
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
    "cond_begins": {"vi": "Bắt đầu bằng", "en": "Begins with"},
    "cond_ends": {"vi": "Kết thúc bằng", "en": "Ends with"},
    "cond_duplicate": {"vi": "Giá trị trùng lặp", "en": "Duplicate values"},
    "cond_above_avg": {"vi": "Trên trung bình", "en": "Above average"},
    "cond_below_avg": {"vi": "Dưới trung bình", "en": "Below average"},
    "cond_top_n": {"vi": "Top N lớn nhất", "en": "Top N"},
    "cond_manage": {"vi": "Quản lý quy tắc...", "en": "Manage rules..."},
    "cond_delete": {"vi": "Xóa quy tắc", "en": "Delete rule"},
    "cond_clear_all": {"vi": "Xóa tất cả", "en": "Clear all"},
    "cond_value": {"vi": "Giá trị", "en": "Value"},
    "cond_value2": {"vi": "Giá trị thứ hai", "en": "Second value"},
    "cond_pick_color": {"vi": "Chọn màu tô", "en": "Pick fill color"},
    "cond_invalid": {"vi": "Giá trị không hợp lệ", "en": "Invalid value"},
    "wrap_overflow": {"vi": "Tràn", "en": "Overflow"},
    "wrap_wrap": {"vi": "Xuống dòng", "en": "Wrap"},
    "wrap_clip": {"vi": "Cắt", "en": "Clip"},
    "paste_special": {"vi": "Dán đặc biệt...", "en": "Paste Special..."},
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
    # --- hộp thoại Dán đặc biệt (Ctrl+Alt+V) ---
    "ps_paste_group": {"vi": "Dán", "en": "Paste"},
    "ps_all": {"vi": "Tất cả", "en": "All"},
    "ps_formulas": {"vi": "Công thức", "en": "Formulas"},
    "ps_values": {"vi": "Giá trị", "en": "Values"},
    "ps_formats": {"vi": "Định dạng", "en": "Formats"},
    "ps_op_group": {"vi": "Phép tính", "en": "Operation"},
    "ps_op_none": {"vi": "Không", "en": "None"},
    "ps_op_add": {"vi": "Cộng", "en": "Add"},
    "ps_op_sub": {"vi": "Trừ", "en": "Subtract"},
    "ps_op_mul": {"vi": "Nhân", "en": "Multiply"},
    "ps_op_div": {"vi": "Chia", "en": "Divide"},
    "ps_skip_blanks": {"vi": "Bỏ qua ô trống", "en": "Skip blanks"},
    "ps_transpose": {"vi": "Xoay hàng / cột", "en": "Transpose"},
    # --- hộp thoại Định dạng ô (Ctrl+1) ---
    "format_cells": {"vi": "Định dạng ô", "en": "Format Cells"},
    "fc_tab_number": {"vi": "Số", "en": "Number"},
    "fc_tab_align": {"vi": "Căn lề", "en": "Alignment"},
    "fc_tab_font": {"vi": "Phông chữ", "en": "Font"},
    "fc_tab_border": {"vi": "Viền", "en": "Border"},
    "fc_tab_fill": {"vi": "Tô màu", "en": "Fill"},
    "fc_tab_protect": {"vi": "Bảo vệ", "en": "Protection"},
    "fc_category": {"vi": "Thể loại:", "en": "Category:"},
    "fc_decimals": {"vi": "Số chữ số thập phân:", "en": "Decimal places:"},
    "fc_thousands": {"vi": "Dùng dấu phân tách hàng nghìn", "en": "Use thousands separator"},
    "fc_custom_code": {"vi": "Mã định dạng tùy chỉnh:", "en": "Custom format code:"},
    "fc_sample": {"vi": "Mẫu:", "en": "Sample:"},
    "fc_horizontal": {"vi": "Theo chiều ngang:", "en": "Horizontal:"},
    "fc_vertical": {"vi": "Theo chiều dọc:", "en": "Vertical:"},
    "fc_halign_general": {"vi": "Tự động", "en": "General"},
    "fc_font_family": {"vi": "Phông:", "en": "Font:"},
    "fc_font_size": {"vi": "Cỡ:", "en": "Size:"},
    "fc_no_color": {"vi": "Tự động", "en": "Automatic"},
    "fc_no_fill": {"vi": "Không tô màu", "en": "No fill"},
    "fc_pick_color": {"vi": "Chọn màu...", "en": "Pick color..."},
    "fc_border_preset": {"vi": "Kiểu viền:", "en": "Border preset:"},
    "fc_locked": {"vi": "Khóa ô", "en": "Locked"},
    "fc_hidden": {"vi": "Ẩn công thức", "en": "Hidden"},
    "fc_protect_note": {
        "vi": "Khóa ô / ẩn công thức chỉ có hiệu lực sau khi bật Bảo vệ trang tính.",
        "en": "Locking cells or hiding formulas has no effect until you protect the sheet.",
    },
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
