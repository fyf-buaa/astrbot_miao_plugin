from __future__ import annotations

from typing import Any

from ..components.meta import Meta
from .base import Base


class Artifact(Base):
    def __init__(self, data: dict[str, Any], game: str = "gs") -> None:
        self.game = game
        self.id = data.get("id", "")
        self.name = data.get("name", "")
        self.meta = data

    @property
    def set_name(self) -> str:
        return self.meta.get("set", self.meta.get("name", ""))

    @property
    def idx(self) -> int:
        return int(self.meta.get("idx", 1))

    @property
    def abbr(self) -> str:
        s = ArtifactSet.get(self.set_name, self.game)
        if s:
            return s.meta.get("abbr", self.name[:8])
        return self.name[:8]

    @property
    def img(self) -> str:
        g = "gs" if self.is_gs else "sr"
        if g == "sr":
            idx_map = {1: "0", 2: "1", 3: "2", 4: "3", 5: "4", 6: "4"}
            return f"meta-sr/artifact/{self.set_name}/arti-{idx_map.get(self.idx, '0')}.webp"
        return f"meta-gs/artifact/imgs/{self.set_name}/{self.idx}.webp"

    @staticmethod
    def get(name: Any, game: str = "gs") -> "Artifact | bool":
        if not name:
            return False
        if isinstance(name, dict):
            return Artifact.get(name.get("id") or name.get("name"), name.get("game", game))
        # Try direct arti lookup first (for piece IDs registered from data.json idxs)
        data = Meta.get_data(game, "arti", name)
        if data:
            return Artifact(data, game)
        if game == "gs" and isinstance(name, str) and name.isdigit() and len(name) == 5:
            from .artifact import ArtifactSet
            arti_set = ArtifactSet.get(name)
            if arti_set:
                idx_map = {4: 1, 2: 2, 5: 3, 1: 4, 3: 5}
                idx = idx_map.get(int(name[3]), 1)
                return arti_set.get_arti(idx)
        return False

    @staticmethod
    def get_set_name_by_arti(name: str) -> str:
        arti = Artifact.get(name)
        if arti:
            return arti.set_name
        return ""


class ArtifactSet(Base):
    def __init__(self, data: dict[str, Any], game: str = "gs") -> None:
        self.game = game
        self.meta = data

    @property
    def idxs(self) -> dict[str, str]:
        return self.meta.get("idxs", {})

    @property
    def img(self) -> str:
        arti = Artifact.get(self.idxs.get("1") or self.idxs.get("5"), self.game)
        return arti.img if arti else ""

    def get_arti_name(self, idx: int = 1) -> str:
        return self.idxs.get(str(idx), "")

    def get_arti(self, idx: int = 1) -> Artifact | bool:
        return Artifact.get(self.get_arti_name(idx), self.game)

    @staticmethod
    def get(name: Any, game: str = "gs") -> "ArtifactSet | bool":
        if game == "gs" and isinstance(name, str) and name.isdigit() and len(name) >= 2:
            name = name[:2]
        data = Meta.match_game(game, "artiSet", name)
        if data:
            return ArtifactSet(data["data"], data["game"])
        return False

    @staticmethod
    def get_artis_set_buff(name: str, num: int, game: str = "gs") -> list[dict[str, Any]]:
        arti_buffs = Meta.get_meta(game, "arti", "artiBuffs") or {}
        entry = arti_buffs.get(name, {}).get(str(num))
        if not entry:
            return []
        return entry if isinstance(entry, list) else [entry]
