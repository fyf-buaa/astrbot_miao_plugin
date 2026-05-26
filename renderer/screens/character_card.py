from __future__ import annotations

from typing import Any

from .. import make_canvas
from ...vendored.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel,
    draw_section_title, draw_badge, draw_stars,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    COLOR_ELEM, elem_color, elem_gradient, RARITY_BORDER,
    PADDING, CARD_PADDING, SECTION_GAP,
)


async def render_character_card(data: dict[str, Any]) -> bytes:
    card = data.get("data", {})
    uid = data.get("uid", "")
    bg = data.get("bg", {})
    char_name = card.get("name", "")
    elem = card.get("elem", "hydro")
    elem_c = elem_color(elem)

    cw = 900
    card_w = cw - PADDING * 2
    pad = CARD_PADDING
    c = make_canvas(cw, 1200, BG_PAGE)

    # ── card art background ──
    c.assets  # ensure loaded
    card_art = None
    if c.assets and char_name:
        card_art = c.assets.card_art(char_name)
    if card_art:
        c.image(card_art, 0, 0, cw, 320)
        c.overlay(0, 0, cw, 320, (0, 0, 0, 100))
        start, end = elem_gradient(elem)
        # gradient overlay at bottom
        c.gradient(0, 260, cw, 60, (0, 0, 0, 0), (0, 0, 0, 100))
    else:
        start, end = elem_gradient(elem)
        c.gradient(0, 0, cw, 200, start, end)

    # ── header info ──
    face = card.get("face", "")
    if face:
        c.round_image(face, PADDING, 30, 100)
    fx = PADDING + 120 if face else PADDING
    c.text_shadow(char_name, fx, 36, font_name="NZBZ", font_size=48,
                  color=(255, 255, 255), shadow_color=(0, 0, 0, 100))
    lv = card.get("level", 1)
    cons = card.get("cons", 0)
    fetter = card.get("fetter", 0)
    star = card.get("star", 5)
    c.text_shadow(f"Lv.{lv}  C{cons}  好感{fetter}", fx, 96,
                  font_size=24, color=(200, 210, 240, 255),
                  shadow_color=(0, 0, 0, 80))
    c.text(f"{'★' * star}", fx, 130, font_size=22, color=(255, 215, 0))
    # element badge
    draw_badge(c, fx, 160, elem.upper(), bg_color=elem_c, font_size=16)

    y = 340

    # ── stats summary ──
    hp = card.get("hp", 0)
    atk = card.get("atk", 0)
    em = card.get("em", 0)
    crit_rate = card.get("critRate", 0)
    crit_dmg = card.get("critDmg", 0)

    draw_shadow_panel(c, PADDING, y, card_w, 90)
    stat_items = [
        ("HP", hp, True), ("ATK", atk, True),
        ("EM", em, False), ("暴击", crit_rate, False),
        ("爆伤", crit_dmg, False),
    ]
    sw = (card_w - pad * 2) // len(stat_items)
    for i, (sname, sval, is_raw) in enumerate(stat_items):
        sx = PADDING + pad + i * sw
        val_str = _fmt_stat(sval, is_raw)
        c.text(sname, sx, y + pad + 4, font_size=18, color=TEXT_MED)
        c.text(val_str, sx, y + pad + 32, font_size=28, color=elem_c)
    y += 110

    # ── weapon ──
    weapon = card.get("weapon", {})
    if weapon and weapon.get("name"):
        draw_shadow_panel(c, PADDING, y, card_w, 120)
        w_img = weapon.get("img", "")
        if w_img:
            w_star = weapon.get("star", 5)
            border_c = RARITY_BORDER.get(w_star, (255, 215, 0, 200))
            c.rect(PADDING + pad - 2, y + pad - 2, 84, 84,
                   radius=10, fill=border_c[:3] + (40,))
            c.image(w_img, PADDING + pad, y + pad, w=80, h=80)
        c.text(weapon.get("name", ""), PADDING + pad + 100, y + pad + 8,
               font_size=28, color=TEXT_DARK)
        w_lv = weapon.get("level", 1)
        w_af = weapon.get("affix", 1)
        c.text(f"Lv.{w_lv}  精炼{w_af}", PADDING + pad + 100, y + pad + 48,
               font_size=22, color=TEXT_MED)
        draw_stars(c, PADDING + pad + 100, y + pad + 80, weapon.get("star", 5), 14)
        y += 140

    # ── talent ──
    talent = card.get("talent", {})
    keys = ["a", "e", "q"]
    has_talent = any(
        (isinstance(talent.get(k), dict) and talent[k].get("level", 0))
        or (not isinstance(talent.get(k), dict) and talent.get(k, 0))
        for k in keys
    )
    if has_talent:
        draw_shadow_panel(c, PADDING, y, card_w, 100)
        tl_size = 56
        tl_gap = 16
        total_tl = len(keys) * (tl_size + 12) + (len(keys) - 1) * tl_gap
        sx = PADDING + (card_w - total_tl) // 2
        for i, k in enumerate(keys):
            t = talent.get(k, {})
            lv = t.get("level", 1) if isinstance(t, dict) else (t or 1)
            original = t.get("original", lv) if isinstance(t, dict) else lv
            tx = sx + i * (tl_size + 12 + tl_gap)
            ty = y + 18
            # talent bg with element theme
            talent_bg = None
            if c.assets:
                talent_bg = c.assets.talent_bg(elem)
            if talent_bg:
                c.image(talent_bg, tx - 2, ty - 2, w=tl_size + 16, h=tl_size + 16)
            c.rect(tx, ty, tl_size + 12, tl_size + 12, radius=8, fill=elem_c)
            # talent icon
            talent_icon = None
            if c.assets and char_name:
                talent_icon = c.assets.char_talent(char_name, card.get("_game", "gs"), k)
            if talent_icon:
                c.image(talent_icon, tx + 6, ty + 6, w=tl_size, h=tl_size)
            c.text(str(lv), tx + (tl_size + 12) // 2, ty + tl_size + 20,
                   font_size=24, color=TEXT_DARK, anchor="mt")
            c.text(k.upper(), tx + (tl_size + 12) // 2, ty + tl_size + 46,
                   font_size=14, color=TEXT_LIGHT, anchor="mt")
        y += 120

    # ── artifact set ──
    artis_set = card.get("artisSet", {})
    sname = artis_set.get("sName", "")
    if sname:
        draw_shadow_panel(c, PADDING, y, card_w, 50)
        c.text(f"套装: {sname}", PADDING + pad, y + pad + 4,
               font_size=22, color=TEXT_DARK)
        y += 70

    # ── artifact pieces ──
    artis_data = card.get("artis", {})
    draw_shadow_panel(c, PADDING, y, card_w, 120)
    for idx in [1, 2, 3, 4, 5]:
        arti = artis_data.get(str(idx), {}) if isinstance(artis_data, dict) else {}
        ax = PADDING + pad + (idx - 1) * 130
        ai = arti.get("img", "")
        if ai:
            c.image(ai, ax, y + pad + 8, w=56, h=56)
        slv = arti.get("level", 0)
        if slv:
            c.text(f"+{slv}", ax + 28, y + pad + 68,
                   font_size=18, color=TEXT_LIGHT, anchor="mt")
    y += 140

    # ── source & update time ──
    src = card.get("source", "")
    ut = card.get("updateTime", "")
    if src or ut:
        c.text(f"数据源: {src}  {ut}", PADDING, y + 10,
               font_size=18, color=TEXT_LIGHT)

    draw_footer(c, cw, y + 40)
    return c.to_bytes()


def _fmt_stat(val: Any, is_raw: bool = False) -> str:
    try:
        vf = float(val)
        if is_raw:
            if vf >= 10000:
                return f"{vf:.0f}"
            return f"{vf:.0f}"
        return f"{vf:.1f}%"
    except (ValueError, TypeError):
        return str(val)
