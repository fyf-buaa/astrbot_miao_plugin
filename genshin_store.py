"""JSON-based persistent storage for genshin plugin data (replaces SQLite store).

Stores per-user data (aliases, notes, ledger cache, cookie) in a single
``{data_dir}/genshin/users.json`` file.

UID bindings are managed by :class:`UIDStore` (``uid_bindings.json``).
This store also directly reads/writes that file for index-based operations
not exposed by the UIDStore API (e.g. ``delete_uid_by_index``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from .uid_store import UIDStore

logger = logging.getLogger("astrbot_plugin_miao.genshin_store")


def _default_user() -> dict[str, Any]:
    return {
        "ck": "",
        "aliases": {},
        "notes": [],
        "ledger_cache": {},
    }


class GenshinStore:
    """JSON-backed store for plugin-specific per-user metadata.

    Args:
        data_dir: Root data directory (same as passed to ``UIDStore``).
        uid_store: Shared ``UIDStore`` instance for UID lookups.
    """

    def __init__(self, data_dir: str, uid_store: UIDStore) -> None:
        self._base_dir = Path(data_dir)
        self._store_dir = self._base_dir / "genshin"
        self._users_path = self._store_dir / "users.json"
        self._uid_bindings_path = self._base_dir / "uid_bindings.json"
        self._uid_store = uid_store
        self._lock = asyncio.Lock()
        self._cache: dict[str, dict[str, Any]] | None = None

    # ── Internal helpers ─────────────────────────────────────────────

    async def _load(self) -> dict[str, dict[str, Any]]:
        if self._cache is not None:
            return self._cache
        self._store_dir.mkdir(parents=True, exist_ok=True)
        if self._users_path.exists():
            try:
                loaded = json.loads(self._users_path.read_text(encoding="utf-8"))
                self._cache = {} if not isinstance(loaded, dict) else loaded
            except (json.JSONDecodeError, OSError):
                logger.warning("genshin_store: corrupted users.json, resetting")
                self._cache = {}
        else:
            self._cache = {}
        return self._cache

    async def _save(self) -> None:
        if self._cache is None:
            return
        self._store_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._users_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._cache, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._users_path)

    def _ensure_user(self, qq: str) -> dict[str, Any]:
        assert self._cache is not None
        if qq not in self._cache:
            self._cache[qq] = _default_user()
        return self._cache[qq]

    async def _read_uid_bindings(self) -> dict[str, Any]:
        """Read raw ``uid_bindings.json`` (shared with UIDStore)."""
        if self._uid_bindings_path.exists():
            try:
                return json.loads(self._uid_bindings_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {"users": {}}

    async def _write_uid_bindings(self, data: dict[str, Any]) -> None:
        """Write to ``uid_bindings.json`` atomically."""
        self._base_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._uid_bindings_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._uid_bindings_path)

    # ── Per-user data ───────────────────────────────────────────────

    async def get_user(self, qq: str | int) -> dict[str, Any]:
        """Return per-user data dict enriched with current UID map."""
        async with self._lock:
            await self._load()
            qq_str = str(qq)
            user = self._ensure_user(qq_str)
            uid_map = await self._uid_store.get_uid_map(qq_str)
            user["uids"] = uid_map.get("gs_list", [])
            user["main_uid"] = uid_map.get("gs_main", "")
            return dict(user)

    async def set_aliases(self, qq: str | int, role_id: str, aliases: list[str]) -> None:
        """Append aliases to a character's alias list for a user."""
        async with self._lock:
            await self._load()
            qq_str = str(qq)
            user = self._ensure_user(qq_str)
            existing = user.setdefault("aliases", {}).setdefault(role_id, [])
            for a in aliases:
                if a not in existing:
                    existing.append(a)
            await self._save()

    async def delete_alias(self, qq: str | int, role_id: str, alias: str) -> bool:
        """Remove a single alias. Returns ``False`` if not found."""
        async with self._lock:
            await self._load()
            qq_str = str(qq)
            user = self._ensure_user(qq_str)
            aliases = user.setdefault("aliases", {}).get(role_id, [])
            if alias not in aliases:
                return False
            aliases.remove(alias)
            await self._save()
            return True

    async def get_aliases(self, qq: str | int, role_id: str) -> list[str]:
        """Return alias list for a character (empty list if none)."""
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            return list(user.get("aliases", {}).get(role_id, []))

    async def add_note(self, qq: str | int, note: str) -> None:
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            user.setdefault("notes", []).append(note)
            await self._save()

    async def set_ck(self, qq: str | int, ck: str) -> None:
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            user["ck"] = ck
            await self._save()

    async def delete_ck(self, qq: str | int) -> None:
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            user["ck"] = ""
            await self._save()

    async def set_ledger_cache(
        self, qq: str | int, game: str, data: dict[str, Any], month: int = 0
    ) -> None:
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            cache = user.setdefault("ledger_cache", {})
            cache.setdefault(game, {})[str(month)] = data
            await self._save()

    async def get_ledger_cache(self, qq: str | int, game: str) -> dict[str, Any]:
        async with self._lock:
            await self._load()
            user = self._ensure_user(str(qq))
            return dict(user.get("ledger_cache", {}).get(game, {}))

    # ── UID list index-based operations ─────────────────────────────

    async def delete_uid_by_index(self, qq: str | int, index: int) -> bool:
        """Remove the *index*-th Genshin UID (1-based) from the user's list.

        Returns ``False`` if the index is out of range.
        """
        async with self._lock:
            bindings = await self._read_uid_bindings()
            qq_str = str(qq)
            user = bindings.setdefault("users", {}).get(qq_str)
            if not user:
                return False
            gs_list = user.get("gs_list", [])
            if index < 1 or index > len(gs_list):
                return False
            removed = gs_list.pop(index - 1)
            if user.get("gs_main") == removed:
                user["gs_main"] = gs_list[0] if gs_list else ""
            await self._write_uid_bindings(bindings)
            return True

    async def toggle_main_uid(self, qq: str | int, index: int) -> bool:
        """Set the *index*-th Genshin UID (1-based) as the main UID.

        Returns ``False`` if the index is out of range.
        """
        async with self._lock:
            bindings = await self._read_uid_bindings()
            qq_str = str(qq)
            user = bindings.setdefault("users", {}).get(qq_str)
            if not user:
                return False
            gs_list = user.get("gs_list", [])
            if index < 1 or index > len(gs_list):
                return False
            user["gs_main"] = gs_list[index - 1]
            await self._write_uid_bindings(bindings)
            return True

    # ── Utility ──────────────────────────────────────────────────────

    async def user_count(self) -> int:
        async with self._lock:
            await self._load()
            return len(self._cache) if self._cache else 0

    async def all_users(self) -> dict[str, dict[str, Any]]:
        async with self._lock:
            await self._load()
            return dict(self._cache) if self._cache else {}
