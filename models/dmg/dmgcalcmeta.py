from __future__ import annotations

from typing import Any

from ...components.meta import Meta


def get_dmg_calc_meta(game: str = "gs") -> dict[str, Any]:
    return Meta.get_meta(game, "dmg") or {}


def get_char_dmg_data(char_id: str, game: str = "gs") -> dict[str, Any] | None:
    return Meta.get_data(game, "dmg", char_id)


def get_skill_multiplier(char_id: str, skill_key: str, skill_name: str, talent_level: int, game: str = "gs") -> float:
    data = get_char_dmg_data(char_id, game)
    if not data:
        return 0.0
    multipliers = data.get("multipliers", {})
    skill_tables = multipliers.get(skill_key, [])
    for tbl in skill_tables:
        if tbl["name"] == skill_name:
            values = tbl["values"]
            idx = min(talent_level - 1, len(values) - 1)
            if idx >= 0:
                return values[idx]
    return 0.0


def get_skill_multiplier_indexed(char_id: str, skill_key: str, skill_name: str, talent_level: int, index: int, game: str = "gs") -> float:
    data = get_char_dmg_data(char_id, game)
    if not data:
        return 0.0
    multipliers = data.get("multipliers", {})
    skill_tables = multipliers.get(skill_key, [])
    for tbl in skill_tables:
        if tbl["name"] == skill_name:
            values = tbl.get("values", [])
            if index < len(values):
                return values[index]
            idx = min(talent_level - 1, len(values) - 1)
            if idx >= 0:
                return values[idx]
    return 0.0
