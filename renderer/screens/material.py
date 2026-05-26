from __future__ import annotations

from typing import Any

from .. import make_canvas
from app.render.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel,
    draw_char_icon, draw_stars,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    PADDING, CARD_PADDING,
)


async def render_today_material(data: dict[str, Any]) -> bytes:
    uid = data.get("uid", "")
    day = data.get("day", "")
    city_data = data.get("data", [])
    game = data.get("game", "gs")

    if game == "sr" or not city_data:
        c = make_canvas(800, 400, BG_PAGE)
        c.text("今日材料", 400, 160, font_name="NZBZ", font_size=48,
               color=TEXT_DARK, anchor="mm")
        c.text("暂无数据", 400, 260, font_size=32,
               color=TEXT_LIGHT, anchor="mm")
        return c.to_bytes()

    cw = 1200
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160
    item_h = 140
    gap = 16

    total = len(city_data)
    ch = header_h + 40 + total * (item_h + gap) + 100
    c = make_canvas(cw, max(500, ch), BG_PAGE)
    draw_panel_header(c, cw, "今日材料", f"{day}  UID: {uid}")

    y = header_h + 40
    for cd in city_data:
        city = cd.get("city", "")
        mtype = cd.get("type", "talent")
        material = cd.get("material", {})
        chars = cd.get("data", [])

        # city header
        type_label = "天赋材料" if mtype == "talent" else "武器材料"
        c.rect(margin, y, card_w, 50, radius=14, fill=ACCENT_BLUE[:3] + (40,))
        c.text(f"{city} - {type_label}", margin + CARD_PADDING, y + 10,
               font_size=26, color=TEXT_DARK)

        mat_name = material.get("name", "")
        if mat_name:
            tw = c.text_size(mat_name, font_size=22)[0]
            c.text(mat_name, margin + card_w - tw - CARD_PADDING, y + 14,
                   font_size=22, color=TEXT_MED)
        y += 60

        # character grid
        per_row = 3
        card_w_item = (card_w - CARD_PADDING * 2 - gap * (per_row - 1)) // per_row
        for idx, char in enumerate(chars[:6]):
            col = idx % per_row
            row = idx // per_row
            cx = margin + CARD_PADDING + col * (card_w_item + gap)
            cy = y + row * (item_h)

            c.rect(cx, cy, card_w_item, item_h - 30, radius=12, fill=BG_CARD)
            face = char.get("face", "")
            if face:
                c.image(face, cx + (card_w_item - 60) // 2, cy + 8, w=60, h=60)
            cn = char.get("name", "")
            c.text(cn, cx + card_w_item // 2, cy + 76,
                   font_size=22, color=TEXT_DARK, anchor="mt")
            cl = char.get("level", 0)
            cc = char.get("cons", 0)
            c.text(f"Lv.{cl}  {cc}命", cx + card_w_item // 2, cy + 104,
                   font_size=18, color=TEXT_LIGHT, anchor="mt")

        y += ((len(chars) + per_row - 1) // per_row) * item_h + gap

    draw_footer(c, cw, y + 10)
    return c.to_bytes()


async def render_calendar(data: dict[str, Any]) -> bytes:
    date_list = data.get("dateList", [])
    now_date = data.get("nowDate", 0)
    char_birth = data.get("charBirth", {})
    game = data.get("game", "gs")

    cw = 1200
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160

    days_total = max((sum(len(d.get("date", [])) for d in date_list)), 1)
    cell_w = min((card_w - 20) // days_total, 120)
    cell_h = 80
    rows = 3

    ch = header_h + 40 + rows * (cell_h + 4) + 60
    c = make_canvas(cw, max(500, ch), BG_PAGE)

    # ── theme background ──
    if c.assets:
        cal_bg = c.assets.resolve("wiki/imgs/calendar-icon.png")
    draw_panel_header(c, cw, "日历", "角色生日")

    y = header_h + 30
    cx = margin

    for d in date_list:
        month = d.get("month", 0)
        dates = d.get("date", [])
        weeks = d.get("week", [])

        mc = (100, 140, 220, 200) if game == "gs" else (160, 100, 200, 200)
        span = len(dates)
        c.rect(cx, y, cell_w * span + 8, 40, radius=8, fill=mc)
        c.text(f"{month}月", cx + (cell_w * span + 8) // 2, y + 6,
               font_size=22, color=(255, 255, 255), anchor="mt")
        y += 44

        week_names = "一二三四五六日"
        for i, dn in enumerate(dates):
            wx = cx + i * cell_w
            is_today = dn == now_date
            bg = (60, 100, 200, 80) if is_today else (255, 255, 255, 200)
            c.rect(wx, y, cell_w - 4, cell_h, radius=8, fill=bg)

            c.text(f"{dn}日", wx + (cell_w - 4) // 2, y + 4,
                   font_size=20, color=TEXT_DARK, anchor="mt")
            if i < len(weeks):
                wn = week_names[weeks[i]] if weeks[i] < len(week_names) else ""
                c.text(f"周{wn}", wx + (cell_w - 4) // 2, y + 30,
                       font_size=16, color=TEXT_LIGHT, anchor="mt")

            mmdd = f"{month}-{dn}"
            births = char_birth.get(mmdd, [])
            b_y = y + 54
            for b in births[:2]:
                bn = b.get("name", "")[:3]
                bs = b.get("star", 5)
                bc = (255, 215, 0, 200) if bs >= 5 else (200, 100, 255, 200)
                c.text(bn, wx + (cell_w - 4) // 2, b_y,
                       font_size=16, color=bc, anchor="mt")
                b_y += 20

        y += cell_h + 8
        y += 4 if game == "gs" else 44

    draw_footer(c, cw, y + 20)
    return c.to_bytes()
