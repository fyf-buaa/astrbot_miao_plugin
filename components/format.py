from __future__ import annotations

from typing import Any

_ELEM_MAP: dict[str, str] = {
    "风": "anemo", "风元素": "anemo",
    "火": "pyro", "火元素": "pyro",
    "雷": "electro", "雷元素": "electro",
    "水": "hydro", "水元素": "hydro",
    "冰": "cryo", "冰元素": "cryo",
    "草": "dendro", "草元素": "dendro",
    "岩": "geo", "岩元素": "geo",
    "物": "phys", "物理": "phys",
    "anemo": "anemo", "pyro": "pyro", "electro": "electro",
    "hydro": "hydro", "cryo": "cryo", "dendro": "dendro", "geo": "geo",
    "phys": "phys", "physical": "phys",
}


class Format:
    @staticmethod
    def elem(val: str, default: str = "", game: str = "gs") -> str:
        return _ELEM_MAP.get(val, default)

    @staticmethod
    def elem_name(elem: str) -> str:
        rev = {v: k for k, v in _ELEM_MAP.items()}
        return rev.get(elem, elem)

    @staticmethod
    def comma(val: Any, decimals: int = 0) -> str:
        try:
            f = float(val)
            return f"{f:,.{decimals}f}"
        except (ValueError, TypeError):
            return str(val)

    @staticmethod
    def is_elem(key: str, game: str = "gs") -> bool:
        return key in ("anemo", "pyro", "electro", "hydro", "cryo", "dendro", "geo", "phys")

    @staticmethod
    def same_elem(a: str, b: str, game: str = "gs") -> bool:
        return Format.elem(a) == Format.elem(b)

    @staticmethod
    def each_elem(data: dict[str, Any], game: str = "gs") -> dict[str, Any]:
        return data
