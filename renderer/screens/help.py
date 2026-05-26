from __future__ import annotations

import re
from typing import Any

from .. import make_canvas
from ...vendored.pillow_elements import (
    draw_panel_header, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE,
    BG_CARD, PADDING, CARD_PADDING, CARD_GAP,
)


async def render_help(data: dict[str, Any]) -> bytes:
    help_cfg = data.get("helpCfg", {})
    help_groups = data.get("helpGroup", [])
    title = help_cfg.get("title", "使用帮助")
    subtitle = help_cfg.get("subTitle", "Yunzai-Bot & Miao-Plugin")

    canvas_w = 2000
    row_h = 96
    header_h = 280
    footer_h = 80
    group_header_h = 70
    group_margin = 30
    content_x = 80
    content_w = canvas_w - content_x * 2
    per_row = 3
    col_w = (content_w - CARD_GAP * (per_row - 1)) // per_row

    items: list[dict] = []
    for group in help_groups:
        for h in group.get("list", []):
            items.append(h)

    total_items = len(items)
    total_rows = (total_items + per_row - 1) // per_row
    group_count = len(help_groups)
    groups_height = group_count * group_header_h + max(1, group_count) * group_margin + total_rows * row_h
    canvas_h = header_h + groups_height + footer_h + 60

    c = make_canvas(canvas_w, canvas_h, (245, 240, 235, 255))

    # ── header with theme bg ──
    header_img = None
    if c.assets:
        header_img = c.assets.resolve("help/theme/default/main.png")
    if header_img and header_img.exists():
        c.image("help/theme/default/main.png", 0, 0, canvas_w, header_h)
        c.overlay(0, 0, canvas_w, header_h, (0, 0, 0, 80))
    else:
        c.gradient(0, 0, canvas_w, header_h, (80, 120, 200, 255), (60, 80, 160, 255))

    c.text(title, canvas_w // 2, 70, font_name="NZBZ", font_size=72,
           color=(255, 255, 255), anchor="mt")
    c.text(subtitle, canvas_w // 2, 160, font_size=30,
           color=(200, 210, 240, 255), anchor="mt")

    # ── help groups ──
    y_offset = header_h + 20
    for gi, group in enumerate(help_groups):
        gname = group.get("group", "")
        glist = group.get("list", [])
        if not glist:
            continue

        y_offset += group_margin

        # group header
        c.rect(content_x, y_offset, content_w, group_header_h, radius=12,
               fill=ACCENT_BLUE[:3] + (30,))
        c.rect(content_x + CARD_PADDING, y_offset + group_header_h - 3,
               60, 3, radius=2, fill=ACCENT_BLUE)
        c.text(gname, content_x + CARD_PADDING, y_offset + 18, font_size=32,
               color=TEXT_DARK)

        y_offset += group_header_h + 10

        for hi, h in enumerate(glist):
            col_idx = hi % per_row
            row_idx = hi // per_row

            ix = content_x + col_idx * (col_w + CARD_GAP)
            iy = y_offset + row_idx * row_h

            # card with left accent bar
            c.rect(ix, iy, col_w, row_h - 6, radius=12, fill=(255, 255, 255, 220))
            c.rect(ix + 12, iy + 12, 6, row_h - 36, radius=3, fill=(100, 140, 220))

            title_text = h.get("title", "")
            desc_text = h.get("desc", "")
            c.text(title_text, ix + 34, iy + 12, font_size=28, color=TEXT_DARK)
            if desc_text:
                c.text(desc_text, ix + 34, iy + 48, font_size=22, color=TEXT_LIGHT)

        y_offset += ((len(glist) + per_row - 1) // per_row) * row_h

    y_offset += 30
    c.text("Created By Miao-Plugin", canvas_w // 2, y_offset,
           font_size=22, color=TEXT_LIGHT, anchor="mt")

    return c.to_bytes()
