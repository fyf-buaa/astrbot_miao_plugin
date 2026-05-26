from __future__ import annotations

from ..adapter import MiaoEvent
from ._help_render import render_help, version_info


async def help_handler(e: MiaoEvent) -> None:
    """Handle help command: reply with rendered help image."""
    result = await render_help(e)
    if isinstance(result, bytes):
        e.reply_image(result)


async def version_handler(e: MiaoEvent) -> None:
    """Handle version command: reply with rendered version info image."""
    result = await version_info(e)
    if isinstance(result, bytes):
        e.reply_image(result)
