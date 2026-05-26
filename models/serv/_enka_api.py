from __future__ import annotations

import logging
from typing import Any

import aiohttp

from . import _enka_data

URL = "https://enka.network/api/uid/{uid}"
USER_AGENT = "Miao-Plugin/3.1"


_session: aiohttp.ClientSession | None = None


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def _request(uid: str, cfg: dict[str, Any]) -> dict[str, Any]:
    url = URL.format(uid=uid)
    headers = {"User-Agent": cfg.get("userAgent", USER_AGENT)}
    logging.debug("[enka] GET %s", url)
    session = await _get_session()
    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
        logging.debug("[enka] response status=%d for uid=%s", resp.status, uid)
        if resp.status != 200:
            return {"error": f"HTTP {resp.status}", "retcode": resp.status}
        return await resp.json()


async def fetch_user(uid: str, cfg: dict[str, Any]) -> dict[str, Any]:
    return await _request(uid, cfg)


class EnkaApi:
    id = "enka"
    cfg_key = "enkaApi"

    async def request(self, uid: str, cfg: dict[str, Any]) -> dict[str, Any]:
        data = await _request(uid, cfg)
        if not data.get("playerInfo"):
            if data.get("error"):
                return {"error": data["error"], "cd": 60}
            return {"error": "empty", "cd": 300}
        return data

    def update_player(self, player: Any, data: dict[str, Any]) -> None:
        pinfo = data.get("playerInfo", {})
        player.set_basic_data({
            "name": pinfo.get("nickname", ""),
            "face": pinfo.get("profilePicture", {}).get("avatarId", 0),
            "card": pinfo.get("nameCardId", 0),
            "level": pinfo.get("worldLevel", 0),
            "word": pinfo.get("worldLevel", 0),
            "sign": pinfo.get("signature", ""),
        })
        for avatar_data in data.get("avatarInfoList", []):
            _enka_data.set_avatar(player, avatar_data, "enka")

    def cd_time(self, data: dict[str, Any]) -> int:
        return data.get("ttl", 60)


enka_api = EnkaApi()
