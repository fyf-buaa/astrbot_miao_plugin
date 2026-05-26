from __future__ import annotations

from typing import Any


def _eval_buff_data(profile: Any, buff_data: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, val in buff_data.items():
        if isinstance(val, (int, float)):
            result[key] = float(val)
        elif isinstance(val, str):
            try:
                result[key] = float(val)
            except (ValueError, TypeError):
                pass
        elif isinstance(val, dict):
            result[key] = 0.0
    return result


def get_buffs(profile: Any, buffs: list[dict[str, Any]] | None, game: str = "gs") -> list[dict[str, Any]]:
    if not buffs:
        return []
    cons = getattr(profile, "cons", 0)
    result: list[dict[str, Any]] = []
    for b in buffs:
        entry = dict(b)
        check_val = entry.get("check")
        if check_val is not None:
            if isinstance(check_val, (int, float)):
                if cons < check_val:
                    continue
        data = entry.get("data", {})
        entry["_values"] = _eval_buff_data(profile, data)
        result.append(entry)
    result.sort(key=lambda x: x.get("sort", 999))
    return result
