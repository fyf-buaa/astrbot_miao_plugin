from __future__ import annotations

from typing import Any


class Button:
    def __init__(self, e: Any = None) -> None:
        self.prefix = "*" if (e and getattr(e, "isSr", False)) else "#"

    def bind_uid(self) -> list:
        return [{"text": "绑定UID", "input": f"{self.prefix}绑定uid"}]

    def profile(self, char: dict[str, Any] = None, uid: str = "") -> list:
        if not char:
            return []
        name = char.get("name", "")
        return [
            [{"text": f"{name}面板", "input": f"{self.prefix}{name}面板{uid}"}],
        ]
