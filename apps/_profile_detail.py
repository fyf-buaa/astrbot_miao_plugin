from __future__ import annotations

import re
from typing import Any

from ..components.common import render
from ..components.meta import Meta
from ..models.player import Player


async def detail(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()

    is_sr = "星铁" in msg or getattr(e, "isSr", False)
    game = "sr" if is_sr else "gs"

    char_name, change_info = _parse_msg(msg)
    if not char_name:
        e.reply("请指定角色名，如 #雷神面板"); return

    resolved = _resolve_char_id(char_name, game)
    if not resolved:
        e.reply(f"未找到角色：{char_name}"); return
    char_id = resolved["id"]
    game = resolved["game"]
    is_sr = game == "sr"

    uid = str(getattr(e, "uid", ""))
    uid_map = getattr(e, "_uid_map", {}) or {}
    if game == "sr":
        uid = uid_map.get("sr", "") or ""
    elif game == "zzz":
        uid = uid_map.get("zzz", "") or ""
    elif game == "gs":
        uid = uid_map.get("gs_main", "") or ""
        if not uid:
            uid = (uid_map.get("gs_list") or [""])[0]
    if not uid:
        e.reply("请先绑定 UID"); return

    player = Player.create(e, game)

    avatar = player.get_avatar(char_id, create=False)
    if not avatar:
        e.reply("暂未获取该角色面板数据，请先使用 #更新面板"); return

    data = _build_profile_data(avatar)
    if is_sr:
        return await render("profile/super-character/sr_profile", data, e=e, scale=1.2)
    return await render("profile/super-character/profile", data, e=e, scale=1.2)


def _parse_msg(msg: str) -> tuple[str, str]:
    msg = re.sub(r"^[#/]+", "", msg)
    for prefix in ["星铁", "原神", "绝区零"]:
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
            break
    for suffix in ["面板", "面版", "详情", "详细", "圣遗物", "遗器", "伤害", "换"]:
        if suffix in msg:
            parts = msg.split(suffix, 1)
            return parts[0].strip(), suffix
    return msg.strip(), ""


def _resolve_char_id(name: str, game: str = "gs") -> dict[str, Any] | bool:
    for g in [game, "sr" if game == "gs" else "gs"]:
        data = Meta.get_data(g, "char", name)
        if data:
            cid = str(data.get("id", ""))
            if cid:
                return {"id": cid, "game": g}
        _id = Meta.get_id(g, "char", name)
        if _id:
            data = Meta.get_data(g, "char", _id)
            if data:
                cid = str(data.get("id", ""))
                if cid:
                    return {"id": cid, "game": g}
    return False


def _build_profile_data(avatar: Any) -> dict[str, Any]:
    detail = avatar.get_detail()
    weapon = detail.get("weapon", {})
    talent = detail.get("talent", {})

    # enriched artifact data with scoring
    from ..models.artis.artismark import get_mark_detail, get_key_title_map

    artis_mark_raw = get_mark_detail(avatar, with_detail=True)
    artis_mark = artis_mark_raw if isinstance(artis_mark_raw, dict) else {}
    artis_raw = detail.get("artis", [])

    # Chinese title map with hardcoded fallback
    _FALLBACK_TITLES = {
        "hp": "生命值", "atk": "攻击力", "def": "防御力", "em": "元素精通",
        "mastery": "元素精通", "cpct": "暴击率", "cdmg": "暴击伤害",
        "recharge": "充能效率", "heal": "治疗加成", "dmg": "伤害加成",
        "phy": "物理伤害", "physDmg": "物理伤害",
        "hpPlus": "小生命", "atkPlus": "小攻击", "defPlus": "小防御",
        "hpPct": "大生命", "atkPct": "大攻击", "defPct": "大防御",
        "speed": "速度", "stance": "击破特攻",
        "effPct": "效果命中", "effDef": "效果抵抗",
        "shield": "护盾强效", "critRate": "暴击率", "critDmg": "暴击伤害",
        "pyroDmg": "火伤加成", "hydroDmg": "水伤加成", "anemoDmg": "风伤加成",
        "electroDmg": "雷伤加成", "cryoDmg": "冰伤加成", "geoDmg": "岩伤加成",
        "dendroDmg": "草伤加成", "physDmg": "物伤加成",
    }
    key_title = get_key_title_map(avatar.game)
    if not key_title:
        key_title = _FALLBACK_TITLES

    # build enriched artis list with mark/img/set/abbr per piece
    artis_enriched = []
    artis_mark_pieces = artis_mark.get("artis", {}) if artis_mark else {}
    for piece in artis_raw:
        idx = piece.get("idx", "1")
        md = artis_mark_pieces.get(idx, {}) if isinstance(artis_mark_pieces, dict) else {}
        artis_enriched.append({
            "idx": idx,
            "name": md.get("name", piece.get("name", "")),
            "abbr": md.get("abbr", ""),
            "set": md.get("set", ""),
            "img": md.get("img", ""),
            "level": md.get("level", piece.get("level", 0)),
            "star": piece.get("star", 5),
            "main": piece.get("main", {}),
            "attrs": piece.get("attrs", []),
            "mark": md.get("mark", "0"),
            "markClass": md.get("markClass", ""),
        })

    # aggregate all substats across pieces (allAttr)
    all_attr: dict[str, dict] = {}
    for piece in artis_enriched:
        attrs = piece.get("attrs", [])
        if not isinstance(attrs, list):
            continue
        for attr in attrs:
            if not isinstance(attr, dict):
                continue
            k = attr.get("key", "")
            if not k:
                continue
            if k not in all_attr:
                all_attr[k] = {"key": k, "value": 0.0, "upNum": 0}
            all_attr[k]["value"] += attr.get("value", 0)
            all_attr[k]["upNum"] += attr.get("upNum", 0)

    all_attr_list = sorted(all_attr.values(), key=lambda x: -x["value"])

    return {
        "name": detail.get("name", ""),
        "level": detail.get("level", 1),
        "cons": detail.get("cons", 0),
        "fetter": detail.get("fetter", 0),
        "star": detail.get("star", 5),
        "elem": detail.get("elem", "anemo"),
        "face": detail.get("face", ""),
        "side": detail.get("side", ""),
        "splash": detail.get("splash", ""),
        "gacha": detail.get("gacha", ""),
        "game": avatar.game,
        "char_name": avatar.name,
        "weapon": {
            "name": weapon.get("name", ""),
            "level": weapon.get("level", 1),
            "affix": weapon.get("affix", 1),
            "star": weapon.get("star", 5),
            "img": weapon.get("img", ""),
            "abbr": weapon.get("abbr", ""),
            "type": weapon.get("type", ""),
            "hp": weapon.get("hp", 0),
            "atk": weapon.get("atk", 0),
            "def": weapon.get("def", 0),
        },
        "talent": {
            k: {
                "level": v.get("level", 1) if isinstance(v, dict) else v,
                "original": v.get("original", 1) if isinstance(v, dict) else v,
            }
            for k, v in talent.items()
        } if talent else {},
        "artisSet": detail.get("artisSet", {}),
        "artis": artis_enriched,
        "artisMark": {
            "total": artis_mark.get("mark", "0"),
            "markClass": artis_mark.get("markClass", ""),
            "classTitle": artis_mark.get("classTitle", ""),
            "allAttr": all_attr_list,
            "keyTitle": key_title,
            "artis": artis_mark.get("artis", {}),
        },
        "hp": detail.get("hp", 0),
        "atk": detail.get("atk", 0),
        "def": detail.get("def", 0),
        "em": detail.get("em", 0),
        "critRate": detail.get("critRate", 0),
        "critDmg": detail.get("critDmg", 0),
        "recharge": detail.get("recharge", 0),
        "heal": detail.get("heal", 0),
        "dmgBonus": detail.get("dmgBonus", 0),
        "speed": detail.get("speed", 0),
        "effPct": detail.get("effPct", 0),
        "effDef": detail.get("effDef", 0),
        "stance": detail.get("stance", 0),
    }
