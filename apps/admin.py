from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

from ..components.cfg import Cfg
from ..components.common import render
from ..components.version import Version
from ..tools.path import miao_path

_res_path = Path(f"{miao_path}/resources/")
_plus_path = _res_path / "miao-res-plus"
_RES_URL = "https://gitee.com/yoimiya-kokomi/miao-res-plus.git"


async def update_res_handler(e: Any) -> bool:
    """Git pull image resources (miao-res-plus)."""
    if not getattr(e, "isMaster", False):
        await e.reply("只有主人才能命令喵喵哦~ \n(*/ω＼*)")
        return True

    if _plus_path.exists():
        await e.reply("开始尝试更新，请耐心等待~")
        proc = await asyncio.create_subprocess_exec(
            "git", "pull",
            cwd=str(_plus_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out = stdout.decode("utf-8", errors="replace")
        if re.search(r"(Already up[ -]to[ -]date|已经是最新的)", out):
            await e.reply("目前所有图片都已经是最新了~")
        elif proc.returncode == 0:
            nums = re.findall(r"(\d+) files changed", out)
            if nums:
                await e.reply(f"报告主人，更新成功，此次更新了{nums[0]}个图片~")
            else:
                await e.reply("图片加量包更新成功~")
        else:
            await e.reply(f"更新失败！\n{stderr.decode('utf-8', errors='replace')[:500]}")
    else:
        await e.reply("开始尝试安装图片加量包，请耐心等待~")
        _res_path.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            "git", "clone", _RES_URL, str(_plus_path), "--depth=1",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0 and _plus_path.exists():
            await e.reply("图片加量包安装成功~")
        else:
            err = stderr.decode("utf-8", errors="replace")[:500]
            await e.reply(f"安装失败！请手动克隆至 resources/miao-res-plus\n{err}")
    return True


async def sys_cfg_handler(e: Any) -> bool:
    """Toggle system config items and render the admin panel."""
    if not getattr(e, "isMaster", False):
        await e.reply("只有主人才能命令喵喵哦~ \n(*/ω＼*)")
        return True

    msg = str(getattr(e, "msg", ""))
    parts = msg.split(maxsplit=1)
    if len(parts) >= 2:
        rest = parts[1].strip()
        if rest:
            sub = rest.split(maxsplit=1)
            key = sub[0].strip()
            val = sub[1].strip() if len(sub) > 1 else ""
            schema = Cfg.get_cfg_schema()
            items: dict = {}
            if isinstance(schema, dict):
                for g in schema.values():
                    items.update(g.get("cfg", {}))
            item = items.get(key)
            if item:
                if val:
                    Cfg.set(item["cfgKey"], val)
                else:
                    Cfg.set(item["cfgKey"], not Cfg.get(item["cfgKey"], False))

    schema = Cfg.get_cfg_schema()
    cfg = Cfg.get_cfg()
    img_plus = _plus_path.exists()

    img_data = await render("admin/index", {
        "schema": list(schema.values()),
        "cfg": cfg,
        "imgPlus": img_plus,
        "isMiao": Version.is_miao,
        "bgType": "",
    }, e=e, scale=1.4)
    await e.reply_image(img_data)
    return True
