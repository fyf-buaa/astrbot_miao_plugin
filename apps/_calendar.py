from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from ..adapter import MiaoEvent
from ..components.common import render
from ..components.meta import Meta


def _get_birthday_data() -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for _id in Meta.get_ids("gs", "char"):
        data = Meta.get_data("gs", "char", _id)
        if not data:
            continue
        birth = data.get("birth", "")
        if not birth or "-" not in str(birth):
            continue
        parts = str(birth).split("-")
        key = f"{int(parts[0])}-{int(parts[1])}"
        if key not in result:
            result[key] = []
        result[key].append({
            "name": data.get("name", ""),
            "star": data.get("star", 5),
            "face": f"/img/avatar/{data.get('id', '')}.png",
        })
    return result


async def get_calendar(e: MiaoEvent, game: str = "gs") -> bytes:
    """Render calendar page."""
    now = datetime.now()

    date_list: list[dict[str, Any]] = []
    for offset in range(-15, 46):
        d = now + timedelta(days=offset)
        if d.day == 1:
            date_list.append({
                "month": d.month,
                "year": d.year,
                "date": [d.day],
                "week": [d.weekday()],
            })
        elif date_list:
            date_list[-1]["date"].append(d.day)
            date_list[-1]["week"].append(d.weekday())

    birthdays = _get_birthday_data()

    return await render("wiki/calendar", {
        "game": game,
        "dateList": date_list,
        "nowDate": now.day,
        "charBirth": birthdays,
    }, e=e, scale=1.2)
