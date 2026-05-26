from __future__ import annotations

from typing import Any

from .pillow_draw import draw_stars as _draw_stars

# ── Core Palette ─────────────────────────────────────────────────────

WHITE = (255, 255, 255, 255)
BG_PAGE = (245, 243, 240, 255)
BG_CARD = (255, 255, 255, 255)
BG_CARD_HOVER = (255, 255, 255, 255)
BG_HEADER = (60, 80, 160, 255)

TEXT_DARK = (40, 40, 55, 255)
TEXT_MED = (70, 70, 90, 255)
TEXT_LIGHT = (110, 110, 130, 255)
TEXT_HINT = (140, 140, 155, 255)
TEXT_WHITE = (255, 255, 255, 255)
TEXT_ACCENT = (255, 100, 50, 255)

ACCENT_BLUE = (80, 120, 200, 255)
ACCENT_DARK = (60, 80, 160, 255)

# ── Star / Rarity ────────────────────────────────────────────────────

STAR_5 = (255, 215, 0, 255)
STAR_4 = (180, 80, 220, 255)
STAR_3 = (80, 160, 255, 255)

STAR_COLORS: dict[int, tuple[int, int, int, int]] = {
    5: (255, 215, 0, 255),
    4: (180, 80, 220, 255),
    3: (80, 160, 255, 255),
}

RARITY_BORDER: dict[int, tuple[int, int, int, int]] = {
    5: (255, 200, 50, 200),
    4: (180, 100, 220, 200),
    3: (100, 160, 240, 200),
}

# ── Element Colors ───────────────────────────────────────────────────

COLOR_ELEM: dict[str, tuple[int, int, int, int]] = {
    "pyro":       (255, 100, 50, 255),
    "hydro":      (50, 150, 255, 255),
    "cryo":       (100, 200, 255, 255),
    "electro":    (180, 80, 255, 255),
    "anemo":      (120, 220, 180, 255),
    "geo":        (255, 200, 50, 255),
    "dendro":     (100, 200, 80, 255),
    "quantum":    (80, 150, 255, 255),
    "imaginary":  (255, 210, 80, 255),
    "physical":   (180, 180, 180, 255),
    # aliases
    "fire":       (255, 100, 50, 255),
    "ice":        (100, 200, 255, 255),
    "wind":       (120, 220, 180, 255),
    "lightning":  (180, 80, 255, 255),
    "thunder":    (180, 80, 255, 255),
}


def elem_color(elem: str) -> tuple[int, int, int, int]:
    return COLOR_ELEM.get(elem, ACCENT_BLUE)


def elem_gradient(elem: str) -> tuple[tuple, tuple]:
    c = elem_color(elem)
    darker = tuple(max(0, v - 50) for v in c[:3]) + (c[3],)
    return c, darker


# ── Layout Constants ─────────────────────────────────────────────────

PADDING = 30
CARD_PADDING = 20
SECTION_GAP = 16
CARD_GAP = 12

HEADER_H = 80
HEADER_H_LARGE = 160

# ── Drawing Helpers ──────────────────────────────────────────────────


def draw_panel_header(c: Any, width: int, title: str,
                      subtitle: str = "",
                      elem: str | None = None,
                      height: int = HEADER_H_LARGE) -> int:
    if elem and elem in COLOR_ELEM:
        start, end = elem_gradient(elem)
    else:
        start, end = (60, 90, 170, 255), (40, 60, 130, 255)
    c.gradient(0, 0, width, height, start, end)
    # subtle bottom shadow line
    c.rect(0, height - 3, width, 3, fill=(0, 0, 0, 30), radius=0)
    c.text(title, 50, 36, font_name="NZBZ", font_size=52, color=TEXT_WHITE)
    if subtitle:
        c.text(subtitle, 50, 100, font_size=28, color=(200, 210, 240, 255))
    return height


def draw_footer(c: Any, width: int, y: int, text: str = "Miao-Plugin") -> int:
    c.text(text, width // 2, y + 10, font_size=22, color=TEXT_LIGHT, anchor="mt")
    return 50


def draw_char_icon(c: Any, path: str, x: int, y: int, size: int,
                   star: int = 5) -> None:
    border_color = RARITY_BORDER.get(star, STAR_5)
    c.rect(x - 2, y - 2, size + 4, size + 4, radius=8,
           fill=border_color[:3] + (60,), outline=border_color, border=2)
    c.image(path, x, y, w=size, h=size)


def draw_stars(c: Any, x: int, y: int, star: int, size: int = 20) -> int:
    from .pillow_draw import draw_stars as _ds
    _ds(c.draw, x, y, star, size, (255, 215, 0))
    return star * (size + 4)


def draw_rounded_panel(c: Any, x: int, y: int, w: int, h: int,
                       fill: tuple[int, ...] = BG_CARD,
                       radius: int = 16) -> None:
    c.rect(x, y, w, h, radius=radius, fill=fill)


def draw_shadow_panel(c: Any, x: int, y: int, w: int, h: int,
                      radius: int = 16, fill: tuple = BG_CARD) -> None:
    """Panel with a darker drop-shadow layer behind it."""
    offset = 4
    blur = 6
    # shadow layer
    c.rect(x + 2, y + offset, w, h, radius=radius, fill=(0, 0, 0, 30))
    # main panel
    c.rect(x, y, w, h, radius=radius, fill=fill)


def draw_section_title(c: Any, x: int, y: int, w: int, text: str,
                       color: tuple = ACCENT_BLUE) -> int:
    """Section title with a colored left bar."""
    bar_w = 4
    c.rect(x, y, bar_w, 28, radius=2, fill=color)
    c.text(text, x + bar_w + 10, y, font_name="HYWH", font_size=26, color=TEXT_DARK)
    return 36


def draw_horiz_line(c: Any, x: int, y: int, w: int,
                    color: tuple = (200, 200, 200, 150), width: int = 1) -> None:
    c.rect(x, y, w, width, fill=color)


def draw_info_row(c: Any, x: int, y: int, label: str, value: str,
                  label_color: tuple = TEXT_MED,
                  value_color: tuple = TEXT_DARK,
                  font_size: int = 24, spacing: int = 8) -> int:
    """Label | Value row, returns consumed height."""
    lw = c.text_size(label, "HYWH", font_size)[0]
    c.text(label, x, y, font_size=font_size, color=label_color)
    c.text(value, x + lw + spacing, y, font_size=font_size, color=value_color)
    return font_size + 6


def draw_badge(c: Any, x: int, y: int, text: str,
               bg_color: tuple = ACCENT_BLUE,
               text_color: tuple = TEXT_WHITE,
               font_size: int = 20, pad_x: int = 10, pad_y: int = 4) -> tuple[int, int]:
    """Rounded badge / tag."""
    tw, th = c.text_size(text, "HYWH", font_size)
    bw = tw + pad_x * 2
    bh = th + pad_y * 2
    c.rect(x, y, bw, bh, radius=bh // 2, fill=bg_color)
    c.text(text, x + bw // 2, y + bh // 2, font_size=font_size,
           color=text_color, anchor="mm")
    return bw, bh


def draw_gradient_badge(c: Any, x: int, y: int, text: str,
                        elem: str = "", font_size: int = 20) -> tuple[int, int]:
    """Badge colored by element."""
    color = elem_color(elem) if elem else ACCENT_BLUE
    return draw_badge(c, x, y, text, bg_color=color, font_size=font_size)


# ── Layout Helpers ───────────────────────────────────────────────────


class Layout:
    """Reusable layout calculations."""

    @staticmethod
    def card_width(container_w: int, columns: int, gap: int = CARD_GAP) -> int:
        return (container_w - PADDING * 2 - gap * (columns - 1)) // columns

    @staticmethod
    def grid_pos(index: int, columns: int, card_w: int, gap: int,
                 start_x: int, start_y: int) -> tuple[int, int]:
        col = index % columns
        row = index // columns
        x = start_x + col * (card_w + gap)
        y = start_y + row * (card_w + gap)  # square cards
        return x, y
