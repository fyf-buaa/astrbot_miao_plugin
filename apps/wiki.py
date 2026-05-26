from __future__ import annotations

from ..adapter import MiaoEvent
from ._calendar import get_calendar
from ._today_material import today_material
from ._wiki_char import character_talent, character_wiki

# ── Regex patterns (preserved from py_miao_plugin) ─────────────────────
WIKI_PATTERN: str = r"^#喵喵WIKI$"
CHAR_WIKI_PATTERN: str = r"^#(.+)(WIKI|wiki|资料|百科)$"
CALENDAR_PATTERN: str = r"^(#|喵喵)+(日历|日历列表)$"
TODAY_MATERIAL_PATTERN: str = r"^#(今日|今天)?(素材|材料|天赋)[ \|0-9]*$"
CHAR_TALENT_PATTERN: str = r"^#(.+)(天赋|技能)(表|数据)?$"
CHAR_MATERIAL_PATTERN: str = r"^#(.+)(材料|突破)$"

# ── Handler functions ──────────────────────────────────────────────────


async def wiki_handler(e: MiaoEvent) -> None:
    """Handle #喵喵WIKI — render general wiki info."""
    result = await character_wiki(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def charWiki_handler(e: MiaoEvent) -> None:
    """Handle #角色WIKI — render character wiki page."""
    result = await character_wiki(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def calendar_handler(e: MiaoEvent) -> None:
    """Handle #日历 — render calendar with birthdays."""
    result = await get_calendar(e, "gs")
    if isinstance(result, bytes):
        e.reply_image(result)


async def todayMaterial_handler(e: MiaoEvent) -> None:
    """Handle #今日材料 — render today's material page."""
    result = await today_material(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def charTalent_handler(e: MiaoEvent) -> None:
    """Handle #角色天赋 — render character talent page."""
    result = await character_talent(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def charMaterial_handler(e: MiaoEvent) -> None:
    """Handle #角色材料 — render character wiki page (materials tab)."""
    result = await character_wiki(e)
    if isinstance(result, bytes):
        e.reply_image(result)
