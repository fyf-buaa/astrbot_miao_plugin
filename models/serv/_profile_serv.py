from __future__ import annotations

from typing import Any


class ProfileServ:
    def __init__(self, api: Any) -> None:
        self.api = api
        self.name = getattr(api, "id", "unknown")

    async def request_profile(self, player: Any) -> dict[str, Any]:
        config_mod = getattr(self.api, "cfg_key", None)
        url_cfg: dict[str, Any] = {}
        if config_mod:
            from ...components.cfg import Cfg
            url_cfg = Cfg.get(config_mod, {})

        req_data = await self.api.request(player.uid, url_cfg)
        return req_data

    def update_player(self, player: Any, data: dict[str, Any]) -> None:
        self.api.update_player(player, data)

    def cd_time(self, data: dict[str, Any]) -> int:
        return self.api.cd_time(data)
