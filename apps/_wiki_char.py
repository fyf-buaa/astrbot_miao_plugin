from __future__ import annotations

from typing import Any

from ..models.character import Character

from ..adapter import MiaoEvent
from ..components.common import render

WEAPON_TYPE_MAP: dict[str, str] = {
    "sword": "单手剑",
    "claymore": "双手剑",
    "polearm": "长柄武器",
    "bow": "弓",
    "catalyst": "法器",
    "long_ranged": "远程",
    "melee": "近战",
    "assist": "辅助",
    "magic": "法师",
}

GROW_KEY_MAP: dict[str, str] = {
    "hp": "生命值",
    "atk": "攻击力",
    "def": "防御力",
    "recharge": "元素充能效率",
    "em": "元素精通",
    "cpct": "暴击率",
    "cdmg": "暴击伤害",
    "dmg": "元素伤害加成",
    "heal": "治疗加成",
    "phy": "物理伤害加成",
}

MAT_MAP: dict[str, dict[str, str]] = {
    "gem": {"type": "gem", "num": "1"},
    "boss": {"type": "boss", "num": "1"},
    "specialty": {"type": "specialty", "num": "1"},
    "normal": {"type": "normal", "num": "1"},
    "talent": {"type": "talent", "num": "1"},
    "weekly": {"type": "weekly", "num": "1"},
}

TALENT_KEYS: dict[str, str] = {
    "a": "普通攻击",
    "e": "元素战技",
    "q": "元素爆发",
}

ATTR_MAP: dict[str, str] = {
    "hp": "生命值",
    "atk": "攻击力",
    "def": "防御力",
    "em": "元素精通",
}


async def character_wiki(e: MiaoEvent) -> bytes | None:
    """Render character wiki page."""
    msg = str(getattr(e, "msg", "")).strip()
    game = "sr" if "星铁" in msg else "gs"
    char_name = msg.replace("#", "").replace("喵喵", "").replace("WIKI", "").replace("wiki", "").strip()
    if not char_name:
        e.reply("请指定角色名，如 #甘雨WIKI")
        return None

    char = Character.get(char_name, game)
    if not char:
        e.reply(f"未找到角色 {char_name}")
        return None

    detail = char.get_detail()
    if not detail:
        e.reply("未找到角色数据")
        return None

    data = {
        "title": detail.get("title", ""),
        "name": detail.get("name", char.name),
        "desc": detail.get("desc", ""),
        "weaponTypeName": WEAPON_TYPE_MAP.get(detail.get("weapon", ""), detail.get("weapon", "")),
        "astro": detail.get("astro", ""),
        "birthday": detail.get("birth", ""),
        "allegiance": detail.get("allegiance", ""),
        "cncv": detail.get("cncv", ""),
        "jpcv": detail.get("jpcv", ""),
        "star": detail.get("star", char.star),
    }

    base_attr = detail.get("baseAttr", {})
    grow_attr = detail.get("growAttr", {})
    attr_list: list[dict[str, str]] = []
    for ak, av in base_attr.items():
        title = GROW_KEY_MAP.get(ak, ak.upper())
        val = f"{av:.2f}" if isinstance(av, float) else str(av)
        if grow_attr.get("key") == ak:
            val += f" + {grow_attr.get('value', 0):.2f}%"
        attr_list.append({"title": title, "value": val})

    materials = detail.get("materials", {})
    mat_list: list[dict[str, str]] = []
    for mk, mv in materials.items():
        mat_list.append({
            "type": MAT_MAP.get(mk, {}).get("type", mk),
            "num": MAT_MAP.get(mk, {}).get("num", "1"),
            "name": mv,
        })

    imgs = {
        "splash": f"/meta-gs/character/{char.name}/splash.png",
        "face": char.face or f"/img/avatar/{char.id}.png",
    }

    return await render("wiki/character-wiki", {
        "data": data,
        "attr": attr_list,
        "materials": mat_list,
        "imgs": imgs,
        "game": game,
    }, e=e, scale=1.2)


async def character_talent(e: MiaoEvent) -> bytes | None:
    """Render character talent page."""
    msg = str(getattr(e, "msg", "")).strip()
    game = "sr" if "星铁" in msg else "gs"
    char_name = msg.replace("#", "").replace("天赋", "").replace("技能", "").strip()
    if not char_name:
        e.reply("请指定角色名，如 #甘雨天赋")
        return None

    char = Character.get(char_name, game)
    if not char:
        e.reply(f"未找到角色 {char_name}")
        return None

    detail = char.get_detail()
    talent = detail.get("talent", {})

    talent_list: list[dict[str, Any]] = []
    for tk, tname in TALENT_KEYS.items():
        td = talent.get(tk, {})
        talent_list.append({
            "key": tk,
            "name": td.get("name", tname),
            "desc": td.get("desc", [""])[0] if td.get("desc") else "",
            "id": td.get("id", ""),
        })

    imgs = {
        "card": f"/meta-gs/character/{char.name}/card.png",
        "face": char.face or f"/img/avatar/{char.id}.png",
        "qFace": f"/img/avatar/{char.id}.png",
    }

    base_attr = detail.get("baseAttr", {})
    line: list[dict[str, str]] = []
    for ak, av in base_attr.items():
        entry = ATTR_MAP.get(ak)
        if entry:
            line.append({"num": f"{av:.1f}" if isinstance(av, float) else str(av), "label": entry})

    return await render("wiki/character-talent", {
        "name": char.name,
        "title": detail.get("title", ""),
        "desc": detail.get("desc", ""),
        "detail": detail,
        "imgs": imgs,
        "line": line,
        "talent": talent_list,
        "game": game,
    }, e=e, scale=1.2)
