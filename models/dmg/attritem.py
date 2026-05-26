from __future__ import annotations

from typing import Any


class AttrItem:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.fmt = data.get("format", "pct")
        self.value = data.get("value", 0)
        self.title = data.get("title", self.name)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "format": self.fmt, "value": self.value, "title": self.title}
