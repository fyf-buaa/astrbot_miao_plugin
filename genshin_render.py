"""Adapted image renderer for genshin plugin (uses vendored pillow elements).

Migrated from ``yunzai-py/plugins/genshin/render.py`` – replaced
``app.render.*`` imports with local ``vendored.pillow_*`` modules.
Returns raw PNG bytes instead of ``MessageSegment.image(...)``.
"""

from __future__ import annotations

from typing import Any

from .renderer import make_canvas
from .vendored.pillow_elements import (
    TEXT_DARK,
    TEXT_WHITE,
    ACCENT_BLUE,
    BG_CARD,
    draw_footer,
    PADDING,
)

# ── Palette ─────────────────────────────────────────────────────────

BG_PAGE = (245, 243, 240, 255)

_TYPE_COLORS: dict[str, tuple[int, int, int, int]] = {
    "原神": (60, 120, 200, 255),
    "星铁": (160, 80, 200, 255),
    "绝区零": (230, 140, 50, 255),
}


# ── Template renderers ──────────────────────────────────────────────


async def render_uid_list(data: dict[str, Any]) -> bytes:
    """Render the UID list as a PNG image, returns raw bytes."""
    uids: list[dict[str, Any]] = data.get("uids", [])
    main_uid: str = data.get("main_uid", "")
    qq: Any = data.get("qq", "")

    width = 480
    pad = PADDING
    header_h = 64
    section_h = 34
    row_h = 50
    gap = 6
    section_gap = 14
    top_pad = 16
    bottom_pad = 20

    groups: dict[str, list[dict[str, Any]]] = {}
    for u in uids:
        t = u.get("type", "其他")
        groups.setdefault(t, []).append(u)

    rows_total = sum(len(v) for v in groups.values())
    groups_total = len(groups)
    content_h = (
        top_pad
        + groups_total * (section_h + gap)
        + rows_total * (row_h + gap)
        + bottom_pad
    )
    height = header_h + content_h + 40

    c = make_canvas(width, max(height, 200), BG_PAGE)

    # Header
    c.gradient(0, 0, width, header_h, (60, 90, 170, 255), (40, 60, 130, 255))
    c.text("绑定 UID 列表", 24, 16, font_name="HYWH", font_size=28, color=TEXT_WHITE)
    if qq:
        c.text(
            f"QQ: {qq}",
            width - 24,
            18,
            font_size=18,
            color=(200, 210, 240, 255),
            anchor="rt",
        )

    y = header_h + top_pad

    for type_name, uid_list in groups.items():
        bg = _TYPE_COLORS.get(type_name, ACCENT_BLUE)
        c.rect(pad, y, width - 2 * pad, section_h, radius=6, fill=bg)
        c.text(
            f"  {type_name}",
            pad + 12,
            y + 6,
            font_name="HYWH",
            font_size=20,
            color=TEXT_WHITE,
        )
        y += section_h + gap

        for u in uid_list:
            uid_str: str = u.get("uid", "")
            is_main: bool = u.get("is_main", False)
            cx = pad + 8
            cw = width - 2 * pad - 16

            if is_main:
                c.rect(
                    cx,
                    y,
                    cw,
                    row_h,
                    radius=8,
                    fill=(230, 237, 255, 255),
                    outline=ACCENT_BLUE,
                    border=2,
                )
            else:
                c.rect(cx, y, cw, row_h, radius=8, fill=BG_CARD)

            c.text(
                uid_str,
                cx + 16,
                y + 16,
                font_name="number",
                font_size=22,
                color=TEXT_DARK if not is_main else ACCENT_BLUE,
            )

            type_label = u.get("type", "")
            tw = c.text_size(type_label, "HYWH", 16)[0]
            tag_x = cx + cw - tw - 20
            tag_y = y + (row_h - 24) // 2
            c.rect(tag_x, tag_y, tw + 12, 24, radius=4, fill=bg)
            c.text(
                type_label,
                tag_x + (tw + 12) // 2,
                tag_y + 12,
                font_size=16,
                color=TEXT_WHITE,
                anchor="mm",
            )

            if is_main:
                badge_x = tag_x - 54
                c.rect(badge_x, tag_y, 46, 24, radius=4, fill=ACCENT_BLUE)
                c.text(
                    "主",
                    badge_x + 23,
                    tag_y + 12,
                    font_size=16,
                    color=TEXT_WHITE,
                    anchor="mm",
                )

            y += row_h + gap

        y += section_gap - gap

    draw_footer(c, width, y)
    return c.to_bytes()
