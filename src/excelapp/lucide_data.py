"""Dữ liệu icon Lucide (https://lucide.dev, ISC license) — nhúng sẵn.

Sinh tự động từ assets/icons/*.svg. Mỗi value là phần tử con bên trong
<svg> (đã bỏ wrapper) — stroke="currentColor" giữ nguyên để tô màu lúc render.
"""

from __future__ import annotations

ICONS: dict[str, str] = {
    "align_center": "<path d=\"M21 5H3\" /><path d=\"M17 12H7\" /><path d=\"M19 19H5\" />",
    "align_left": "<path d=\"M21 5H3\" /><path d=\"M15 12H3\" /><path d=\"M17 19H3\" />",
    "align_right": "<path d=\"M21 5H3\" /><path d=\"M21 12H9\" /><path d=\"M21 19H7\" />",
    "bold": "<path d=\"M6 12h9a4 4 0 0 1 0 8H7a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h7a4 4 0 0 1 0 8\" />",
    "borders": "<path d=\"M12 3v18\" /><rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" /><path d=\"M3 9h18\" /><path d=\"M3 15h18\" />",
    "cond_format": "<path d=\"M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z\" /><circle cx=\"13.5\" cy=\"6.5\" r=\".5\" fill=\"currentColor\" /><circle cx=\"17.5\" cy=\"10.5\" r=\".5\" fill=\"currentColor\" /><circle cx=\"6.5\" cy=\"12.5\" r=\".5\" fill=\"currentColor\" /><circle cx=\"8.5\" cy=\"7.5\" r=\".5\" fill=\"currentColor\" />",
    "copy": "<rect width=\"14\" height=\"14\" x=\"8\" y=\"8\" rx=\"2\" ry=\"2\" /><path d=\"M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2\" />",
    "cut": "<circle cx=\"6\" cy=\"6\" r=\"3\" /><path d=\"M8.12 8.12 12 12\" /><path d=\"M20 4 8.12 15.88\" /><circle cx=\"6\" cy=\"18\" r=\"3\" /><path d=\"M14.8 14.8 20 20\" />",
    "fill_color": "<path d=\"M11 7 6 2\" /><path d=\"M18.992 12H2.041\" /><path d=\"M21.145 18.38A3.34 3.34 0 0 1 20 16.5a3.3 3.3 0 0 1-1.145 1.88c-.575.46-.855 1.02-.855 1.595A2 2 0 0 0 20 22a2 2 0 0 0 2-2.025c0-.58-.285-1.13-.855-1.595\" /><path d=\"m8.5 4.5 2.148-2.148a1.205 1.205 0 0 1 1.704 0l7.296 7.296a1.205 1.205 0 0 1 0 1.704l-7.592 7.592a3.615 3.615 0 0 1-5.112 0l-3.888-3.888a3.615 3.615 0 0 1 0-5.112L5.67 7.33\" />",
    "filter": "<path d=\"M10 20a1 1 0 0 0 .553.895l2 1A1 1 0 0 0 14 21v-7a2 2 0 0 1 .517-1.341L21.74 4.67A1 1 0 0 0 21 3H3a1 1 0 0 0-.742 1.67l7.225 7.989A2 2 0 0 1 10 14z\" />",
    "find": "<path d=\"m21 21-4.34-4.34\" /><circle cx=\"11\" cy=\"11\" r=\"8\" />",
    "font_color": "<path d=\"M4 20h16\" /><path d=\"m6 16 6-12 6 12\" /><path d=\"M8 12h8\" />",
    "italic": "<line x1=\"19\" x2=\"10\" y1=\"4\" y2=\"4\" /><line x1=\"14\" x2=\"5\" y1=\"20\" y2=\"20\" /><line x1=\"15\" x2=\"9\" y1=\"4\" y2=\"20\" />",
    "merge": "<path d=\"M12 21v-6\" /><path d=\"M12 9V3\" /><path d=\"M3 15h18\" /><path d=\"M3 9h18\" /><rect width=\"18\" height=\"18\" x=\"3\" y=\"3\" rx=\"2\" />",
    "number_format": "<line x1=\"4\" x2=\"20\" y1=\"9\" y2=\"9\" /><line x1=\"4\" x2=\"20\" y1=\"15\" y2=\"15\" /><line x1=\"10\" x2=\"8\" y1=\"3\" y2=\"21\" /><line x1=\"16\" x2=\"14\" y1=\"3\" y2=\"21\" />",
    "paste": "<path d=\"M11 14h10\" /><path d=\"M16 4h2a2 2 0 0 1 2 2v1.344\" /><path d=\"m17 18 4-4-4-4\" /><path d=\"M8 4H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 1.793-1.113\" /><rect x=\"8\" y=\"2\" width=\"8\" height=\"4\" rx=\"1\" />",
    "redo": "<path d=\"m15 14 5-5-5-5\" /><path d=\"M20 9H9.5A5.5 5.5 0 0 0 4 14.5A5.5 5.5 0 0 0 9.5 20H13\" />",
    "sort_asc": "<path d=\"m3 8 4-4 4 4\" /><path d=\"M7 4v16\" /><path d=\"M11 12h4\" /><path d=\"M11 16h7\" /><path d=\"M11 20h10\" />",
    "sort_desc": "<path d=\"m3 16 4 4 4-4\" /><path d=\"M7 20V4\" /><path d=\"M11 4h10\" /><path d=\"M11 8h7\" /><path d=\"M11 12h4\" />",
    "strike": "<path d=\"M16 4H9a3 3 0 0 0-2.83 4\" /><path d=\"M14 12a4 4 0 0 1 0 8H6\" /><line x1=\"4\" x2=\"20\" y1=\"12\" y2=\"12\" />",
    "underline": "<path d=\"M6 4v6a6 6 0 0 0 12 0V4\" /><line x1=\"4\" x2=\"20\" y1=\"20\" y2=\"20\" />",
    "undo": "<path d=\"M9 14 4 9l5-5\" /><path d=\"M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11\" />",
    "valign_bottom": "<rect width=\"14\" height=\"6\" x=\"5\" y=\"12\" rx=\"2\" /><rect width=\"10\" height=\"6\" x=\"7\" y=\"2\" rx=\"2\" /><path d=\"M2 22h20\" />",
    "valign_middle": "<rect width=\"14\" height=\"6\" x=\"5\" y=\"16\" rx=\"2\" /><rect width=\"10\" height=\"6\" x=\"7\" y=\"2\" rx=\"2\" /><path d=\"M2 12h20\" />",
    "valign_top": "<rect width=\"14\" height=\"6\" x=\"5\" y=\"16\" rx=\"2\" /><rect width=\"10\" height=\"6\" x=\"7\" y=\"6\" rx=\"2\" /><path d=\"M2 2h20\" />",
    "wrap_clip": "<path d=\"M2 12h6\" /><path d=\"M22 12h-6\" /><path d=\"M12 2v2\" /><path d=\"M12 8v2\" /><path d=\"M12 14v2\" /><path d=\"M12 20v2\" /><path d=\"m19 9-3 3 3 3\" /><path d=\"m5 15 3-3-3-3\" />",
    "wrap_overflow": "<path d=\"m18 8 4 4-4 4\" /><path d=\"M2 12h20\" /><path d=\"m6 8-4 4 4 4\" />",
    "wrap_text": "<path d=\"m16 16-3 3 3 3\" /><path d=\"M3 12h14.5a1 1 0 0 1 0 7H13\" /><path d=\"M3 19h6\" /><path d=\"M3 5h18\" />",
}
