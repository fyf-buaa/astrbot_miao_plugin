from __future__ import annotations

import re
from typing import Any

from ...components.format import Format

_BASE_ATTR_GS = ["atk", "def", "hp", "mastery", "recharge", "cpct", "cdmg", "dmg", "phy", "heal", "shield", "coloringDmg"]
_BASE_ATTR_SR = ["atk", "def", "hp", "speed", "recharge", "cpct", "cdmg", "dmg", "heal", "stance", "effPct", "effDef", "joy"]


def _base_attrs(game: str = "gs") -> list[str]:
    return _BASE_ATTR_GS if game == "gs" else _BASE_ATTR_SR


def _attr_reg(game: str = "gs") -> re.Pattern:
    keys = "|".join(_base_attrs(game))
    return re.compile(rf"^({keys})(Base|Plus|Pct|Inc)$")


class AttrData:
    def __init__(self, char: Any, data: dict[str, float] | None = None) -> None:
        self.game = getattr(char, "game", "gs")
        self._attr: dict[str, dict[str, float]] = {}
        self._base: dict[str, float] = {}
        self._init(data)

    def _init(self, data: dict[str, float] | None = None) -> None:
        for key in _base_attrs(self.game):
            self._attr[key] = {"base": 0.0, "plus": 0.0, "pct": 0.0}
            self._base[key] = 0.0
        if data:
            self.set_attr(data, True)

    def _get(self, key: str) -> float:
        if key in _base_attrs(self.game):
            a = self._attr[key]
            return a["base"] * (1 + a["pct"] / 100) + a["plus"]
        m = _attr_reg(self.game).match(key)
        if m:
            k = m.group(1)
            k2 = m.group(2).lower()
            return self._attr.get(k, {}).get(k2, 0.0)
        return 0.0

    def add_attr(self, key: str, val: float, is_base: bool = False) -> bool:
        attr = self._attr
        base = self._base

        if self.game == "sr" and Format.is_elem(key, self.game):
            if Format.same_elem(getattr(self, "elem", ""), key, self.game):
                key = "dmg"

        if key in _base_attrs(self.game):
            attr[key]["plus"] += val
            if is_base:
                base[key] = base.get(key, 0) + val
            return True

        m = _attr_reg(self.game).match(key)
        if m:
            k = m.group(1)
            k2 = m.group(2).lower()
            attr[k][k2] = attr[k].get(k2, 0) + val
            if k2 == "base" or is_base:
                base[k] = base.get(k, 0) + val
            return True
        return False

    def set_attr(self, data: dict[str, float], with_base: bool = False) -> None:
        if with_base:
            for key in ["hp", "def", "atk", "speed"]:
                base_key = f"{key}Base"
                if key in data and base_key in data:
                    data[f"{key}Plus"] = data[key] - data[base_key]
                    del data[key]
        for key, val in data.items():
            if self.game == "sr" and Format.is_elem(key, self.game):
                if getattr(self, "elem", "") == Format.elem(key, "", self.game):
                    self.add_attr("dmg", val)
            else:
                self.add_attr(key, float(val))

    def get_attr(self) -> dict[str, Any]:
        ret: dict[str, Any] = {}
        for key in _base_attrs(self.game):
            ret[key] = self._get(key)
            if key in ("hp", "atk", "def", "speed"):
                ret[f"{key}Base"] = self._get(f"{key}Base")
        ret["_calc"] = True
        ret["staticAttr"] = self._attr
        return ret

    def get_base(self) -> dict[str, float]:
        return self._base

    @staticmethod
    def create(char: Any, data: dict[str, float] | None = None) -> "AttrData":
        return AttrData(char, data)
