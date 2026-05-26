from __future__ import annotations

from typing import Any


async def enemy_level(e: Any) -> Any:
    msg = str(getattr(e, "msg", ""))
    import re
    m = re.search(r"(\d{1,3})", msg)
    if m:
        level = int(m.group(1))
        e._enemyLv = level
        return await e.reply(f"目标敌人等级已设置为 {level}")
    return await e.reply("请指定敌人等级，如 #敌人等级90")
