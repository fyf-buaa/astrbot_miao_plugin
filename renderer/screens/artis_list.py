from __future__ import annotations

from typing import Any

from .. import make_canvas
from app.render.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel, draw_char_icon,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    PADDING, CARD_PADDING,
)

async def render_artis_list(data: dict[str, Any]) -> bytes:
    artis = data.get("artis", [])
    uid = data.get("uid", "") or data.get("uid_text", "")
    game = data.get("game", "gs")

    if not artis:
        c = make_canvas(800, 400, BG_PAGE)
        c.text("暂无圣遗物数据", 400, 200, font_size=36,
               color=TEXT_LIGHT, anchor="mm")
        return c.to_bytes()

    cw = 1200
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160
    item_h = 160
    gap = 16

    total = len(artis)
    y = header_h + 30

    c = make_canvas(cw, header_h + 30 + total * (item_h + gap) + 60, BG_PAGE)
    draw_panel_header(c, cw, "圣遗物列表", f"UID: {uid}")

    key_title = data.get("artisKeyTitle", {})

    for i, arti in enumerate(artis):
        name = arti.get("charName", "") or arti.get("name", "")
        char_name = arti.get("charName", "")
        face = arti.get("face", "")
        img = arti.get("img", "")
        main = arti.get("main", {})
        attrs = arti.get("attrs", [])
        mark = arti.get("mark", 0)
        mark_cls = arti.get("markClass", "")
        star = arti.get("star", 5)
        level = arti.get("level", 0)

        draw_shadow_panel(c, margin, y, card_w, item_h)

        if face:
            draw_char_icon(c, face, margin + 12, y + 12, 80, star=star)
        if img:
            c.image(img, margin + 120, y + 20, w=70, h=70)

        c.text(name, margin + 210, y + 14, font_size=26, color=TEXT_DARK)
        mc = (80, 200, 80) if "S" in str(mark_cls) else (
            (200, 180, 80) if "A" in str(mark_cls) else TEXT_LIGHT)
        c.text(f"{mark:.1f}分 - {mark_cls}", margin + 210, y + 50,
               font_size=22, color=mc)
        c.text(f"+{level}", margin + 210, y + 82,
               font_size=22, color=TEXT_LIGHT)

        mk = main.get("key", "")
        mv = main.get("value", 0)
        if mk:
            mk_label = key_title.get(mk, mk)
            c.text(mk_label, margin + card_w - 200, y + 16,
                   font_size=22, color=TEXT_MED)
            c.text(f"+{mv}", margin + card_w - 100, y + 16,
                   font_size=22, color=ACCENT_BLUE)

        ax = margin + card_w - 300
        ay = y + 50
        for attr in attrs[:4]:
            ak = attr.get("key", "")
            av = attr.get("value", 0)
            if ak:
                ak_label = key_title.get(ak, ak)
                c.text(ak_label, ax, ay, font_size=18, color=TEXT_LIGHT)
                sw = c.text_size(ak_label, font_size=18)[0]
                c.text(f"+{av}", ax + sw + 8, ay,
                       font_size=18, color=TEXT_DARK)
                ay += 26

        y += item_h + gap

    draw_footer(c, cw, y + 10)
    return c.to_bytes()
