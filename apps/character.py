from __future__ import annotations

from ..adapter import MiaoEvent
from ..apps._avatar_wife import _build_wife_regex, wife_render
from ..apps._character_card import card_render

CHARACTER_PATTERN: str = r"^/喵喵角色卡片$"
WIFE_PATTERN: str = _build_wife_regex()


async def character_handler(e: MiaoEvent) -> None:
    """Handle character card command: #喵喵角色卡片 [name]"""
    result = await card_render(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def wife_handler(e: MiaoEvent) -> None:
    """Handle wife/husband command: #老婆/老公/女儿 etc."""
    result = await wife_render(e)
    if isinstance(result, bytes):
        e.reply_image(result)
