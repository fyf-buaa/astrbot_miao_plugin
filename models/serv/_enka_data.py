from __future__ import annotations

from typing import Any

from ..weapon import Weapon

_ARTIS_IDX_MAP: dict[str, int] = {
    "EQUIP_BRACER": 1,
    "EQUIP_NECKLACE": 2,
    "EQUIP_SHOES": 3,
    "EQUIP_RING": 4,
    "EQUIP_DRESS": 5,
    "生之花": 1,
    "死之羽": 2,
    "时之沙": 3,
    "空之杯": 4,
    "理之冠": 5,
}


def _get_talent(char_id: int | str, skill_level_map: dict[str, int]) -> dict[str, Any]:
    from ..character import Character
    char = Character.get(char_id)
    talent_id_map: dict[str, str] = {}
    talent_elem_map: dict[str, str] = {}
    if char and char.meta:
        talent_id_map = char.meta.get("talentId", {})
        talent_elem_map = char.meta.get("talentElem", {})

    elem = ""
    idx = 0
    ret: dict[str, int] = {}
    for sid, lv in skill_level_map.items():
        sid_str = str(sid)
        if sid_str in talent_id_map:
            key = talent_id_map[sid_str]
            if not elem:
                elem = talent_elem_map.get(sid_str, "")
            ret[key] = int(lv)
        else:
            key = ["a", "e", "q"][idx] if idx < 3 else f"t{idx}"
            idx += 1
            if key not in ret:
                ret[key] = int(lv)
    return {"elem": elem, "talent": ret}


def _get_weapon(equip_list: list[dict[str, Any]]) -> dict[str, Any]:
    ds: dict[str, Any] = {}
    for temp in equip_list:
        flat = temp.get("flat", {})
        if flat.get("itemType") == "ITEM_WEAPON":
            ds = temp
            break
    weapon = ds.get("weapon", {})
    affix_values = list((weapon.get("affixMap", {}) or {}).values())
    affix = (affix_values[0] if affix_values else 0) + 1
    w = Weapon.get(ds.get("itemId"))
    return {
        "name": w.name if w else "",
        "level": int(weapon.get("level", 1)),
        "promote": int(weapon.get("promoteLevel", 0)),
        "affix": affix,
    }


def _get_artifact(equip_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    from ..artifact import Artifact
    ret: dict[str, dict[str, Any]] = {}
    for ds in equip_list:
        flat = ds.get("flat", {})
        if flat.get("itemType") != "ITEM_RELIQUARY":
            continue
        re = ds.get("reliquary", {})
        equip_type = flat.get("equipType", "")
        idx = _ARTIS_IDX_MAP.get(equip_type)
        if not idx:
            continue
        arti = Artifact.get(ds.get("itemId"))
        ret[str(idx)] = {
            "id": str(ds.get("itemId", "")),
            "name": arti.name if arti else "",
            "level": min(20, max(0, (re.get("level", 1) or 1) - 1)),
            "star": int(flat.get("rankLevel", 5)),
            "mainId": re.get("mainPropId", ""),
            "attrIds": re.get("appendPropIdList", []),
        }
    return ret


def set_avatar(player: Any, data: dict[str, Any], data_source: str = "enka") -> Any:
    from ..character import Character
    avatar_id = data.get("avatarId")
    char = Character.get(avatar_id)
    if not char:
        return None
    avatar = player.get_avatar(char.id, create=True)
    talent_ret = _get_talent(char.id, data.get("skillLevelMap", {}))
    avatar.set_avatar({
        "level": int(data.get("propMap", {}).get("4001", {}).get("val", 1)),
        "promote": int(data.get("propMap", {}).get("1002", {}).get("val", 0)),
        "cons": len(data.get("talentIdList", [])),
        "fetter": int(data.get("fetterInfo", {}).get("expLevel", 0)),
        "costume": data.get("costumeId", 0) if char.check_costume(data.get("costumeId", 0)) else 0,
        "elem": talent_ret["elem"],
        "weapon": _get_weapon(data.get("equipList", [])),
        "talent": talent_ret["talent"],
        "artis": _get_artifact(data.get("equipList", [])),
        "fightPropMap": data.get("fightPropMap", {}),
    }, data_source)
    player._update.append(avatar.id)
    return avatar
