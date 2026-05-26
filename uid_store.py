from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class UIDStore:
    """JSON-based persistent UID binding store.

    Thread-safe via ``asyncio.Lock``.  Data is lazy-loaded on first access,
    cached in memory, and written to disk on every mutation.
    """

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_path = self._data_dir / "uid_bindings.json"
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] | None = None

    # ── private helpers ──────────────────────────────────────────────

    async def _load(self) -> dict[str, Any]:
        """Lazy-load the JSON file into ``self._data``."""
        if self._data is not None:
            return self._data

        if self._data_path.exists():
            try:
                with open(self._data_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("uid_store: failed to load %s, resetting – %s", self._data_path, exc)
                self._data = {"users": {}}
        else:
            self._data = {"users": {}}

        assert self._data is not None
        return self._data

    async def _save(self) -> None:
        """Atomically write ``self._data`` to disk (tmp + replace)."""
        if self._data is None:
            return
        self._data_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._data_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        tmp.replace(self._data_path)

    def _ensure_user(self, qq: str) -> dict[str, Any]:
        """Return the user entry dict, creating it with defaults if absent."""
        assert self._data is not None
        users = self._data.setdefault("users", {})
        if qq not in users:
            users[qq] = {"gs_main": "", "gs_list": [], "sr": "", "zzz": "", "default_game": ""}
        user = users[qq]
        user.setdefault("gs_main", "")
        user.setdefault("gs_list", [])
        user.setdefault("sr", "")
        user.setdefault("zzz", "")
        user.setdefault("default_game", "")
        return user

    # ── public API ───────────────────────────────────────────────────

    async def get_uid_map(self, qq: str) -> dict[str, Any]:
        """Return the full UID map for a user.

        Shape: ``{"gs_main": str, "gs_list": list[str], "sr": str, "zzz": str}``
        """
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)
            result: dict[str, Any] = {
                "gs_main": user.get("gs_main", ""),
                "gs_list": list(user.get("gs_list", [])),
                "sr": user.get("sr", ""),
                "zzz": user.get("zzz", ""),
            }
            if not result["gs_main"] and result["gs_list"]:
                result["gs_main"] = result["gs_list"][0]
            return result

    async def set_uid(self, qq: str, game: str, uid: str) -> None:
        """Bind *uid* for *game* under *qq*.

        For ``gs`` the UID is appended to the list and promoted to main.
        For ``sr`` / ``zzz`` the single-UID field is overwritten.
        """
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)

            if game == "gs":
                gs_list = user.setdefault("gs_list", [])
                if uid not in gs_list:
                    gs_list.append(uid)
                user["gs_main"] = uid
            elif game == "sr":
                user["sr"] = uid
            elif game == "zzz":
                user["zzz"] = uid
            else:
                logger.warning("uid_store: unknown game '%s'", game)
                return

            await self._save()
            logger.debug("set_uid qq=%s game=%s uid=%s", qq, game, uid)

    async def get_uid(self, qq: str, game: str) -> str:
        """Return the current UID for *game*, or ``""`` if absent."""
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)

            if game == "gs":
                uid = user.get("gs_main", "")
                if not uid and user.get("gs_list"):
                    uid = user["gs_list"][0]
            elif game == "sr":
                uid = user.get("sr", "")
            elif game == "zzz":
                uid = user.get("zzz", "")
            else:
                uid = ""

            return uid

    async def delete_uid(self, qq: str, game: str) -> None:
        """Remove the binding for *game*.

        For ``gs`` the UID is removed from the list; if it was the main,
        the next available UID in the list becomes main.
        """
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)

            if game == "gs":
                removed = user.get("gs_main", "")
                user["gs_main"] = ""
                gs_list = user.get("gs_list", [])
                if removed in gs_list:
                    gs_list.remove(removed)
                if gs_list:
                    user["gs_main"] = gs_list[0]
            elif game == "sr":
                user["sr"] = ""
            elif game == "zzz":
                user["zzz"] = ""
            else:
                return

            await self._save()
            logger.debug("delete_uid qq=%s game=%s", qq, game)

    async def set_default_game(self, qq: str, game: str) -> None:
        """Persist the default-game preference for *qq*."""
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)
            user["default_game"] = game
            await self._save()
            logger.debug("set_default_game qq=%s game=%s", qq, game)

    async def get_default_game(self, qq: str) -> str:
        """Return the default game for *qq*, or ``""``."""
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)
            return user.get("default_game", "")

    async def get_gs_uids(self, qq: str) -> list[str]:
        """Return all Genshin Impact UIDs bound to *qq*."""
        async with self._lock:
            await self._load()
            user = self._ensure_user(qq)
            return list(user.get("gs_list", []))

    async def find_qq(self, uid: str) -> str | None:
        """Reverse-lookup the user who owns *uid*, or ``None``."""
        async with self._lock:
            await self._load()
            data = self._data or {}
            users = data.get("users", {})
            for qq, user in users.items():
                if user.get("gs_main") == uid:
                    return qq
                if uid in user.get("gs_list", []):
                    return qq
                if user.get("sr") == uid:
                    return qq
                if user.get("zzz") == uid:
                    return qq
            return None
