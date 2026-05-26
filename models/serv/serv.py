from __future__ import annotations

import logging
from typing import Any

from ._enka_api import enka_api
from ._mihomo_api import mihomo_api
from ._profile_serv import ProfileServ

_apis: dict[str, Any] = {
    "gs": enka_api,
    "sr": mihomo_api,
}

_servs: dict[str, ProfileServ] = {}


def get_serv(uid: str, game: str = "gs", from_mys: bool = False) -> ProfileServ:
    api = _apis.get(game, _apis["gs"])
    serv_key = f"{api.id}_{game}"
    if serv_key not in _servs:
        _servs[serv_key] = ProfileServ(api)
    return _servs[serv_key]


async def req(e: Any, player: Any, from_mys: bool = False) -> int | bool:
    serv = get_serv(player.uid, player.game, from_mys)
    uid = player.uid
    try:
        player._update = []
        req_data = await serv.request_profile(player)
        has_data = isinstance(req_data, dict) and bool(req_data.get("playerInfo" if player.game == "gs" else "detailInfo"))
        logging.debug("[serv] uid=%s game=%s has_data=%s", uid, player.game, has_data)
        data = req_data
        if player.game == "gs" and isinstance(data, dict) and data.get("playerInfo"):
            serv.update_player(player, data)
            player.save()
            result = len(player._update) if player._update else 1
            logging.debug("[serv] result=%s for uid=%s (updated %d avatars)", result, uid, len(player._update))
            return result
        elif player.game == "sr" and isinstance(data, dict) and data.get("detailInfo"):
            serv.update_player(player, data)
            player.save()
            result = len(player._update) if player._update else 1
            logging.debug("[serv] sr result=%s for uid=%s (updated %d avatars)", result, uid, len(player._update))
            return result
        return 0
    except Exception as err:
        logging.error("[serv] req exception uid=%s game=%s: %s", uid, player.game, err, exc_info=True)
        if not getattr(e, "_isReplyed", False):
            e.reply(f"UID:{uid}更新面板失败")
        return False
