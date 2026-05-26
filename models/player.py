from __future__ import annotations

from typing import Any

from ..components.data import Data
from .base import Base
from ._avatar_model import Avatar
from ._character_model import Character

_DATA_DIR = "data/PlayerData"


class Player(Base):
    def __init__(self, uid: str, game: str = "gs") -> None:
        self.uid = uid
        self.game = game
        self.name: str = ""
        self.level: int = 0
        self.word: int = 0
        self.face: int = 0
        self.card: int = 0
        self.sign: str = ""
        self._avatars: dict[str, Any] = {}
        self._update: list[Any] = []
        self._profile: Any = None
        self.e: Any = None

    @property
    def _file(self) -> str:
        return f"{_DATA_DIR}/{self.game}/{self.uid}.json"

    @property
    def has_profile(self) -> bool:
        for avatar in self._avatars.values():
            if isinstance(avatar, Avatar) and avatar.is_profile:
                return True
        return False

    def reload(self) -> None:
        data = Data.read_json(self._file, "root")
        self.set_basic_data(data)
        self._avatars = {}
        if data.get("avatars"):
            for avatar_id, avatar_data in data["avatars"].items():
                self._avatars[avatar_id] = avatar_data
        import logging
        logging.info("[player] reload uid=%s game=%s avatars=%d file=%s",
                     self.uid, self.game, len(self._avatars), self._file)

    def save(self) -> None:
        ret: dict[str, Any] = {
            "uid": self.uid,
            "name": self.name,
            "level": self.level,
            "word": self.word,
            "face": self.face,
            "card": self.card,
            "sign": self.sign,
            "avatars": {},
        }
        for avatar_id, avatar in self._avatars.items():
            if isinstance(avatar, Avatar):
                av: dict[str, Any] = {
                    "id": avatar.id,
                    "name": avatar.name,
                    "elem": avatar.elem,
                    "level": avatar.level,
                    "promote": getattr(avatar, "promote", 0),
                    "cons": avatar.cons,
                    "fetter": avatar.fetter,
                    "costume": avatar.costume,
                    "talent": avatar.talent,
                    "weapon": {
                        "id": avatar.weapon.get("id", ""),
                        "level": avatar.weapon.get("level", 1),
                        "promote": avatar.weapon.get("promote", 0),
                        "affix": avatar.weapon.get("affix", 1),
                    },
                    "artis": {},
                    "_source": getattr(avatar, "_source", ""),
                    "_time": getattr(avatar, "_time", 0),
                    "_update": getattr(avatar, "_update", 0),
                }
                if avatar.game == "sr":
                    av["trees"] = getattr(avatar, "_trees", [])
                    if avatar.weapon.get("name"):
                        av["weapon"]["name"] = avatar.weapon.get("name", "")
                else:
                    if avatar.weapon.get("name"):
                        av["weapon"]["name"] = avatar.weapon.get("name", "")
                raw_artis = getattr(avatar._artis, "_data", {}) if hasattr(avatar, "_artis") else {}
                for idx_str, piece in raw_artis.items():
                    av["artis"][idx_str] = {
                        "id": piece.get("id", ""),
                        "name": piece.get("name", ""),
                        "level": piece.get("level", 0),
                        "star": piece.get("star", 5),
                        "mainId": piece.get("mainId", 0),
                        "attrIds": piece.get("attrIds", []),
                        "type": piece.get("type", 0),
                    }
                ret["avatars"][avatar_id] = av
            else:
                ret["avatars"][avatar_id] = avatar
        Data.write_json(self._file, ret, "root")

    def set_basic_data(self, ds: dict[str, Any]) -> None:
        self.name = ds.get("name", self.name or "")
        self.level = ds.get("level", self.level or 0)
        self.word = ds.get("word", self.word or 0)
        self.face = ds.get("face", self.face or 0)
        self.card = ds.get("card", self.card or 0)
        self.sign = ds.get("sign", self.sign or "")
        self._profile = ds.get("_profile", self._profile)

    def get_avatar(self, avatar_id: int | str, create: bool = False) -> Avatar | None:
        sid = str(avatar_id)
        import logging
        logging.info("[player] get_avatar sid=%s game=%s avatars_keys=%s", sid, self.game, list(self._avatars.keys()))
        char = Character.get(sid, self.game)
        if not char:
            logging.warning("[player] get_avatar char not found for sid=%s game=%s", sid, self.game)
            return None

        if self.game == "gs" and hasattr(char, "_is_traveler") and char._is_traveler() and not create:
            sid = "10000005" if "10000005" in self._avatars else "10000007"

        if sid not in self._avatars:
            if create:
                self._avatars[sid] = Avatar({"id": sid}, self.game)
            else:
                return None

        avatar = self._avatars[sid]
        if not isinstance(avatar, Avatar):
            data = avatar
            avatar = Avatar(data, self.game)
            avatar.set_avatar(data)
            self._avatars[sid] = avatar
        return avatar

    def for_each_avatar(self, fn) -> None:
        for avatar_id in list(self._avatars.keys()):
            avatar = self.get_avatar(avatar_id)
            if avatar and avatar.has_data and avatar.game == self.game:
                if fn(avatar, avatar_id) is False:
                    break

    def get_avatar_data(self, ids: list[str] | None = None) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if ids:
            for _id in ids:
                avatar = self.get_avatar(_id)
                if avatar:
                    ret[_id] = avatar.get_detail()
        else:
            self.for_each_avatar(lambda a, _id: ret.update({_id: a.get_detail()}))
        return ret

    async def refresh_profile(self, force: int = 2, from_mys: bool = False) -> int:
        from .serv.serv import req
        result = await req(self.e, self, from_mys)
        if result is False or result is None:
            return 0
        return int(result)

    @staticmethod
    def create(val: Any, game: str = "gs") -> "Player":
        if hasattr(val, "uid"):
            uid = str(val.uid) if val.uid else ""
            e = val
            if hasattr(val, "_uid_map"):
                umap = val._uid_map
                if game == "sr":
                    uid = umap.get("sr", "") or ""
                elif game == "zzz":
                    uid = umap.get("zzz", "") or ""
                elif not uid:
                    uid = umap.get("gs_main", "") or ""
                    if not uid and umap.get("gs_list"):
                        uid = umap.get("gs_list", [""])[0]
            elif not uid and hasattr(val, "_mys") and val._mys and val._mys.get("uid"):
                uid = val._mys["uid"]
            player = Player(str(uid) if uid else "", game if game else ("sr" if getattr(val, "isSr", False) else "gs"))
            player.e = e
            player.reload()
        else:
            player = Player(str(val), game)
            player.reload()
        return player

    @staticmethod
    def del_by_uid(uid: str, game: str = "gs") -> None:
        Data.del_file(f"{_DATA_DIR}/{game}/{uid}.json", "root")
