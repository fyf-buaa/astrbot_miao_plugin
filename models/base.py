from __future__ import annotations

from typing import Any


class Base:
    _cache_pool: dict[str, Any] = {}

    def _get_cache(self, key: str) -> Any:
        return self._cache_pool.get(key)

    def _cache(self, ttl: int = 0) -> Any:
        return self

    def get_data(self, keys: str = "") -> dict[str, Any]:
        ret: dict[str, Any] = {}
        if not keys:
            return ret
        for k in keys.split(","):
            k = k.strip()
            if hasattr(self, k):
                ret[k] = getattr(self, k)
        return ret

    @property
    def is_gs(self) -> bool:
        return getattr(self, "game", "gs") == "gs"

    @property
    def is_sr(self) -> bool:
        return getattr(self, "game", "gs") == "sr"
