from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .pillow_fonts import FontManager
from .pillow_draw import crop_circle, rounded_rect, gradient_bar


class Canvas:
    """Shared Pillow canvas for plugin image generation.
    Pass `res_root` to constructor or it defaults to current directory.
    """

    def __init__(self, width: int, height: int,
                 background: tuple[int, ...] = (255, 255, 255, 255),
                 res_root: Path | str | None = None,
                 font_dir: Path | str | None = None,
                 asset_loader: Any | None = None):  # AssetLoader instance
        self.width = width
        self.height = height
        self.img = Image.new("RGBA", (width, height), background)
        self.draw = ImageDraw.Draw(self.img, "RGBA")
        self._res_root = Path(res_root) if res_root else Path(".")
        self._font_dir = Path(font_dir) if font_dir else None
        self.assets = asset_loader

    def _font(self, name: str, size: int):
        if self._font_dir:
            return FontManager.get(name, size, font_dir=self._font_dir)
        return FontManager.get(name, size)

    # ── Basic Shapes ─────────────────────────────────────────────────

    def rect(self, x: int, y: int, w: int, h: int,
             fill: tuple[int, ...] | None = None,
             radius: int = 0,
             outline: tuple[int, ...] | None = None,
             border: int = 1) -> None:
        if radius > 0:
            rounded_rect(self.draw, x, y, w, h, radius, fill=fill, outline=outline, width=border)
        else:
            if fill:
                self.draw.rectangle([x, y, x + w, y + h], fill=fill)
            if outline:
                self.draw.rectangle([x, y, x + w, y + h], outline=outline, width=border)

    def hline(self, x: int, y: int, w: int,
              color: tuple = (200, 200, 200, 150), width: int = 1) -> None:
        self.draw.rectangle([x, y, x + w, y + width], fill=color)

    def vline(self, x: int, y: int, h: int,
              color: tuple = (200, 200, 200, 150), width: int = 1) -> None:
        self.draw.rectangle([x, y, x + width, y + h], fill=color)

    # ── Shadow Panel ─────────────────────────────────────────────────

    def shadow_rect(self, x: int, y: int, w: int, h: int,
                    radius: int = 12,
                    shadow_offset: tuple = (0, 4),
                    shadow_blur: int = 6,
                    shadow_color: tuple = (0, 0, 0, 35),
                    fill: tuple = (255, 255, 255, 230)) -> None:
        """Draw a rounded rect with a drop shadow behind it."""
        ox, oy = shadow_offset
        # shadow layer
        self.rect(x + ox, y + oy, w, h, radius=radius, fill=shadow_color)
        # blur the shadow: draw it multiple times with decreasing opacity
        for i in range(shadow_blur):
            alpha = int(shadow_color[3] * (1 - i / shadow_blur) * 0.3)
            blur_color = shadow_color[:3] + (max(0, alpha),)
            self.rect(x + ox - i, y + oy - i, w + i * 2, h + i * 2,
                      radius=radius + i, fill=blur_color)
        # main panel
        self.rect(x, y, w, h, radius=radius, fill=fill)

    # ── Gradients ────────────────────────────────────────────────────

    def gradient(self, x: int, y: int, w: int, h: int,
                 start: tuple[int, ...], end: tuple[int, ...],
                 direction: str = "vertical") -> None:
        gradient_bar(self.img, x, y, w, h, start, end, direction)

    def gradient_multi(self, x: int, y: int, w: int, h: int,
                       colors: list[tuple[float, tuple[int, ...]]],
                       direction: str = "vertical") -> None:
        """Multi-color gradient.
        colors = [(position_0_to_1, color), ...]
        """
        length = h if direction == "vertical" else w
        if length == 0:
            return
        draw = ImageDraw.Draw(self.img)
        for i in range(length):
            ratio = i / length
            for j in range(len(colors) - 1):
                p1, c1 = colors[j]
                p2, c2 = colors[j + 1]
                if p1 <= ratio <= p2:
                    seg = (ratio - p1) / (p2 - p1) if p2 > p1 else 0
                    color = tuple(
                        int(c1[k] + (c2[k] - c1[k]) * seg) for k in range(len(c1))
                    )
                    break
            else:
                color = colors[-1][1]
            if direction == "vertical":
                draw.line([(x, y + i), (x + w, y + i)], fill=color, width=1)
            else:
                draw.line([(x + i, y), (x + i, y + h)], fill=color, width=1)

    # ── Text ─────────────────────────────────────────────────────────

    def text(self, text: str, x: int, y: int,
             font_name: str = "HYWH", font_size: int = 28,
             color: tuple[int, ...] = (255, 255, 255),
             anchor: str = "lt",
             max_width: int = 0,
             line_spacing: int = 8) -> tuple[int, int]:
        font = self._font(font_name, font_size)
        if max_width:
            return FontManager.draw_text_multiline(
                self.draw, text, x, y, font, color,
                max_width=max_width, line_spacing=line_spacing, anchor=anchor)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        self.draw.text((x, y), text, fill=color, font=font, anchor=anchor)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def text_size(self, text: str, font_name: str = "HYWH",
                  font_size: int = 28) -> tuple[int, int]:
        font = self._font(font_name, font_size)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def text_shadow(self, text: str, x: int, y: int,
                    font_name: str = "HYWH", font_size: int = 28,
                    color: tuple = (255, 255, 255),
                    shadow_color: tuple = (0, 0, 0, 80),
                    shadow_offset: tuple = (1, 2),
                    anchor: str = "lt") -> tuple[int, int]:
        """Text with a drop shadow drawn behind it."""
        sx, sy = shadow_offset
        font = self._font(font_name, font_size)
        self.draw.text((x + sx, y + sy), text, fill=shadow_color, font=font, anchor=anchor)
        self.draw.text((x, y), text, fill=color, font=font, anchor=anchor)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def gradient_text(self, text: str, x: int, y: int,
                      font_name: str = "HYWH", font_size: int = 28,
                      colors: list[tuple] | None = None,
                      direction: str = "horizontal",
                      anchor: str = "lt") -> tuple[int, int]:
        """Text filled with a gradient.
        colors = [(position, (r,g,b,a)), ...]. If None, uses blue-to-purple.
        """
        if colors is None:
            colors = [(0.0, (60, 120, 255, 255)), (1.0, (180, 80, 255, 255))]
        font = self._font(font_name, font_size)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Create a text mask
        mask = Image.new("L", (tw, th), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.text((-bbox[0], -bbox[1]), text, fill=255, font=font)
        # Create gradient image
        grad = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(grad)
        length = tw if direction == "horizontal" else th
        for i in range(length):
            ratio = i / length if length else 0
            for j in range(len(colors) - 1):
                p1, c1 = colors[j]
                p2, c2 = colors[j + 1]
                if p1 <= ratio <= p2:
                    seg = (ratio - p1) / (p2 - p1) if p2 > p1 else 0
                    col = tuple(int(c1[k] + (c2[k] - c1[k]) * seg) for k in range(4))
                    break
            else:
                col = colors[-1][1]
            if direction == "horizontal":
                gdraw.line([(i, 0), (i, th)], fill=col, width=1)
            else:
                gdraw.line([(0, i), (tw, i)], fill=col, width=1)
        # Apply mask
        result = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        result.paste(grad, mask=mask)
        self.img.paste(result, (x + bbox[0], y + bbox[1]), result)
        return tw, th

    # ── Images ───────────────────────────────────────────────────────

    def image(self, path: str, x: int, y: int,
              w: int | None = None, h: int | None = None) -> None:
        rel = path.lstrip("/")
        abs_path = self._res_root / rel
        if not abs_path.exists():
            return
        try:
            src = Image.open(abs_path).convert("RGBA")
        except Exception:
            return
        if w and h:
            src = src.resize((w, h), Image.LANCZOS)
        elif w:
            ratio = w / src.width
            src = src.resize((w, int(src.height * ratio)), Image.LANCZOS)
        elif h:
            ratio = h / src.height
            src = src.resize((int(src.width * ratio), h), Image.LANCZOS)
        self.img.paste(src, (x, y), src if src.mode == "RGBA" else None)

    def round_image(self, path: str, x: int, y: int, size: int,
                    radius: int | None = None) -> None:
        """Load image and clip to circle or rounded rect."""
        rel = path.lstrip("/")
        abs_path = self._res_root / rel
        if not abs_path.exists():
            return
        try:
            src = Image.open(abs_path).convert("RGBA")
        except Exception:
            return
        src = src.resize((size, size), Image.LANCZOS)
        if radius is None:
            # circle
            src = crop_circle(src)
        else:
            # rounded rect mask
            mask = Image.new("L", (size, size), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
            result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            result.paste(src, mask=mask)
            src = result
        self.img.paste(src, (x, y), src if src.mode == "RGBA" else None)

    def sprite(self, img: Image.Image, x: int, y: int,
               w: int | None = None, h: int | None = None) -> None:
        """Paste a pre-cropped sprite (PIL Image)."""
        if w and h:
            img = img.resize((w, h), Image.LANCZOS)
        self.img.paste(img, (x, y), img if img.mode == "RGBA" else None)

    def paste(self, other: Image.Image, x: int, y: int) -> None:
        self.img.paste(other, (x, y), other if other.mode == "RGBA" else None)

    # ── Overlays ─────────────────────────────────────────────────────

    def overlay(self, x: int, y: int, w: int, h: int,
                color: tuple = (0, 0, 0, 100)) -> None:
        """Semi-transparent overlay — for 'locked' / inactive states."""
        overlay_img = Image.new("RGBA", (w, h), color)
        self.img.paste(overlay_img, (x, y), overlay_img)

    # ── Export ───────────────────────────────────────────────────────

    def to_bytes(self, fmt: str = "PNG") -> bytes:
        buf = io.BytesIO()
        self.img.save(buf, format=fmt)
        return buf.getvalue()

    def to_pil(self) -> Image.Image:
        return self.img.copy()

    def crop_to(self, h: int) -> None:
        self.img = self.img.crop((0, 0, self.img.width, min(h, self.img.height)))
