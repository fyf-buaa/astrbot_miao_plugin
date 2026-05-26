from __future__ import annotations

import asyncio
from typing import Any

from ..vendored.pillow_canvas import Canvas


async def render(path: str, params: dict[str, Any] | None = None,
                 e: Any = None, scale: float = 1) -> bytes:
    from ..renderer import render as pillow_render
    img_data = await pillow_render(path, params or {})
    return img_data


class Common:
    render = staticmethod(render)

    @staticmethod
    async def sleep(ms: int) -> None:
        await asyncio.sleep(ms / 1000)
