from __future__ import annotations

from typing import Any

from .. import make_canvas
from app.render.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel,
    draw_char_icon, draw_stars,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    PADDING,
)


async def render_rank_list(data: dict[str, Any]) -> bytes:
    title = data.get("title", "排名")
    mode = data.get("mode", "dmg")
    rank_list = data.get("list", [])
    rank_cfg = data.get("rankCfg", {})

    if not rank_list:
        c = make_canvas(800, 400, BG_PAGE)
        c.text("暂无排名数据", 400, 200, font_size=36,
               color=TEXT_LIGHT, anchor="mm")
        return c.to_bytes()

    cw = 1200
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160
    item_h = 120
    gap = 12

    total = len(rank_list)
    ch = header_h + 30 + total * (item_h + gap) + 80
    c = make_canvas(cw, max(500, ch), BG_PAGE)

    # ── background ──
    bg_img = None
    if c.assets:
        bg_img = c.assets.dmg_rank_bg()
    if bg_img:
        c.image(bg_img, 0, 0, cw, ch)

    draw_panel_header(c, cw, title)

    y = header_h + 30

    # rank info
    time_str = rank_cfg.get("time", "")
    limit_txt = rank_cfg.get("limitTxt", "无限制")
    number = rank_cfg.get("number", 0)
    draw_shadow_panel(c, margin, y, card_w, 60)
    c.text(f"排名范围: 本群 / {time_str} / 面板更新",
           margin + PADDING, y + 12, font_size=20, color=TEXT_MED)
    c.text(f"参与条件: {limit_txt}  人数: {number}",
           margin + PADDING, y + 38, font_size=18, color=TEXT_LIGHT)
    y += 80

    for i, ds in enumerate(rank_list):
        rank = i + 1
        sname = ds.get("sName", ds.get("name", ""))
        cons = ds.get("cons", 0)
        star = ds.get("star", 5)
        face = ds.get("imgs", {}).get("face", "") if isinstance(ds.get("imgs"), dict) else ""

        draw_shadow_panel(c, margin, y, card_w, item_h)

        # rank number badge
        if rank <= 3:
            medal_colors = [(255, 215, 0), (200, 200, 210), (200, 150, 100)]
            mc = medal_colors[rank - 1]
            c.rect(margin + 12, y + 10, 44, item_h - 20, radius=10, fill=mc + (200,))
        else:
            c.rect(margin + 12, y + 10, 44, item_h - 20, radius=10,
                   fill=(180, 180, 190, 80))
        c.text(f"#{rank}", margin + 34, y + item_h // 2,
               font_size=26, color=(255, 255, 255), anchor="mm")

        if face:
            draw_char_icon(c, face, margin + 72, y + 12, 80, star=star)

        c.text(sname, margin + 170, y + 18, font_size=28, color=TEXT_DARK)
        c.text(f"{cons}命", margin + 170, y + 56, font_size=22, color=TEXT_MED)
        draw_stars(c, margin + 170 + 80, y + 60, star, 14)

        val = ds.get("value", ds.get("dmg", 0))
        if val:
            val_str = _format_val(val)
            tw = c.text_size(val_str, font_size=28)[0]
            c.text(val_str, margin + card_w - tw - 24, y + item_h // 2 - 8,
                   font_size=28, color=ACCENT_BLUE, anchor="mt")

        y += item_h + gap

    draw_footer(c, cw, y + 10)
    return c.to_bytes()


def _format_val(v: Any) -> str:
    try:
        vf = float(v)
        if vf >= 10000:
            return f"{vf / 10000:.1f}万"
        if vf >= 1000:
            return f"{vf:.0f}"
        return f"{vf:.2f}"
    except (ValueError, TypeError):
        return str(v)
