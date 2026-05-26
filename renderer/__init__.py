from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..vendored.pillow_canvas import Canvas
from ..vendored.pillow_assets import AssetLoader

from ..tools.path import miao_path
from ..tools.font_init import ensure_fonts

logger = logging.getLogger("astrbot_plugin_miao.renderer")

_miao_res = Path(f"{miao_path}/resources")
_miao_font = _miao_res / "common" / "font"
_miao_assets = AssetLoader(_miao_res)

# Ensure Chinese fonts are available at import time
try:
    ensure_fonts(_miao_font)
except Exception as e:
    logger.warning("Font initialization failed: %s. Chinese text may not render.", e)


def make_canvas(w: int, h: int, bg: tuple[int, ...] = (255, 255, 255, 255)) -> Canvas:
    return Canvas(w, h, bg, res_root=_miao_res, font_dir=_miao_font, asset_loader=_miao_assets)


async def render(template: str, data: dict[str, Any]) -> bytes:
    if template == "help/index":
        from .screens.help import render_help
        return await render_help(data)
    if template == "help/version-info":
        from .screens.admin import render_version_info
        return await render_version_info(data)
    if template == "admin/index":
        from .screens.admin import render_admin
        return await render_admin(data)
    if template.startswith("profile/super-character/"):
        from .screens.profile import render_profile
        return await render_profile(data)
    if template.startswith("profile/normal-character/"):
        from .screens.profile_list import render_profile_list
        return await render_profile_list(data)
    if template.startswith("character/character-card"):
        from .screens.character_card import render_character_card
        return await render_character_card(data)
    if template.startswith("character/avatar-list"):
        from .screens.profile_list import render_avatar_list
        return await render_avatar_list(data)
    if template.startswith("character/artis-list"):
        from .screens.artis_list import render_artis_list
        return await render_artis_list(data)
    if template.startswith("character/damage"):
        from .screens.damage import render_damage
        return await render_damage(data)
    if template.startswith("character/rank-profile-list"):
        from .screens.rank import render_rank_list
        return await render_rank_list(data)
    if template.startswith("wiki/character-wiki"):
        from .screens.wiki import render_wiki
        return await render_wiki(data)
    if template.startswith("wiki/character-talent"):
        from .screens.wiki import render_talent
        return await render_talent(data)
    if template.startswith("wiki/today-material"):
        from .screens.material import render_today_material
        return await render_today_material(data)
    if template.startswith("wiki/calendar"):
        from .screens.material import render_calendar
        return await render_calendar(data)
    raise ValueError(f"Unknown template: {template}")
