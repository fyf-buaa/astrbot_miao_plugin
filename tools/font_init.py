"""Font initialization for Chinese text rendering.

Ensures required Chinese fonts are available for Pillow rendering.
Falls back to system-installed Chinese fonts if bundled fonts are missing.
"""
from __future__ import annotations

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger("astrbot_plugin_miao.font_init")

# Required fonts for rendering (name → filename)
REQUIRED_FONTS: dict[str, str] = {
    "HYWH": "HYWH-65W.ttf",        # 华文黑体 (primary Chinese font)
    "NZBZ": "NZBZ.ttf",             # Chinese font
    "number": "tttgbnumber.ttf",    # Number font
}

# System font fallback paths by OS
_SYSTEM_FONT_PATHS: dict[str, list[str]] = {
    "nt": [  # Windows
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\simhei.ttf",    # 黑体
        r"C:\Windows\Fonts\simsun.ttc",    # 宋体
    ],
    "posix": [  # Linux / macOS
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # Noto Sans CJK
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",  # macOS PingFang
        "/System/Library/Fonts/STHeiti Medium.ttc",  # macOS 黑体
    ],
}


def _find_system_font() -> str | None:
    """Find an available system Chinese font."""
    paths = _SYSTEM_FONT_PATHS.get(os.name, [])
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def ensure_fonts(font_dir: Path | str) -> None:
    """Ensure required fonts exist in font_dir.

    If bundled fonts are missing, copies system fonts as fallback.
    """
    font_dir = Path(font_dir)
    font_dir.mkdir(parents=True, exist_ok=True)

    missing = []
    for name, filename in REQUIRED_FONTS.items():
        if not (font_dir / filename).exists():
            missing.append((name, filename))

    if not missing:
        logger.debug("All required fonts found in %s", font_dir)
        return

    logger.warning(
        "Missing %d font(s) in %s: %s",
        len(missing), font_dir, [f for _, f in missing],
    )

    # Try to find a system font to use as fallback
    system_font = _find_system_font()
    if system_font:
        logger.info("Using system font fallback: %s", system_font)
        for name, filename in missing:
            target = font_dir / filename
            if not target.exists():
                try:
                    shutil.copy2(system_font, target)
                    logger.info("Copied system font to %s", target)
                except Exception as e:
                    logger.error("Failed to copy system font: %s", e)
    else:
        logger.error(
            "No system Chinese font found. Chinese text may not render correctly. "
            "Please install a Chinese font (e.g., 微软雅黑, 文泉驿微米黑, or Noto Sans CJK)."
        )


def check_fonts(font_dir: Path | str) -> dict[str, bool]:
    """Check which required fonts are available.

    Returns dict mapping font name to availability status.
    """
    font_dir = Path(font_dir)
    result = {}
    for name, filename in REQUIRED_FONTS.items():
        result[name] = (font_dir / filename).exists()
    return result
