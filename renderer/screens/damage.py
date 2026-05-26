from __future__ import annotations

from typing import Any

from .. import make_canvas
from ...vendored.pillow_elements import (
    draw_footer, draw_shadow_panel,
    TEXT_DARK, TEXT_LIGHT, BG_CARD,
    PADDING, CARD_PADDING, elem_color,
)


async def render_damage(data: dict[str, Any]) -> bytes:
    char_name = data.get("charName", "")
    elem = data.get("elem", "physical")
    game = data.get("game", "sr")
    results = data.get("results", [])
    enemy_lv = data.get("enemyLv", 103)

    elem_c = elem_color(elem)
    cw = 1120
    margin = PADDING
    card_w = cw - margin * 2
    pad = CARD_PADDING

    header_h = 160
    item_h = 68
    gap = 12

    total = len(results)
    y = header_h + 24
    c = make_canvas(cw, header_h + 24 + total * (item_h + gap) + 80, (245, 243, 240, 255))

    # header
    c.gradient(0, 0, cw, header_h, elem_c[:3] + (255,), tuple(max(0, v - 60) for v in elem_c[:3]) + (255,))
    c.text(f"{char_name} 伤害计算", cw // 2, 36, font_name="NZBZ",
           font_size=52, color=(255, 255, 255), anchor="mt")
    c.text(f"敌方等级 {enemy_lv}", cw // 2, 100,
           font_size=26, color=(200, 210, 240, 255), anchor="mt")

    for i, r in enumerate(results):
        is_def = r.get("isDefault", False)
        title = r.get("title", f"伤害{i+1}")
        avg = r.get("avg", 0)
        crit = r.get("crit", 0)
        raw = r.get("raw", 0)
        no_crit = r.get("noCrit", 0)
        stat = r.get("stat", "atk").upper()
        mp = r.get("multiplier", 0)

        draw_shadow_panel(c, margin, y, card_w, item_h, radius=12,
                          fill=(255, 255, 255, 245) if is_def else BG_CARD)

        # Left accent bar for default
        if is_def:
            c.rect(margin + pad, y + 8, 5, item_h - 16, radius=3, fill=elem_c)

        # Title
        tx = margin + pad + (16 if is_def else 8)
        c.text(title, tx, y + 14, font_size=24, color=TEXT_DARK)

        # Multiplier info
        c.text(f"倍率 {mp*100:.1f}%  |  {stat}", tx, y + 44,
               font_size=18, color=TEXT_LIGHT)

        # Damage numbers (right-aligned)
        avg_str = _fmt_dmg(avg)
        crit_str = _fmt_dmg(crit)
        no_crit_str = _fmt_dmg(no_crit)
        raw_str = _fmt_dmg(raw)

        rx = margin + card_w - pad
        c.text(f"暴击", rx - 20, y + 12, font_size=18, color=TEXT_LIGHT, anchor="rt")
        c.text(crit_str, rx - 20, y + 38, font_size=26, color=elem_c, anchor="rt")

        c.text(f"期望", rx - 230, y + 12, font_size=18, color=TEXT_LIGHT, anchor="rt")
        c.text(avg_str, rx - 230, y + 38, font_size=26, color=TEXT_DARK, anchor="rt")

        c.text(f"不暴击", rx - 420, y + 12, font_size=18, color=TEXT_LIGHT, anchor="rt")
        c.text(no_crit_str, rx - 420, y + 38, font_size=26, color=TEXT_DARK, anchor="rt")

        y += item_h + gap

    draw_footer(c, cw, y + 10)
    c.crop_to(y + 60)
    return c.to_bytes()


def _fmt_dmg(val: float) -> str:
    if val >= 1000000:
        return f"{val/10000:.0f}万"
    if val >= 10000:
        return f"{val/10000:.2f}万"
    return f"{val:.0f}"
