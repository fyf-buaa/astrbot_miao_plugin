from __future__ import annotations

import re
from typing import Any

from ..components.common import render
from ..models.player import Player


def get_star_filter(msg: str):
    required = 0
    if re.search(r"(五|4|5)?(星)", msg):
        required = 5 if re.search(r"(五|5)星", msg) else 4
    return lambda ds: ds.get("star", 0) == required if required else True


async def stat_summary(e: Any) -> Any:
    game = "sr" if "星铁" in str(getattr(e, "msg", "")) else "gs"
    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")
    player = Player.create(e, game)
    player.e = e
    await player.refresh_profile(1)
    chars: list[dict[str, Any]] = []
    player.for_each_avatar(lambda avatar, aid: chars.append({
        "id": aid,
        "name": avatar.name,
        "level": avatar.level,
        "cons": avatar.cons,
        "star": avatar.char.star if avatar.char else 5,
        "elem": avatar.elem,
        "fetter": avatar.fetter,
        "face": avatar.imgs.get("face", ""),
        "talent": avatar.talent,
        "weapon": avatar.weapon,
        "isProfile": avatar.is_profile,
    }))
    msg = str(getattr(e, "msg", ""))
    sf = get_star_filter(msg)
    chars = [c for c in chars if sf(c)]
    chars.sort(key=lambda c: (-c["star"], -c["level"], -c["cons"]))
    return await render("profile/normal-character/list", {
        "playerName": player.name or uid,
        "characters": chars,
        "element": "default",
    }, e=e, scale=1.2)


async def talent_stat(e: Any) -> Any:
    game = "sr" if "星铁" in str(getattr(e, "msg", "")) else "gs"
    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")
    player = Player.create(e, game)
    chars: list[dict[str, Any]] = []
    player.for_each_avatar(lambda avatar, aid: chars.append({
        "id": aid,
        "name": avatar.name,
        "level": avatar.level,
        "cons": avatar.cons,
        "star": avatar.char.star if avatar.char else 5,
        "elem": avatar.elem,
        "face": avatar.imgs.get("face", ""),
        "talent": avatar.talent,
    }))
    chars.sort(key=lambda c: (-c["star"], -c["level"], -c["cons"]))
    msg_parts = []
    for c in chars[:20]:
        talent = c.get("talent", {})
        lvs = []
        for sk in ("a", "e", "q"):
            entry = talent.get(sk, {})
            lv = entry.get("level", 1) if isinstance(entry, dict) else entry
            lvs.append(str(lv))
        msg_parts.append(f"{c['name']} {'/'.join(lvs)}")
    return await e.reply("天赋等级 (A/E/Q):\n" + "\n".join(msg_parts) if msg_parts else "暂无角色数据")


async def avatar_list(e: Any) -> Any:
    game = "sr" if "星铁" in str(getattr(e, "msg", "")) else "gs"
    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")
    player = Player.create(e, game)
    chars: list[dict[str, Any]] = []
    player.for_each_avatar(lambda avatar, aid: chars.append({
        "id": aid,
        "name": avatar.name,
        "level": avatar.level,
        "cons": avatar.cons,
        "star": avatar.char.star if avatar.char else 5,
        "elem": avatar.elem,
        "face": avatar.imgs.get("face", ""),
        "side": avatar.imgs.get("side", ""),
        "weapon": avatar.weapon,
        "isProfile": avatar.is_profile,
    }))
    chars.sort(key=lambda c: (-c["star"], -c["level"], -c["cons"]))
    return await render("character/avatar-list", {
        "uid": uid,
        "chars": chars,
        "element": "default",
    }, e=e, scale=1.2)
