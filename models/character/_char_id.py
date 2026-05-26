from __future__ import annotations

from ...components.meta import Meta


class _CharId:
    @staticmethod
    def get_id(val: any, game: str = "gs") -> str | bool:
        if isinstance(val, (int, float)):
            return str(int(val))
        if isinstance(val, str) and val.isdigit():
            return val
        data = Meta.get_data(game, "char", val)
        if data:
            return data.get("id", "")
        return False

    @staticmethod
    def is_traveler(_id: str | int) -> bool:
        return str(_id) in ("10000005", "10000007", "20000000")

    @staticmethod
    def is_trailblazer(_id: str | int) -> bool:
        return str(_id).startswith("800")


char_id = _CharId()
