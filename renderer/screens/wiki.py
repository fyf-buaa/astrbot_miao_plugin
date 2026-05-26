from __future__ import annotations

from typing import Any

from .. import make_canvas
from ...vendored.pillow_elements import (
    draw_panel_header, draw_footer, draw_shadow_panel, draw_char_icon,
    draw_stars, draw_section_title, draw_badge, elem_color,
    BG_PAGE, TEXT_DARK, TEXT_MED, TEXT_LIGHT, ACCENT_BLUE, BG_CARD,
    COLOR_ELEM, PADDING, CARD_PADDING, SECTION_GAP,
)


async def render_wiki(data: dict[str, Any]) -> bytes:
    cdata = data.get("data", {})
    attrs = data.get("attr", [])
    materials = data.get("materials", [])
    imgs = data.get("imgs", {})
    game = data.get("game", "gs")

    cw = 1200
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160
    y = header_h + 30

    splash = imgs.get("splash", "")
    if splash:
        spl_h = 400
        if c.assets:
            abs_p = c.assets.resolve(splash)
            if abs_p.exists():
                from PIL import Image as _PIL
                try:
                    with _PIL.open(abs_p) as _tmp:
                        _ow, _oh = _tmp.size
                        spl_h = int(card_w * _oh / _ow)
                except OSError:
                    pass
        c = make_canvas(cw, header_h + spl_h + 200, BG_PAGE)
        draw_panel_header(c, cw, cdata.get("name", ""), "WIKI")
        # card bg texture for splash area
        if c.assets:
            card_bg = c.assets.resolve("wiki/imgs/card-bg.png")
        c.image(splash, margin, y, w=card_w, h=spl_h)
        c.overlay(margin, y, card_w, spl_h, (0, 0, 0, 80))
        # name overlay on splash
        c.text_shadow(cdata.get("name", ""), margin + CARD_PADDING, y + spl_h - 60,
                      font_name="NZBZ", font_size=42, color=(255, 255, 255),
                      shadow_color=(0, 0, 0, 120))
        y += spl_h + 20
    else:
        c = make_canvas(cw, header_h + 500, BG_PAGE)
        draw_panel_header(c, cw, cdata.get("name", ""), "WIKI")

    # basic info
    draw_shadow_panel(c, margin, y, card_w, 200)
    info_y = y + CARD_PADDING
    labels = [
        ("武器", cdata.get("weaponTypeName", "")),
        ("命之座", cdata.get("astro", "")),
        ("生日", cdata.get("birthday", "")),
        ("归属", cdata.get("allegiance", "")),
        ("中文CV", cdata.get("cncv", "")),
        ("日文CV", cdata.get("jpcv", "")),
    ]
    for i, (lbl, val) in enumerate(labels):
        ix = margin + CARD_PADDING + (i % 2) * (card_w // 2)
        iy = info_y + (i // 2) * 40
        c.text(f"{lbl}: ", ix, iy, font_size=24, color=TEXT_MED)
        tw = c.text_size(f"{lbl}: ", font_size=24)[0]
        c.text(val, ix + tw, iy, font_size=24, color=TEXT_DARK)

    # element badge
    elem = cdata.get("elem", "")
    if elem:
        draw_badge(c, margin + card_w - 80, info_y, elem.upper(),
                   bg_color=elem_color(elem), font_size=18)
    y += 220

    # base stats
    if attrs:
        draw_shadow_panel(c, margin, y, card_w, 40 + len(attrs) * 36)
        st = cdata.get("star", 0)
        c.text(f"100级基础属性 {st}星", margin + CARD_PADDING, y + 10,
               font_size=24, color=TEXT_MED)
        y += 50
        for attr in attrs:
            at = attr.get("title", "")
            av = attr.get("value", "")
            c.text(at, margin + CARD_PADDING + 16, y, font_size=22, color=TEXT_DARK)
            tw = c.text_size(at, font_size=22)[0]
            c.text(av, margin + CARD_PADDING + 26 + tw, y, font_size=22, color=ACCENT_BLUE)
            y += 36
        y += 10

    # materials
    if materials:
        draw_shadow_panel(c, margin, y, card_w, 40 + len(materials) * 36)
        c.text("突破材料", margin + CARD_PADDING, y + 10, font_size=24, color=TEXT_MED)
        y += 50
        for mat in materials:
            mt = mat.get("type", "")
            mn2 = mat.get("name", "") or mat.get("label", "")
            c.text(f"{mt}: {mn2}", margin + CARD_PADDING + 16, y,
                   font_size=22, color=TEXT_DARK)
            y += 36
        y += 10

    draw_footer(c, cw, y + 20)
    return c.to_bytes()


async def render_talent(data: dict[str, Any]) -> bytes:
    name = data.get("name", "")
    title = data.get("title", "")
    detail = data.get("detail", {})
    imgs = data.get("imgs", {})
    line = data.get("line", [])
    talents = data.get("talent", [])
    game = data.get("game", "gs")
    mode = data.get("mode", "talent")

    cw = 1000
    margin = PADDING
    card_w = cw - margin * 2
    header_h = 160
    y = header_h + 30

    c = make_canvas(cw, header_h + 80, BG_PAGE)
    display_name = f"{title}·{name}" if game == "gs" else name
    draw_panel_header(c, cw, display_name, "天赋")

    # head card
    draw_shadow_panel(c, margin, y, card_w, 200)
    face = imgs.get("face", "")
    if face:
        draw_char_icon(c, face, margin + CARD_PADDING, y + CARD_PADDING, 120)
    c.text(name, margin + 160, y + 28, font_size=34, color=TEXT_DARK)

    # talent icon
    elem = detail.get("elem", "hydro")
    if c.assets:
        talent_bg = c.assets.talent_bg(elem)
        if talent_bg:
            c.image(talent_bg, margin + 160, y + 80, w=80, h=80)

    desc = data.get("desc", detail.get("desc", ""))
    c.text(desc[:100], margin + 160, y + 80, font_size=22, color=TEXT_MED,
           max_width=card_w - 180)
    y += 220

    # base stats
    if line:
        draw_shadow_panel(c, margin, y, card_w, 60)
        lv_label = "100" if game == "gs" else "80"
        c.text(f"{lv_label}级基础数据", margin + CARD_PADDING, y + 14,
               font_size=24, color=TEXT_MED)
        lx = margin + 200
        for item in line:
            num = item.get("num", "")
            label = item.get("label", "")
            c.text(num, lx, y + 10, font_size=28, color=ACCENT_BLUE, anchor="mt")
            c.text(label, lx, y + 40, font_size=18, color=TEXT_LIGHT, anchor="mt")
            lx += 120
        y += 80

    # talent list
    if mode == "talent" and talents:
        for t in talents:
            tk = t.get("key", "")
            tn = t.get("name", "")
            td = t.get("desc", "")

            draw_shadow_panel(c, margin, y, card_w, 110)
            elem_c = elem_color(elem)
            # talent bg
            if c.assets:
                talent_bg = c.assets.talent_bg(elem)
                if talent_bg:
                    c.image(talent_bg, margin + CARD_PADDING - 2, y + 14 - 2, w=56, h=56)
            c.rect(margin + CARD_PADDING, y + 16, 50, 50, radius=12, fill=elem_c)
            # talent icon
            char_name = detail.get("name", name)
            if c.assets and game:
                ticon = c.assets.char_talent(char_name, game, tk)
                if ticon:
                    c.image(ticon, margin + CARD_PADDING + 5, y + 21, w=40, h=40)
            c.text(tk.upper(), margin + CARD_PADDING + 25, y + 41,
                   font_size=26, color=(255, 255, 255, 255), anchor="mm")
            c.text(tn, margin + 86, y + 18, font_size=28, color=TEXT_DARK)
            c.text(td[:80], margin + 86, y + 56, font_size=20,
                   color=TEXT_MED, max_width=card_w - 106)
            y += 125

    draw_footer(c, cw, y + 20)
    return c.to_bytes()
