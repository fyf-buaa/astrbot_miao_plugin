from __future__ import annotations

import logging
import re
from typing import Any

from ..components.cfg import Cfg

logger = logging.getLogger(__name__)
from ..components.common import render
from ..components.format import Format
from ..models.character import Character
from ..models.player import Player
from ..models.profilerank import ProfileRank


async def group_rank(e: Any) -> Any:
    group_id = getattr(e, "group_id", None)
    msg = str(getattr(e, "msg", ""))
    game = "sr" if "星铁" in msg else "gs"

    if not Cfg.get("groupRank", False):
        return await e.reply("群面板排名功能已禁用，Bot主人可通过【#喵喵设置】启用...")

    typ = "mark"
    if re.search(r"(分|圣遗物|遗器|评分|ACE)", msg):
        typ = "mark"
    if re.search(r"(词条)", msg):
        typ = "valid"
    if re.search(r"(双爆|双暴)", msg):
        typ = "crit"
    if re.search(r"(伤害|期望)", msg):
        typ = "dmg"

    name = re.sub(r"[#星铁最强最高分第一词条双爆双暴极限最高最多最牛圣遗物遗器评分群内群排名排行面板面版详情榜]", "", msg).strip()

    char = Character.get(name, game) if name else None

    if not group_id and not (char and "极限" in msg):
        return await e.reply("该命令仅在群聊中可用")

    group_cfg = ProfileRank.get_group_cfg(group_id)
    if group_cfg.get("status") == 1:
        return await e.reply("本群已关闭群排名，群管理员或Bot主人可通过【#启用排名】启用...")

    if "最强" in msg or "最高" in msg or "第一" in msg:
        return await _rank_detail(e, group_id, char, typ, game)

    return await _rank_list(e, group_id, char, typ, game, group_cfg)


async def _rank_detail(e: Any, group_id: int, char: Any, typ: str, game: str) -> Any:
    if not char:
        return await e.reply("请指定角色名")
    uids = ProfileRank.get_top_n(group_id, char.id, typ, 1)
    if not uids:
        return await e.reply(f"暂无排名：请通过【{'*' if game == 'sr' else '#'}面板】查看角色面板以更新排名信息...")
    target_uid = uids[0]["uid"]
    player = Player.create(target_uid, game)
    avatar = player.get_avatar(char.id)
    if not avatar or not avatar.is_profile:
        return await e.reply("排名数据异常")
    e.uid = target_uid
    from ._profile_detail import detail
    return await detail(e)


async def _rank_list(e: Any, group_id: int, char: Any, typ: str, game: str, group_cfg: dict) -> Any:
    if char:
        uids = ProfileRank.get_top_n(group_id, char.id, typ, int(Cfg.get("rankNumber", 15)))
    else:
        uids = ProfileRank.get_top_per_char(group_id, typ, game)

    if not uids:
        return await e.reply(f"暂无排名：请通过【{'*' if game == 'sr' else '#'}面板】查看角色面板以更新排名信息...")

    rank_data_list: list[dict[str, Any]] = []
    for entry in uids:
        uid = entry.get("uid", entry.get("value", ""))
        cid = entry.get("charId", char.id if char else 0)
        player = Player.create(e, game)
        avatar = player.get_avatar(cid)
        if not avatar or not avatar.is_profile:
            continue
        profile_rank = await ProfileRank.create({"groupId": group_id, "uid": uid})
        rank_info = await profile_rank.get_rank_data(avatar, True)
        mark = rank_info.get("mark", {})
        talent = getattr(avatar, "talent", {})
        weapon = getattr(avatar, "weapon", {})
        imgs = avatar.imgs if hasattr(avatar, "imgs") else {}
        artis_set = getattr(avatar, "artis", None)
        artis_set_data = artis_set.get_set_data() if artis_set else {}

        tmp = {
            "uid": uid,
            "isMax": not char,
            "id": avatar.id,
            "star": avatar.char.star if avatar.char else 5,
            "name": avatar.name,
            "sName": getattr(avatar.char, "abbr", avatar.name)[:8],
            "level": avatar.level,
            "fetter": avatar.fetter,
            "cons": avatar.cons,
            "weapon": {
                "name": weapon.get("name", ""),
                "abbr": weapon.get("abbr", ""),
                "star": weapon.get("star", 5),
                "img": weapon.get("img", ""),
                "affix": weapon.get("affix", 1),
                "level": weapon.get("level", 1),
            },
            "elem": avatar.elem,
            "talent": {k: {"level": v.get("level", 1) if isinstance(v, dict) else v,
                           "original": v.get("original", 1) if isinstance(v, dict) else v}
                       for k, v in talent.items()} if talent else {},
            "imgs": imgs,
            "artisSet": artis_set_data,
            "artisMark": {},
            "_mark": 0,
            "_formatmark": "0",
        }

        if mark:
            m_data = mark.get("data") or {}
            tmp["artisMark"] = {"mark": m_data.get("mark", "0"), "markClass": m_data.get("markClass", "D")}
            tmp["_mark"] = float(m_data.get("_mark", 0))
            tmp["_formatmark"] = Format.comma(tmp["_mark"], 1)

        if typ == "crit":
            tmp["_mark"] = tmp.get("_mark", 0) * 6.6044
            tmp["_formatmark"] = Format.comma(tmp["_mark"], 1)

        dmg_info = rank_info.get("dmg", {})
        if dmg_info and dmg_info.get("value"):
            tmp["dmg"] = {"title": f"{avatar.name}伤害", "avg": Format.comma(dmg_info["value"], 1),
                          "rank": dmg_info.get("rank", 99)}

        tmp["_dmg"] = 0 - (tmp.get("dmg", {}) or {}).get("rank", 0)
        tmp["_star"] = 5 - tmp["star"]
        rank_data_list.append(tmp)

    if char:
        rank_data_list.sort(key=lambda x: x.get("_dmg", 0) if typ == "dmg" else x.get("_mark", 0), reverse=True)
    else:
        rank_data_list.sort(key=lambda x: (x.get("uid", ""), x.get("_star", 0), x.get("id", 0)))

    mode_titles = {"mark": "圣遗物评分", "crit": "双爆副词条", "valid": "加权有效词条", "dmg": ""}
    title_name = char.name if char else "全角色"
    title = f"{'*' if game == 'sr' else '#'}{title_name}{mode_titles.get(typ, '')}排行"

    return await render("character/rank-profile-list", {
        "title": title,
        "list": rank_data_list,
        "elem": char.elem if char else "default",
        "game": game,
        "mode": typ,
        "rankCfg": group_cfg,
        "bodyContainerStyle": "",
        "isMemosprite": False,
        "isJoy": False,
        "save_id": char.id if char else 0,
    }, e=e, scale=1.4)


async def reset_rank(e: Any) -> Any:
    group_id = getattr(e, "group_id", None)
    if not group_id:
        return await e.reply("该命令仅在群聊中可用")
    if not getattr(e, "isMaster", False):
        return await e.reply("只有管理员可重置排名")
    msg = str(getattr(e, "msg", ""))
    game = "sr" if "星铁" in msg else "gs"
    name = re.sub(r"[#星铁重置重设排名排行群内面板详情面版]", "", msg).strip()
    if name:
        char = Character.get(name, game)
        if not char:
            return await e.reply(f"重置排名失败，角色：{name}不存在")
        ProfileRank.reset_group(group_id, char.id, game)
        await e.reply(f"本群{char.name}排名已重置...")
    else:
        ProfileRank.reset_group(group_id)
        await e.reply("本群全部角色排名已重置...")


async def refresh_rank(e: Any) -> Any:
    group_id = getattr(e, "group_id", None)
    if not group_id:
        return await e.reply("该命令仅在群聊中可用")
    if not getattr(e, "isMaster", False) and not getattr(e, "isAdmin", False):
        return await e.reply("只有主人及群管理员可刷新排名...")
    await e.reply("面板数据刷新中，等待时间可能较长，请耐心等待...")
    game = "sr" if "星铁" in str(getattr(e, "msg", "")) else "gs"
    ProfileRank.reset_group(group_id, 0, game)
    uid_map = ProfileRank.get_all_uids_with_qq()
    count = 0
    for uid, info in uid_map.items():
        qq = info.get("qq", "")
        player = Player.create(e, game)
        profiles = {}
        player.for_each_avatar(lambda a, aid: profiles.update({aid: a}) if a.is_profile else None)
        ProfileRank.set_uid_info(uid, qq, info.get("type", "bind"),
                                 len(profiles), sum(1 for a in profiles.values() if a.name in ("安柏", "凯亚", "丽莎")))
        rank = await ProfileRank.create({"groupId": group_id, "uid": uid, "qq": qq})
        for aid, avatar in profiles.items():
            await rank.get_rank_data(avatar, True)
        if rank.allow_rank:
            count += 1
    await e.reply(f"本群排名已刷新，共刷新{count}个UID数据...")


async def manage_rank(e: Any) -> Any:
    group_id = getattr(e, "group_id", None)
    if not group_id:
        return await e.reply("该命令仅在群聊中可用")
    is_close = bool(re.search(r"(关闭|禁用)", str(getattr(e, "msg", ""))))
    if not getattr(e, "isMaster", False) and not getattr(e, "isAdmin", False):
        return await e.reply(f"只有主人及群管理员可{'禁用' if is_close else '启用'}排名...")
    ProfileRank.set_group_cfg(group_id, 1 if is_close else 0)
    if is_close:
        await e.reply("当前群排名功能已禁用...")
    else:
        await e.reply("当前群排名功能已启用...\n如数据有问题可通过【#刷新排名】命令来刷新当前群内排名")
