from __future__ import annotations

import asyncio
import copy
import logging
from typing import Any

from ..character import Character

logger = logging.getLogger("py_miao_plugin")


class EnkaHSRApi:
    id = "enkahsr"
    name = "EnkaHSR"
    cfg_key = "enkaHSRApi"

    async def request(self, uid: str, cfg: dict[str, Any]) -> dict[str, Any]:
        import aiohttp as _aiohttp
        base_url = cfg.get("url", "").rstrip("/")
        if not base_url:
            base_url = "https://enka.network"
        url = f"{base_url}/api/hsr/{uid}"
        headers = {"User-Agent": cfg.get("userAgent", "Miao-Plugin/2.3")}
        logger.info("[EnkaHSR] requesting uid=%s url=%s", uid, url)
        timeout_obj = _aiohttp.ClientTimeout(total=60)
        for attempt in range(2):
            try:
                async with _aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=timeout_obj) as resp:
                        if resp.status != 200:
                            text = await resp.text()
                            logger.warning("[EnkaHSR] HTTP %d for uid=%s: %s", resp.status, uid, text[:300])
                            return {}
                        data = await resp.json()
                        logger.info("[EnkaHSR] success uid=%s", uid)
                        return data
            except asyncio.TimeoutError:
                logger.warning("[EnkaHSR] timeout uid=%s attempt=%d", uid, attempt + 1)
                if attempt == 1:
                    return {}
            except Exception as ex:
                logger.warning("[EnkaHSR] error uid=%s attempt=%d: %s", uid, attempt + 1, ex)
                if attempt == 1:
                    return {}

    def _response(self, data: dict[str, Any]) -> dict[str, Any] | None:
        detail_info = data.get("detailInfo")
        if not detail_info:
            return None
        avatars: dict[str, Any] = {}
        ac = detail_info.get("assistAvatarDetail")
        if ac and not isinstance(ac, list):
            avatars[str(ac.get("AvatarID", ac.get("avatarId", "")))] = ac
        for ds in detail_info.get("avatarDetailList", []):
            avatars[str(ds.get("avatarId", ""))] = ds
        if not avatars:
            return None
        detail_info["avatars"] = avatars
        return detail_info

    def update_player(self, player: Any, data: dict[str, Any]) -> None:
        try:
            detail_info = self._response(data)
            if not detail_info:
                return
            hsr_data = _HomoData()
            player.set_basic_data({
                "name": detail_info.get("nickname", ""),
                "face": detail_info.get("headIcon", 0),
                "level": detail_info.get("level", 0),
                "sign": detail_info.get("signature", ""),
            })
            for avatar_id_str, ds in detail_info.get("avatars", {}).items():
                ds_to_process = ds
                avatar_id = ds.get("avatarId", 0)
                enhanced_id = ds.get("enhancedId", 0)
                if enhanced_id == 1 and avatar_id in Character.ENHANCED_CHAR_IDS:
                    ds_to_process = copy.deepcopy(ds)
                    new_id = int("2" + str(avatar_id)[1:])
                    ds_to_process["avatarId"] = new_id
                    skill_list = ds_to_process.get("skillTreeList", [])
                    for skill in skill_list:
                        old_prefix = "1" + str(avatar_id)
                        new_prefix = str(new_id)
                        sid_str = str(skill.get("pointId", ""))
                        if sid_str.startswith(old_prefix):
                            skill["pointId"] = int(sid_str.replace(old_prefix, new_prefix, 1))
                avatar = hsr_data.set_avatar(player, ds_to_process)
                if avatar:
                    player._update.append(ds_to_process.get("avatarId", 0))
        except Exception:
            logger.error("[EnkaHSR] update_player error", exc_info=True)

    def cd_time(self, data: dict[str, Any]) -> int:
        return data.get("ttl", 60)


class _HomoData:
    def set_avatar(self, player: Any, data: dict[str, Any]) -> Any:
        avatar_id = data.get("avatarId", 0)
        char = Character.get(avatar_id, "sr")
        if not char:
            return None
        avatar = player.get_avatar(char.id, create=True)
        set_data: dict[str, Any] = {
            "level": data.get("level", 1),
            "promote": data.get("promotion", 0),
            "cons": data.get("rank", 0),
            "weapon": self._get_weapon(data.get("equipment", {})),
        }
        talent_data = self._get_talent(data.get("skillTreeList", []), char)
        set_data.update(talent_data)
        set_data["artis"] = self._get_artis(data.get("relicList", []))
        avatar.set_avatar(set_data, "EnkaHSR")
        return avatar

    def _get_weapon(self, equipment: dict[str, Any]) -> dict[str, Any]:
        if not equipment:
            return {}
        return {
            "id": equipment.get("tid", 0),
            "level": equipment.get("level", 1),
            "promote": equipment.get("promotion", 0),
            "affix": equipment.get("rank", 1),
        }

    def _get_talent(self, skill_tree: list[dict[str, Any]], char: Any) -> dict[str, Any]:
        talent: dict[str, Any] = {}
        trees: list[int] = []
        for d in skill_tree:
            pid = d.get("pointId", 0)
            key = char.get_talent_key(pid)
            if key:
                talent[key] = {"level": d.get("level", 1), "original": d.get("level", 1)}
            else:
                trees.append(pid)
        return {"talent": talent, "trees": trees}

    def _get_artis(self, relics: list[dict[str, Any]]) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for ds in relics:
            sub_list = ds.get("subAffixList", [])
            attr_ids = []
            for s in sub_list:
                aid = s.get("affixId")
                if not aid:
                    continue
                attr_ids.append(f"{aid},{s.get('cnt', 0)},{s.get('step', 0)}")
            ret[str(ds.get("type", ""))] = {
                "id": ds.get("tid", 0),
                "level": ds.get("level", 0),
                "mainId": ds.get("mainAffixId", 0),
                "attrIds": attr_ids,
            }
        return ret


enka_hsr_api = EnkaHSRApi()
