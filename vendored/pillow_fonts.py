from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import ImageFont


class FontManager:
    """Shared font loader with caching. Each plugin passes its font_dir on each get()."""
    _cache: dict[str, ImageFont.FreeTypeFont] = {}

    @classmethod
    def get(cls, name: str, size: int,
            font_dir: Path | str | None = None) -> ImageFont.FreeTypeFont:
        fd = Path(font_dir) if font_dir else Path(".")
        key = f"{name}_{size}_{fd}"
        if key in cls._cache:
            return cls._cache[key]
        font = cls._load(name, size, fd)
        cls._cache[key] = font
        return font

    @classmethod
    def _load(cls, name: str, size: int, fd: Path) -> ImageFont.FreeTypeFont:
        font_map = {
            "HYWH": "HYWH-65W.ttf",
            "HYWenHei": "HYWenHei-55W.ttf",
            "NZBZ": "NZBZ.ttf",
            "number": "tttgbnumber.ttf",
            "icon": "iconfont.woff2",
            "icon_sr": "iconfont_sr.woff2",
        }
        filename = font_map.get(name)
        if filename:
            path = fd / filename
            if path.exists():
                try:
                    return ImageFont.truetype(str(path), size)
                except Exception:
                    pass
        if (fd / "HYWH-65W.ttf").exists():
            try:
                return ImageFont.truetype(str(fd / "HYWH-65W.ttf"), size)
            except Exception:
                pass
        if (fd / "HYWenHei-55W.ttf").exists():
            try:
                return ImageFont.truetype(str(fd / "HYWenHei-55W.ttf"), size)
            except Exception:
                pass
        try:
            return ImageFont.truetype(str(fd / "tttgbnumber.ttf"), size)
        except Exception:
            return ImageFont.load_default()

    @classmethod
    def text_size(cls, draw: Any, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    @classmethod
    def wrap_text(cls, draw: Any, text: str, font: ImageFont.FreeTypeFont,
                  max_width: int) -> list[str]:
        lines: list[str] = []
        for paragraph in text.split("\n"):
            if not paragraph:
                lines.append("")
                continue
            line = ""
            for ch in paragraph:
                test = line + ch
                w = draw.textbbox((0, 0), test, font=font)[2] - draw.textbbox((0, 0), test, font=font)[0]
                if w > max_width and line:
                    lines.append(line)
                    line = ch
                else:
                    line = test
            if line:
                lines.append(line)
        return lines

    @classmethod
    def draw_text_multiline(cls, draw: Any, text: str, x: int, y: int,
                            font: ImageFont.FreeTypeFont, color: tuple[int, ...],
                            max_width: int = 0, line_spacing: int = 8,
                            anchor: str = "lt") -> tuple[int, int]:
        lines = cls.wrap_text(draw, text, font, max_width) if max_width else text.split("\n")
        total_h = 0
        max_w = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lh = bbox[3] - bbox[1]
            lw = bbox[2] - bbox[0]
            draw.text((x, y + total_h), line, fill=color, font=font, anchor=anchor)
            total_h += lh + line_spacing
            max_w = max(max_w, lw)
        return max_w, total_h - line_spacing
