from __future__ import annotations

from datetime import datetime

from ..models.character import Character

from ..adapter import MiaoEvent
from ..components.common import render
from ..components.meta import Meta

_WEEKDAY_MATERIAL_MAP: dict[str, dict[str, list[str]]] = {
    "1": {"talent": ["自由"], "weapon": ["高塔孤王"]},
    "2": {"talent": ["抗争"], "weapon": ["雾海云间"]},
    "3": {"talent": ["诗文"], "weapon": ["凛风奔狼"]},
    "4": {"talent": ["自由", "抗争", "诗文"], "weapon": ["高塔孤王", "雾海云间", "凛风奔狼"]},
    "5": {"talent": ["抗争", "诗文", "自由"], "weapon": ["雾海云间", "凛风奔狼", "高塔孤王"]},
    "6": {"talent": ["诗文", "自由", "抗争"], "weapon": ["凛风奔狼", "高塔孤王", "雾海云间"]},
    "7": {"talent": [], "weapon": []},
}

_MATERIAL_ICONS: dict[str, str] = {
    "自由": "/wiki/imgs/天赋书·自由.png",
    "抗争": "/wiki/imgs/天赋书·抗争.png",
    "诗文": "/wiki/imgs/天赋书·诗文.png",
    "高塔孤王": "/wiki/imgs/武器突破·高塔孤王.png",
    "雾海云间": "/wiki/imgs/武器突破·雾海云间.png",
    "凛风奔狼": "/wiki/imgs/武器突破·凛风奔狼.png",
}

_CITY_MAP: dict[str, str] = {
    "蒙德": "Mondstadt",
    "璃月": "Liyue",
    "稻妻": "Inazuma",
    "须弥": "Sumeru",
    "枫丹": "Fontaine",
    "纳塔": "Natlan",
}


def _get_char_material_info() -> list[dict]:
    chars: list[dict] = []
    for _id in Meta.get_ids("gs", "char"):
        data = Meta.get_data("gs", "char", _id)
        if not data or not data.get("star"):
            continue
        char = Character.get(_id)
        if not char or not char.is_release:
            continue
        detail = char.get_detail()
        materials = detail.get("materials", {})
        talent_mat = materials.get("talent", "")
        weapon_type = detail.get("weapon", "")
        chars.append({
            "name": char.name,
            "star": char.star,
            "cons": 0,
            "isMax": False,
            "face": char.face or f"/img/avatar/{char.id}.png",
            "talentMat": talent_mat,
            "weaponType": weapon_type,
        })
    return chars


async def today_material(e: MiaoEvent) -> bytes | None:
    """Render today's material page."""
    msg = str(getattr(e, "msg", "")).strip()
    game = "sr" if "星铁" in msg else "gs"

    now = datetime.now()
    weekday = str(now.isoweekday())

    today_mats = _WEEKDAY_MATERIAL_MAP.get(weekday, {"talent": [], "weapon": []})
    day_name = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]

    if game == "sr":
        talent_str = "、".join(today_mats.get("talent", [])) or "无（周日）"
        weapon_str = "、".join(today_mats.get("weapon", [])) or "无（周日）"
        e.reply(f"{day_name} 天赋材料：{talent_str}\n武器材料：{weapon_str}")
        return None

    all_chars = _get_char_material_info()
    talent_chars = [c for c in all_chars if c["talentMat"] in today_mats["talent"]]
    talent_chars.sort(key=lambda c: (-c["star"], c["name"]))

    city_data: list[dict] = []
    for city_name, _city_key in _CITY_MAP.items():
        for mtype in ("talent", "weapon"):
            mats = today_mats.get(mtype, [])
            if not mats:
                continue
            city_chars = [c for c in talent_chars]
            city_data.append({
                "city": city_name,
                "type": mtype,
                "material": {"name": "、".join(mats), "icons": [_MATERIAL_ICONS.get(m, "") for m in mats]},
                "data": city_chars[:30],
            })

    return await render("wiki/today-material", {
        "uid": getattr(e, "uid", ""),
        "day": day_name,
        "data": city_data,
        "game": game,
    }, e=e, scale=1.2)
