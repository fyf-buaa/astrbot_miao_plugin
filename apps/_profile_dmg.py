from __future__ import annotations

import re
from typing import Any

from ..components.common import render
from ..models.player import Player
from ..models.profiledmg import ProfileDmg


async def calc_damage_handler(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    game = "sr" if "星铁" in msg else getattr(e, "game", "gs")
    uid = str(getattr(e, "uid", ""))
    if not uid:
        e.reply("请先绑定 UID"); return

    player = Player.create(e, game)
    char_name = re.sub(r"^[#/]+", "", msg).replace("伤害", "").replace("星铁", "").replace("原神", "").strip()
    char_name = re.sub(r"\d+$", "", char_name).strip()
    if not char_name:
        e.reply("请指定角色，如 #雷神伤害 或 #星铁遐蝶伤害"); return

    found = {}
    def _find(a, aid):
        if char_name in a.name:
            found["avatar"] = a
            return False
    player.for_each_avatar(_find)
    avatar = found.get("avatar")
    if not avatar:
        e.reply(f"未找到角色 {char_name}"); return

    p_dmg = ProfileDmg(avatar, game)
    if not p_dmg.char:
        e.reply(f"角色 {char_name} 的伤害计算配置未找到"); return

    results = await p_dmg.calc_damage_full(enemy_lv=103)
    if isinstance(results, dict) and results.get("noConfig"):
        e.reply(f"暂未支持 {char_name}，请继续浏览其他角色"); return

    if results and isinstance(results, list):
        return await render("character/damage", {
            "charName": avatar.name,
            "elem": getattr(avatar, "elem", "physical") or "physical",
            "game": game,
            "results": results,
            "enemyLv": 103,
        }, e=e, scale=1.2)

    if isinstance(results, list) and len(results) == 0:
        e.reply(f"暂未支持 {char_name}，请继续浏览其他角色"); return

    result = await p_dmg.calc_damage_simple()
    if not result:
        e.reply("伤害计算失败（角色面板数据可能不完整）"); return
    e.reply(
        f"{avatar.name} 伤害估算\n"
        f"  基础: {result['raw']}\n"
        f"  期望: {result['avg']}\n"
        f"  暴击: {result['crit']}"
    ); return
