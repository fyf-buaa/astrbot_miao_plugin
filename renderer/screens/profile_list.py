from __future__ import annotations

from typing import Any

from PIL import Image

from .. import make_canvas
from ...vendored.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    RARITY_BORDER, PADDING, CARD_GAP,
)


async def render_profile_list(data: dict[str, Any]) -> bytes:
    chars = data.get("characters", []) or data.get("chars", [])
    player_name = data.get("playerName", data.get("uid", ""))

    cw = 1200
    per_row = 6
    card_w = 180
    card_h = 280
    gap = CARD_GAP
    margin = PADDING
    rows = (len(chars) + per_row - 1) // per_row
    header_h = 160
    footer_h = 60
    ch = header_h + 30 + rows * (card_h + gap) + footer_h

    c = make_canvas(cw, ch, BG_PAGE)

    # ── background ──
    bg_img = None
    if c.assets:
        bg_img = c.assets.profile_bg(1)
    if bg_img:
        c.image(bg_img, 0, 0, cw, ch)
        c.overlay(0, 0, cw, ch, (0, 0, 0, 30))
    draw_panel_header(c, cw, player_name, "角色面板列表")

    y = header_h + 30
    for i, ch_data in enumerate(chars):
        row = i // per_row
        col = i % per_row
        cx = margin + col * (card_w + gap)
        cy = y + row * (card_h + gap)

        star = ch_data.get("star", 5)
        border_c = RARITY_BORDER.get(star, (255, 215, 0, 200))

        # card background with rarity glow
        c.rect(cx, cy, card_w, card_h, radius=14, fill=(255, 255, 255, 240))
        c.rect(cx - 1, cy - 1, card_w + 2, card_h + 2, radius=15,
               fill=border_c[:3] + (40,))

        # avatar with frame
        face = ch_data.get("face", "")
        if face:
            # compose avatar with frame
            if c.assets:
                composed = c.assets.compose_avatar_frame(face, star, 100)
                if composed:
                    c.sprite(composed, cx + (card_w - 108) // 2, cy + 12)
                else:
                    c.image(face, cx + 30, cy + 16, w=120, h=120)
            else:
                c.image(face, cx + 30, cy + 16, w=120, h=120)

        name = ch_data.get("name", "")
        c.text(name, cx + card_w // 2, cy + 136,
               font_size=26, color=TEXT_DARK, anchor="mt")
        lv = ch_data.get("level", 0)
        con = ch_data.get("cons", 0)
        elem = ch_data.get("elem", "")
        c.text(f"Lv.{lv}  C{con}", cx + card_w // 2, cy + 172,
               font_size=20, color=TEXT_MED, anchor="mt")

        # star rating at bottom
        star_count = ch_data.get("star", 5)
        star_total_w = star_count * 18 + (star_count - 1) * 4
        star_x = cx + (card_w - star_total_w) // 2
        for s in range(star_count):
            c.rect(star_x + s * 22, cy + card_h - 36, 18, 18, radius=9,
                   fill=(255, 215, 0, 200))

    draw_footer(c, cw, ch - footer_h)
    return c.to_bytes()
