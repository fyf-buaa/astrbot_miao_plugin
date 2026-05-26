from __future__ import annotations

from typing import Any

from ..components.common import render
from ..models.player import Player


async def profile_list(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    is_sr = "星铁" in msg or getattr(e, "isSr", False)
    game = "sr" if is_sr else "gs"

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
        "face": avatar.imgs.get("face", ""),
        "isProfile": avatar.is_profile,
    }))

    return await render("profile/normal-character/list", {
        "playerName": player.name or uid,
        "characters": chars,
        "element": "default",
    }, e=e, scale=1.2)


async def refresh_profile(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    is_sr = "星铁" in msg or getattr(e, "isSr", False)
    game = "sr" if is_sr else "gs"

    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")

    from ..tools._cooldown import CooldownCache
    cd_key = f"refresh_profile:{uid}:{game}"
    if not CooldownCache.check(cd_key, ttl=300):
        return await e.reply("该 UID 5 分钟内已更新，请稍后再试")

    import logging
    logging.info("[profile] refresh uid=%s game=%s", uid, game)

    player = Player.create(e, game)
    player.e = e
    success = await player.refresh_profile()
    logging.info("[profile] refresh result uid=%s success=%s", uid, success)
    if success > 0:
        game_name = "星铁" if game == "sr" else "原神"
        return await e.reply(f"{game_name}面板更新完成，共更新 {success} 个角色")
    return await e.reply("面板更新失败，请稍后重试")


async def delete_profile(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    is_sr = "星铁" in msg or getattr(e, "isSr", False)
    game = "sr" if is_sr else "gs"

    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")

    Player.del_by_uid(uid, game)
    return await e.reply(f"UID {uid} 面板数据已删除")


async def profile_reload(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    is_sr = "星铁" in msg or getattr(e, "isSr", False)
    game = "sr" if is_sr else "gs"

    uid = str(getattr(e, "uid", ""))
    if not uid:
        return await e.reply("请先绑定 UID")

    player = Player.create(e, game)
    player.reload()
    return await e.reply(f"UID {uid} 面板数据已重新加载（{game}）")
