from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw


def rounded_rect(draw: Any, x: int, y: int, w: int, h: int, r: int,
                 fill: tuple[int, ...] | str | None = None,
                 outline: tuple[int, ...] | str | None = None,
                 width: int = 1) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill, outline=outline, width=width)


def gradient_bar(img: Image.Image, x: int, y: int, w: int, h: int,
                 color_start: tuple[int, ...], color_end: tuple[int, ...],
                 direction: str = "vertical") -> None:
    for i in range(h if direction == "vertical" else w):
        ratio = i / max(h if direction == "vertical" else w, 1)
        color = tuple(int(c1 + (c2 - c1) * ratio) for c1, c2 in zip(color_start, color_end))
        if direction == "vertical":
            ImageDraw.Draw(img).line([(x, y + i), (x + w, y + i)], fill=color, width=1)
        else:
            ImageDraw.Draw(img).line([(x + i, y), (x + i, y + h)], fill=color, width=1)


def star_shape(cx: int, cy: int, r: int, pts: int = 5) -> list[float]:
    import math
    points: list[float] = []
    for i in range(pts * 2):
        angle = math.pi / 2 - i * math.pi / pts
        radius = r if i % 2 == 0 else r * 0.4
        points.append(cx + radius * math.cos(angle))
        points.append(cy - radius * math.sin(angle))
    return points


def draw_stars(draw: Any, x: int, y: int, star: int, size: int = 20,
               color: tuple[int, ...] = (255, 215, 0)) -> None:
    gap = 4
    for i in range(star):
        cx = x + i * (size + gap)
        points = star_shape(cx + size // 2, y + size // 2, size // 2)
        draw.polygon(points, fill=color)


def crop_circle(img: Image.Image) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, img.width, img.height], fill=255)
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result
