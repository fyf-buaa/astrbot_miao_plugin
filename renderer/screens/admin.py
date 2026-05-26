from __future__ import annotations

from typing import Any

from .. import make_canvas
from app.render.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    PADDING, CARD_PADDING, SECTION_GAP,
)


async def render_admin(data: dict[str, Any]) -> bytes:
    schema = data.get("schema", [])
    cfg = data.get("cfg", {})
    is_miao = data.get("isMiao", False)
    img_plus = data.get("imgPlus", False)

    cw = 1200
    y = 0
    header_h = 160
    margin = PADDING
    card_w = cw - margin * 2
    row_h = 60

    total_h = header_h + 30
    for group in schema:
        gcfg = group.get("cfg", {})
        total_h += 80 + len(gcfg) * (row_h + 8) + 30
    total_h += 80

    c = make_canvas(cw, max(600, total_h), BG_PAGE)
    draw_panel_header(c, cw, "喵喵管理面板", "#喵喵设置")

    y = header_h + 30
    for group in schema:
        title = group.get("title", "")
        gcfg = group.get("cfg", {})
        if not gcfg:
            continue
        c.rect(margin, y, card_w, 60, radius=14, fill=ACCENT_BLUE[:3] + (40,))
        c.text(title, margin + CARD_PADDING, y + 14, font_size=32, color=TEXT_DARK)
        y += 70

        for key, item in gcfg.items():
            draw_shadow_panel(c, margin, y, card_w, row_h)
            item_title = item.get("title", key)
            c.text(item_title, margin + CARD_PADDING, y + 14, font_size=26,
                   color=TEXT_DARK)

            val = cfg.get(key, "")
            is_on = bool(val) or (item.get("miao") and is_miao)
            if item.get("type") in ("num", "str"):
                val_text = str(val) if val else str(item.get("def", ""))
                tw = c.text_size(val_text, font_size=24)[0]
                c.text(val_text, margin + card_w - tw - CARD_PADDING, y + 16,
                       font_size=24, color=TEXT_MED)
            else:
                status = "默认开启" if (item.get("miao") and is_miao) else ("已开启" if is_on else "已关闭")
                col = (80, 200, 80) if is_on else (200, 100, 100)
                tw = c.text_size(status, font_size=24)[0]
                c.text(status, margin + card_w - tw - CARD_PADDING, y + 16,
                       font_size=24, color=col)
            y += row_h + 8

    img_txt = "已安装" if img_plus else "未安装"
    c.text(f"图片扩展包: {img_txt}", margin, y + 10,
           font_size=22, color=TEXT_LIGHT)
    y += 50

    draw_footer(c, cw, y)
    return c.to_bytes()


async def render_version_info(data: dict[str, Any]) -> bytes:
    versions = data.get("changelogs", [])
    current = data.get("currentVersion", "")

    cw = 1000
    y = 0
    header_h = 160
    margin = PADDING
    card_w = cw - margin * 2

    total_h = header_h + 30
    for v in versions:
        logs = v.get("logs", [])
        total_h += 80 + len(logs) * 60 + 30
    total_h += 60

    c = make_canvas(cw, max(400, total_h), BG_PAGE)
    draw_panel_header(c, cw, "版本信息")

    y = header_h + 30
    for v in versions:
        ver = v.get("version", "")
        is_dev = ver.endswith("v")
        logs = v.get("logs", [])

        c.rect(margin, y, card_w, 60, radius=14, fill=ACCENT_BLUE[:3] + (40,))
        ver_label = "当前版本" if is_dev else "喵喵版本"
        c.text(f"{ver_label} {ver}", margin + CARD_PADDING, y + 14,
               font_size=32, color=TEXT_DARK)
        y += 70

        for log_entry in logs:
            title = log_entry.get("title", "")
            sub_logs = log_entry.get("logs", [])

            c.text(title, margin + CARD_PADDING, y + 4, font_size=24, color=TEXT_DARK,
                   max_width=card_w - CARD_PADDING * 2)
            tw, th = c.text_size(title, font_size=24)
            y += th + 8

            for sl in sub_logs[:5]:
                c.text(f"· {sl}", margin + CARD_PADDING + 20, y + 2,
                       font_size=20, color=TEXT_MED, max_width=card_w - 68)
                y += 36
            y += 10

    draw_footer(c, cw, y)
    return c.to_bytes()
