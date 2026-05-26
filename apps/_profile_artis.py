from __future__ import annotations

from typing import Any

from ..components.common import render
from ..models.player import Player
from ..models.artis.artismark import get_key_title_map, get_mark_class, get_mark_detail


async def artis_list(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    game = "sr" if "星铁" in msg else getattr(e, "game", "gs")
    uid = str(getattr(e, "uid", ""))
    if not uid:
        e.reply("请先绑定 UID"); return

    player = Player.create(e, game)
    chars: list[dict[str, Any]] = []
    player.for_each_avatar(lambda avatar, aid: chars.append({
        "avatar": avatar,
        "id": aid,
        "name": avatar.name,
        "elem": avatar.elem,
        "face": avatar.imgs.get("face", "") or avatar.imgs.get("side", ""),
        "side": avatar.imgs.get("side", ""),
    }))

    if not chars:
        e.reply("没有已获取的角色面板数据，请先使用 #更新面板"); return

    artis_key_title = get_key_title_map(game)
    artis_list_data: list[dict[str, Any]] = []
    for char_info in chars:
        avatar = char_info["avatar"]
        if not avatar.is_profile:
            continue
        artis_detail = get_mark_detail(avatar, True)
        if not artis_detail:
            continue
        pieces = artis_detail.get("artis", {})
        for idx_str, arti in pieces.items():
            if isinstance(arti, dict):
                main_attr = arti.get("main", {})
                sub_attrs = arti.get("attrs", [])
                mark_val = arti.get("_mark", 0)
                if not isinstance(mark_val, (int, float)):
                    mark_val = 0
                artis_list_data.append({
                    "face": char_info["face"] or f"meta-{game}/character/{avatar.name}/imgs/face.webp",
                    "charName": avatar.name,
                    "name": arti.get("name", ""),
                    "img": arti.get("img", ""),
                    "main": main_attr,
                    "attrs": sub_attrs,
                    "mark": round(mark_val, 1),
                    "markClass": get_mark_class(round(mark_val, 1)),
                    "star": arti.get("star", 5),
                    "level": arti.get("level", 0),
                })

    artis_list_data.sort(key=lambda x: (-x["mark"], -x["star"], -x["level"]))

    return await render("character/artis-list", {
        "uid": uid,
        "game": game,
        "artis": artis_list_data,
        "artisKeyTitle": artis_key_title,
    }, e=e, scale=1.2)
