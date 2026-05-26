from __future__ import annotations

from typing import Any

from ..components.format import Format
from ..components.meta import Meta
from .base import Base

_META_KEYS = ["id", "name", "abbr", "star", "elem", "weapon", "talentId", "talentElem", "talentCons", "costume", "eta"]


class Character(Base):
    def __init__(self, char_id: int | str, elem: str = "", game: str = "gs") -> None:
        self._id = str(char_id)
        self.game = game
        self.elem = elem
        self.meta: dict[str, Any] = {}
        self._detail: dict[str, Any] = {}
        self._imgs: dict[str, Any] = {}

        if not self.is_custom:
            meta = Meta.get_data(game, "char", self._id) or Meta.get_data(game, "char", str(int(char_id)) if isinstance(char_id, str) else str(char_id)) or {}
            self.meta = meta
            if self.is_gs:
                self.elem = Format.elem(elem or meta.get("elem", ""), "anemo")
        else:
            self.meta = {}

    @property
    def id(self) -> int:
        return int(self._id) if self._id.isdigit() else self._id

    @property
    def is_custom(self) -> bool:
        return not (self.game == "sr" or (isinstance(self.id, int) and 10000000 <= self.id <= 29999999))

    @property
    def is_release(self) -> bool:
        if self.is_custom:
            return False
        eta = self.meta.get("eta")
        if eta:
            from datetime import datetime
            try:
                return float(eta) < datetime.now().timestamp()
            except (ValueError, TypeError):
                pass
        return False

    def _get(self, key: str) -> Any:
        if key in _META_KEYS:
            return self.meta.get(key)
        detail = self.get_detail()
        return detail.get(key)

    @property
    def name(self) -> str:
        return self.meta.get("name", self._id)

    @property
    def abbr(self) -> str:
        return self.meta.get("abbr", "")

    @property
    def star(self) -> int:
        return int(self.meta.get("star", 4))

    @property
    def weapon_type(self) -> str:
        return self.meta.get("weapon", "")

    @property
    def elem_name(self) -> str:
        if self.is_sr:
            return self.elem
        return Format.elem_name(self.elem)

    @property
    def face(self) -> str:
        return self.get_imgs().get("face", "")

    @property
    def side(self) -> str:
        return self.get_imgs().get("side", "")

    @property
    def imgs(self) -> dict[str, Any]:
        return self.get_imgs()

    @property
    def talent_id(self) -> dict[str, Any]:
        return self.meta.get("talentId", {})

    ENHANCED_CHAR_IDS: list[int] = [1212, 1205, 1005, 1006, 1004, 1102, 1217, 1310, 1306, 1307]

    def get_talent_key(self, point_id: int) -> str | bool:
        pid_str = str(point_id)
        if pid_str in self.talent_id:
            return self.talent_id[pid_str]
        if self.is_sr:
            import re
            reg = re.compile(rf"^1?{self._id}")
            suffix = reg.sub("", pid_str)
            mapping = {
                "001": "a", "002": "e", "003": "q", "004": "t",
                "007": "z", "301": "me", "302": "mt", "420": "xe",
            }
            return mapping.get(suffix, False)
        return False

    def get_lv_attr(self, level: int, promote: int) -> dict[str, float]:
        detail = self.get_detail()
        meta_attr = detail.get("attr", {})
        if not meta_attr:
            return {}
        if self.is_sr:
            lv_attr = meta_attr.get(str(promote), {})
            base = lv_attr.get("attrs", {})
            grow = lv_attr.get("grow", {})
            ret: dict[str, float] = {}
            for k, v in base.items():
                ret[k] = float(v) + float(grow.get(k, 0)) * (level - 1)
            return ret
        return {}

    @property
    def talent_cons(self) -> dict[str, int]:
        if self.is_sr:
            return self.meta.get("talentCons", {})
        if self._is_traveler():
            return {"e": 3, "q": 5} if self.elem in ("dendro", "hydro", "pyro") else {"e": 5, "q": 3}
        return self.meta.get("talentCons", {})

    def _is_traveler(self) -> bool:
        return self.is_gs and self._id in ("10000005", "10000007", 10000005, 10000007)

    def check_costume(self, costume_id: int) -> bool:
        costumes = self.meta.get("costume", [])
        return costume_id in costumes

    def check_wife_type(self, wtype: int) -> bool:
        from ..components.meta import Meta
        meta_wife = Meta.get_meta("gs", "char", "wifeData") or {}
        key = ["girlfriend", "boyfriend", "daughter", "son"][wtype] if 0 <= wtype <= 3 else "girlfriend"
        return str(self.id) in (meta_wife.get(key, {}) or {})

    def get_imgs(self, costume: str = "") -> dict[str, Any]:
        cache_id = f"costume{costume}" if costume else "costume0"
        if cache_id not in self._imgs:
            from .character._char_img import get_imgs, get_imgs_sr
            if self.is_sr:
                self._imgs[cache_id] = get_imgs_sr(self.name, self.talent_cons)
            else:
                elem = self.elem if self._is_traveler() else ""
                self._imgs[cache_id] = get_imgs(self.name, costume, elem, self.weapon_type, self.talent_cons)
        return self._imgs.get(cache_id, {})

    def get_detail(self) -> dict[str, Any]:
        if self._detail:
            return self._detail
        if self.is_custom:
            return {}
        from ..components.data import Data
        from ..tools.path import miao_path
        name = f"旅行者/{self.elem}" if self._is_traveler() else self.name
        path = f"resources/meta-{self.game}/character/{name}/data.json"
        self._detail = Data.read_json(path, "miao") or {}
        self.meta["_detail"] = self._detail
        return self._detail

    @staticmethod
    def get(val: Any, game: str = "gs") -> "Character | bool":
        from .character._char_id import char_id as _cid
        if isinstance(val, str):
            import re
            traveler_pat = re.compile(r"旅行者|主角?|空|荧|爷")
            if traveler_pat.search(val) and game == "gs":
                elem = Format.elem(traveler_pat.sub("", val).strip(), "")
                if elem:
                    val = {"id": "20000000", "elem": elem}
                    if isinstance(val, dict):
                        return Character(val["id"], val.get("elem", ""), game)
        if isinstance(val, dict):
            return Character(val.get("id", ""), val.get("elem", ""), val.get("game", game))
        _id = _cid.get_id(val, game)
        if not _id:
            return False
        return Character(_id, game=game)

    def get_data(self, keys: str = "") -> dict[str, Any]:
        base = dict(self.meta)
        detail = self.get_detail()
        base.update(detail)
        return base
