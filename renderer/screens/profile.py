from __future__ import annotations

from typing import Any

from pathlib import Path

from .. import make_canvas
from ...tools.path import miao_path
from ...vendored.pillow_elements import (
    draw_panel_header, draw_footer, draw_stars, draw_shadow_panel,
    draw_section_title, draw_badge, draw_horiz_line,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    COLOR_ELEM, elem_color, elem_gradient,
    PADDING, CARD_PADDING, CARD_GAP, SECTION_GAP,
    STAR_COLORS,
)

from PIL import Image as _PIL


def _extract_bg(splash_rel: str) -> tuple[int, int, int, int]:
    p = Path(f"{miao_path}/resources") / splash_rel.lstrip("/")
    if not p.exists():
        return BG_PAGE
    try:
        with _PIL.open(p) as _img:
            sm = _img.resize((1, 1), _PIL.LANCZOS).convert("RGBA")
            avg = sm.getpixel((0, 0))
    except OSError:
        return BG_PAGE
    lighten = 0.55
    return (
        min(255, int(avg[0] + (255 - avg[0]) * lighten)),
        min(255, int(avg[1] + (255 - avg[1]) * lighten)),
        min(255, int(avg[2] + (255 - avg[2]) * lighten)),
        255,
    )


async def render_profile(data: dict[str, Any]) -> bytes:
    game = data.get("game", "gs")
    if game == "sr":
        return await _render_profile_sr(data)
    return await _render_profile_gs(data)


async def render_profile_sr(data: dict[str, Any]) -> bytes:
    return await _render_profile_sr(data)


# ── GS profile ──────────────────────────────────────────────────────

async def _render_profile_gs(data: dict[str, Any]) -> bytes:
    elem = data.get("elem", "hydro")
    elem_c = elem_color(elem)
    cw = 1120
    margin = PADDING
    card_w = cw - margin * 2
    pad = CARD_PADDING
    y = 0

    # header
    splash = data.get("splash", "") or data.get("side", "")
    header_h = 300
    bg_color = BG_PAGE
    ch = make_canvas(cw, header_h, BG_PAGE)
    if splash and ch.assets.exists(splash):
        abs_p = ch.assets.resolve(splash)
        if abs_p.exists():
            try:
                with _PIL.open(abs_p) as _tmp:
                    _ow, _oh = _tmp.size
                    header_h = max(300, int(cw * _oh / _ow))
                    bg_color = _extract_bg(splash)
            except OSError:
                pass
        ch = make_canvas(cw, header_h, bg_color)
        ch.image(splash, 0, 0, w=cw)
    else:
        ch = make_canvas(cw, header_h, BG_PAGE)
        start, end = elem_gradient(elem)
        ch.gradient(0, 0, cw, header_h, start, end)
    ch.text_shadow(data.get("name", ""), PADDING, 36, font_name="NZBZ",
                   font_size=64, color=(255, 255, 255), shadow_color=(0, 0, 0, 160))
    lv = data.get("level", 1)
    cons = data.get("cons", 0)
    fetter = data.get("fetter", 0)
    star = data.get("star", 5)
    ch.text_shadow(f"Lv.{lv}  C{cons}  好感{fetter}", PADDING, 110,
                   font_size=28, color=(200, 210, 240, 255), shadow_color=(0, 0, 0, 140))
    ch.text_shadow(f"{star}\u2605", PADDING, 152, font_size=26, color=(255, 215, 0),
                   shadow_color=(0, 0, 0, 140))
    draw_badge(ch, PADDING, 194, elem.upper(), bg_color=elem_c, font_size=18)

    c = make_canvas(cw, header_h + 5000, bg_color)
    c.paste(ch.to_pil(), 0, 0)
    y = header_h + 20

    # GS stats
    stats = [
        ("生命值", data.get("hp", 0), "hp"),
        ("攻击力", data.get("atk", 0), "atk"),
        ("防御力", data.get("def", 0), "def"),
        ("元素精通", data.get("em", 0), "em"),
        ("暴击率", data.get("critRate", 0), "cpct"),
        ("暴击伤害", data.get("critDmg", 0), "cdmg"),
        ("充能效率", data.get("recharge", 0), "recharge"),
        ("治疗加成", data.get("heal", 0), "heal"),
        ("伤害加成", data.get("dmgBonus", 0), "dmg"),
    ]
    y = _draw_stats_grid(c, margin, card_w, pad, y, stats, elem_c, game="gs")
    y += SECTION_GAP

    # weapon + talent side by side (GS)
    weapon = data.get("weapon", {})
    talent = data.get("talent", {})
    keys_gs = ["a", "e", "q"]
    has_weapon = bool(weapon and weapon.get("name"))
    has_talent = _has_talent(talent, keys_gs)
    if has_weapon or has_talent:
        left_w = (card_w - CARD_GAP) // 2
        right_w = card_w - left_w - CARD_GAP
        parea_h = max(148, (64 + CARD_GAP + 30) if has_weapon else 0) + pad * 2 - 20
        draw_shadow_panel(c, margin, y, card_w, parea_h)
        draw_section_title(c, margin + pad, y + pad, 200, "武器和天赋", color=elem_c)
        if has_weapon:
            _draw_weapon_gs_at(c, margin + pad, y, left_w, pad, weapon, elem_c)
        if has_talent:
            _draw_talent_gs_at(c, margin + pad + left_w + CARD_GAP, y, right_w, pad, talent, keys_gs, data, elem, elem_c)
        y += parea_h + SECTION_GAP

    # artifact / relic scoring + pieces
    artis_mark = data.get("artisMark", {})
    artis_set = data.get("artisSet", {})
    sname = artis_set.get("sName", "")
    artis = data.get("artis", [])
    if sname or artis_mark:
        y = _draw_artis_set(c, margin, card_w, pad, y, sname,
                            artis_mark=artis_mark, game="gs", artis=artis, elem_c=elem_c)
        y += SECTION_GAP

    draw_footer(c, cw, y + 10)
    c.crop_to(y + 60)
    return c.to_bytes()


# ── SR profile ──────────────────────────────────────────────────────

async def _render_profile_sr(data: dict[str, Any]) -> bytes:
    elem = data.get("elem", "physical")
    elem_c = elem_color(elem)
    cw = 1120
    margin = PADDING
    card_w = cw - margin * 2
    pad = CARD_PADDING
    y = 0

    # header
    splash = data.get("splash", "") or data.get("side", "")
    header_h = 300
    bg_color = BG_PAGE
    ch = make_canvas(cw, header_h, BG_PAGE)
    if splash and ch.assets.exists(splash):
        abs_p = ch.assets.resolve(splash)
        if abs_p.exists():
            try:
                with _PIL.open(abs_p) as _tmp:
                    _ow, _oh = _tmp.size
                    header_h = max(300, int(cw * _oh / _ow))
                    bg_color = _extract_bg(splash)
            except OSError:
                pass
        ch = make_canvas(cw, header_h, bg_color)
        ch.image(splash, 0, 0, w=cw)
    else:
        ch = make_canvas(cw, header_h, BG_PAGE)
        start, end = elem_gradient(elem)
        ch.gradient(0, 0, cw, header_h, start, end)
    ch.text_shadow(data.get("name", ""), PADDING, 36, font_name="NZBZ",
                   font_size=64, color=(255, 255, 255), shadow_color=(0, 0, 0, 160))
    lv = data.get("level", 1)
    cons = data.get("cons", 0)
    star = data.get("star", 5)
    ch.text_shadow(f"Lv.{lv}  {cons}星魂", PADDING, 110,
                   font_size=28, color=(200, 210, 240, 255), shadow_color=(0, 0, 0, 140))
    ch.text_shadow(f"{star}\u2605", PADDING, 152, font_size=26, color=(255, 215, 0),
                   shadow_color=(0, 0, 0, 140))
    draw_badge(ch, PADDING, 194, elem.upper(), bg_color=elem_c, font_size=18)

    c = make_canvas(cw, header_h + 5000, bg_color)
    c.paste(ch.to_pil(), 0, 0)
    y = header_h + 20

    cons = data.get("cons", 0)

    # SR stats (includes speed, effPct, effDef, stance, etc.)
    stats = [
        ("生命值", data.get("hp", 0), "hp"),
        ("攻击力", data.get("atk", 0), "atk"),
        ("防御力", data.get("def", 0), "def"),
        ("速度", data.get("speed", 0), "speed"),
        ("暴击率", data.get("critRate", 0), "cpct"),
        ("暴击伤害", data.get("critDmg", 0), "cdmg"),
        ("充能效率", data.get("recharge", 0), "recharge"),
        ("击破特攻", data.get("stance", 0), "stance"),
        ("治疗加成", data.get("heal", 0), "heal"),
        ("效果命中", data.get("effPct", 0), "effPct"),
        ("效果抵抗", data.get("effDef", 0), "effDef"),
        ("伤害加成", data.get("dmgBonus", 0), "dmg"),
    ]
    y = _draw_stats_grid(c, margin, card_w, pad, y, stats, elem_c, game="sr")
    y += SECTION_GAP

    # weapon + talent side by side
    weapon = data.get("weapon", {})
    talent = data.get("talent", {})
    sr_keys = _sr_talent_keys(talent)
    has_weapon = bool(weapon and weapon.get("name"))
    has_talent = _has_talent(talent, sr_keys)
    if has_weapon or has_talent:
        left_w = (card_w - CARD_GAP) // 2
        right_w = card_w - left_w - CARD_GAP
        parea_h = 0
        if has_weapon:
            parea_h = max(parea_h, _weapon_sr_height(weapon, data, pad))
        if has_talent:
            parea_h = max(parea_h, 130)
        parea_h = max(parea_h, 130) + pad * 2 - 40
        draw_shadow_panel(c, margin, y, card_w, parea_h)
        draw_section_title(c, margin + pad, y + pad, 200, "光锥和天赋", color=elem_c)
        if has_weapon:
            _draw_weapon_sr_at(c, margin + pad, y, left_w, pad, weapon, data, elem_c)
        if has_talent:
            _draw_talent_sr_at(c, margin + pad + left_w + CARD_GAP, y, right_w, pad, talent, sr_keys, data, elem, elem_c)
        y += parea_h + SECTION_GAP

    # trees (SR: trace tree nodes)
    tree = data.get("tree", {})
    if tree:
        y = _draw_trees(c, margin, card_w, pad, y, tree, elem_c)
        y += SECTION_GAP

    # relic set + pieces
    artis_mark = data.get("artisMark", {})
    artis_set = data.get("artisSet", {})
    sname = artis_set.get("sName", "")
    artis = data.get("artis", [])
    if sname or artis_mark:
        y = _draw_artis_set(c, margin, card_w, pad, y, sname,
                            artis_mark=artis_mark, game="sr", artis=artis, elem_c=elem_c)
        y += SECTION_GAP

    draw_footer(c, cw, y + 10)
    c.crop_to(y + 60)
    return c.to_bytes()


# ── stat grid (shared, game-aware icon loading) ─────────────────────

def _tint_icon(path: str, color: tuple) -> _PIL.Image | None:
    from PIL import ImageOps
    p = Path(path) if isinstance(path, str) else path
    if not p.exists():
        return None
    try:
        img = _PIL.open(p).convert("RGBA")
    except OSError:
        return None
    r, g, b, a = color
    arr = img.load()
    for y in range(img.height):
        for x in range(img.width):
            px = arr[x, y]
            if px[3] > 0 and px[0] >= 200 and px[1] >= 200 and px[2] >= 200:
                arr[x, y] = (r, g, b, px[3])
    return img


def _draw_stats_grid(c, margin, card_w, pad, y, stats, elem_c, game="gs"):
    per_row = 3
    stat_card_w = (card_w - pad * 2 - CARD_GAP * (per_row - 1)) // per_row
    stat_h = 52
    rows = (len(stats) + per_row - 1) // per_row
    area_h = rows * stat_h + (rows - 1) * CARD_GAP + pad * 2

    draw_shadow_panel(c, margin, y, card_w, area_h)
    sy0 = y + pad
    for i, (sname, sval, skey) in enumerate(stats):
        col = i % per_row
        row = i // per_row
        sx = margin + pad + col * (stat_card_w + CARD_GAP)
        sy = sy0 + row * (stat_h + CARD_GAP)

        c.rect(sx, sy, stat_card_w, stat_h, radius=10, fill=(248, 248, 250, 255))
        icon_img = None
        if game == "sr" and c.assets:
            icon_path = c.assets.sr_attr_icon(skey)
            if icon_path:
                icon_img = _tint_icon(c.assets.resolve(icon_path), elem_c)
        if icon_img is not None:
            rs = icon_img.resize((24, 24), _PIL.LANCZOS)
            c.paste(rs, sx + 10, sy + (stat_h - 24) // 2)
        c.text(sname, sx + 40, sy + (stat_h - 20) // 2,
               font_size=20, color=TEXT_MED)
        val_str = _stat_str(sval, game, skey)
        c.text(val_str, sx + stat_card_w - 10, sy + (stat_h - 30) // 2,
               font_size=30, color=elem_c, anchor="rt")
    return y + area_h


# ── weapon ──────────────────────────────────────────────────────────

def _draw_weapon_gs(c, margin, card_w, pad, y, weapon, elem_c):
    draw_shadow_panel(c, margin, y, card_w, 140)
    w_img = weapon.get("img", "")
    if w_img:
        c.rect(margin + pad - 2, y + pad - 2, 104, 104,
               radius=12, fill=elem_c[:3] + (60,))
        c.image(w_img, margin + pad, y + pad, w=100, h=100)
    c.text(weapon.get("name", ""), margin + pad + 120, y + pad + 8,
           font_size=30, color=TEXT_DARK)
    w_lv = weapon.get("level", 1)
    w_af = weapon.get("affix", 1)
    c.text(f"Lv.{w_lv}  精炼{w_af}", margin + pad + 120, y + pad + 52,
           font_size=24, color=TEXT_MED)
    draw_stars(c, margin + pad + 120, y + pad + 88, weapon.get("star", 5), 16)
    return y + 160


def _draw_weapon_gs_at(c, x0, y0, w, pad, weapon, elem_c):
    content_cy = y0 + pad + 130 // 2
    w_img = weapon.get("img", "")
    icon_cy = content_cy + 20
    if w_img:
        c.rect(x0 + pad, icon_cy - 34, 68, 68, radius=10, fill=elem_c[:3] + (60,))
        c.image(w_img, x0 + pad + 4, icon_cy - 30, w=60, h=60)
    tx = x0 + pad + 82
    c.text(weapon.get("name", ""), tx, content_cy - 20,
           font_size=22, color=TEXT_DARK)
    w_lv = weapon.get("level", 1)
    w_af = weapon.get("affix", 1)
    c.text(f"Lv.{w_lv}  精炼{w_af}", tx, content_cy + 6,
           font_size=18, color=TEXT_MED)
    draw_stars(c, tx, content_cy + 30, weapon.get("star", 5), 12)


def _draw_talent_gs_at(c, x0, y0, w, pad, talent, keys, data, elem, elem_c):
    label_map = {"a": "普攻", "e": "战技", "q": "爆发"}
    tl_size = 64
    tl_gap = 10
    item_w = tl_size + 8
    total_w = len(keys) * item_w + (len(keys) - 1) * tl_gap
    sx = x0 + max(0, (w - total_w - pad) // 2)
    content_cy = y0 + pad + 130 // 2
    for i, k in enumerate(keys):
        t = talent.get(k, {})
        lv = t.get("level", 1) if isinstance(t, dict) else (t or 1)
        tx = sx + i * (item_w + tl_gap)
        ty = content_cy - tl_size // 2
        talent_bg = c.assets.talent_bg(elem) if c.assets else None
        if talent_bg:
            c.image(talent_bg, tx - 3, ty - 3, w=tl_size + 14, h=tl_size + 14)
        c.rect(tx, ty, tl_size + 8, tl_size + 8, radius=10, fill=elem_c)
        ticon = c.assets.char_talent(data.get("char_name", ""), "gs", k) if c.assets else None
        if ticon:
            c.image(ticon, tx + 4, ty + 4, w=tl_size, h=tl_size)
        else:
            c.text(k.upper(), tx + (tl_size + 8) // 2, ty + (tl_size + 8) // 2,
                   font_size=28, color=(255, 255, 255, 200), anchor="mm")
        c.text(label_map.get(k, k.upper()), tx + (tl_size + 8) // 2, ty - 6,
               font_size=16, color=TEXT_MED, anchor="mb")
        c.text(str(lv), tx + (tl_size + 8) // 2, ty + tl_size + 16,
               font_size=26, color=TEXT_DARK, anchor="mt")


def _weapon_sr_height(weapon: dict, data: dict, pad: int) -> int:
    from PIL import Image as _PIL
    splash_path = None
    splash_img_h = 0
    if hasattr(weapon, "get") and weapon.get("name"):
        w_type = weapon.get("type", "")
        splash_path = f"meta-sr/weapon/{w_type}/{weapon.get('name','')}/splash.webp"
        p = Path(f"{miao_path}/resources") / splash_path.lstrip("/")
        if p.exists():
            try:
                with _PIL.open(p) as tmp:
                    _ow, _oh = tmp.size
                    splash_img_h = int(140 * _oh / _ow)
            except OSError:
                pass
    return max(200, splash_img_h + pad * 2 + 6)


def _draw_weapon_sr_at(c, x0, y0, w, pad, weapon, data, elem_c):
    splash_path = None
    if c.assets and weapon.get("name"):
        w_type = weapon.get("type", "")
        splash_path = c.assets.weapon_splash(weapon["name"], w_type, "sr")
    splash_w = 140
    splash_h = 140
    if splash_path and c.assets:
        abs_p = c.assets.resolve(splash_path)
        if abs_p.exists():
            from PIL import Image as _PIL
            try:
                with _PIL.open(abs_p) as tmp:
                    _ow, _oh = tmp.size
                    splash_h = int(splash_w * _oh / _ow)
            except OSError:
                splash_h = 200
    content_cy = y0 + pad + 130 // 2
    img_top = max(y0 + pad, content_cy - splash_h // 2)
    tx = x0 + splash_w + 12
    txt_cy = content_cy
    c.text(weapon.get("name", ""), tx, txt_cy - 22,
           font_size=24, color=TEXT_DARK)
    w_lv = weapon.get("level", 1)
    w_af = weapon.get("affix", 1)
    c.text(f"Lv.{w_lv}  叠影{w_af}阶", tx, txt_cy + 4,
           font_size=20, color=TEXT_MED)
    draw_stars(c, tx, txt_cy + 32, weapon.get("star", 5), 14)
    if splash_path:
        c.image(splash_path, x0, img_top, w=splash_w, h=splash_h)


def _draw_talent_sr_at(c, x0, y0, w, pad, talent, keys, data, elem, elem_c):
    label_map = {"a": "普攻", "e": "战技", "t": "天赋", "q": "爆发",
                 "me": "忆灵技", "mt": "忆灵天赋", "xe": "欢愉技"}
    tl_size = 70
    tl_gap = 6
    item_w = tl_size + 8
    total_w = len(keys) * item_w + (len(keys) - 1) * tl_gap
    sx = x0 + max(0, w - total_w - 76)
    content_cy = y0 + pad + 130 // 2
    for i, k in enumerate(keys):
        t = talent.get(k, {})
        lv = t.get("level", 1) if isinstance(t, dict) else (t or 1)
        tx = sx + i * (item_w + tl_gap)
        ty = content_cy - tl_size // 2
        talent_bg = c.assets.talent_bg(elem) if c.assets else None
        if talent_bg:
            c.image(talent_bg, tx - 3, ty - 3, w=tl_size + 16, h=tl_size + 16)
        c.rect(tx, ty, tl_size + 10, tl_size + 10, radius=8, fill=elem_c)
        ticon = c.assets.char_talent(data.get("char_name", ""), "sr", k) if c.assets else None
        if ticon:
            c.image(ticon, tx + 5, ty + 5, w=tl_size, h=tl_size)
        c.text(label_map.get(k, k.upper()), tx + (tl_size + 10) // 2, ty - 6,
               font_size=16, color=TEXT_MED, anchor="mb")
        c.text(str(lv), tx + (tl_size + 10) // 2, ty + tl_size + 14,
               font_size=26, color=TEXT_DARK, anchor="mt")


def _draw_weapon_sr(c, margin, card_w, pad, y, weapon, data, elem_c):
    splash_path = None
    if c.assets and weapon.get("name"):
        w_type = weapon.get("type", "")
        splash_path = c.assets.weapon_splash(weapon["name"], w_type, "sr")
    splash_w = 120
    splash_h = 120
    if splash_path and c.assets:
        abs_p = c.assets.resolve(splash_path)
        if abs_p.exists():
            from PIL import Image
            try:
                with Image.open(abs_p) as tmp:
                    orig_w, orig_h = tmp.size
                    splash_h = int(splash_w * orig_h / orig_w)
            except OSError:
                splash_h = 160

    panel_h = max(170, splash_h + pad * 2)
    draw_shadow_panel(c, margin, y, card_w, panel_h)

    if splash_path:
        c.image(splash_path, margin + pad, y + (panel_h - splash_h) // 2, w=splash_w, h=splash_h)
    else:
        w_img = weapon.get("img", "")
        if w_img:
            c.image(w_img, margin + pad, y + pad, w=100, h=100)
    ix = margin + pad + splash_w + 20
    c.text(weapon.get("name", ""), ix, y + pad + 8,
           font_size=30, color=TEXT_DARK)
    w_lv = weapon.get("level", 1)
    w_af = weapon.get("affix", 1)
    c.text(f"Lv.{w_lv}  叠影{w_af}阶", ix, y + pad + 48,
           font_size=24, color=TEXT_MED)
    draw_stars(c, ix, y + pad + 82, weapon.get("star", 5), 14)

    hp = weapon.get("hp", 0)
    atk = weapon.get("atk", 0)
    defense = weapon.get("def", 0)
    if any([hp, atk, defense]):
        stat_x = ix
        stat_y = y + pad + 110
        for label, val, key in [("生命", hp, "hp"), ("攻击", atk, "atk"), ("防御", defense, "def")]:
            icon_p = c.assets.sr_attr_icon(key) if c.assets else None
            if icon_p:
                c.image(icon_p, stat_x, stat_y + 2, w=16, h=16)
            c.text(f"{val}", stat_x + 20, stat_y, font_size=18, color=TEXT_MED)
            stat_x += 80
    return y + panel_h + 20


# ── talent ──────────────────────────────────────────────────────────

def _draw_talent_gs(c, margin, card_w, pad, y, talent, keys, data, elem, elem_c):
    draw_shadow_panel(c, margin, y, card_w, 130)
    tl_size = 64
    tl_gap = 20
    total_w = len(keys) * (tl_size + 8) + (len(keys) - 1) * tl_gap
    sx = margin + (card_w - total_w) // 2
    for i, k in enumerate(keys):
        t = talent.get(k, {})
        lv = t.get("level", 1) if isinstance(t, dict) else (t or 1)
        original = t.get("original", lv) if isinstance(t, dict) else lv
        tx = sx + i * (tl_size + 8 + tl_gap)
        ty = y + 25
        talent_bg = c.assets.talent_bg(elem) if c.assets else None
        if talent_bg:
            c.image(talent_bg, tx - 4, ty - 4, w=tl_size + 8, h=tl_size + 8)
        c.rect(tx, ty, tl_size + 8, tl_size + 8, radius=10, fill=elem_c)
        ticon = c.assets.char_talent(data.get("char_name", ""), "gs", k) if c.assets else None
        if ticon:
            c.image(ticon, tx + 4, ty + 4, w=tl_size, h=tl_size)
        else:
            c.text(k.upper(), tx + (tl_size + 8) // 2, ty + (tl_size + 8) // 2,
                   font_size=28, color=(255, 255, 255, 200), anchor="mm")
        c.text(str(lv), tx + (tl_size + 8) // 2, ty + tl_size + 14,
               font_size=26, color=TEXT_DARK, anchor="mt")
        c.text(k.upper(), tx + (tl_size + 8) // 2, ty + tl_size + 44,
               font_size=16, color=TEXT_MED, anchor="mt")
        # crown at talent >= 10
        if lv >= 10 or (isinstance(t, dict) and t.get("original", 0) >= 10):
            crown_p = c.assets.crown_profile("gs") if c.assets else None
            if not crown_p and c.assets:
                crown_p = c.assets.crown_gs()
            if crown_p:
                c.image(crown_p, tx + tl_size - 12, ty - 8, w=24, h=24)
    return y + 150


def _draw_talent_sr(c, margin, card_w, pad, y, talent, keys, data, elem, elem_c):
    draw_shadow_panel(c, margin, y, card_w, 130)
    tl_size = 56
    tl_gap = 16
    total_w = len(keys) * (tl_size + 6) + (len(keys) - 1) * tl_gap
    sx = margin + (card_w - total_w) // 2

    label_map = {"a": "普攻", "e": "战技", "t": "天赋", "q": "爆发",
                 "me": "忆灵技", "mt": "忆灵天赋", "xe": "欢愉技"}
    for i, k in enumerate(keys):
        t = talent.get(k, {})
        lv = t.get("level", 1) if isinstance(t, dict) else (t or 1)
        tx = sx + i * (tl_size + 6 + tl_gap)
        ty = y + 18
        talent_bg = c.assets.talent_bg(elem) if c.assets else None
        if talent_bg:
            c.image(talent_bg, tx - 2, ty - 2, w=tl_size + 10, h=tl_size + 10)
        c.rect(tx, ty, tl_size + 6, tl_size + 6, radius=8, fill=elem_c)
        ticon = c.assets.char_talent(data.get("char_name", ""), "sr", k) if c.assets else None
        if ticon:
            c.image(ticon, tx + 3, ty + 3, w=tl_size, h=tl_size)
        c.text(label_map.get(k, k.upper()), tx + (tl_size + 6) // 2, ty - 2,
               font_size=14, color=TEXT_MED, anchor="mb")
        c.text(str(lv), tx + (tl_size + 6) // 2, ty + tl_size + 12,
               font_size=24, color=TEXT_DARK, anchor="mt")
    return y + 150


def _sr_talent_keys(talent: dict) -> list[str]:
    """Return SR talent keys based on available data and special paths."""
    base = ["a", "e", "t", "q"]
    if not talent:
        return base
    extras = []
    for k in ("me", "mt", "xe"):
        if k in talent:
            extras.append(k)
    return base + extras


# ── trace trees (SR only) ───────────────────────────────────────────

def _draw_trees(c, margin, card_w, pad, y, tree_data, elem_c):
    draw_shadow_panel(c, margin, y, card_w, 100)
    draw_section_title(c, margin + pad, y + pad, 200, "行迹", color=elem_c)
    ty = y + pad + 36
    tx_start = margin + pad
    if isinstance(tree_data, dict):
        items = list(tree_data.items())[:8]
    elif isinstance(tree_data, list):
        items = [(str(i), v) for i, v in enumerate(tree_data[:8])]
    else:
        items = []
    for i, (tk, tv) in enumerate(items):
        col = i % 4
        row = i // 4
        cx = tx_start + col * 120
        cy = ty + row * 36
        unlocked = bool(tv) if not isinstance(tv, str) else True
        color = elem_c if unlocked else (180, 180, 190, 150)
        icon_p = c.assets.sr_tree_icon(tk) if c.assets else None
        if icon_p:
            c.image(icon_p, cx, cy, w=22, h=22)
            c.text(tk, cx + 28, cy + 2, font_size=18, color=color)
        else:
            c.text(tk, cx, cy + 2, font_size=18, color=color)
    return y + 120


# ── artifact / relic ────────────────────────────────────────────────

def _draw_artis_set(c, margin, card_w, pad, y, sname, artis_mark=None, game="gs", artis=None, elem_c=None):
    dy = y
    artis_mark = artis_mark if isinstance(artis_mark, dict) else {}
    dy = y
    # scoring summary
    if artis_mark:
        total = artis_mark.get("total", "0")
        cls = artis_mark.get("markClass", "")
        title = artis_mark.get("classTitle", "")
        all_attr = artis_mark.get("allAttr", [])
        key_title = artis_mark.get("keyTitle", {})

        # total score + rating + set name row
        h1 = 60
        draw_shadow_panel(c, margin, dy, card_w, h1)
        draw_section_title(c, margin + pad, dy + pad, 200, f"圣遗物总分: {total}", color=elem_c or ACCENT_BLUE)
        mc = _mark_color(cls)
        x0 = margin + pad
        c.text(f"评级: {cls}", x0 + 260, dy + pad + 4,
               font_size=26, color=mc)
        sx = x0 + 460
        c.text(f"套装: {sname}", sx, dy + pad + 4,
               font_size=26, color=TEXT_DARK)
        if title:
            cjk = sum(1 for ch in f"套装: {sname}" if '\u4e00' <= ch <= '\u9fff')
            latin = len(f"套装: {sname}") - cjk
            sname_w = cjk * 26 + latin * 13
            tx = max(sx + sname_w + 16, x0 + 780)
            c.text(title, tx, dy + pad + 4,
                   font_size=20, color=TEXT_LIGHT)
        dy += h1 + SECTION_GAP

        # aggregated substats
        title_map = key_title if key_title else {
            "hp": "生命值", "atk": "攻击力", "def": "防御力", "em": "元素精通",
            "mastery": "元素精通", "cpct": "暴击率", "cdmg": "暴击伤害",
            "recharge": "充能效率", "heal": "治疗加成", "dmg": "伤害加成",
            "phy": "物理伤害", "physDmg": "物理伤害",
            "hpPlus": "小生命", "atkPlus": "小攻击", "defPlus": "小防御",
            "hpPct": "大生命", "atkPct": "大攻击", "defPct": "大防御",
            "speed": "速度", "stance": "击破特攻",
            "effPct": "效果命中", "effDef": "效果抵抗",
            "critRate": "暴击率", "critDmg": "暴击伤害",
        }
        if all_attr:
            title_h = 41
            row_h = 26
            h2 = title_h + ((len(all_attr) + 4) // 5) * row_h + 10
            draw_shadow_panel(c, margin, dy, card_w, h2)
            draw_section_title(c, margin + pad, dy + 6, 200, "副词条汇总", color=elem_c or ACCENT_BLUE)
            attr_per_row = 5
            for i, attr in enumerate(all_attr[:15]):
                col = i % attr_per_row
                row = i // attr_per_row
                k = attr.get("key", "")
                v = attr.get("value", 0)
                un = attr.get("upNum", 0)
                label = title_map.get(k, k)
                ax = margin + pad + col * 200
                ay = dy + title_h + row * row_h
                c.text(f"{label}: +{_fmt_artis_val(k, v)}", ax, ay,
                       font_size=18, color=TEXT_DARK)
                if un:
                    c.text(f"[{un}]", ax + 170, ay,
                           font_size=16, color=TEXT_LIGHT)
            dy += h2 + SECTION_GAP

    else:
        h = 60
        draw_shadow_panel(c, margin, dy, card_w, h)
        c.text(f"套装: {sname}", margin + pad, dy + pad + 4,
               font_size=24, color=TEXT_DARK)
        dy += h + SECTION_GAP

    # individual pieces
    artis_arr = artis_mark.get("artis", {}) if artis_mark else {}
    piece_list = artis if isinstance(artis, list) else []
    if not piece_list:
        return dy

    per_row = 3
    count = len(piece_list)
    rows = (count + per_row - 1) // per_row
    pw = (card_w - pad * 2 - CARD_GAP * (per_row - 1)) // per_row
    ph = 210
    area_h = rows * ph + (rows - 1) * CARD_GAP + pad * 2 + 20
    draw_shadow_panel(c, margin, dy, card_w, area_h)
    draw_section_title(c, margin + pad, dy + pad, 200,
                       "圣遗物" if game == "gs" else "遗器", color=elem_c or ACCENT_BLUE)
    sy = dy + pad + 30
    title_map = artis_mark.get("keyTitle", {}) if artis_mark else {}
    # hardcoded fallback for key titles
    if not title_map:
        title_map = {
            "hp": "生命值", "atk": "攻击力", "def": "防御力", "em": "元素精通",
            "mastery": "元素精通", "cpct": "暴击率", "cdmg": "暴击伤害",
            "recharge": "充能效率", "heal": "治疗加成", "dmg": "伤害加成",
            "phy": "物理伤害", "physDmg": "物理伤害",
            "hpPlus": "小生命", "atkPlus": "小攻击", "defPlus": "小防御",
            "hpPct": "大生命", "atkPct": "大攻击", "defPct": "大防御",
            "speed": "速度", "stance": "击破特攻",
            "effPct": "效果命中", "effDef": "效果抵抗",
            "critRate": "暴击率", "critDmg": "暴击伤害",
        }
    for i, piece in enumerate(piece_list):
        col = i % per_row
        row = i // per_row
        px = margin + pad + col * (pw + CARD_GAP)
        py = sy + row * (ph + CARD_GAP)

        idx = piece.get("idx", str(i + 1))
        piece_mark = artis_arr.get(idx, {})

        # card bg
        c.rect(px, py, pw, ph, radius=10, fill=(255, 255, 255, 255))
        c.rect(px, py, pw, ph, radius=10, outline=(220, 220, 230, 200), border=1)

        # icon
        img_path = piece_mark.get("img", piece.get("img", ""))
        if img_path:
            c.image(img_path, px + pad, py + 12, w=56, h=56)
        lv = piece.get("level", 0)
        if lv:
            c.text(f"+{lv}", px + pad + 28, py + 70,
                   font_size=16, color=TEXT_MED, anchor="mt")

        # name + score
        name = piece_mark.get("abbr", piece.get("name", ""))[:8]
        mark_str = piece_mark.get("mark", "0")
        mark_cls = piece_mark.get("markClass", "")
        mc = _mark_color(mark_cls)
        c.text(name, px + pad + 66, py + 14, font_size=20, color=TEXT_DARK)
        c.text(f"{mark_str} {mark_cls}", px + pad + 66, py + 40,
               font_size=18, color=mc)

        # main stat
        main = piece.get("main", {})
        if isinstance(main, dict):
            mk = main.get("key", "")
            mv = main.get("value", 0)
        else:
            mk, mv = "", 0
        if mk:
            mlabel = title_map.get(mk, mk)
            mval = _fmt_artis_val(mk, mv)
            c.text(f"{mlabel}", px + pad, py + 82, font_size=18, color=TEXT_MED)
            c.text(f"+{mval}", px + pad + 110, py + 82,
                   font_size=20, color=elem_c)

        # sub stats
        attrs = piece.get("attrs", [])
        if not isinstance(attrs, list):
            attrs = []
        for si, attr in enumerate(attrs[:4]):
            ak = attr.get("key", "")
            av = attr.get("value", 0)
            if not ak:
                continue
            a_label = title_map.get(ak, ak)
            a_val = _fmt_artis_val(ak, av)
            sy2 = py + 108 + si * 24
            c.text(f"{a_label}", px + pad, sy2, font_size=16, color=TEXT_MED)
            c.text(f"+{a_val}", px + pad + 100, sy2,
                   font_size=16, color=TEXT_DARK)
            # upgrade indicator
            upnum = attr.get("upNum", 0)
            if upnum:
                for ui in range(min(upnum, 5)):
                    c.rect(px + pad + 160 + ui * 10, sy2 + 2, 8, 8, radius=4,
                           fill=elem_c[:3] + (230,))

    return dy + area_h + SECTION_GAP


# ── helpers ─────────────────────────────────────────────────────────

def _has_talent(talent: dict, keys: list[str]) -> bool:
    return any(
        (isinstance(talent.get(k), dict) and talent[k].get("level", 0))
        or (not isinstance(talent.get(k), dict) and talent.get(k, 0))
        for k in keys
    )


def _stat_str(v: Any, game: str = "gs", key: str = "") -> str:
    try:
        vf = float(v)
        if key in ("critRate", "critDmg", "cpct", "cdmg",
                     "recharge", "heal", "effPct", "effDef",
                     "stance", "dmgBonus", "dmg"):
            return f"{vf:.1f}%"
        if vf >= 10000:
            return f"{vf:.0f}"
        if vf >= 1000:
            return f"{vf:.1f}"
        return f"{vf:.1f}"
    except (ValueError, TypeError):
        return str(v)


def _mark_color(cls: str) -> tuple:
    if cls in ("ACE", "MAX", "SSS"):
        return (255, 180, 0, 255)
    if cls in ("SS", "S"):
        return (255, 100, 50, 255)
    if cls in ("A",):
        return (80, 200, 80, 255)
    if cls in ("B",):
        return (80, 160, 255, 255)
    return TEXT_LIGHT


def _fmt_artis_val(key: str, value: float) -> str:
    pct_keys = ("cpct", "cdmg", "recharge", "heal", "effPct", "effDef",
                "stance", "dmg", "phy", "dmgBonus", "critRate", "critDmg")
    if key in pct_keys:
        return f"{value:.1f}%"
    if key.endswith("Pct") or key in ("hpPct", "atkPct", "defPct"):
        return f"{value:.1f}%"
    if value >= 1000:
        return f"{value:.0f}"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)
