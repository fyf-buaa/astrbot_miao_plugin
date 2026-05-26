from __future__ import annotations

from typing import Any

from ..components.meta import Meta
from .base import Base


class Weapon(Base):
    def __init__(self, meta: dict[str, Any], game: str = "gs") -> None:
        self.id = meta.get("id", "")
        self.name = meta.get("name", "")
        self.meta = meta
        self.type = meta.get("type", "")
        self.star = int(meta.get("star", 4))
        self.game = game
        self._detail: dict[str, Any] = {}

    @property
    def img(self) -> str:
        return f"{'meta-gs' if self.is_gs else 'meta-sr'}/weapon/{self.type}/{self.name}/icon.webp"

    @property
    def abbr(self) -> str:
        name = self.name
        abbr = self.meta.get("abbr", "")
        return name if len(name) <= 4 else (abbr or name)

    @property
    def detail(self) -> dict[str, Any]:
        return self.get_detail()

    def get_detail(self) -> dict[str, Any]:
        if self._detail:
            return self._detail
        from ..components.data import Data
        path = f"resources/meta-gs/weapon/{self.type}/{self.name}/data.json" if self.is_gs else f"resources/meta-sr/weapon/{self.type}/{self.name}/data.json"
        self._detail = Data.read_json(path, "miao") or {}
        return self._detail

    def calc_attr(self, level: int, promote: int = -1) -> dict[str, float]:
        detail = self.get_detail()
        if not detail:
            return {}
        if self.is_sr:
            return self._calc_attr_sr(detail, level, promote)
        return self._calc_attr_gs(detail, level, promote)

    def _calc_attr_sr(self, detail: dict[str, Any], level: int, promote: int) -> dict[str, float]:
        attr_data = detail.get("attr", {})
        promote_data = attr_data.get(str(promote), {})
        base_attrs = promote_data.get("attrs", {})
        grow_data = detail.get("growAttr", {})

        result: dict[str, float] = {}
        for stat_key, base_val in base_attrs.items():
            grown = float(base_val) + float(grow_data.get(stat_key, 0)) * (level - 1)
            if stat_key in ("hp", "atk", "def"):
                result[stat_key] = grown
                result[stat_key + "Base"] = grown
            else:
                result[stat_key] = grown
        return result

    def _calc_attr_gs(self, detail: dict[str, Any], level: int, promote: int) -> dict[str, float]:
        attr_data = detail.get("attr", {})
        atk_data = attr_data.get("atk", {})
        bonus_key = attr_data.get("bonusKey", "")
        bonus_data = attr_data.get("bonusData", {})

        def _pick(values: dict[str, float], lv: int, prom: int) -> float:
            key = str(lv)
            plus_key = f"{lv}+"
            if plus_key in values and prom > 0:
                return float(values[plus_key])
            if key in values:
                return float(values[key])
            keys = sorted((int(k.rstrip("+")) for k in values if k.rstrip("+").isdigit()))
            prev_k = 1
            prev_v = float(values.get("1", 0))
            for k in keys:
                if k >= lv:
                    if k == lv:
                        return float(values.get(str(k), prev_v))
                    ratio = (lv - prev_k) / max(k - prev_k, 1)
                    v = float(values.get(str(k), prev_v))
                    return prev_v + (v - prev_v) * ratio
                prev_k = k
                prev_v = float(values.get(str(k), prev_v))
            return prev_v

        base_atk = _pick(atk_data, level, promote)
        bonus_val = _pick(bonus_data, level, promote) if bonus_data else 0.0
        return {"atkBase": base_atk, "bonusKey": bonus_key, "bonusValue": bonus_val}

    @staticmethod
    def get(name: Any, game: str = "gs", typ: str = "") -> "Weapon | bool":
        if isinstance(name, dict):
            name = name.get("name", name.get("id", ""))
        if not name:
            return False
        data = Meta.get_data(game, "weapon", name)
        if data:
            return Weapon(data, game)
        if typ and game == "gs":
            meta = Meta.get_meta(game, "weapon")
            weapon_type = meta.get("weaponType", {})
            name2 = name + weapon_type.get(typ, typ)
            data = Meta.get_data(game, "weapon", name2)
            if data:
                return Weapon(data, game)
        return False
