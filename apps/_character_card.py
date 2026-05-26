from __future__ import annotations

from typing import Any

from ..components.common import render
from ..models.character import Character
from ..models.player import Player


def _get_card_bg(char: Any) -> dict[str, Any]:
    default = {"img": "", "mode": "center", "width": 600, "height": 480}
    return default


async def card_render(e: Any) -> Any:
    msg = str(getattr(e, "msg", "")).strip()
    game = "gs"
    uid = str(getattr(e, "uid", ""))
    char_name = msg.replace("#", "").replace("喵喵角色卡片", "").replace("卡片", "").strip()

    char = Character.get(char_name, game) if char_name else None
    if not char:
        e.reply("未找到角色，请指定正确的角色名"); return

    avatar = None
    if uid and char.is_release:
        player = Player.create(e, game)
        avatar = player.get_avatar(char.id)

    return await _render_card(e, avatar or char, uid, game)


async def _render_card(e: Any, avatar: Any, uid: str, game: str) -> Any:
    from ..models.character import Character
    char = Character.get(avatar.id) if hasattr(avatar, "id") else None
    if not char:
        char = avatar if isinstance(avatar, Character) else None
    if not char:
        char_id = getattr(avatar, "id", getattr(avatar, "char", None))
        if char_id:
            char = Character.get(str(char_id))
    if not char:
        e.reply("未找到角色信息"); return

    bg = _get_card_bg(char)
    is_custom = getattr(char, "is_custom", False)
    is_release = getattr(char, "is_release", False)
    has_data = getattr(avatar, "is_profile", False) if avatar else False

    data: dict[str, Any] = {
        "id": char.id,
        "name": char.name,
        "sName": char.abbr or char.name,
        "elem": char.elem,
        "star": char.star,
        "weapon": char.weapon_type,
        "level": getattr(avatar, "level", 0) if has_data else 0,
        "cons": getattr(avatar, "cons", 0) if has_data else 0,
        "fetter": getattr(avatar, "fetter", 0) if has_data else 0,
        "source": getattr(avatar, "_source", "") if has_data else "",
        "updateTime": "",
    }

    if has_data:
        detail = avatar.get_detail() if hasattr(avatar, "get_detail") else {}
        weapon = detail.get("weapon", {}) or getattr(avatar, "weapon", {})
        talent = detail.get("talent", {}) or getattr(avatar, "talent", {})
        artis_set = detail.get("artisSet", {}) or (avatar.artis.get_set_data() if hasattr(avatar, "artis") else {})
        data.update({
            "level": detail.get("level", getattr(avatar, "level", 0)),
            "cons": detail.get("cons", getattr(avatar, "cons", 0)),
            "fetter": detail.get("fetter", getattr(avatar, "fetter", 0)),
            "weapon": weapon,
            "talent": talent,
            "artis": {},
            "artisSet": artis_set,
            "imgs": detail.get("imgs", {}),
            "source": detail.get("source", getattr(avatar, "_source", "")),
        })

    return await render("character/character-card", {
        "uid": uid,
        "data": data,
        "bg": bg,
        "custom": is_custom,
        "isRelease": is_release,
        "widthStyle": "",
        "mode": bg.get("mode", "center"),
    }, e=e, scale=1.2)
