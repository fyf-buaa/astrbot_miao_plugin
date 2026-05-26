from __future__ import annotations

import asyncio
from typing import Any, Callable


class _MetaData:
    def __init__(self, game: str = "gs", typ: str = "") -> None:
        self.game = game
        self.type = typ
        self.data: dict[str, Any] = {}
        self.alias: dict[str, str] = {}
        self.alias2: dict[str, str] = {}
        self.cfg: dict[str, Any] = {}
        self.alias_fn: Callable | None = None

    def add_data(self, datas: dict[str, Any], pk: str = "id") -> None:
        for _id, ds in datas.items():
            _id = str(ds.get(pk, _id))
            self.data[_id] = ds
            name = ds.get("name")
            if name and name != _id:
                self.alias[name] = _id

    def add_data_item(self, _id: str, ds: dict[str, Any]) -> None:
        self.data[_id] = ds
        self.alias[_id] = _id
        name = ds.get("name")
        if name:
            self.alias[name] = _id

    def add_abbr(self, ds: dict[str, str]) -> None:
        for txt, _id in ds.items():
            _id = self.alias.get(_id, self.alias2.get(_id, _id))
            self.alias[txt.lower()] = _id
            entry = self.data.get(_id)
            if entry:
                entry["abbr"] = txt

    def add_alias(self, ds: dict[str, str], is_private: bool = False) -> None:
        target = self.alias2 if is_private else self.alias
        for _id, txt in ds.items():
            for t in txt.split(","):
                t = t.strip().lower()
                if not t:
                    continue
                resolved = self.alias.get(_id, self.alias2.get(_id, _id))
                if resolved and resolved.isdigit():
                    target[t] = resolved
                elif t in target and target[t].isdigit():
                    pass
                else:
                    target[t] = resolved

    def add_alias_fn(self, fn: Callable | None) -> None:
        if fn:
            self.alias_fn = fn

    def add_meta(self, cfg_map: dict[str, Any]) -> None:
        self.cfg.update(cfg_map)

    def get_id(self, txt: str) -> str | bool:
        txt = str(txt).strip().lower()
        if txt in self.data:
            return txt
        if txt in self.alias or txt in self.alias2:
            _id = self.alias.get(txt, self.alias2.get(txt, False))
            if _id in self.data:
                return _id
            if _id in self.alias:
                return self.alias[_id]
            if _id in self.alias2:
                return self.alias2[_id]
            return False
        if self.alias_fn:
            _id = self.alias_fn(txt)
            if _id in self.alias or _id in self.alias2:
                real = self.alias.get(_id, self.alias2.get(_id, False))
                if real in self.data:
                    return real
                if real in self.alias:
                    return self.alias[real]
                return real if real else False
        return False

    def get_data(self, txt: str | int) -> Any:
        _id = self.get_id(txt)
        if _id:
            data = self.data.get(_id)
            if data:
                return data
            if _id in self.alias or _id in self.alias2:
                real = self.alias.get(_id, self.alias2.get(_id, ""))
                if real in self.data:
                    return self.data[real]
        return None

    def get_meta(self, key: str = "") -> Any:
        if not key:
            return self.cfg
        return self.cfg.get(key)

    def get_ids(self) -> list[str]:
        return list(self.data.keys())

    def get_alias(self) -> list[str]:
        return list(self.alias.keys())

    async def for_each(self, fn: Callable) -> None:
        for _id, ds in self.data.items():
            ret = fn(ds, _id)
            if asyncio.iscoroutine(ret):
                ret = await ret
            if ret is False:
                break


_meta_store: dict[str, _MetaData] = {}
_meta_loaded: bool = False


def _ensure_meta_loaded() -> None:
    global _meta_loaded
    if not _meta_loaded:
        _meta_loaded = True
        from ..models._meta_loader import load_all_meta
        load_all_meta()


class Meta:
    @staticmethod
    def create(game: str = "gs", typ: str = "") -> _MetaData:
        _ensure_meta_loaded()
        key = f"{game}.{typ}"
        if key not in _meta_store:
            _meta_store[key] = _MetaData(game, typ)
        return _meta_store[key]

    @staticmethod
    def add_alias_fn(game: str, typ: str, fn: Callable) -> None:
        Meta.create(game, typ).add_alias_fn(fn)

    @staticmethod
    def get_id(game: str, typ: str, txt: str = "") -> str | bool:
        return Meta.create(game, typ).get_id(txt)

    @staticmethod
    def get_ids(game: str, typ: str) -> list[str]:
        return Meta.create(game, typ).get_ids()

    @staticmethod
    def get_data(game: str, typ: str, txt: str = "") -> Any:
        return Meta.create(game, typ).get_data(txt)

    @staticmethod
    def get_meta(game: str, typ: str, key: str = "") -> Any:
        return Meta.create(game, typ).get_meta(key)

    @staticmethod
    def get_alias(game: str, typ: str) -> list[str]:
        return Meta.create(game, typ).get_alias()

    @staticmethod
    async def for_each(game: str, typ: str, fn: Callable) -> None:
        await Meta.create(game, typ).for_each(fn)

    @staticmethod
    def match_game(game: str, typ: str, txt: str) -> dict | bool:
        txt = txt.strip().lower()
        games = ["gs", "sr"] if (not game or game == "gs") else ["sr", "gs"]
        for g in games:
            _id = Meta.get_id(g, typ, txt)
            if _id:
                data = Meta.get_data(g, typ, _id)
                return {"game": g, "id": _id, "data": data}
        return False
