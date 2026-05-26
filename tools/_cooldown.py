from __future__ import annotations

import time
from typing import Any


class CooldownCache:
    """Simple in-memory TTL cooldown cache.

    Usage::

        if CooldownCache.check("my_key", ttl=60):
            ...  # cooldown not active, proceed
        else:
            ...  # still in cooldown

        CooldownCache.clear("my_key")   # force-expire
    """

    _cache: dict[str, float] = {}

    @staticmethod
    def check(key: str, ttl: int = 300) -> bool:
        """Return *True* if *key* is not on cooldown (or TTL expired).

        On first call (or after expiry) the key is set and ``True`` is
        returned so the caller can proceed.  Subsequent calls within
        *ttl* seconds return ``False``.
        """
        now = time.time()
        deadline = CooldownCache._cache.get(key)
        if deadline is None or now >= deadline:
            CooldownCache._cache[key] = now + ttl
            return True
        return False

    @staticmethod
    def clear(key: str) -> None:
        """Remove *key* from the cache (force-expire)."""
        CooldownCache._cache.pop(key, None)
